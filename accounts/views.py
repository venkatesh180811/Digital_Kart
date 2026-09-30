import random
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, EmailMultiAlternatives
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.sessions.models import Session

from .forms import RegisterForm, EmailAuthenticationForm, ProfileForm, AddressForm
from .models import EmailVerificationToken, OTP, Address, SavedCard, UserSession

User = get_user_model()
logger = logging.getLogger(__name__)


def _send_verification_email(request, user):
    token_obj = EmailVerificationToken.objects.create(user=user)
    verify_url = request.build_absolute_uri(f"/accounts/verify-email/{token_obj.token}/")
    subject = "Verify your DigitalKart account"
    text_body = f"Hi {user.username},\n\nPlease verify your email by visiting:\n{verify_url}\n\nThis link expires in 24 hours."
    html_body = render_to_string("emails/verify_email.html", {"user": user, "verify_url": verify_url})
    _send_email(subject, text_body, html_body, [user.email])


def _send_otp_email(user, code):
    subject = "Your DigitalKart login OTP"
    text_body = f"Hi {user.username},\n\nYour one-time login code is: {code}\n\nThis code expires in 10 minutes.\n\nIf you did not request this, please ignore this email."
    html_body = render_to_string("emails/otp_email.html", {"user": user, "code": code})
    _send_email(subject, text_body, html_body, [user.email])


def _send_password_reset_email(user, reset_url):
    subject = "Reset your DigitalKart password"
    text_body = f"Hi {user.username},\n\nClick the link below to reset your password:\n{reset_url}\n\nThis link expires in 1 hour.\n\nIf you did not request this, please ignore this email."
    html_body = render_to_string("emails/password_reset.html", {"user": user, "reset_url": reset_url})
    _send_email(subject, text_body, html_body, [user.email])


def _send_email(subject, text_body, html_body, recipient_list):
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        msg.attach_alternative(html_body, "text/html")
        sent = msg.send(fail_silently=False)
        logger.info("Email sent to %s | subject=%s | status=%s", recipient_list, subject, sent)
        return sent
    except Exception as exc:
        logger.exception("Failed to send email to %s | subject=%s | error=%s", recipient_list, subject, exc)
        raise


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            _send_verification_email(request, user)
            messages.success(request, "Account created! Check your email to verify your account.")
            return redirect("accounts:login")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def verify_email_view(request, token):
    token_obj = get_object_or_404(EmailVerificationToken, token=token)
    if token_obj.is_valid():
        user = token_obj.user
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        token_obj.is_used = True
        token_obj.save(update_fields=["is_used"])
        messages.success(request, "Your email has been verified. You can now log in.")
    else:
        messages.error(request, "This verification link is invalid or has expired.")
    return redirect("accounts:login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = EmailAuthenticationForm(request, data=request.POST)
        email = request.POST.get("username", "").lower().strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get("next")
            return redirect(next_url or "home")
        messages.error(request, "Invalid email or password.")
    else:
        form = EmailAuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


def request_otp_view(request):
    """Send a 6-digit OTP to the user's email for OTP-based login."""
    if request.method == "POST":
        email = request.POST.get("email", "").lower().strip()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No account found with that email.")
            return redirect("accounts:request_otp")
        code = f"{random.randint(0, 999999):06d}"
        OTP.objects.create(user=user, code=code, purpose="login")
        try:
            _send_otp_email(user, code)
        except Exception:
            messages.error(request, "Could not send OTP. Please try again later or use password login.")
            return redirect("accounts:request_otp")
        request.session["otp_email"] = email
        messages.success(request, "OTP sent to your email.")
        return redirect("accounts:verify_otp")
    return render(request, "accounts/request_otp.html")


def verify_otp_view(request):
    email = request.session.get("otp_email")
    if not email:
        return redirect("accounts:request_otp")
    if request.method == "POST":
        code = request.POST.get("code", "")
        user = get_object_or_404(User, email=email)
        otp = OTP.objects.filter(user=user, code=code, purpose="login", is_used=False).order_by("-created_at").first()
        if otp and otp.is_valid():
            otp.is_used = True
            otp.save(update_fields=["is_used"])
            login(request, user)
            del request.session["otp_email"]
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("home")
        messages.error(request, "Invalid or expired OTP.")
    return render(request, "accounts/verify_otp.html", {"email": email})


def password_reset_request_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").lower().strip()
        user = User.objects.filter(email=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = request.build_absolute_uri(f"/accounts/reset-password/{uid}/{token}/")
            try:
                _send_password_reset_email(user, reset_url)
            except Exception:
                messages.error(request, "Could not send reset email. Please try again later.")
                return redirect("accounts:login")
        messages.success(request, "If that email exists, a reset link has been sent.")
        return redirect("accounts:login")
    return render(request, "accounts/password_reset_request.html")


def password_reset_confirm_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")
            if password1 and password1 == password2:
                user.set_password(password1)
                user.save()
                messages.success(request, "Password reset successfully. Please log in.")
                return redirect("accounts:login")
            messages.error(request, "Passwords do not match.")
        return render(request, "accounts/password_reset_confirm.html")
    messages.error(request, "This password reset link is invalid or has expired.")
    return redirect("accounts:login")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully.")
            return redirect("accounts:profile")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "accounts/change_password.html", {"form": form})


@login_required
def address_list_view(request):
    addresses = request.user.addresses.all()
    return render(request, "accounts/address_list.html", {"addresses": addresses})


@login_required
def address_add_view(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address added.")
            return redirect("accounts:address_list")
    else:
        form = AddressForm()
    return render(request, "accounts/address_form.html", {"form": form, "title": "Add Address"})


@login_required
def address_edit_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated.")
            return redirect("accounts:address_list")
    else:
        form = AddressForm(instance=address)
    return render(request, "accounts/address_form.html", {"form": form, "title": "Edit Address"})


@login_required
def address_delete_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.success(request, "Address removed.")
    return redirect("accounts:address_list")


@login_required
def saved_cards_view(request):
    cards = request.user.saved_cards.all()
    return render(request, "accounts/saved_cards.html", {"cards": cards})


@login_required
def saved_card_add(request):
    if request.method == "POST":
        card_brand = request.POST.get("card_brand", "").strip()
        last4 = request.POST.get("last4", "").strip()
        expiry_month = request.POST.get("expiry_month", "").strip()
        expiry_year = request.POST.get("expiry_year", "").strip()
        gateway_token = request.POST.get("gateway_token", "").strip()

        if not (card_brand and last4 and expiry_month and expiry_year and gateway_token):
            messages.error(request, "Please fill all card details.")
        else:
            SavedCard.objects.create(
                user=request.user,
                gateway_token=gateway_token,
                card_brand=card_brand,
                last4=last4,
                expiry_month=int(expiry_month),
                expiry_year=int(expiry_year),
            )
            messages.success(request, "Card saved successfully.")
            return redirect("accounts:saved_cards")
    return redirect("accounts:saved_cards")


@login_required
def saved_card_remove(request, card_id):
    card = get_object_or_404(SavedCard, id=card_id, user=request.user)
    card.delete()
    messages.info(request, "Card removed.")
    return redirect("accounts:saved_cards")


@login_required
def saved_card_set_default(request, card_id):
    card = get_object_or_404(SavedCard, id=card_id, user=request.user)
    request.user.saved_cards.exclude(id=card.id).update(gateway_token="")
    card.gateway_token = "default"
    card.save(update_fields=["gateway_token"])
    messages.success(request, "Default card updated.")
    return redirect("accounts:saved_cards")


@login_required
def sessions_view(request):
    sessions = request.user.active_sessions.all()
    current_session_key = request.session.session_key
    return render(request, "accounts/sessions.html", {
        "sessions": sessions,
        "current_session_key": current_session_key,
    })


@login_required
def logout_session(request, session_key):
    if request.session.session_key == session_key:
        messages.error(request, "You cannot log out your current session.")
        return redirect("accounts:sessions")
    session = UserSession.objects.filter(user=request.user, session_key=session_key).first()
    if session:
        session.delete()
        try:
            Session.objects.filter(session_key=session_key).delete()
        except Exception:
            pass
        messages.success(request, "Session logged out.")
    else:
        messages.error(request, "Session not found.")
    return redirect("accounts:sessions")


@login_required
def logout_all_sessions(request):
    if request.method == "POST":
        request.user.active_sessions.exclude(session_key=request.session.session_key).delete()
        try:
            Session.objects.exclude(session_key=request.session.session_key).delete()
        except Exception:
            pass
        messages.success(request, "All other sessions have been logged out.")
    return redirect("accounts:sessions")


@receiver(user_logged_in)
def create_user_session(sender, request, user, **kwargs):
    session_key = request.session.session_key
    if not session_key:
        return
    UserSession.objects.filter(user=user, session_key=session_key).delete()
    UserSession.objects.create(
        user=user,
        session_key=session_key,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        is_current=True,
    )
    UserSession.objects.filter(user=user).exclude(session_key=session_key).update(is_current=False)


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
