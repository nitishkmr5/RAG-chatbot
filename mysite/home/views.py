from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.shortcuts import render
from .models import Conversation, Message
from .helper import invoke_and_save
import json

@csrf_exempt
def get_conversations(request):
    conversations = Conversation.objects.all().order_by('-created_at')
    data = [{'id': conv.id, 'title': conv.title} for conv in conversations]
    return JsonResponse(data, safe=False)

@csrf_exempt
def get_conversation(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        messages = conversation.messages.all().order_by('created_at')
        data = [{'role': msg.role, 'content': msg.content} for msg in messages]
        return JsonResponse(data, safe=False)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)

@csrf_exempt
def add_conversation(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        conversation = Conversation(id=data['id'], title=data['title'])
        conversation.save()
        return JsonResponse({'status': 'success'})

@csrf_exempt
def add_message(request, conversation_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            message = Message(conversation=conversation, role=data['role'], content=data['content'])
            message.save()
            return JsonResponse({'status': 'success'})
        except Conversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found'}, status=404)

@csrf_exempt
def delete_conversation(request, conversation_id):
    if request.method == 'DELETE':
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            conversation.delete()
            return JsonResponse({'status': 'success'})
        except Conversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found'}, status=404)

import uuid
def pdf_upload(request):
    image = request.FILES["file"]
    # result = invoke_and_save(session_id, user_input, file_path)

    conversation = Conversation(id=uuid.uuid1(), title=image.name, pdf_file=image)
    conversation.save()

    return render(request, 'home/home2.html')
        



def chat_home(request):
    if request.method == 'POST':
        return JsonResponse("sssss", safe=False)
    else:
        return render(request, 'home/home2.html')

class ChatbotAPI(APIView):
    permission_classes = [AllowAny]
    
    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        # if not user_input:
            # return Response({"error": "No input provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        print("================>")
        user_input = request.data['curr_input']
        session_id = request.data['conversation_id']
        print(user_input)
        print(session_id)

        result = invoke_and_save(session_id, user_input)
        print(result)
        # result = "testing response"
        return JsonResponse(result, safe=False)