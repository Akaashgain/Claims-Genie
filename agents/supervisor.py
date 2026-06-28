from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents.document_agent import answer_document_question
from agents.planner import plan_document


class AgentState(TypedDict):
    question: str
    document_type: str
    answer: str
    sources: list[dict]


def planner_node(state: AgentState) -> AgentState:
    state["document_type"] = plan_document(state["question"])
    return state


def document_node(state: AgentState) -> AgentState:
    result = answer_document_question(state["question"], state["document_type"])
    state["answer"] = result["answer"]
    state["sources"] = result["sources"]
    return state


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("planner", planner_node)
    graph.add_node("document_agent", document_node)
    graph.set_entry_point("planner")
    graph.add_edge("planner", "document_agent")
    graph.add_edge("document_agent", END)
    return graph.compile()


APP_GRAPH = build_graph()


def run_agent(question: str) -> dict:
    result = APP_GRAPH.invoke(
        {"question": question, "document_type": "all", "answer": "", "sources": []}
    )
    return {
        "document_type": result["document_type"],
        "answer": result["answer"],
        "sources": result["sources"],
    }
