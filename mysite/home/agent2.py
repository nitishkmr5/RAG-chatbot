import os

from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import FAISS
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
from langchain.tools import DuckDuckGoSearchRun


load_dotenv()
# os.environ["GOOGLE_CSE_ID"] = os.getenv("GOOGLE_CSE_ID")
# os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = "43f936b3bdb5f42bf"
GOOGLE_API_KEY = "AIzaSyBQZf7ZcOCZDJzEbOF3J4s4EWlMIYlZU0U"

print("+++++++++++++++++++++++++++++++++++++++")
print(os.getenv("GOOGLE_CSE_ID"))
search = GoogleSearchAPIWrapper()

current_dir = os.path.dirname(os.path.abspath(__file__))
print("\n")
print(current_dir)
print("\n")

output_parser = StrOutputParser()

search = DuckDuckGoSearchRun()

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

loader = PyPDFLoader(current_dir+"/pdfs/Vinove.pdf")
document = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=150)
splits = text_splitter.split_documents(document)

vectorstore = FAISS.from_documents(splits, embeddings)

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3},
)

llm = ChatGroq(model="mixtral-8x7b-32768")

contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, just "
    "reformulate it if needed and otherwise return it as is."
)

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

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

rag_chain = create_retrieval_chain(
    history_aware_retriever, question_answer_chain)

react_docstore_prompt = hub.pull("hwchase17/react")

def get_current_time(*agrs, **kwargs):
    import datetime
    now = datetime.datetime.now()
    return now.strftime("%I:%M %p")

def search_wikipedia(query):
    from wikipedia import summary
    try:
        return summary(query, sentences=2)
    except:
        return "I couldn't find any information on that."

tools = [
    Tool(
        name="Time",
        func=get_current_time,
        description="Useful for when you need to know the current time"
    ),
    # Tool(
    #     name="Wikipedia",
    #     func=search_wikipedia,
    #     description="Useful for when you need to know information about a topic"
    # ),
    # Tool(
    #     name="DuckDuckGo Search",
    #     func=search.run,
    #     description="Useful for when you need to answer questions about current events. You should ask targeted questions."
    # ),
    Tool(
        name="Answer Question",
        func=lambda input, **kwargs: rag_chain.invoke(
            {"input": input, "chat_history": kwargs.get("chat_history", [])}
        ),
        description="useful for when you need to answer questions about the context",
    ),
    # Tool(
    #     name="google_search",
    #     description="Search Google for final results.",
    #     func=search.run,
    # )
]

agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=react_docstore_prompt,
)

agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent, tools=tools, handle_parsing_errors=True, verbose=True,
)

chat_history = []
while True:
    query = input("You: ")
    if query.lower() == "exit":
        break
    response = agent_executor.invoke(
        {"input": query, "chat_history": chat_history})
    print(f"AI: {response['output']}")

    # Update history
    chat_history.append(HumanMessage(content=query))
    chat_history.append(AIMessage(content=response["output"]))