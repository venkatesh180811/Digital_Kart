import json
import os
import time
from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import ChatConversation, ChatMessage
from .services import execute_tool, TOOL_REGISTRY, build_system_prompt, search_products, get_product_details


def _get_client_ip(request):
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _get_session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _get_or_create_conversation(request):
    if request.user.is_authenticated:
        conversation, _ = ChatConversation.objects.get_or_create(
            user=request.user,
            session_key="",
            defaults={"session_key": ""},
        )
    else:
        session_key = _get_session_key(request)
        conversation, _ = ChatConversation.objects.get_or_create(
            user=None,
            session_key=session_key,
            defaults={"session_key": session_key},
        )
    return conversation


def _trim_history(messages, max_messages=20):
    if len(messages) > max_messages:
        return messages[-max_messages:]
    return messages


def _call_ai_provider(messages):
    api_key = getattr(settings, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        tools = []
        for name, meta in TOOL_REGISTRY.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": meta["description"],
                    "parameters": meta["parameters"],
                },
            })

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=800,
            temperature=0.2,
        )
        return response
    except Exception:
        return None


def _process_ai_response(response, user):
    message = response.choices[0].message
    tool_calls = getattr(message, "tool_calls", None)

    if not tool_calls:
        return {"reply": message.content or "I'm not sure how to help with that. Could you rephrase?", "products": []}

    tool_messages = []
    products = []
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        try:
            arguments = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            arguments = {}

        result = execute_tool(function_name, arguments, user)
        tool_messages.append({
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": function_name,
            "content": json.dumps(result, ensure_ascii=False),
        })

        if function_name == "search_products":
            products = result[:6] if isinstance(result, list) else []
        elif function_name == "get_product_details":
            if isinstance(result, dict) and result:
                products = [result]

    followup = _call_ai_provider_with_tools(messages + [message] + tool_messages)
    if followup:
        reply = followup.choices[0].message.content or "Here is what I found."
    else:
        reply = "Here is what I found based on your request."

    return {"reply": reply, "products": products}


def _call_ai_provider_with_tools(messages):
    api_key = getattr(settings, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        tools = []
        for name, meta in TOOL_REGISTRY.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": meta["description"],
                    "parameters": meta["parameters"],
                },
            })
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=800,
            temperature=0.2,
        )
        return response
    except Exception:
        return None


@require_http_methods(["GET", "POST"])
def chatbot_view(request):
    return render(request, "chatbot/chatbot_widget.html")


@require_http_methods(["POST"])
@csrf_exempt
def chat_api(request):
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid request."}, status=400)

    user_message = (data.get("message") or "").strip()
    if not user_message:
        return JsonResponse({"success": False, "message": "Please type a message."}, status=400)

    conversation = _get_or_create_conversation(request)
    ChatMessage.objects.create(conversation=conversation, role="user", content=user_message)

    history_qs = ChatMessage.objects.filter(conversation=conversation).order_by("created_at")
    history = [
        {"role": m.role, "content": m.content}
        for m in history_qs
    ]
    history = _trim_history(history)

    messages = [{"role": "system", "content": build_system_prompt()}]
    messages.extend(history)

    api_key = getattr(settings, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        fallback_reply = (
            "I'm currently running in limited mode. "
            "Please configure OPENAI_API_KEY to enable full AI support. "
            "Meanwhile, you can browse products, track orders from the Orders page, or contact support."
        )
        ChatMessage.objects.create(conversation=conversation, role="assistant", content=fallback_reply)
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=["updated_at"])
        return JsonResponse({"success": True, "message": fallback_reply, "products": []})

    response = _call_ai_provider(messages)
    if response is None:
        fallback_reply = "Sorry, I'm having trouble connecting right now. Please try again."
        ChatMessage.objects.create(conversation=conversation, role="assistant", content=fallback_reply)
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=["updated_at"])
        return JsonResponse({"success": True, "message": fallback_reply, "products": []})

    processed = _process_ai_response(response, request.user)
    reply = processed.get("reply", "I'm here to help.")
    products = processed.get("products", [])

    ChatMessage.objects.create(conversation=conversation, role="assistant", content=reply)
    conversation.updated_at = timezone.now()
    conversation.save(update_fields=["updated_at"])

    return JsonResponse({"success": True, "message": reply, "products": products})
