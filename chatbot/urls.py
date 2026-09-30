from django.urls import path
from . import views

app_name = "chatbot"

urlpatterns = [
    path("widget/", views.chatbot_view, name="chatbot_widget"),
    path("api/chat/", views.chat_api, name="chat_api"),
]
