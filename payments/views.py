import hashlib
import hmac
import json
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from orders.models import Order, OrderStatusHistory
from .models import Payment


def _verify_razorpay_signature(order_id, payment_id, signature, secret):
    try:
        msg = f"{order_id}|{payment_id}"
        expected = hmac.new(
            secret.encode("utf-8"),
            msg.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature or "")
    except Exception:
        return False


def _verify_razorpay_webhook(body, signature, secret):
    try:
        expected = hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature or "")
    except Exception:
        return False


def _verify_stripe_signature(payload, sig_header, secret):
    try:
        import stripe
        stripe.api_key = secret
        event = stripe.Webhook.construct_event(
            payload, sig_header, secret
        )
        return event
    except Exception:
        return None


@login_required
def payment_start(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payment, _ = Payment.objects.get_or_create(
        order=order,
        defaults={
            "gateway": order.payment_method,
            "amount": order.grand_total,
        },
    )

    razorpay_key = getattr(settings, "RAZORPAY_KEY_ID", "")
    stripe_key = getattr(settings, "STRIPE_PUBLISHABLE_KEY", "")
    gateway = order.payment_method

    context = {
        "order": order,
        "payment": payment,
        "razorpay_key": razorpay_key,
        "stripe_key": stripe_key,
        "gateway": gateway,
        "amount_paise": int(order.grand_total * 100),
        "simulation_mode": not (razorpay_key and gateway == "razorpay") and not (stripe_key and gateway == "stripe"),
    }

    if gateway == "razorpay" and razorpay_key:
        try:
            import razorpay
            client = razorpay.Client(auth=(razorpay_key, getattr(settings, "RAZORPAY_KEY_SECRET", "")))
            data = {
                "amount": int(order.grand_total * 100),
                "currency": "INR",
                "receipt": order.order_number,
                "payment_capture": 1,
            }
            rzp_order = client.order.create(data=data)
            payment.gateway_order_id = rzp_order.get("id")
            payment.save(update_fields=["gateway_order_id"])
            context["rzp_order"] = rzp_order
        except Exception as exc:
            messages.warning(request, f"Razorpay initialization failed: {exc}")
            context["simulation_mode"] = True

    if gateway == "stripe" and stripe_key:
        try:
            import stripe
            stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", "")
            stripe_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "inr",
                        "product_data": {"name": f"Order {order.order_number}"},
                        "unit_amount": int(order.grand_total * 100),
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=request.build_absolute_uri(f"/payments/{order.id}/success/?session_id={{CHECKOUT_SESSION_ID}}"),
                cancel_url=request.build_absolute_uri(f"/payments/{order.id}/failure/"),
            )
            payment.gateway_order_id = stripe_session.id
            payment.save(update_fields=["gateway_order_id"])
            context["stripe_session_id"] = stripe_session.id
            context["stripe_session_url"] = stripe_session.url
        except Exception as exc:
            messages.warning(request, f"Stripe initialization failed: {exc}")
            context["simulation_mode"] = True

    return render(request, "payments/payment_start.html", context)


@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.is_paid = True
    order.status = "confirmed"
    order.save(update_fields=["is_paid", "status"])
    Payment.objects.filter(order=order).update(
        status="success",
        gateway_payment_id=request.GET.get("payment_id", "") or request.GET.get("session_id", ""),
    )
    OrderStatusHistory.objects.create(order=order, status="confirmed", note="Payment successful")
    messages.success(request, "Payment successful! Your order is confirmed.")
    return redirect("orders:order_detail", order.id)


@login_required
def payment_failure(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    Payment.objects.filter(order=order).update(
        status="failed",
        gateway_payment_id=request.GET.get("payment_id", "") or request.GET.get("session_id", ""),
    )
    messages.error(request, "Payment failed. Please try again or choose Cash on Delivery.")
    return redirect("orders:order_detail", order.id)


@login_required
def razorpay_callback(request, order_id):
    if request.method != "POST":
        return HttpResponse(status=405)
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payment = Payment.objects.filter(order=order).first()
    if not payment:
        return HttpResponse(status=404)

    razorpay_order_id = request.POST.get("order_id", "")
    razorpay_payment_id = request.POST.get("payment_id", "")
    razorpay_signature = request.POST.get("signature", "")

    razorpay_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")
    if not razorpay_secret or not _verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature, razorpay_secret):
        return JsonResponse({"status": "invalid signature"}, status=400)

    payment.gateway_payment_id = razorpay_payment_id
    payment.status = "success"
    payment.save(update_fields=["gateway_payment_id", "status"])
    order.is_paid = True
    order.status = "confirmed"
    order.save(update_fields=["is_paid", "status"])
    OrderStatusHistory.objects.create(order=order, status="confirmed", note="Payment captured via Razorpay Checkout")
    return redirect("orders:order_detail", order.id)


def razorpay_webhook(request, order_id):
    if request.method != "POST":
        return HttpResponse(status=405)
    order = get_object_or_404(Order, id=order_id)
    payment = Payment.objects.filter(order=order).first()
    if not payment:
        return HttpResponse(status=404)

    razorpay_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")
    if not razorpay_secret:
        return JsonResponse({"status": "ignored", "reason": "missing credentials"})

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    signature = request.headers.get("X-Razorpay-Signature", "")
    body = json.dumps(payload, separators=(",", ":"))
    if not _verify_razorpay_webhook(body, signature, razorpay_secret):
        return JsonResponse({"status": "invalid"}, status=400)

    event = payload.get("event", "")
    if event == "payment.captured":
        payment.gateway_payment_id = payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id", "")
        payment.status = "success"
        payment.save(update_fields=["gateway_payment_id", "status"])
        order.is_paid = True
        order.status = "confirmed"
        order.save(update_fields=["is_paid", "status"])
        OrderStatusHistory.objects.create(order=order, status="confirmed", note="Payment captured via Razorpay webhook")
    elif event in ("payment.failed", "payment.cancelled"):
        payment.status = "failed"
        payment.gateway_payment_id = payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id", "")
        payment.save(update_fields=["status", "gateway_payment_id"])
        order.status = "pending"
        order.save(update_fields=["status"])
        OrderStatusHistory.objects.create(order=order, status="pending", note="Razorpay payment failed")
    return JsonResponse({"status": "ok"})


def stripe_webhook(request, order_id):
    if request.method != "POST":
        return HttpResponse(status=405)
    order = get_object_or_404(Order, id=order_id)
    payload = request.body or b""
    sig_header = request.headers.get("Stripe-Signature", "")
    secret = getattr(settings, "STRIPE_SECRET_KEY", "")
    if not secret:
        return HttpResponse(status=400)

    event = _verify_stripe_signature(payload, sig_header, secret)
    if event is None:
        return HttpResponse(status=400)

    payment = Payment.objects.filter(order=order).first()
    if not payment:
        return HttpResponse(status=404)

    event_type = event.get("type", "")
    if event_type == "checkout.session.completed":
        session = event.get("data", {}).get("object", {})
        payment.gateway_payment_id = session.get("id", "")
        payment.status = "success"
        payment.save(update_fields=["gateway_payment_id", "status"])
        order.is_paid = True
        order.status = "confirmed"
        order.save(update_fields=["is_paid", "status"])
        OrderStatusHistory.objects.create(order=order, status="confirmed", note="Stripe payment completed")
    elif event_type in ("checkout.session.expired", "payment_intent.payment_failed"):
        session = event.get("data", {}).get("object", {})
        payment.status = "failed"
        payment.gateway_payment_id = session.get("id", "")
        payment.save(update_fields=["status", "gateway_payment_id"])
        order.status = "pending"
        order.save(update_fields=["status"])
        OrderStatusHistory.objects.create(order=order, status="pending", note="Stripe payment failed")

    return HttpResponse(status=200)
