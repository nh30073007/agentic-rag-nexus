# test_full_system.py
import os
import sys
sys.path.insert(0, os.getcwd())

print("=" * 50)
print("🔍 Full System Test")
print("=" * 50)

# 1. কনফিগারেশন চেক
from app.core.config import settings
print(f"📋 LLM Provider: {settings.DEFAULT_LLM_PROVIDER}")
print(f"📋 Ollama Model: {settings.OLLAMA_MODEL}")
print(f"📋 Groq API Key: {'SET' if settings.GROQ_API_KEY else 'NOT SET'}")

# 2. LLM Service টেস্ট
from app.services.llm_service import llm_service
print("\n🧪 Testing LLM Service...")
try:
    response = llm_service.chat_sync_simple("Say 'Hello, system test!'")
    print(f"✅ Response: {response[:100]}...")
    print(f"✅ Used Model: {llm_service.last_used_model}")
except Exception as e:
    print(f"❌ LLM Service Error: {e}")

# 3. LangGraph গ্রাফ টেস্ট
print("\n🧪 Testing LangGraph Graph...")
try:
    from app.graph.builder import build_graph
    graph = build_graph()
    print("✅ Graph built successfully!")
except Exception as e:
    print(f"❌ Graph Error: {e}")

print("=" * 50)
print("✅ Test Complete!")