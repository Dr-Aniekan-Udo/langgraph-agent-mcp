import os
import json
import logging
from dotenv import load_dotenv
from typing import Optional

from aioconsole import ainput

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent
from langgraph.graph import StateGraph

from gemini_utilities.system_input import system_instruction
from gemini_utilities.response_encoder import CustomEncoder

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)


class AgentState(dict):
    pass


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.server_params: Optional[StdioServerParameters] = None
        self.sys_query: str = system_instruction

        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found. Please add it to your .env file.")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.0,
            max_retries=2,
            api_key=google_api_key
        )

    async def connect_to_server(self, server_file_path: str):
        command = "python" if server_file_path.endswith(".py") else "node"
        logger.info(f"Using command: {command} for server: {server_file_path}")
        self.server_params = StdioServerParameters(command=command, args=[server_file_path])

    def build_langgraph_agent(self, tools):
        # System + memory support prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.sys_query),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(self.llm, tools, prompt=prompt)

        # Define LangGraph
        graph = StateGraph(AgentState)
        graph.add_node("agent", agent)
        graph.set_entry_point("agent")
        graph.set_finish_point("agent")
        return graph.compile()

    async def run_agent(self):
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await self.session.initialize()

                tools = await load_mcp_tools(self.session)
                logger.info(f"\nLoaded tools: {[tool.name for tool in tools]}")

                graph = self.build_langgraph_agent(tools)

                memory = {"messages": []}  # Chat history memory

                while True:
                    print("\nMCP client active! Type \u001b[31m quit \u001b[0m to exit.")
                    query = await ainput("\nQuery: ")
                    if query.lower() == "quit":
                        print("Shutting down MCP client...")
                        break

                    memory["messages"].append({"role": "user", "content": query})

                    try:
                        result = await graph.ainvoke(memory)
                        response = result.get("messages")[-1]

                        # Add response to memory
                        memory["messages"].append(response)

                        try:
                            formatted_response = json.dumps(response, indent=2, cls=CustomEncoder)
                        except Exception:
                            formatted_response = str(response)

                        print(f"\nGemini: \u001b[32m{formatted_response}\u001b[0m")

                    except Exception as e:
                        logger.error(f"\n\u001b[31mError during agent processing: {e}\u001b[0m")
