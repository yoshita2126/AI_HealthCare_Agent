from langgraph.graph import StateGraph, END
from app.models.state import AgentState
from app.agents.intake_agent import intake_node
from app.agents.diagnostics_agent import diagnostics_node
from app.agents.escalation_agent import escalation_node
from app.agents.summarizer_agent import summarizer_node

def build_coordinator_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("intake", intake_node)
    workflow.add_node("diagnostics", diagnostics_node)
    workflow.add_node("escalation", escalation_node)
    workflow.add_node("summarizer", summarizer_node)
    
    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "diagnostics")
    workflow.add_edge("diagnostics", "escalation")
    workflow.add_edge("escalation", "summarizer")
    workflow.add_edge("summarizer", END)
    
    return workflow.compile()

coordinator_app = build_coordinator_graph()
