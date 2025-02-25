# models.py
from django.db import models

class Conversation(models.Model):
    id = models.CharField(max_length=36, primary_key=True)
    title = models.CharField(max_length=100)
    pdf_file = models.FileField(upload_to='home/pdfs/', default='home/pdfs/default.pdf')
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=10)  # 'user' or 'assistant'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)