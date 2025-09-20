#!/usr/bin/env python3
"""
Voice Controller robuste avec gestion d'erreurs améliorée
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

load_dotenv()

class VoiceControllerRobust:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview')
        self.ws = None
        self.is_recording = False
        self.desktop_path = Path.home() / "Desktop"
        self.recording_stopped = threading.Event()
        # Queue thread-safe pour communiquer entre le callback audio et asyncio
        self.audio_queue = queue.Queue(maxsize=100)
        # État de connexion
        self.connection_active = True
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        # Variables pour le feedback visuel
        self.current_volume = 0.0
        self.show_volume_bar = False
        
    # ========== FONCTIONS D'OUTILS ==========
    def create_folder(self, folder_path):
        """Créer un dossier"""
        try:
            full_path = self.desktop_path / folder_path
            full_path.mkdir(parents=True, exist_ok=True)
            return f"✅ Dossier créé: {full_path.name}"
        except Exception as e:
            return f"❌ Erreur création dossier: {e}"
    
    def create_file(self, file_path):
        """Créer un fichier vide"""
        try:
            full_path = self.desktop_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()
            return f"✅ Fichier créé: {full_path.name}"
        except Exception as e:
            return f"❌ Erreur création fichier: {e}"
    
    def list_contents(self, folder_path=""):
        """Lister le contenu d'un dossier"""
        try:
            if folder_path:
                target_path = self.desktop_path / folder_path
            else:
                target_path = self.desktop_path
            
            if not target_path.exists():
                return f"❌ Dossier introuvable: {target_path}"
            
            items = list(target_path.iterdir())
            if not items:
                return f"📁 Dossier vide: {target_path.name}"
            
            result = f"📁 Contenu de {target_path.name}:\n"
            for item in sorted(items):
                icon = "📁" if item.is_dir() else "📄"
                result += f"  {icon} {item.name}\n"
            return result
        except Exception as e:
            return f"❌ Erreur lecture dossier: {e}"
    
    async def execute_function_call(self, function_name, arguments):
        """Exécuter un appel de fonction"""
        print(f"🛠️ Exécution: {function_name}({arguments})")
        
        try:
            if function_name == "create_folder":
                return self.create_folder(arguments.get("folder_path", ""))
            elif function_name == "create_file":
                return self.create_file(arguments.get("file_path", ""))
            elif function_name == "list_contents":
                return self.list_contents(arguments.get("folder_path", ""))
            else:
                return f"❌ Fonction inconnue: {function_name}"
        except Exception as e:
            return f"❌ Erreur exécution: {e}"
    
    # ========== CONNEXION ET CONFIGURATION ==========
    async def connect_to_realtime(self, max_retries=3):
        """Se connecter à l'API OpenAI Realtime avec retry logic"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'OpenAI-Beta': 'realtime=v1'
        }
        
        uri = f"wss://api.openai.com/v1/realtime?model={self.model}"
        
        for attempt in range(max_retries):
            try:
                print(f"🔗 Tentative de connexion {attempt + 1}/{max_retries}...")
                
                # Configuration WebSocket optimisée pour la stabilité
                self.ws = await websockets.connect(
                    uri, 
                    additional_headers=headers,
                    ping_interval=30,  # Ping toutes les 30 secondes
                    ping_timeout=10,   # Timeout de 10 secondes pour les pings
                    close_timeout=10,  # Timeout de fermeture
                    max_size=None,     # Pas de limite de taille des messages
                    compression=None   # Désactiver la compression pour réduire la latence
                )
                print("✅ Connecté à OpenAI Realtime API")
                return True
                
            except Exception as e:
                print(f"❌ Erreur de connexion (tentative {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Backoff exponentiel
                    print(f"⏳ Nouvelle tentative dans {wait_time} secondes...")
                    await asyncio.sleep(wait_time)
                else:
                    print("❌ Échec de toutes les tentatives de connexion")
                    
        return False
    
    async def send_session_config(self):
        """Configuration de session avec outils"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": """Tu es un assistant vocal français qui peut gérer des fichiers sur le bureau Mac. 
                
Quand l'utilisateur demande de créer des dossiers/fichiers ou lister le contenu, utilise OBLIGATOIREMENT les outils disponibles.

Exemples:
- "crée 3 dossiers" → utilise create_folder 3 fois avec des noms comme "dossier-1", "dossier-2", "dossier-3"
- "liste le bureau" → utilise list_contents
- "crée un fichier test.txt" → utilise create_file

IMPORTANT: Utilise toujours les outils, ne réponds jamais sans action.""",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1"},
                "tools": [
                    {
                        "type": "function",
                        "name": "create_folder",
                        "description": "Créer un dossier sur le bureau",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "folder_path": {
                                    "type": "string",
                                    "description": "Nom du dossier à créer"
                                }
                            },
                            "required": ["folder_path"]
                        }
                    },
                    {
                        "type": "function",
                        "name": "create_file",
                        "description": "Créer un fichier vide sur le bureau",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Nom du fichier à créer"
                                }
                            },
                            "required": ["file_path"]
                        }
                    },
                    {
                        "type": "function",
                        "name": "list_contents",
                        "description": "Lister le contenu du bureau",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "folder_path": {
                                    "type": "string",
                                    "description": "Chemin du dossier (vide pour le bureau)"
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        try:
            await self.ws.send(json.dumps(config))
            print("📤 Configuration avec outils envoyée")
        except Exception as e:
            print(f"❌ Erreur envoi config: {e}")
    
    async def listen_to_responses(self):
        """Écouter les réponses de l'API avec gestion de reconnexion"""
        while self.connection_active:
            try:
                async for message in self.ws:
                    try:
                        data = json.loads(message)
                        message_type = data.get("type")
                        
                        print(f"🔍 Message reçu: {message_type}")
                        
                        if message_type == "session.created":
                            print("✅ Session créée")
                            self.reconnect_attempts = 0  # Reset sur succès
                        elif message_type == "input_audio_buffer.speech_started":
                            print("🎤 Parole détectée")
                        elif message_type == "input_audio_buffer.speech_stopped":
                            print("🔇 Fin de parole")
                        elif message_type == "conversation.item.input_audio_transcription.completed":
                            transcript = data.get("transcript", "")
                            print(f"📝 Vous avez dit: '{transcript}'")
                        elif message_type == "response.function_call_arguments.delta":
                            # Arguments de fonction en cours
                            print("📞 Préparation appel de fonction...")
                        elif message_type == "response.function_call_arguments.done":
                            # Appel de fonction terminé
                            function_name = data.get("name")
                            arguments_str = data.get("arguments", "{}")
                            call_id = data.get("call_id")
                            
                            try:
                                arguments = json.loads(arguments_str) if arguments_str else {}
                            except json.JSONDecodeError:
                                arguments = {}
                            
                            # Exécuter la fonction
                            result = await self.execute_function_call(function_name, arguments)
                            print(f"📤 Résultat: {result}")
                            
                            # Envoyer le résultat à l'API
                            function_result = {
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "function_call_output",
                                    "call_id": call_id,
                                    "output": str(result)
                                }
                            }
                            await self.safe_send(json.dumps(function_result))
                            
                            # Demander une nouvelle réponse
                            await self.safe_send(json.dumps({"type": "response.create"}))
                            
                        elif message_type == "response.text.delta":
                            text = data.get("delta", "")
                            print(text, end="", flush=True)
                        elif message_type == "response.done":
                            print("\n✅ Réponse terminée")
                        elif message_type == "error":
                            error_details = data.get("error", {})
                            print(f"❌ Erreur API: {error_details}")
                        
                    except json.JSONDecodeError:
                        print(f"❌ Erreur parsing JSON: {message}")
                    except Exception as e:
                        print(f"❌ Erreur traitement message: {e}")
                        
            except websockets.exceptions.ConnectionClosed as e:
                print(f"🔌 Connexion fermée: {e}")
                if self.connection_active and not await self.handle_reconnection():
                    break
            except Exception as e:
                print(f"❌ Erreur écoute: {e}")
                if self.connection_active and not await self.handle_reconnection():
                    break
    
    async def handle_reconnection(self):
        """Gère la reconnexion automatique"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print(f"❌ Nombre maximum de tentatives de reconnexion atteint ({self.max_reconnect_attempts})")
            self.connection_active = False
            return False
        
        self.reconnect_attempts += 1
        wait_time = min(30, 2 ** self.reconnect_attempts)  # Backoff avec maximum de 30s
        
        print(f"🔄 Tentative de reconnexion {self.reconnect_attempts}/{self.max_reconnect_attempts} dans {wait_time}s...")
        await asyncio.sleep(wait_time)
        
        if await self.connect_to_realtime(max_retries=1):
            print("✅ Reconnexion réussie!")
            await self.send_session_config()
            return True
        else:
            print("❌ Échec de la reconnexion")
            return False
    
    def audio_callback(self, indata, frames, time, status):
        """Callback pour l'audio en temps réel - VERSION CORRIGÉE"""
        if status:
            print(f"⚠️ Statut audio: {status}")
        
        if self.is_recording and self.ws:
            try:
                # Convertir en PCM16
                audio_data = (indata[:, 0] * 32767).astype(np.int16)
                
                # Calculer le volume pour le feedback visuel
                volume_norm = np.linalg.norm(indata[:, 0]) * 10
                self.current_volume = volume_norm
                
                # Vérifier que les données ne sont pas silencieuses
                max_amplitude = np.max(np.abs(audio_data))
                if max_amplitude > 10:  # Seuil très bas (corrigé de 100 à 10)
                    audio_b64 = self.numpy_to_base64(audio_data)
                    
                    # Envoyer à l'API de manière sécurisée
                    message = {
                        "type": "input_audio_buffer.append",
                        "audio": audio_b64
                    }
                    
                    # ✅ SOLUTION: Utiliser une queue thread-safe au lieu d'asyncio
                    try:
                        self.audio_queue.put_nowait(json.dumps(message))
                    except queue.Full:
                        # Si la queue est pleine, on ignore ce chunk audio
                        pass
                    
            except Exception as e:
                print(f"❌ Erreur callback audio: {e}")
    
    async def process_audio_queue(self):
        """Traiter la queue d'audio de manière asynchrone"""
        while True:
            try:
                # Attendre un message de la queue avec timeout
                message = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.audio_queue.get(timeout=0.1)
                )
                await self.safe_send(message)
            except queue.Empty:
                # Pas de message, continuer
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"❌ Erreur traitement queue audio: {e}")
    
    async def safe_send(self, message):
        """Envoi sécurisé de message avec gestion d'erreur améliorée"""
        try:
            if self.ws:
                await self.ws.send(message)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connexion fermée lors de l'envoi")
            # Ne pas imprimer l'erreur de keepalive ping timeout répétitivement
            return
        except Exception as e:
            # Filtrer les erreurs de keepalive ping timeout répétitives
            if "keepalive ping timeout" not in str(e):
                print(f"❌ Erreur envoi: {e}")
    
    def numpy_to_base64(self, audio_data):
        """Convertir numpy array en base64"""
        import base64
        return base64.b64encode(audio_data.tobytes()).decode('utf-8')
    
    def wait_for_enter(self):
        """Attendre l'entrée utilisateur dans un thread séparé"""
        try:
            input("Appuyez sur Entrée pour arrêter...")
            self.recording_stopped.set()
        except:
            self.recording_stopped.set()
    
    async def start_recording(self):
        """Démarrer l'enregistrement"""
        self.is_recording = True
        self.recording_stopped.clear()
        print("🎤 Enregistrement démarré - Parlez maintenant!")
        
        # Démarrer l'attente d'entrée dans un thread
        input_thread = threading.Thread(target=self.wait_for_enter)
        input_thread.daemon = True
        input_thread.start()
        
        try:
            with sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=24000,
                dtype=np.float32
            ):
                # Attendre que l'utilisateur appuie sur Entrée
                while not self.recording_stopped.is_set():
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            print(f"❌ Erreur enregistrement: {e}")
        
        self.is_recording = False
        print("🔇 Enregistrement arrêté")
        
        # Finaliser l'audio
        try:
            await self.ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
            await self.ws.send(json.dumps({"type": "response.create"}))
            print("📤 Audio envoyé pour traitement")
        except Exception as e:
            print(f"❌ Erreur finalisation: {e}")
    
    def show_test_menu(self):
        """Affiche le menu des commandes de test"""
        print("\n" + "="*50)
        print("🧪 MODE TEST - COMMANDES CLAVIER")
        print("="*50)
        print("1️⃣  - Créer un dossier 'test-dossier'")
        print("2️⃣  - Créer 3 dossiers (dossier-1, dossier-2, dossier-3)")
        print("3️⃣  - Créer un fichier 'test.txt'")
        print("4️⃣  - Créer plusieurs fichiers (.txt, .py, .md)")
        print("5️⃣  - Lister le contenu du bureau")
        print("6️⃣  - Créer une structure projet complète")
        print("🎤 - Passer en mode vocal (Entrée)")
        print("❌ - Quitter (q)")
        print("="*50)
    
    async def execute_test_command(self, command):
        """Exécute une commande de test selon le numéro choisi"""
        print(f"\n🧪 Exécution de la commande de test: {command}")
        
        if command == "1":
            # Test: créer un dossier
            result = await self.execute_function_call("create_folder", {"folder_path": "test-dossier"})
            print(f"📤 Résultat: {result}")
            
        elif command == "2":
            # Test: créer 3 dossiers
            for i in range(1, 4):
                result = await self.execute_function_call("create_folder", {"folder_path": f"dossier-{i}"})
                print(f"📤 Résultat: {result}")
                await asyncio.sleep(0.5)  # Petite pause entre les créations
                
        elif command == "3":
            # Test: créer un fichier
            result = await self.execute_function_call("create_file", {"file_path": "test.txt"})
            print(f"📤 Résultat: {result}")
            
        elif command == "4":
            # Test: créer plusieurs fichiers
            files = ["readme.txt", "script.py", "documentation.md", "config.json"]
            for file in files:
                result = await self.execute_function_call("create_file", {"file_path": file})
                print(f"📤 Résultat: {result}")
                await asyncio.sleep(0.3)
                
        elif command == "5":
            # Test: lister le contenu
            result = await self.execute_function_call("list_contents", {"folder_path": ""})
            print(f"📤 Résultat:\n{result}")
            
        elif command == "6":
            # Test: créer une structure projet complète
            print("🏗️ Création d'une structure de projet complète...")
            
            # Créer les dossiers
            folders = ["mon-projet", "mon-projet/src", "mon-projet/docs", "mon-projet/tests"]
            for folder in folders:
                result = await self.execute_function_call("create_folder", {"folder_path": folder})
                print(f"📁 {result}")
                await asyncio.sleep(0.2)
            
            # Créer les fichiers
            files = [
                "mon-projet/README.md",
                "mon-projet/requirements.txt",
                "mon-projet/src/main.py",
                "mon-projet/src/utils.py",
                "mon-projet/docs/guide.md",
                "mon-projet/tests/test_main.py"
            ]
            for file in files:
                result = await self.execute_function_call("create_file", {"file_path": file})
                print(f"📄 {result}")
                await asyncio.sleep(0.2)
                
            print("✅ Structure de projet créée avec succès!")
        
        else:
            print("❌ Commande inconnue")
    
    async def run(self):
        """Fonction principale avec mode test"""
        print("🎤 VOICE CONTROLLER ROBUSTE")
        print("="*40)
        print(f"📁 Bureau: {self.desktop_path}")
        
        if not await self.connect_to_realtime():
            return
        
        await self.send_session_config()
        
        # Démarrer l'écoute des réponses
        response_task = asyncio.create_task(self.listen_to_responses())
        
        # ✅ SOLUTION: Démarrer le traitement de la queue audio
        audio_queue_task = asyncio.create_task(self.process_audio_queue())
        
        try:
            while True:
                try:
                    self.show_test_menu()
                    user_input = input("\n👉 Votre choix: ").strip()
                    
                    if user_input.lower() == 'q':
                        break
                    elif user_input == "":
                        # Mode vocal
                        print("\n🎤 Mode vocal activé - Parlez maintenant!")
                        await self.start_recording()
                        # Attendre un peu avant la prochaine commande
                        await asyncio.sleep(2)
                    elif user_input in ["1", "2", "3", "4", "5", "6"]:
                        # Mode test
                        await self.execute_test_command(user_input)
                        input("\nAppuyez sur Entrée pour continuer...")
                    else:
                        print("❌ Choix invalide. Utilisez 1-6, Entrée (vocal) ou 'q' (quitter)")
                        
                except EOFError:
                    print("\n👋 Au revoir!")
                    break
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
        finally:
            self.connection_active = False  # Arrêter les tentatives de reconnexion
            response_task.cancel()
            audio_queue_task.cancel()
            if self.ws:
                try:
                    await self.ws.close()
                except:
                    pass

if __name__ == "__main__":
    # Gérer proprement Ctrl+C
    def signal_handler(sig, frame):
        print('\n👋 Arrêt du programme...')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(VoiceControllerRobust().run())
    except KeyboardInterrupt:
        print("\n👋 Programme arrêté")