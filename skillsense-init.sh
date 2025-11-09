#!/bin/bash
# Quick start script for SkillSense

set -e

echo "🧠 SkillSense Quick Start"
echo "========================="
echo ""

# Check if Ollama is running
echo "📡 Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Please install Ollama first."
    echo "   Visit: https://ollama.com"
    exit 1
fi

# Check for required models
echo "🤖 Checking AI models..."
if ! ollama list | grep -q "gemma3:4b"; then
    echo "⏬ Pulling gemma3:4b model..."
    ollama pull gemma3:4b
fi

if ! ollama list | grep -q "dengcao/Qwen3-Embedding-0.6B"; then
    echo "⏬ Pulling embedding model..."
    ollama pull dengcao/Qwen3-Embedding-0.6B:Q8_0
fi

echo "✅ AI models ready!"
echo ""

# Initialize database
echo "🗄️  Initializing database..."
cd apps/backend
if command -v uv &> /dev/null; then
    uv run python init_skillsense_db.py
else
    python3 init_skillsense_db.py
fi
cd ../..

echo ""
echo "✨ SkillSense is ready!"
echo ""
echo "🚀 Start the servers with:"
echo "   npm run dev"
echo ""
echo "📍 Then visit:"
echo "   Dashboard:  http://localhost:3000/dashboard"
echo "   API Docs:   http://localhost:8000/api/docs"
echo ""
echo "📖 Documentation:"
echo "   - SKILLSENSE_README.md - Features and architecture"
echo "   - TESTING_GUIDE.md     - Testing scenarios"
echo ""
