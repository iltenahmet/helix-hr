from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI 
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
import os

load_dotenv()
open_ai_api_key = os.getenv("OPENAI_API_KEY")
conversation_started = False

llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=open_ai_api_key)
memory = MemorySaver() # TODO: Use a database to store memory

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile(checkpointer=memory)

system_message = {"role": "system", "content": "You are an AI assistant specializing in HR recruitment."}

def stream_graph_updates(user_input: str) -> str:
    global conversation_started
    config = {"configurable": {"thread_id": "1"}}
    user_message = {"role": "user", "content": user_input}

    if conversation_started == False:
        messages = [system_message, user_message]
        conversation_started = True
    else:
        messages = [user_message]

    events = graph.stream(
        {"messages": messages},
        config,
        stream_mode="values"
    )

    last_message = None
    for event in events:
        last_message = event["messages"][-1].content

    return last_message if last_message else "No messages found"

def ask_agent(user_input: str) -> str:
    return stream_graph_updates(user_input)
