"""Application-wide constants."""

# Agent Roles
AGENT_QUERY_ANALYST = "query_analyst"
AGENT_RETRIEVER = "retriever"
AGENT_SYNTHESIZER = "synthesizer"
AGENT_CRITIC = "critic"

# Graph Node Names
NODE_QUERY_ANALYZER = "query_analyzer"
NODE_RETRIEVER = "retriever"
NODE_SYNTHESIZER = "synthesizer"
NODE_CRITIC = "critic"
NODE_HUMAN_GATE = "human_gate"
NODE_END = "end"

# Edge Conditions
CONDITION_APPROVED = "approved"
CONDITION_REJECTED = "rejected"
CONDITION_RETRY = "retry"
CONDITION_MAX_RETRIES = "max_retries"

# HTTP Status
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_COMPLETED = "completed"