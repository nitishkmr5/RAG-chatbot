from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent, create_structured_chat_agent
from langchain_core.tools import Tool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory

load_dotenv()

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
    Tool(
        name="Wikipedia",
        func=search_wikipedia,
        description="Useful for when you need to know information about a topic"
    )
]

prompt = hub.pull("hwchase17/structured-chat-agent")

llm = ChatGroq(
    model="mixtral-8x7b-32768", temperature=0
)

memory = ConversationBufferMemory(
    memory_key="chat_history", return_messages=True
)

agent = create_structured_chat_agent(
    llm=llm, tools=tools, prompt=prompt
)

agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
    memory=memory,
    handle_parsing_errors=True
)

initial_message = "You are an AI assistant that can provide helpful answers using available tools.\nIf you are unable to answer, you can use the following tools: Time and Wikipedia."
memory.chat_memory.add_message(SystemMessage(content=initial_message))


# response = agent_executor.invoke({"input": "What time is it?"})

while True:
    user_input = input("User: ")
    if user_input.lower() == "exit":
        break

    # Add the user's message to the conversation memory
    memory.chat_memory.add_message(HumanMessage(content=user_input))

    # Invoke the agent with the user input and the current chat history
    response = agent_executor.invoke({"input": user_input})
    print("Bot:", response["output"])

    # Add the agent's response to the conversation memory
    memory.chat_memory.add_message(AIMessage(content=response["output"]))