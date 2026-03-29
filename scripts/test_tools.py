"""Test agent_reference + function tools locally."""
import os, sys, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from app.services.agent_service import agent_service

print("=== Test 1: Chat with tool call (vocabulary query) ===")
thread = agent_service.create_thread()
result = agent_service.chat(thread, "How do you say meeting in Korean? Look up vocabulary")
print(f"Response ({len(result)} chars):")
print(result[:500])
print()

print("=== Test 2: Non-streaming simple chat ===")
thread2 = agent_service.create_thread()
result2 = agent_service.chat(thread2, "Hello")
print(f"Response2 ({len(result2)} chars):")
print(result2[:500])

print("\n=== DONE ===")
agent_service.cleanup()
