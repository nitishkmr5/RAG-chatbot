import os
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader

from dotenv import load_dotenv
load_dotenv()
os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY") if os.getenv("GROQ_API_KEY") else "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"
groq_api_key = os.getenv("GROQ_API_KEY") if os.getenv("GROQ_API_KEY") else "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"

llm = ChatGroq(model="mixtral-8x7b-32768", groq_api_key=groq_api_key)

def load_embeddings():
    print("Loading Embeddings model for RAG...")
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

embeddings = load_embeddings()

from langchain.vectorstores import FAISS

def load_pdf_documents(folder_path):
    """Load and process PDF documents into a FAISS vector store."""
    documents = []
    print("-----------------------------------------__>>>>>>>>>>>>")
    print(folder_path)
    print(os.listdir(folder_path))
    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            file_path = os.path.join(folder_path, filename)
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            documents.extend(docs)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=150)
    splits = text_splitter.split_documents(documents)

    vectorstore = FAISS.from_documents(splits, embeddings)
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k":3})
    return {"vectorstore": vectorstore, "retriever": retriever}

def load_document(file_path):
    loader = PyPDFLoader(file_path)
    document = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=150)
    splits = text_splitter.split_documents(document)

    vectorstore = FAISS.from_documents(splits, embeddings)
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k":3})
    return {"vectorstore": vectorstore, "retriever": retriever}

data = load_pdf_documents("home/pdfs")

vectorstore = data["vectorstore"]

retriever = vectorstore.as_retriever()

contextualize_q_system_prompt = """Given a chat history and the latest user question \
    which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, \
    just reformulate it if needed and otherwise return it as is."""

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

qa_system_prompt = """
Context:
{context}

INSTRUCTIONS:
Answer the users QUESTION using the DOCUMENT text above.
Keep your answer ground in the facts of the DOCUMENT.
If the DOCUMENT doesn’t contain the facts to answer the QUESTION return NONE
   """

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm,qa_prompt)

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
