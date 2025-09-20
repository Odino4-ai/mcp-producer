#!/bin/bash

# Script d'installation pour l'intégration OpenAI + MCP
echo "🚀 Installation de l'intégration OpenAI Agents SDK + MCP..."

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

echo "✅ Python3 trouvé: $(python3 --version)"

# Installer les dépendances OpenAI Agents SDK
echo "📦 Installation d'OpenAI Agents SDK..."
pip3 install openai-agents

# Installer les dépendances MCP
echo "📦 Installation des dépendances MCP..."
pip3 install mcp

# Vérifier les installations
echo "🔍 Vérification des installations..."

if python3 -c "import agents" 2>/dev/null; then
    echo "✅ OpenAI Agents SDK installé"
else
    echo "❌ Échec installation OpenAI Agents SDK"
fi

if python3 -c "from agents.mcp import MCPServerStdio" 2>/dev/null; then
    echo "✅ MCP integration disponible"
else
    echo "❌ MCP integration non disponible"
fi

if python3 -c "import mcp" 2>/dev/null; then
    echo "✅ MCP core installé"
else
    echo "❌ MCP core non installé"
fi

# Vérifier les variables d'environnement
echo "🔍 Vérification des variables d'environnement..."

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY non défini"
    echo "💡 Définissez votre clé API OpenAI:"
    echo "   export OPENAI_API_KEY='your-openai-api-key'"
else
    echo "✅ OPENAI_API_KEY configuré"
fi

if [ -z "$NOTION_TOKEN" ]; then
    echo "⚠️  NOTION_TOKEN non défini"
    echo "💡 Définissez votre token Notion:"
    echo "   export NOTION_TOKEN='your-notion-token'"
else
    echo "✅ NOTION_TOKEN configuré"
fi

echo ""
echo "🎯 Installation terminée !"
echo ""
echo "📋 Prochaines étapes:"
echo "  1. Configurez OPENAI_API_KEY si ce n'est pas fait"
echo "  2. Configurez NOTION_TOKEN si ce n'est pas fait"
echo "  3. Testez avec: python3 openai-mcp-integration.py"
echo ""
