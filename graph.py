from langchain.schema import Document
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from typing import List

from nodes.planning_node import planning_node
from nodes.writing_node import writing_node
from nodes.saving_node import saving_node
from nodes.perplexity_node import perplexity_node
from nodes.web_search_node import sync_web_search_node
from nodes.next_node import next_node
from nodes.extract_input_node import extract_data_from_pdf

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        initial_prompt: initial prompt
        plan: plan
        num_steps: number of steps
        llm_name: name of the LLM
        word_count: word count of the final document
    """
    initial_prompt : str
    plan : str
    num_steps : int
    final_doc : str
    write_steps : List[str]
    word_count : int
    llm_name : str



def create_workflow(llm):
    workflow = StateGraph(GraphState)

    # workflow.add_node("planning_node", planning_node)
    # workflow.add_node("writing_node", writing_node)
    # workflow.add_node("saving_node", saving_node)
    # workflow.add_node("perplexity_node", perplexity_node)
    workflow.add_node("extract_data_from_pdf",extract_data_from_pdf)
    workflow.add_node("sync_web_search_node", sync_web_search_node)
    workflow.add_node("next_node",next_node)
    # Set entry point
    workflow.set_entry_point("extract_data_from_pdf")

    # Add edges
    workflow.add_edge("extract_data_from_pdf","sync_web_search_node")
    workflow.add_edge("sync_web_search_node","next_node")
    workflow.add_edge("next_node",END)
    # workflow.add_edge("planning_node", "writing_node")
    # workflow.add_edge("writing_node", "saving_node")
    # workflow.add_edge("saving_node", "perplexity_node")
    # workflow.add_edge("perplexity_node", "web_search_node")
    # workflow.add_edge("web_search_node", END)

    return workflow.compile()