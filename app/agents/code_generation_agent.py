from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain import hub
from app.tools.code_generator import get_code_generation_tool
from app.tools.code_executor import get_code_execution_tool
from typing import Dict, Any
from loguru import logger
import json


class AnimationAgentWrapper:
    """Wrapper class for AgentExecutor with animation ID handling"""
    
    def __init__(self, agent_executor: AgentExecutor):
        self.agent_executor = agent_executor
    
    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Custom invoke method that handles animation ID passing"""
        try:
            animation_id = input_data.get("animation_id")
            user_prompt = input_data.get("input")
            
            if not animation_id:
                raise ValueError("animation_id is required")
            
            # First, generate the code
            generation_result = self.agent_executor.invoke(
                {
                    "input": f"""Generate Manim code for the following animation: {user_prompt}. 
                The animation_id is: {animation_id}
                Return structured output in following format:
                {{
                    "animation_id": "{animation_id}",
                    "status": success/error, 
                    "message": description of the result,
                    "download_url": URL to download the animation
                }}
                don't return anything else.
                """
                }
            )

            logger.info(f"Generated code: {generation_result}")

            # Then execute the code with animation_id
            execution_input = {
                "code": generation_result['output'],
                "animation_id": animation_id
            }
            
            execution_result = self.agent_executor.invoke(
                {"input": f"Execute this Manim code with animation_id: {json.dumps(execution_input)}"}
            )

            logger.info(f"Execution result: {execution_result}")

            return execution_result["output"]

        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}")
            raise


def create_code_generation_agent(openai_api_key: str) -> AnimationAgentWrapper:
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

    # Create the agent executor
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
        return_intermediate_steps=True,
    )
    
    # Return the wrapper instead of the raw executor
    return AnimationAgentWrapper(executor)
