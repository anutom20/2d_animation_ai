from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain import hub
from app.tools.manim_tool import get_manim_tool
from app.models import AnimationResponse


def create_animation_agent(openai_api_key: str):
    """
    Create a LangChain agent for handling animation requests
    """
    # Initialize the language model
    llm = ChatOpenAI(model="o4-mini", openai_api_key=openai_api_key)
    # llm = llm.with_structured_output(AnimationResponse)

    # Get the Manim tool
    tools = [get_manim_tool()]

    # Get the agent prompt from LangChain hub
    prompt = hub.pull("hwchase17/openai-tools-agent")

    # Create the agent
    agent = create_openai_tools_agent(llm, tools, prompt)

    # Create the agent executor
    agent_executor = AgentExecutor(
        agent=agent, tools=tools, verbose=True, handle_parsing_errors=True
    )

    return agent_executor
