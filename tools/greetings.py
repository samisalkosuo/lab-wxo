from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool
def greeting() -> str:
    """
    Returns a Hello World greeting.
    Use this tool when the user asks for a greeting.
    """
    return "Hello World!"
