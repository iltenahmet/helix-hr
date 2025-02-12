from typing import Annotated, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from os import getenv

load_dotenv()
open_ai_api_key = getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=open_ai_api_key)
memory = MemorySaver()
sequence: List[str] = []


class State(TypedDict):
    messages: Annotated[list, add_messages]


def check_info_sufficiency(state: State):
    print("hit check_info_sufficiency")
    """
    Step 1: Check if enough info is available to generate an HR recruiting sequence.
    """
    prompt = {
        "role": "system",
        "content": "Based on the user interactions so far, do you have enough information to create an HR recruiting sequence? Respond with Yes or No.",
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

    # TODO: delete
    return "create_or_edit_sequence"

    if "Yes" in ai_message.content:
        return "create_or_edit_sequence"
    return "gather_more_info"


def route_tools(
    state: State,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END


def gather_more_info(state: State):
    print("hit gather_more_info")
    """
    Ask questions to gather more details.
    """
    prompt = {
        "role": "system",
        "content": "What additional details do you not have to generate a recruiting sequence? Respond to last user prompt and instruct the user to input the additional details you need.",
    }
    messages = state["messages"] + [prompt]
    response = llm.invoke(messages)
    return {"messages": state["messages"] + [prompt, response]}


def create_or_edit_sequence(state: State):
    global sequence
    if sequence == []:
        return create_sequence(state)
    else:
        # TODO: add logic to edit the sequence
        print("here we'll edit the sequence")
        return create_sequence(state)


def create_sequence(state: State):
    global sequence
    sequence_length = get_number_of_steps(state, 0)

    for i in range(sequence_length):
        previous_steps_text = ""
        if sequence:
            previous_steps_text = "\n".join(
                [f"STEP {idx+1}:\n{sequence[idx]}" for idx in range(len(sequence))]
            )

        instructions = f"""
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
        response = llm.invoke([{"role": "system", "content": instructions}])

        state["messages"].append(response)
        sequence.append(response.content.strip())

    return {
        "messages": state["messages"] + [
            {"role": "assistant", "content": "Here is your recruiting sequence."}
        ]
    }


def get_number_of_steps(state: State, trialCount: int) -> int:
    prompt = "Determine how many steps the sequence should have, respond with a number, e.g. 4."
    print("invoking the llm with prompt: " + prompt)
    response = llm.invoke([{"role": "system", "content": prompt}])
    print("llm has responded with: " + response.content)
    try:
        sequence_length = int(response.content.split()[0])
    except ValueError:
        if trialCount > 4:
            return ValueError("Can't convert response to a number")
        sequence_length = get_number_of_steps(state, trialCount + 1)
    return sequence_length


graph_builder = StateGraph(State)
graph_builder.add_node("check_info_sufficiency", check_info_sufficiency)
graph_builder.add_node("gather_more_info", gather_more_info)
graph_builder.add_node("create_or_edit_sequence", create_or_edit_sequence)

graph_builder.add_edge(START, "check_info_sufficiency")
graph_builder.add_conditional_edges(
    "check_info_sufficiency",
    route_on_info_sufficiency,
    {
        "create_or_edit_sequence": "create_or_edit_sequence",
        "gather_more_info": "gather_more_info",
    },
)
graph_builder.add_edge("gather_more_info", END)
graph_builder.add_edge("create_or_edit_sequence", END)

graph = graph_builder.compile(checkpointer=memory)
graph.get_graph().draw_mermaid_png(output_file_path="state_graph.png")


def ask_agent(user_input: str) -> str:
    print("asking agent: " + user_input)
    config = {"configurable": {"thread_id": "1"}}
    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values",
    )
    print("events: " + str(events))

    last_message = None
    for event in events:
        last_message = event["messages"][-1].content

    return last_message if last_message else "No messages found"


def set_sequence(new_sequence: List[str]):
    global sequence
    sequence = new_sequence


def get_sequence() -> List[str]:
    return sequence
