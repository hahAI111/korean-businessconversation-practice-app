"""
Create/update sujin-voice agent in Azure AI Foundry Portal with MCP tools.

This script is kept for standalone voice agent creation.
For creating both agents, use: python scripts/register_tools.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from azure.ai.projects import AIProjectClient, models
from azure.identity import DefaultAzureCredential

from app.services.agent_service import VOICE_INSTRUCTIONS

ENDPOINT = os.environ["AZURE_AI_ENDPOINT"]
MODEL = os.environ.get("MODEL_DEPLOYMENT", "gpt-5.2")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "https://korean-biz-coach.azurewebsites.net/mcp")

client = AIProjectClient(
    endpoint=ENDPOINT,
    credential=DefaultAzureCredential(),
)

voice_agent = client.agents.create_version(
    agent_name="sujin-voice",
    definition=models.PromptAgentDefinition(
        model=MODEL,
        instructions=VOICE_INSTRUCTIONS,
        tools=[
            models.MCPTool(
                server_url=MCP_SERVER_URL,
                server_label="korean-corpus",
            ),
        ],
    ),
    description="Korean voice conversation partner Sujin with MCP corpus tools",
)
print(f"VOICE AGENT created: sujin-voice v{voice_agent.as_dict().get('version')}")
client.close()
