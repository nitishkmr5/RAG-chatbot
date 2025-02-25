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

class RAGPipeline:
    def __init__(self, model="mixtral-8x7b-32768", embedding_model="sentence-transformers/all-MiniLM-L6-v2"):
        load_dotenv()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(model=model, groq_api_key=self.groq_api_key)
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        self.vectorstore = None
        self.retriever = None
        self.history_aware_retriever = None
        self.rag_chain = None

    def load_document(self, file_path):
        loader = PyPDFLoader(file_path)
        document = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=150)
        splits = text_splitter.split_documents(document)

        self.vectorstore = FAISS.from_documents(splits, self.embeddings)
        self.retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
        return self.retriever

    def setup_rag_chain(self):
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

        self.history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )

        # qa_system_prompt = """
        # Context:
        # {context}
        
        # INSTRUCTIONS:
        # Answer the users QUESTION using the DOCUMENT text above.
        # Keep your answer grounded in the facts of the DOCUMENT.
        # Keep your answer short and to the point.
        # If the DOCUMENT doesn’t contain the facts to answer the QUESTION return NONE
        # """
        qa_system_prompt = """
        You are an AI assistant tasked with answering user questions based strictly on the provided DOCUMENT. 

        DOCUMENT:
        {context}

        INSTRUCTIONS:
        - Answer the user's QUESTION using only the information provided in the DOCUMENT.
        - Do not include external knowledge or assumptions.
        - Keep your answer concise and factual.
        - If the DOCUMENT does not contain enough information to answer the QUESTION, respond with "NONE."
        """

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        self.rag_chain = create_retrieval_chain(self.history_aware_retriever, question_answer_chain)

    def run_query(self, query, chat_history=[]):
        if not self.rag_chain:
            raise ValueError("RAG chain is not initialized. Call setup_rag_chain() first.")
        return self.rag_chain.invoke({"input": query, "chat_history": chat_history})

# Example usage
if __name__ == "__main__":
    rag_pipeline = RAGPipeline()
    retriever = rag_pipeline.load_document("your_document.pdf")
    rag_pipeline.setup_rag_chain()
    response = rag_pipeline.run_query("What is the document about?")
    print(response)
