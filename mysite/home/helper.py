from .models import Conversation, Message
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from django.shortcuts import get_object_or_404
from .rag_pipeline import RAGPipeline

def load_session_history(session_id: str):
    chat_history = ChatMessageHistory()
    try:
        session = Conversation.objects.filter(id=session_id).first()
        if session:
            # Add each message to the chat history
            for message in session.messages.all():
                if message.role == "user":
                    chat_history.add_user_message(message.content)
                elif message.role == "ai":
                    chat_history.add_ai_message(message.content)
    except Exception as e:
        print(f"An error occurred: {e}")

    return chat_history

store = {}
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = load_session_history(session_id)
        store[session_id].add_ai_message("Hi! Ask me anything related to the documents.")
    return store[session_id]

pipelines = {}

def create_pdf_pipeline(session_id, path):
    rag_pipepline = RAGPipeline()
    rag_pipepline.load_document(path)
    rag_pipepline.setup_rag_chain()
    pipelines[session_id] = rag_pipepline
    return rag_pipepline

def invoke_and_save(session_id, input_text):
    conversation = get_object_or_404(Conversation, id=session_id)

    if session_id not in pipelines:
        rag_pipepline = create_pdf_pipeline(session_id, conversation.pdf_file.path)
    else:
        rag_pipepline = pipelines[session_id]

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_pipepline.rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    result = conversational_rag_chain.invoke(
        {"input": input_text},
        config={"configurable": {"session_id": session_id}}
    )["answer"]
    return result