from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.services.agent.lab_schema import LabState, StageID
from app.services.agent.nodes.lab_nodes import (
    node_business_understanding,
    node_data_acquisition,
    node_deployment,
    node_evaluation,
    node_exploration,
    node_modeling,
    node_preparation,
)

# Define the graph
workflow = StateGraph(LabState)

# Add nodes
workflow.add_node(StageID.BUSINESS_UNDERSTANDING.value, node_business_understanding)
workflow.add_node(StageID.DATA_ACQUISITION.value, node_data_acquisition)
workflow.add_node(StageID.PREPARATION.value, node_preparation)
workflow.add_node(StageID.EXPLORATION.value, node_exploration)
workflow.add_node(StageID.MODELING.value, node_modeling)
workflow.add_node(StageID.EVALUATION.value, node_evaluation)
workflow.add_node(StageID.DEPLOYMENT.value, node_deployment)

# Set the entry point
workflow.add_edge(START, StageID.BUSINESS_UNDERSTANDING.value)

# Define edges
workflow.add_edge(StageID.BUSINESS_UNDERSTANDING.value, StageID.DATA_ACQUISITION.value)
workflow.add_edge(StageID.DATA_ACQUISITION.value, StageID.PREPARATION.value)
workflow.add_edge(StageID.PREPARATION.value, StageID.EXPLORATION.value)

# Human-in-the-loop interruption or conditional routing could happen here
# For now, simplistic edge
workflow.add_edge(StageID.EXPLORATION.value, StageID.MODELING.value)

# Another interruption point possibly
workflow.add_edge(StageID.MODELING.value, StageID.EVALUATION.value)

workflow.add_edge(StageID.EVALUATION.value, StageID.DEPLOYMENT.value)
workflow.add_edge(StageID.DEPLOYMENT.value, END)

# Compile the graph
# Using MemorySaver to persist state in memory for the session
checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)
