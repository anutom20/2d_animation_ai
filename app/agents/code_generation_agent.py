from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain import hub
from app.tools.code_generator import get_code_generation_tool
from app.tools.code_executor import get_code_execution_tool
from typing import Dict, Any
from loguru import logger

def create_code_generation_agent(openai_api_key: str) -> AgentExecutor:
    """
    Create a LangChain agent for generating and executing Manim code
    """
    # Initialize the language model
    llm = ChatOpenAI(
        model="o4-mini",  # Using GPT-4 for better code generation
        openai_api_key=openai_api_key,
    )

    # Get the tools
    tools = [get_code_generation_tool(), get_code_execution_tool()]

    # Get the agent prompt from LangChain hub
    prompt = hub.pull("hwchase17/openai-tools-agent")

    # Create the agent
    agent = create_openai_tools_agent(llm, tools, prompt)

    # Create a wrapper function to handle the workflow
    def agent_executor(input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # First, generate the code
            generation_result = agent.invoke({
                "input": f"""Generate Manim code for the following animation: {input_data['input']}. 
                Return structured output in following format:
                {{
                    "animation_id": unique identifier,
                    "status": success/error, 
                    "message": description of the result,
                    "download_url": URL to download the animation
                }}
                don't return anything else.
                """
            })

            logger.info(f"Generated code: {generation_result}")

            # Then execute the code
            execution_result = agent.invoke(
                {"input": f"Execute this Manim code: {generation_result['output']}"}
            )

            logger.info(f"Execution result: {execution_result}")

            return execution_result["output"]

        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}")
            raise

    # Create the agent executor
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
        return_intermediate_steps=True,
        agent_executor=agent_executor,
    )
