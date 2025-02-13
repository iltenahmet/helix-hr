from typing import Annotated, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from os import getenv
from textwrap import dedent
from socketio_instance import socketio
from model import get_db_engine, User, Session
from sqlalchemy.orm import sessionmaker

load_dotenv()
open_ai_api_key = getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=open_ai_api_key)
memory = MemorySaver()
sequence: List[str] = []


class State(TypedDict):
    messages: Annotated[list, add_messages]


def understand_user_intent(state: State):
    information = dedent(
        """\
        You are an AI assistant for a recruiting platform. Your task is to assist users in creating or editing recruiting sequences, plans, or outreach workflows.
        Does the user have any intent of creating or editing a recruiting sequence, plan, or an outreach workflow? Respond with Yes or No.
        """
    )
    prompt = {"role": "system", "content": information}
    messages = state["messages"] + [prompt]
    response = llm.invoke(messages)
    print("Response: ", response.content)
    return {"messages": state["messages"] + [prompt, response]}


def route_on_user_intent(state: State):
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state: {state}")

    if "Yes" in ai_message.content:
        return "check_info_sufficiency"
    return "answer_question"


def answer_question(state: State):
    prompt = {
        "role": "system",
        "content": "Answer the user's last question based on the context provided so far.",
    }
    messages = state["messages"] + [prompt]
    response = llm.invoke(messages)
    return {"messages": state["messages"] + [prompt, response]}


def check_info_sufficiency(state: State):
    prompt = {
        "role": "system",
        "content": "Based on the user interactions so far, do you have enough information to create or edit an HR recruiting sequence? Respond with Yes or No.",
    }
    messages = state["messages"] + [prompt]
    response = llm.invoke(messages)
    return {"messages": state["messages"] + [prompt, response]}


def route_on_info_sufficiency(state: State):
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state: {state}")

    if "Yes" in ai_message.content:
        return "create_or_edit_sequence"
    return "gather_more_info"


def gather_more_info(state: State):
    prompt = {
        "role": "system",
        "content": "What additional details do you not have to generate a recruiting sequence? Ask a brief question to the user.",
    }
    messages = state["messages"] + [prompt]
    response = llm.invoke(messages)
    return {"messages": state["messages"] + [prompt, response]}


def get_last_user_message(state: State) -> str:
    for msg in reversed(state["messages"]):
        if msg["role"] == "user":
            return msg["content"]
    return ""


def create_or_edit_sequence(state: State):
    global sequence
    if sequence == []:
        return create_sequence(state)
    else:
        return edit_sequence(state)


def create_sequence(state: State):
    global sequence
    sequence_length = get_number_of_steps(state, 0)
    socketio.emit("sequence_status", {"status": "generating"})

    for i in range(sequence_length):
        previous_steps_text = ""
        if sequence:
            previous_steps_text = "\n".join(
                [f"STEP {idx+1}:\n{sequence[idx]}" for idx in range(len(sequence))]
            )

        instructions = dedent(
            f"""\
            You are composing exactly ONE email in {sequence_length} steps.
            So far, you have completed {i} steps.
            Below is what you have written so far for steps 1 through {i}:

            {previous_steps_text}

            IMPORTANT GUIDELINES:
            1. Do NOT repeat or restate any text from the previous steps.
            2. Only provide the partial text for step {i+1} (no more, no less).
            3. We will combine all steps at the end, so do not reference current or future steps by name; just continue the email logically.

            Now, please write ONLY the partial text for step {i+1} out of {sequence_length}.
        """
        )

        messages = state["messages"] + [{"role": "system", "content": instructions}]
        response = llm.invoke(messages)

        state["messages"].append(response)
        sequence.append(response.content.strip())

        socketio.emit(
            "sequence_step", {"stepNumber": i + 1, "stepText": response.content.strip()}
        )

    socketio.emit("sequence_done", {"sequence": sequence})

    return {
        "messages": state["messages"]
        + [{"role": "assistant", "content": "Here is your recruiting sequence."}]
    }


def edit_sequence(state: State):
    global sequence
    user_message = state["messages"][-1].content
    print("User message: ", user_message)

    socketio.emit("sequence_status", {"status": "editing"})

    existing_sequence_text = "\n\n".join(
        [f"STEP {idx+1}:\n{step}" for idx, step in enumerate(sequence)]
    )

    instructions = dedent(
        f"""\
        You have an existing email sequence, composed of multiple steps in a single email.
        Below is the CURRENT sequence:

        {existing_sequence_text}

        The user wants to make edits or changes as described here:
        "{user_message}"

        Please produce a NEW version of the sequence that incorporates these edits.
        
        REQUIREMENTS:
        1. If the user wants to add or remove steps, do so.
        2. If the user wants to modify only certain parts, keep the rest intact.
        3. Number each step in order: STEP 1, STEP 2, etc.
        
        Return the updated steps in your response. For example:
        STEP 1:
        <updated text>
        
        STEP 2:
        <updated text>
        
        ...
    """
    )

    messages = state["messages"] + [{"role": "system", "content": instructions}]
    response = llm.invoke(messages)

    updated_text = response.content.strip()
    print("Updated text: ", updated_text)

    new_steps = []
    parts = updated_text.split("STEP ")
    for part in parts:
        if not part.strip():
            continue
        step_num, step_body = part.split(":", 1)
        new_steps.append(step_body.strip())

    sequence = new_steps
    socketio.emit("sequence_done", {"sequence": sequence})

    return {
        "messages": state["messages"]
        + [{"role": "assistant", "content": "Your sequence has been updated."}]
    }


def get_number_of_steps(state: State, trialCount: int) -> int:
    prompt = "Determine how many steps the sequence should have, respond with a number, e.g. 4."
    messages = state["messages"] + [{"role": "system", "content": prompt}]
    response = llm.invoke(messages)
    try:
        sequence_length = int(response.content.split()[0])
        return sequence_length
    except ValueError:
        if trialCount > 4:
            raise ValueError("Can't convert response to a number, the llm responded with: " + response.content)
        else:
            return get_number_of_steps(state, trialCount + 1)


graph_builder = StateGraph(State)
graph_builder.add_node("understand_user_intent", understand_user_intent)
graph_builder.add_node("answer_question", answer_question)
graph_builder.add_node("check_info_sufficiency", check_info_sufficiency)
graph_builder.add_node("gather_more_info", gather_more_info)
graph_builder.add_node("create_or_edit_sequence", create_or_edit_sequence)

graph_builder.add_edge(START, "understand_user_intent")
graph_builder.add_conditional_edges(
    "understand_user_intent",
    route_on_user_intent,
    {
        "check_info_sufficiency": "check_info_sufficiency",
        "answer_question": "answer_question",
    },
)
graph_builder.add_conditional_edges(
    "check_info_sufficiency",
    route_on_info_sufficiency,
    {
        "create_or_edit_sequence": "create_or_edit_sequence",
        "gather_more_info": "gather_more_info",
    },
)
graph_builder.add_edge("answer_question", END)
graph_builder.add_edge("gather_more_info", END)
graph_builder.add_edge("create_or_edit_sequence", END)

graph = graph_builder.compile(checkpointer=memory)
#graph.get_graph().draw_mermaid_png(output_file_path="state_graph.png")


def get_user_info(user_id: int) -> str:
    db = get_db_engine()
    SessionLocal = sessionmaker(bind=db)
    db_session = SessionLocal()
    user = db_session.query(User).filter_by(id=user_id).first()
    db_session.close()
    if user:
        return f"User: {user.username}, Company: {user.company}, Phone: {user.phone_number}"
    return "User information not available"

def ask_agent(user_input: str, user_id: int) -> str:
    user_info = get_user_info(user_id)
    config = {"configurable": {"thread_id": "1"}}
    events = graph.stream(
        {"messages": [{"role": "user", "content": f"{user_info}\n{user_input}"}]},
        config,
        stream_mode="values",
    )

    last_message = None
    for event in events:
        last_message = event["messages"][-1].content

    return last_message if last_message else "No messages found"

def set_sequence(new_sequence: List[str]):
    global sequence
    sequence = new_sequence


def get_sequence() -> List[str]:
    return sequence
