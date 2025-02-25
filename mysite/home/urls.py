from django.urls import path
from .views import ChatbotAPI, chat_home, get_conversation, get_conversations, add_conversation, add_message, delete_conversation, pdf_upload

urlpatterns = [
    path('home/', chat_home, name='chatbot-view'),
    path('chat/', ChatbotAPI.as_view(), name='chatbot-api'),
    path('api/conversations/', get_conversations, name='get_conversations'),
    path('api/conversation/<str:conversation_id>/', get_conversation, name='get_conversation'),
    path('api/add_conversation/', add_conversation, name='add_conversation'),
    path('api/add_message/<str:conversation_id>/', add_message, name='add_message'),
    path('api/delete_conversation/<str:conversation_id>/', delete_conversation, name='delete_conversation'),
    path('api/pdf_upload/', pdf_upload, name='pdf_upload'),
]