#!/usr/bin/env python3
"""
VOICE CONTROLLER HACKATHON FINAL
Contrôleur vocal OpenAI Realtime API + Serveur MCP
Pour hackathon - Interface vocale naturelle pour gestion de fichiers
"""
import asyncio
import json
import os
import sys
import sounddevice as sd
import numpy as np
import websockets
from dotenv import load_dotenv
from pathlib import Path
import threading
import signal
import queue
import base64
import subprocess
import tempfile

load_dotenv()

class VoiceControllerHackathon:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview-2024-10-01')
        self.ws = None
        self.is_recording = False
        self.desktop_path = Path.home() / "Desktop"
        self.recording_stopped = threading.Event()
        self.mcp_server_path = Path(__file__).parent / "mcp_server.py"
        
        # Audio management
        self.audio_queue = queue.Queue(maxsize=200)
        self.current_volume = 0.0
        self.show_volume_bar = True
        
        # Connection state
        self.connection_active = True
        self.session_created = False
        
        print(f"🎯 Voice Controller Hackathon initialisé")
        print(f"📁 Chemin MCP: {self.mcp_server_path}")
        print(f"📁 Desktop: {self.desktop_path}")

    # ========== CONNEXION AU SERVEUR MCP ==========
    async def call_mcp_server(self, function_name, arguments):
        """Appeler le vrai serveur MCP via subprocess"""
        print(f"🔧 Appel MCP: {function_name} avec {arguments}")
        
        # Créer la requête MCP selon le protocole standard
        mcp_request = {
            "jsonrpc": "2.0",
            "id": f"voice_call_{hash(str(arguments))}",
            "method": "tools/call",
            "params": {
                "name": function_name,
                "arguments": arguments
            }
        }
        
        try:
            # Lancer le serveur MCP
            process = subprocess.Popen(
                [sys.executable, str(self.mcp_server_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.mcp_server_path.parent)
            )
            
            # Envoyer la requête
            request_json = json.dumps(mcp_request) + '\n'
            stdout, stderr = process.communicate(input=request_json, timeout=10)
            
            if stderr:
                print(f"⚠️ MCP stderr: {stderr}")
            
            # Parser la réponse
            if stdout.strip():
                try:
                    response = json.loads(stdout.strip())
                    if 'result' in response:
                        # Extraire le texte de la réponse MCP
                        result = response['result']
                        if isinstance(result, dict) and 'content' in result:
                            content = result['content']
                            if isinstance(content, list) and len(content) > 0:
                                return content[0].get('text', str(result))
                        return str(result)
                    elif 'error' in response:
                        return f"❌ Erreur MCP: {response['error']}"
                    else:
                        return f"✅ Commande exécutée: {response}"
                except json.JSONDecodeError as e:
                    print(f"❌ Erreur parsing JSON: {e}")
                    print(f"Raw output: {stdout}")
                    return f"❌ Réponse MCP invalide"
            else:
                return "❌ Aucune réponse du serveur MCP"
                
        except subprocess.TimeoutExpired:
            process.kill()
            return "❌ Timeout du serveur MCP"
        except Exception as e:
            return f"❌ Erreur appel MCP: {e}"

    # ========== FONCTIONS MCP (FALLBACK LOCAL) ==========
    def create_folder_local(self, folder_path):
        """Version locale de create_folder avec effet visuel"""
        try:
            full_path = self.desktop_path / folder_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            # BONUS: Ouvrir dans Finder pour la démo
            subprocess.run(['open', '-R', str(full_path)], check=False)
            
            return f"✅ Dossier créé et ouvert dans Finder: {folder_path}"
        except Exception as e:
            return f"❌ Erreur création dossier: {e}"
    
    def create_file_local(self, file_path):
        """Version locale de create_file"""
        try:
            full_path = self.desktop_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()
            
            # Ouvrir le fichier si c'est un type éditable
            if full_path.suffix.lower() in ['.txt', '.md', '.py', '.js']:
                subprocess.run(['open', str(full_path)], check=False)
            
            return f"✅ Fichier créé: {file_path}"
        except Exception as e:
            return f"❌ Erreur création fichier: {e}"
    
    def list_contents_local(self, folder_path=""):
        """Version locale de list_contents"""
        try:
            target_path = self.desktop_path / folder_path if folder_path else self.desktop_path
            
            if not target_path.exists():
                return f"❌ Dossier introuvable: {folder_path or 'Desktop'}"
            
            items = list(target_path.iterdir())
            if not items:
                return f"📁 Le dossier {folder_path or 'Desktop'} est vide"
            
            result = f"📁 Contenu du {folder_path or 'Desktop'}:\n"
            for item in sorted(items):
                icon = "📁" if item.is_dir() else "📄"
                result += f"  {icon} {item.name}\n"
            return result.strip()
        except Exception as e:
            return f"❌ Erreur lecture dossier: {e}"

    async def execute_function_call(self, function_name, arguments):
        """Exécuter un appel de fonction - MCP puis fallback local"""
        print(f"🛠️ Exécution: {function_name}")
        print(f"📋 Arguments: {arguments}")
        
        # Essayer d'abord le serveur MCP
        try:
            result = await self.call_mcp_server(function_name, arguments)
            
            # Si le serveur MCP fonctionne, utiliser son résultat
            if not result.startswith("❌"):
                print(f"✅ MCP Success: {result}")
                return result
            else:
                print(f"⚠️ MCP Failed, falling back to local: {result}")
        except Exception as e:
            print(f"⚠️ MCP Error, falling back to local: {e}")
        
        # Fallback vers les fonctions locales avec effets visuels
        try:
            if function_name == "create_folder":
                return self.create_folder_local(arguments.get("folder_path", ""))
            elif function_name == "create_file":
                return self.create_file_local(arguments.get("file_path", ""))
            elif function_name == "list_contents":
                return self.list_contents_local(arguments.get("folder_path", ""))
            else:
                return f"❌ Fonction inconnue: {function_name}"
        except Exception as e:
            return f"❌ Erreur exécution locale: {e}"

    # ========== CONNEXION OPENAI REALTIME ==========
    async def connect_to_realtime(self):
        """Se connecter à l'API OpenAI Realtime"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'OpenAI-Beta': 'realtime=v1'
        }
        
        uri = f"wss://api.openai.com/v1/realtime?model={self.model}"
        
        try:
            print("🔗 Connexion à OpenAI Realtime API...")
            self.ws = await websockets.connect(
                uri, 
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
                max_size=None
            )
            print("✅ Connexion WebSocket établie!")
            return True
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return False

    async def send_session_update(self):
        """Configuration session OpenAI avec outils MCP"""
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": """Tu es un assistant vocal français expert en gestion de fichiers sur Mac.

MISSION: Aider l'utilisateur à organiser ses fichiers via des commandes vocales naturelles.

OUTILS DISPONIBLES:
- create_folder: Créer des dossiers et sous-dossiers
- create_file: Créer des fichiers vides
- list_contents: Lister le contenu du bureau ou dossiers

EXEMPLES D'USAGE:
- "Crée un dossier projet" → create_folder avec folder_path="projet"
- "Crée 3 dossiers pour mes clients" → créer "client-1", "client-2", "client-3"
- "Crée un fichier readme dans le dossier projet" → create_file avec file_path="projet/readme.txt"
- "Montre-moi ce qu'il y a sur le bureau" → list_contents

COMPORTEMENT:
- TOUJOURS utiliser les outils pour les demandes de fichiers
- Confirmer les actions effectuées
- Réponses courtes et naturelles
- Si plusieurs dossiers demandés, les créer un par un
- Adapter les noms selon le contexte (si l'utilisateur dit "3 dossiers", créer des noms logiques)

IMPORTANT: Exécute immédiatement les demandes sans demander de confirmation supplémentaire.""",
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
                    "silence_duration_ms": 800
                },
                "tools": [
                    {
                        "type": "function",
                        "name": "create_folder",
                        "description": "Créer un nouveau dossier sur le bureau Mac",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "folder_path": {
                                    "type": "string",
                                    "description": "Nom ou chemin du dossier à créer (ex: 'mon-projet', 'client-michelin', 'projet/sous-dossier')"
                                }
                            },
                            "required": ["folder_path"]
                        }
                    },
                    {
                        "type": "function",
                        "name": "create_file",
                        "description": "Créer un nouveau fichier vide",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Nom ou chemin du fichier à créer (ex: 'readme.txt', 'projet/notes.md')"
                                }
                            },
                            "required": ["file_path"]
                        }
                    },
                    {
                        "type": "function",
                        "name": "list_contents",
                        "description": "Lister le contenu du bureau ou d'un dossier",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "folder_path": {
                                    "type": "string",
                                    "description": "Dossier à lister (vide = bureau)"
                                }
                            }
                        }
                    }
                ],
                "tool_choice": "auto"
            }
        }
        
        try:
            await self.ws.send(json.dumps(session_config))
            print("📤 Configuration session envoyée")
        except Exception as e:
            print(f"❌ Erreur envoi config: {e}")

    # ========== GESTION ÉVÉNEMENTS ==========
    async def listen_to_server_events(self):
        """Écouter les événements du serveur"""
        try:
            async for message in self.ws:
                try:
                    event = json.loads(message)
                    await self.handle_server_event(event)
                except json.JSONDecodeError:
                    print(f"❌ JSON invalide: {message}")
                except Exception as e:
                    print(f"❌ Erreur événement: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connexion fermée")
            self.connection_active = False
        except Exception as e:
            print(f"❌ Erreur écoute: {e}")
            self.connection_active = False

    async def handle_server_event(self, event):
        """Gérer les événements serveur"""
        event_type = event.get("type")
        
        if event_type == "session.created":
            print("✅ Session créée - Prêt à enregistrer!")
            self.session_created = True
            
        elif event_type == "input_audio_buffer.speech_started":
            print("🎤 🟢 Parole détectée...")
            
        elif event_type == "input_audio_buffer.speech_stopped":
            print("🔇 🔴 Fin de parole - Traitement...")
            
        elif event_type == "conversation.item.input_audio_transcription.completed":
            transcript = event.get("transcript", "")
            print(f"📝 Vous avez dit: '{transcript}'")
            
        elif event_type == "response.function_call_arguments.done":
            # Appel de fonction
            function_name = event.get("name")
            arguments_str = event.get("arguments", "{}")
            call_id = event.get("call_id")
            
            print(f"📞 Fonction appelée: {function_name}")
            
            try:
                arguments = json.loads(arguments_str) if arguments_str else {}
            except:
                arguments = {}
            
            # Exécuter la fonction
            result = await self.execute_function_call(function_name, arguments)
            print(f"📤 Résultat: {result}")
            
            # Retourner le résultat à OpenAI
            function_result = {
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": str(result)
                }
            }
            
            await self.safe_send(json.dumps(function_result))
            
            # Demander réponse
            await self.safe_send(json.dumps({"type": "response.create"}))
            
        elif event_type == "response.text.delta":
            text = event.get("delta", "")
            print(text, end="", flush=True)
            
        elif event_type == "response.done":
            print("\n✅ Assistant terminé")
            
        elif event_type == "error":
            error = event.get("error", {})
            print(f"❌ Erreur: {error}")

    # ========== GESTION AUDIO ==========
    def audio_callback(self, indata, frames, time, status):
        """Callback audio optimisé"""
        if status:
            print(f"⚠️ Audio: {status}")
        
        if self.is_recording and self.ws and self.session_created:
            try:
                # Volume pour feedback
                volume = np.linalg.norm(indata[:, 0]) * 10
                self.current_volume = volume
                
                # Conversion PCM16
                audio_data = (indata[:, 0] * 32767).astype(np.int16)
                
                # Filtrage qualité
                max_amp = np.max(np.abs(audio_data))
                if max_amp > 100:  # Seuil minimum
                    audio_b64 = base64.b64encode(audio_data.tobytes()).decode('utf-8')
                    
                    audio_event = {
                        "type": "input_audio_buffer.append",
                        "audio": audio_b64
                    }
                    
                    try:
                        self.audio_queue.put_nowait(json.dumps(audio_event))
                    except queue.Full:
                        pass
                    
            except Exception as e:
                print(f"❌ Callback error: {e}")

    async def process_audio_queue(self):
        """Traiter la queue audio"""
        while self.connection_active:
            try:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.audio_queue.get(timeout=0.1)
                )
                await self.safe_send(message)
            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"❌ Queue error: {e}")

    async def display_volume_bar(self):
        """Barre de volume en temps réel"""
        while self.show_volume_bar and self.is_recording:
            try:
                bar_length = int(min(self.current_volume, 50))
                
                if bar_length > 30:
                    status = "🔊 EXCELLENT"
                    bar = '█' * bar_length
                elif bar_length > 15:
                    status = "🎤 BON"
                    bar = '▓' * bar_length
                elif bar_length > 5:
                    status = "🔉 FAIBLE"
                    bar = '▒' * bar_length
                else:
                    status = "🔈 SILENCE"
                    bar = '░' * bar_length
                
                empty = '·' * (50 - bar_length)
                print(f"\r{status} |{bar}{empty}| {self.current_volume:.1f}    ", end='', flush=True)
                await asyncio.sleep(0.05)
                
            except:
                break

    async def safe_send(self, message):
        """Envoi sécurisé"""
        try:
            if self.ws and self.connection_active:
                await self.ws.send(message)
                return True
        except:
            return False

    # ========== ENREGISTREMENT ==========
    def wait_for_enter(self):
        """Attendre entrée utilisateur"""
        try:
            input("Appuyez sur Entrée pour arrêter...")
            self.recording_stopped.set()
        except:
            self.recording_stopped.set()

    async def start_recording(self):
        """Démarrer enregistrement vocal"""
        if not self.session_created:
            print("❌ Connectez-vous d'abord!")
            return
        
        self.is_recording = True
        self.recording_stopped.clear()
        
        print("\n" + "="*60)
        print("🎤 🔴 ENREGISTREMENT HACKATHON")
        print("="*60)
        print("💬 Exemples de commandes:")
        print("   • 'Crée un dossier projet-hackathon'")
        print("   • 'Crée 3 dossiers pour mes clients'")
        print("   • 'Crée un fichier readme dans le projet'")
        print("   • 'Montre-moi le bureau'")
        print("="*60)
        print("🎤 PARLEZ MAINTENANT...")
        
        # Thread pour input utilisateur
        input_thread = threading.Thread(target=self.wait_for_enter)
        input_thread.daemon = True
        input_thread.start()
        
        try:
            with sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=24000,
                dtype=np.float32,
                blocksize=1024,
                latency='low'
            ):
                volume_task = asyncio.create_task(self.display_volume_bar())
                
                while not self.recording_stopped.is_set():
                    await asyncio.sleep(0.1)
                
                volume_task.cancel()
                
        except Exception as e:
            print(f"❌ Erreur enregistrement: {e}")
        
        self.is_recording = False
        print(f"\n🔇 Enregistrement arrêté - Traitement...")

    # ========== INTERFACE PRINCIPALE ==========
    def show_hackathon_banner(self):
        """Banner hackathon"""
        print("\n" + "="*70)
        print("🎤 VOICE FILE CONTROLLER - HACKATHON DEMO")
        print("="*70)
        print("🚀 OpenAI Realtime API + MCP Server Integration")
        print("🎯 Interface vocale naturelle pour gestion de fichiers")
        print("👨‍💻 Designer industriel → Contrôle digital par voix")
        print("="*70)

    def show_menu(self):
        """Menu hackathon"""
        print("\n🎛️ CONTRÔLES:")
        print("🔗 1 - Connexion OpenAI Realtime")
        print("🎤 2 - Commande vocale")
        print("📋 3 - Test MCP local")
        print("🎯 d - Mode démo continue") 
        print("❌ q - Quitter")

    async def demo_mode(self):
        """Mode démo pour hackathon"""
        print("\n🎯 MODE DÉMO HACKATHON ACTIVÉ")
        print("🎤 Parlez en continu - Ctrl+C pour arrêter")
        
        try:
            while self.connection_active:
                await self.start_recording()
                await asyncio.sleep(1)  # Pause entre enregistrements
        except KeyboardInterrupt:
            print("\n🔚 Fin du mode démo")

    async def run(self):
        """Fonction principale hackathon"""
        self.show_hackathon_banner()
        
        try:
            while True:
                self.show_menu()
                choice = input("\n👉 Choix: ").strip().lower()
                
                if choice == 'q':
                    break
                    
                elif choice == '1':
                    if await self.connect_to_realtime():
                        await self.send_session_update()
                        
                        # Tâches en arrière-plan
                        asyncio.create_task(self.listen_to_server_events())
                        asyncio.create_task(self.process_audio_queue())
                        
                        print("✅ Système prêt pour le hackathon!")
                        input("Appuyez sur Entrée...")
                        
                elif choice == '2':
                    await self.start_recording()
                    
                elif choice == '3':
                    # Test MCP local
                    print("\n🧪 Test MCP local:")
                    result = await self.execute_function_call("list_contents", {})
                    print(f"{result}")
                    input("Appuyez sur Entrée...")
                    
                elif choice == 'd':
                    if self.session_created:
                        await self.demo_mode()
                    else:
                        print("❌ Connectez-vous d'abord (option 1)")
                        
                else:
                    print("❌ Choix invalide")
                    
        except KeyboardInterrupt:
            print("\n👋 Merci pour le hackathon!")
        finally:
            self.connection_active = False
            if self.ws:
                await self.ws.close()

def signal_handler(sig, frame):
    print('\n🛑 Arrêt du système...')
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🎯 HACKATHON VOICE FILE CONTROLLER")
    print("🔧 Initialisation...")
    
    try:
        controller = VoiceControllerHackathon()
        asyncio.run(controller.run())
    except KeyboardInterrupt:
        print("\n🏁 Hackathon terminé!")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")