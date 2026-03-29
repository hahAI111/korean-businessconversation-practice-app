"""
注册 Portal Agent (korean-biz-coach + sujin-voice) 到 Azure AI Foundry。

两个 Agent 都通过 MCPTool 连接 MCP Server, 动态发现和执行工具。

运行: python scripts/register_tools.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MCPTool, PromptAgentDefinition
from azure.identity import DefaultAzureCredential

from app.services.agent_service import TEXT_INSTRUCTIONS, VOICE_INSTRUCTIONS

ENDPOINT = os.environ["AZURE_AI_ENDPOINT"]
MODEL = os.environ.get("MODEL_DEPLOYMENT", "gpt-5.2")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "https://korean-biz-coach.azurewebsites.net/mcp")


def main():
    print(f"Endpoint: {ENDPOINT}")
    print(f"Model: {MODEL}")
    print(f"MCP Server URL: {MCP_SERVER_URL}")

    cred = DefaultAzureCredential()
    proj = AIProjectClient(endpoint=ENDPOINT, credential=cred)

    mcp_tool = MCPTool(
        server_url=MCP_SERVER_URL,
        server_label="korean-corpus",
    )

    # ---- korean-biz-coach with MCP tools ----
    print("\n--- Creating korean-biz-coach with MCP tools ---")
    text_def = PromptAgentDefinition(
        model=MODEL,
        instructions=TEXT_INSTRUCTIONS,
        tools=[mcp_tool],
    )

    v = proj.agents.create_version(
        agent_name="korean-biz-coach",
        definition=text_def,
        description="Korean business text coach with MCP tools",
    )
    print(f"  Version: {v.as_dict()['version']}")

    # ---- sujin-voice with MCP tools ----
    print("\n--- Creating sujin-voice with MCP tools ---")
    voice_def = PromptAgentDefinition(
        model=MODEL,
        instructions=VOICE_INSTRUCTIONS,
        tools=[mcp_tool],
    )
    vv = proj.agents.create_version(
        agent_name="sujin-voice",
        definition=voice_def,
        description="Korean voice partner Sujin with MCP tools",
    )
    print(f"  Version: {vv.as_dict()['version']}")

    proj.close()
    print("\nDONE - Both agents updated with MCP tools")


if __name__ == "__main__":
    main()
