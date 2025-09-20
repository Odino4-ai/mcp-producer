#!/bin/bash

# Script pour démarrer le serveur MCP Notion
# Usage: ./start-mcp-notion.sh

echo "🚀 Démarrage du serveur MCP Notion..."

# Vérifier si Python et les dépendances sont installées
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Vérifier si le package mcp est installé
if ! python3 -c "import mcp" 2>/dev/null; then
    echo "📦 Installation du package MCP..."
    pip3 install mcp
fi

# Charger le fichier .env s'il existe
if [ -f .env ]; then
    echo "📄 Chargement du fichier .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Variables d'environnement
export NOTION_TOKEN="${NOTION_TOKEN:-}"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

if [ -z "$NOTION_TOKEN" ]; then
    echo "⚠️  NOTION_TOKEN non défini - mode simulation activé"
    echo "💡 Pour utiliser l'API Notion réelle, définissez NOTION_TOKEN"
else
    echo "✅ NOTION_TOKEN configuré - mode API réel"
fi

# Démarrer le serveur MCP
echo "🔗 Démarrage du serveur MCP sur stdio..."
python3 mcp-notion-server.py

echo "👋 Serveur MCP Notion arrêté"
