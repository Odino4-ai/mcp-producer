#!/usr/bin/env python3
"""
Contrôleur vocal simplifié pour la gestion de fichiers
Version sans audio pour tester la connexion et les fonctions MCP
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any

import websockets
from dotenv import load_dotenv


class VoiceControllerSimple:
    """Contrôleur vocal simplifié (sans audio)"""
    
    def __init__(self):
        """Initialise le contrôleur"""
        # Charge les variables d'environnement
        load_dotenv()
        
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview')
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY non trouvée dans les variables d'environnement")
        
        # État de l'application
        self.websocket = None
        self.is_connected = False
        
        print(f"🎤 Voice Controller Simple initialisé")
        print(f"   - Modèle: {self.model}")
        print(f"   - API Key: {self.api_key[:20]}...")
    
    def create_session_config(self) -> Dict[str, Any]:
        """Crée la configuration de session avec les fonctions MCP simulées"""
        return {
            "type": "session.update",
            "session": {
                "modalities": ["text"],  # Pas d'audio pour cette version
                "instructions": """Tu es un assistant pour la gestion de fichiers. Tu peux créer des dossiers, des fichiers, et lister le contenu du système de fichiers. 

Utilise les fonctions disponibles pour répondre aux demandes de l'utilisateur. Réponds de manière concise et utile en français.

Fonctions disponibles:
- create_folder: Créer un dossier
- create_file: Créer un fichier vide
- list_contents: Lister le contenu d'un dossier

Sois amical et professionnel dans tes réponses.""",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200
                },
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "create_folder",
                            "description": "Crée un nouveau dossier sur le Desktop",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "folder_path": {
                                        "type": "string",
                                        "description": "Chemin du dossier à créer (ex: 'mon-projet' ou 'projet/sous-dossier')"
                                    }
                                },
                                "required": ["folder_path"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "create_file",
                            "description": "Crée un fichier vide dans un dossier",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "file_path": {
                                        "type": "string",
                                        "description": "Chemin du fichier à créer (ex: 'mon-fichier.txt' ou 'projet/fichier.txt')"
                                    }
                                },
                                "required": ["file_path"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "list_contents",
                            "description": "Liste le contenu d'un dossier",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "folder_path": {
                                        "type": "string",
                                        "description": "Chemin du dossier à lister (vide pour lister le Desktop)"
                                    }
                                },
                                "required": []
                            }
                        }
                    }
                ],
                "tool_choice": "auto",
                "temperature": 0.8,
                "max_response_output_tokens": 4096
            }
        }
    
    async def connect_to_api(self):
        """Se connecte à l'API OpenAI Realtime"""
        url = f"wss://api.openai.com/v1/realtime?model={self.model}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        print(f"🔗 Connexion à l'API OpenAI Realtime...")
        
        try:
            self.websocket = await websockets.connect(url, additional_headers=headers)
            self.is_connected = True
            print("✅ Connexion WebSocket établie!")
            
            # Envoie la configuration de session
            session_config = self.create_session_config()
            await self.websocket.send(json.dumps(session_config))
            print("📤 Configuration de session envoyée")
            
            # Démarre la tâche de réception des messages
            asyncio.create_task(self.handle_messages())
            
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            self.is_connected = False
            raise
    
    async def handle_messages(self):
        """Gère les messages reçus de l'API"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.process_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connexion fermée par le serveur")
            self.is_connected = False
        except Exception as e:
            print(f"❌ Erreur de réception: {e}")
            self.is_connected = False
    
    async def process_message(self, data: Dict[str, Any]):
        """Traite un message reçu de l'API"""
        message_type = data.get("type")
        
        if message_type == "session.created":
            print("✅ Session créée avec succès")
            
        elif message_type == "session.updated":
            print("✅ Session mise à jour")
            
        elif message_type == "conversation.item.input_text.delta":
            print(f"📝 Texte reçu: {data.get('delta', '')}", end="", flush=True)
            
        elif message_type == "conversation.item.input_text.done":
            print(f"\n✅ Texte complet reçu: {data.get('text', '')}")
            
        elif message_type == "conversation.item.output_text.delta":
            print(f"💬 {data.get('delta', '')}", end="", flush=True)
            
        elif message_type == "conversation.item.output_text.done":
            print(f"\n✅ Réponse complète: {data.get('text', '')}")
            
        elif message_type == "conversation.item.tool_call":
            # Exécute la fonction demandée
            await self.execute_tool_call(data.get("tool_call", {}))
            
        elif message_type == "error":
            print(f"❌ Erreur: {data.get('error', {})}")
            
        else:
            print(f"📨 Message: {message_type}")
    
    async def execute_tool_call(self, tool_call: Dict[str, Any]):
        """Exécute un appel de fonction (simulation des outils MCP)"""
        function_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})
        
        print(f"🔧 Exécution de la fonction: {function_name}")
        
        try:
            if function_name == "create_folder":
                result = await self.create_folder(arguments.get("folder_path", ""))
            elif function_name == "create_file":
                result = await self.create_file(arguments.get("file_path", ""))
            elif function_name == "list_contents":
                result = await self.list_contents(arguments.get("folder_path", ""))
            else:
                result = f"Fonction {function_name} non reconnue"
            
            # Envoie le résultat à l'API
            tool_result = {
                "type": "conversation.item.tool_call.result",
                "tool_call_id": tool_call.get("id"),
                "result": result
            }
            
            await self.websocket.send(json.dumps(tool_result))
            print(f"📤 Résultat envoyé: {result}")
            
        except Exception as e:
            error_result = {
                "type": "conversation.item.tool_call.result",
                "tool_call_id": tool_call.get("id"),
                "result": f"Erreur: {str(e)}"
            }
            await self.websocket.send(json.dumps(error_result))
            print(f"❌ Erreur d'exécution: {e}")
    
    async def create_folder(self, folder_path: str) -> str:
        """Crée un dossier (simulation de l'outil MCP)"""
        if not folder_path:
            return "Erreur: chemin du dossier requis"
        
        try:
            desktop_path = os.path.expanduser("~/Desktop")
            full_path = os.path.join(desktop_path, folder_path)
            
            # Sécurise le chemin
            if not os.path.abspath(full_path).startswith(desktop_path):
                return "Erreur: chemin non autorisé"
            
            os.makedirs(full_path, exist_ok=True)
            return f"Dossier '{folder_path}' créé avec succès sur le Desktop"
            
        except Exception as e:
            return f"Erreur lors de la création du dossier: {str(e)}"
    
    async def create_file(self, file_path: str) -> str:
        """Crée un fichier (simulation de l'outil MCP)"""
        if not file_path:
            return "Erreur: chemin du fichier requis"
        
        try:
            desktop_path = os.path.expanduser("~/Desktop")
            full_path = os.path.join(desktop_path, file_path)
            
            # Sécurise le chemin
            if not os.path.abspath(full_path).startswith(desktop_path):
                return "Erreur: chemin non autorisé"
            
            # Crée le dossier parent si nécessaire
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Crée le fichier vide
            with open(full_path, 'w') as f:
                pass
            
            return f"Fichier '{file_path}' créé avec succès sur le Desktop"
            
        except Exception as e:
            return f"Erreur lors de la création du fichier: {str(e)}"
    
    async def list_contents(self, folder_path: str) -> str:
        """Liste le contenu d'un dossier (simulation de l'outil MCP)"""
        try:
            desktop_path = os.path.expanduser("~/Desktop")
            if folder_path:
                full_path = os.path.join(desktop_path, folder_path)
            else:
                full_path = desktop_path
            
            # Sécurise le chemin
            if not os.path.abspath(full_path).startswith(desktop_path):
                return "Erreur: chemin non autorisé"
            
            if not os.path.exists(full_path):
                return f"Le dossier '{folder_path or 'Desktop'}' n'existe pas"
            
            if not os.path.isdir(full_path):
                return f"Le chemin '{folder_path}' n'est pas un dossier"
            
            items = os.listdir(full_path)
            if not items:
                return f"Le dossier '{folder_path or 'Desktop'}' est vide"
            
            # Formate la liste
            result = f"Contenu du dossier '{folder_path or 'Desktop'}':\n"
            for item in sorted(items):
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    result += f"📁 {item}/\n"
                else:
                    size = os.path.getsize(item_path)
                    size_str = f"{size} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                    result += f"📄 {item} ({size_str})\n"
            
            return result
            
        except Exception as e:
            return f"Erreur lors de la lecture du dossier: {str(e)}"
    
    async def send_text_message(self, text: str):
        """Envoie un message texte à l'API"""
        if not self.websocket or not self.is_connected:
            print("❌ Pas de connexion active")
            return
        
        message = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": text
                    }
                ]
            }
        }
        
        await self.websocket.send(json.dumps(message))
        print(f"📤 Message envoyé: {text}")
    
    async def run(self):
        """Lance le contrôleur simplifié"""
        try:
            # Connexion à l'API
            await self.connect_to_api()
            
            print("\n" + "="*60)
            print("🎤 VOICE CONTROLLER SIMPLE (Mode Texte)")
            print("="*60)
            print("Commandes disponibles:")
            print("  - Tapez votre message et appuyez sur Entrée")
            print("  - Ctrl+C pour quitter")
            print("="*60)
            
            # Boucle principale
            while self.is_connected:
                try:
                    # Attend l'entrée utilisateur
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, input, "\n💬 Votre message: "
                    )
                    
                    if user_input.strip():
                        await self.send_text_message(user_input.strip())
                    
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
            
        except Exception as e:
            print(f"❌ Erreur fatale: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Nettoie les ressources"""
        print("\n🧹 Nettoyage des ressources...")
        
        if self.websocket:
            await self.websocket.close()
        
        print("✅ Nettoyage terminé")


async def main():
    """Point d'entrée principal"""
    try:
        controller = VoiceControllerSimple()
        await controller.run()
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())




