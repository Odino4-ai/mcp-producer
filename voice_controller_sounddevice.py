#!/usr/bin/env python3
"""
Contrôleur vocal utilisant sounddevice pour la capture audio
Envoie l'audio à l'API OpenAI Realtime
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, List

import sounddevice as sd
import numpy as np
import websockets
from dotenv import load_dotenv


class VoiceControllerSoundDevice:
    """Contrôleur vocal avec sounddevice"""
    
    def __init__(self):
        """Initialise le contrôleur"""
        # Charge les variables d'environnement
        load_dotenv()
        
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview')
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY non trouvée dans les variables d'environnement")
        
        # Configuration audio
        self.sample_rate = 24000
        self.channels = 1
        
        # État de l'application
        self.websocket = None
        self.is_connected = False
        self.is_recording = False
        
        print(f"🎤 Voice Controller SoundDevice initialisé")
        print(f"   - Modèle: {self.model}")
        print(f"   - API Key: {self.api_key[:20]}...")
        print(f"   - Sample Rate: {self.sample_rate}Hz")
    
    def create_session_config(self) -> Dict[str, Any]:
        """Crée la configuration de session avec les fonctions MCP simulées"""
        return {
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "instructions": """Tu es un assistant vocal pour la gestion de fichiers. Tu peux créer des dossiers, des fichiers, et lister le contenu du système de fichiers. 

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
                        "name": "create_folder",
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
                        "name": "create_file",
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
                        "name": "list_contents",
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
            
        elif message_type == "conversation.item.input_audio_buffer.speech_started":
            print("🗣️ Détection de parole...")
            
        elif message_type == "conversation.item.input_audio_buffer.speech_stopped":
            print("⏹️ Fin de parole détectée")
            
        elif message_type == "conversation.item.output_text.delta":
            print(f"💬 {data.get('delta', '')}", end="", flush=True)
            
        elif message_type == "conversation.item.output_text.done":
            print(f"\n✅ Réponse complète: {data.get('text', '')}")
            
        elif message_type == "conversation.item.output_audio_buffer.speech_started":
            print("🔊 Début de la réponse audio...")
            
        elif message_type == "conversation.item.output_audio_buffer.speech_stopped":
            print("🔇 Fin de la réponse audio")
            
        elif message_type == "conversation.item.output_audio_buffer.delta":
            # Joue l'audio reçu
            await self.play_audio_chunk(data.get("delta", []))
            
        elif message_type == "conversation.item.output_audio_buffer.done":
            print("🎵 Audio complet reçu")
            
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
    
    async def play_audio_chunk(self, audio_data: List[int]):
        """Joue un chunk d'audio reçu de l'API"""
        if not audio_data:
            return
        
        try:
            # Convertit les données en numpy array
            audio_array = np.array(audio_data, dtype=np.int16)
            
            # Joue l'audio
            sd.play(audio_array, samplerate=self.sample_rate)
            sd.wait()
            
        except Exception as e:
            print(f"❌ Erreur de lecture audio: {e}")
    
    def start_recording(self):
        """Démarre l'enregistrement audio"""
        if self.is_recording:
            return
        
        self.is_recording = True
        
        def callback(indata, frames, time, status):
            if status:
                print(f"❌ Erreur de flux: {status}")
            if self.websocket and self.is_connected:
                audio_array = indata[:, 0] * 32768  # Convertit en PCM16
                audio_message = {
                    "type": "conversation.item.input_audio_buffer.append",
                    "audio": audio_array.astype(np.int16).tolist()
                }
                
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.websocket.send(json.dumps(audio_message)),
                        asyncio.get_event_loop()
                    )
                except Exception as e:
                    print(f"❌ Erreur d'envoi audio: {e}")
        
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=callback
        )
        self.stream.start()
        print("🎤 Enregistrement en cours... (Appuyez sur Entrée pour arrêter)")
    
    def stop_recording(self):
        """Arrête l'enregistrement audio"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        self.stream.stop()
        self.stream.close()
        
        # Envoie la fin de l'audio
        if self.websocket and self.is_connected:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.websocket.send(json.dumps({
                        "type": "conversation.item.input_audio_buffer.commit"
                    })),
                    asyncio.get_event_loop()
                )
            except Exception as e:
                print(f"❌ Erreur d'envoi fin audio: {e}")
    
    async def run(self):
        """Lance le contrôleur vocal"""
        try:
            # Connexion à l'API
            await self.connect_to_api()
            
            print("\n" + "="*60)
            print("🎤 VOICE CONTROLLER SOUNDDEVICE")
            print("="*60)
            print("Commandes:")
            print("  - Appuyez sur ENTRÉE pour commencer à parler")
            print("  - Appuyez sur ENTRÉE à nouveau pour arrêter")
            print("  - Ctrl+C pour quitter")
            print("="*60)
            
            # Boucle principale
            while self.is_connected:
                try:
                    # Attend l'entrée utilisateur
                    await asyncio.get_event_loop().run_in_executor(
                        None, input, "Appuyez sur ENTRÉE pour parler (Ctrl+C pour quitter): "
                    )
                    
                    if self.is_recording:
                        self.stop_recording()
                    else:
                        self.start_recording()
                        
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
        
        if self.is_recording:
            self.stop_recording()
        
        if self.websocket:
            await self.websocket.close()
        
        print("✅ Nettoyage terminé")


async def main():
    """Point d'entrée principal"""
    try:
        controller = VoiceControllerSoundDevice()
        await controller.run()
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
