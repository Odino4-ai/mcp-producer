#!/usr/bin/env python3
"""
Integration OpenAI Agents SDK + MCP Notion Server
Connecte le serveur MCP Notion au SDK OpenAI Agents
"""

import asyncio
import os
from pathlib import Path

# Import OpenAI Agents SDK avec MCP
try:
    from openai import OpenAI
    from agents import Agent, Runner
    from agents.mcp import MCPServerStdio
except ImportError as e:
    print("❌ Erreur d'import:", e)
    print("💡 Installez les dépendances:")
    print("   pip install openai-agents")
    exit(1)


class NotionMCPIntegration:
    """Intégration MCP Notion avec OpenAI SDK"""
    
    def __init__(self):
        self.current_dir = Path(__file__).parent
        self.mcp_server_path = self.current_dir / "mcp-notion-server.py"
        
    async def create_notion_agent(self):
        """Crée un agent OpenAI avec accès au serveur MCP Notion"""
        
        # Configuration du serveur MCP Notion en mode Stdio
        async with MCPServerStdio(
            name="Notion MCP Server",
            params={
                "command": "python3",
                "args": [str(self.mcp_server_path)],
                "cwd": str(self.current_dir),
                "env": {
                    "NOTION_TOKEN": os.getenv("NOTION_TOKEN", ""),
                    "PYTHONPATH": str(self.current_dir)
                }
            },
        ) as mcp_server:
            
            # Création de l'agent avec accès MCP
            agent = Agent(
                name="NotionExpert",
                instructions="""
                Vous êtes un expert Notion silencieux et proactif.
                
                🎯 RÈGLES ABSOLUES:
                - Vous écoutez TOUT en silence
                - Vous agissez IMMÉDIATEMENT quand un projet est mentionné
                - Vous créez des structures COMPLÈTES et ANTICIPATOIRES
                
                🏗️ CRÉATION DE PROJETS:
                Dès qu'un nouveau projet est mentionné, vous créez IMMÉDIATEMENT:
                - Page principale avec description complète
                - Structure de dossiers logique et complète
                - Bases de données pour tâches, équipe, ressources
                - Liste de tâches initiale avec tâches anticipées
                - Planning provisoire
                - Sections pour notes de réunion
                
                📋 LISTES DE TÂCHES AUTOMATIQUES:
                - Créez et mettez à jour les to-do lists en temps réel
                - Ajoutez automatiquement les tâches mentionnées
                - Assignez aux bonnes personnes
                - Définissez priorités et échéances
                - Organisez par projet et personne
                
                🔄 MISES À JOUR CONTINUES:
                - Mettez à jour Notion en temps réel pendant la conversation
                - Adaptez la structure selon les nouvelles informations
                - Enrichissez automatiquement le contenu
                - Anticipez les besoins futurs du projet
                
                Utilisez les outils MCP Notion disponibles pour toutes ces opérations.
                """,
                mcp_servers=[mcp_server]
            )
            
            return agent, mcp_server
    
    async def test_notion_integration(self):
        """Test de l'intégration Notion MCP"""
        
        print("🚀 Test de l'intégration OpenAI + MCP Notion...")
        
        try:
            agent, mcp_server = await self.create_notion_agent()
            
            # Test de création de projet
            test_message = """
            Je commence un nouveau projet appelé "Application Mobile E-commerce".
            C'est une application mobile pour vendre des produits en ligne.
            L'équipe comprend: Alice (développeuse), Bob (designer), Charlie (chef de projet).
            Nous devons commencer par la conception, puis le développement, les tests et le déploiement.
            """
            
            print(f"📝 Test avec le message: {test_message}\n")
            
            # Exécution avec l'agent
            result = await Runner.run(
                starting_agent=agent,
                input=test_message
            )
            
            print("✅ Résultat de l'agent:")
            print(result.final_output)
            
            # Test de mise à jour de tâches
            update_message = """
            Pour le projet Application Mobile E-commerce, ajoutons ces nouvelles tâches:
            - Créer les wireframes (Alice, priorité haute, due dans 3 jours)
            - Rechercher les APIs de paiement (Bob, priorité moyenne)
            - Planifier le sprint 1 (Charlie, priorité haute, due demain)
            """
            
            print(f"\n📋 Test de mise à jour avec: {update_message}\n")
            
            result2 = await Runner.run(
                starting_agent=agent,
                input=update_message
            )
            
            print("✅ Résultat de la mise à jour:")
            print(result2.final_output)
            
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            print(f"💡 Détails: {type(e).__name__}")
    
    async def run_interactive_mode(self):
        """Mode interactif avec l'agent Notion"""
        
        print("🎯 Mode interactif - Agent Notion Expert")
        print("💬 Parlez de vos projets, l'agent va automatiquement créer les structures Notion")
        print("❌ Tapez 'quit' pour quitter\n")
        
        try:
            agent, mcp_server = await self.create_notion_agent()
            
            while True:
                try:
                    user_input = input("👤 Vous: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if not user_input:
                        continue
                    
                    print("🤖 Agent Notion en action...")
                    
                    result = await Runner.run(
                        starting_agent=agent,
                        input=user_input
                    )
                    
                    print(f"✅ Action terminée: {result.final_output}\n")
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ Erreur: {e}\n")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
        
        print("👋 Agent Notion arrêté")


async def main():
    """Point d'entrée principal"""
    
    # Vérification des prérequis
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY non défini")
        print("💡 Définissez votre clé API OpenAI:")
        print("   export OPENAI_API_KEY='your-api-key'")
        return
    
    integration = NotionMCPIntegration()
    
    # Vérification du serveur MCP
    if not integration.mcp_server_path.exists():
        print(f"❌ Serveur MCP non trouvé: {integration.mcp_server_path}")
        print("💡 Assurez-vous que mcp-notion-server.py existe")
        return
    
    print("🔗 Intégration OpenAI Agents SDK + MCP Notion")
    print("="*50)
    
    mode = input("Choisissez le mode (1=Test, 2=Interactif): ").strip()
    
    if mode == "1":
        await integration.test_notion_integration()
    elif mode == "2":
        await integration.run_interactive_mode()
    else:
        print("❌ Mode invalide")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Programme arrêté")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
