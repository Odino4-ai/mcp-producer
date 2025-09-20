#!/usr/bin/env python3
"""
Contrôleur Vocal vers MCP
Fait le lien entre la transcription vocale et l'exécution des fonctions MCP
avec retour audio de confirmation
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
import re
import time

load_dotenv()

class VoiceToMCPController:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview-2024-10-01')
        self.ws = None
        self.is_recording = False
        self.desktop_path = Path.home() / "Desktop"
        self.recording_stopped = threading.Event()
        
        # Audio management
        self.audio_queue = queue.Queue(maxsize=200)
        self.current_volume = 0.0
        self.show_volume_bar = True
        
        # Connection state
        self.connection_active = True
        self.session_created = False
        
        # MCP integration
        self.last_transcript = ""
        self.pending_action = None
        
    # ========== FONCTIONS MCP ==========
    def create_folder(self, folder_path):
        """Créer un dossier"""
        try:
            full_path = self.desktop_path / folder_path
            full_path.mkdir(parents=True, exist_ok=True)
            return f"Dossier {folder_path} créé avec succès sur le bureau"
        except Exception as e:
            return f"Erreur lors de la création du dossier: {e}"
    
    def create_file(self, file_path):
        """Créer un fichier"""
        try:
            full_path = self.desktop_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()
            return f"Fichier {file_path} créé avec succès sur le bureau"
        except Exception as e:
            return f"Erreur lors de la création du fichier: {e}"
    
    def list_contents(self, folder_path=""):
        """Lister le contenu"""
        try:
            if folder_path:
                target_path = self.desktop_path / folder_path
                location = f"du dossier {folder_path}"
            else:
                target_path = self.desktop_path
                location = "du bureau"
            
            if not target_path.exists():
                return f"Le dossier {folder_path or 'bureau'} n'existe pas"
            
            items = list(target_path.iterdir())
            if not items:
                return f"Le {folder_path or 'bureau'} est vide"
            
            folders = [item.name for item in items if item.is_dir()]
            files = [item.name for item in items if item.is_file()]
            
            result = f"Contenu {location}: "
            if folders:
                result += f"{len(folders)} dossier(s): {', '.join(folders[:3])}"
                if len(folders) > 3:
                    result += f" et {len(folders)-3} autres"
            if files:
                if folders:
                    result += ". "
                result += f"{len(files)} fichier(s): {', '.join(files[:3])}"
                if len(files) > 3:
                    result += f" et {len(files)-3} autres"
            
            return result
        except Exception as e:
            return f"Erreur lors de la lecture: {e}"
    
    # ========== ANALYSE DES COMMANDES VOCALES ==========
    def parse_voice_command(self, transcript):
        """Analyser la transcription pour identifier les commandes MCP"""
        transcript_lower = transcript.lower().strip()
        
        print(f"🔍 Analyse de la commande: '{transcript}'")
        
        # Patterns pour créer un dossier
        folder_patterns = [
            r"cr[ée]+[r]?\s+(?:un\s+)?dossier\s+(.+)",
            r"fait\s+(?:un\s+)?dossier\s+(.+)",
            r"nouveau\s+dossier\s+(.+)",
            r"dossier\s+(.+)"
        ]
        
        for pattern in folder_patterns:
            match = re.search(pattern, transcript_lower)
            if match:
                folder_name = match.group(1).strip()
                # Nettoyer le nom du dossier
                folder_name = re.sub(r'\s+sur\s+le\s+bureau.*', '', folder_name)
                folder_name = re.sub(r'\s+', '-', folder_name)
                return ("create_folder", {"folder_path": folder_name})
        
        # Patterns pour créer un fichier
        file_patterns = [
            r"cr[ée]+[r]?\s+(?:un\s+)?fichier\s+(.+)",
            r"fait\s+(?:un\s+)?fichier\s+(.+)",
            r"nouveau\s+fichier\s+(.+)",
            r"fichier\s+(.+)"
        ]
        
        for pattern in file_patterns:
            match = re.search(pattern, transcript_lower)
            if match:
                file_name = match.group(1).strip()
                # Nettoyer le nom du fichier
                file_name = re.sub(r'\s+sur\s+le\s+bureau.*', '', file_name)
                file_name = re.sub(r'\s+', '_', file_name)
                # Ajouter extension si manquante
                if '.' not in file_name:
                    file_name += '.txt'
                return ("create_file", {"file_path": file_name})
        
        # Patterns pour lister
        list_patterns = [
            r"list[e]?\s+(?:le\s+)?bureau",
            r"(?:que\s+)?contient\s+le\s+bureau",
            r"montre\s+(?:moi\s+)?le\s+bureau",
            r"affiche\s+le\s+bureau"
        ]
        
        for pattern in list_patterns:
            if re.search(pattern, transcript_lower):
                return ("list_contents", {"folder_path": ""})
        
        # Patterns pour lister un dossier
        list_folder_patterns = [
            r"list[e]?\s+(?:le\s+)?(?:contenu\s+du\s+)?dossier\s+(.+)",
            r"(?:que\s+)?contient\s+le\s+dossier\s+(.+)",
            r"montre\s+(?:moi\s+)?le\s+dossier\s+(.+)"
        ]
        
        for pattern in list_folder_patterns:
            match = re.search(pattern, transcript_lower)
            if match:
                folder_name = match.group(1).strip()
                return ("list_contents", {"folder_path": folder_name})
        
        return None
    
    def generate_confirmation_message(self, action, arguments, result):
        """Générer un message de confirmation naturel"""
        if action == "create_folder":
            folder_name = arguments.get("folder_path", "")
            if "créé avec succès" in result:
                return f"Parfait ! J'ai créé le dossier {folder_name} sur votre bureau."
            else:
                return f"Désolé, je n'ai pas pu créer le dossier {folder_name}. {result}"
                
        elif action == "create_file":
            file_name = arguments.get("file_path", "")
            if "créé avec succès" in result:
                return f"C'est fait ! Le fichier {file_name} a été créé sur votre bureau."
            else:
                return f"Je n'ai pas pu créer le fichier {file_name}. {result}"
                
        elif action == "list_contents":
            folder_name = arguments.get("folder_path", "")
            if "Contenu" in result:
                if folder_name:
                    return f"Voici le contenu du dossier {folder_name}: {result}"
                else:
                    return f"Voici ce qu'il y a sur votre bureau: {result}"
            else:
                return f"Je n'ai pas pu lister le contenu. {result}"
        
        return result
    
    # ========== CONNEXION WEBSOCKET ==========
    async def connect_to_realtime(self):
        """Se connecter à l'API OpenAI Realtime"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'OpenAI-Beta': 'realtime=v1'
        }
        
        uri = f"wss://api.openai.com/v1/realtime?model={self.model}"
        
        try:
            print("🔗 Connexion à OpenAI Realtime...")
            self.ws = await websockets.connect(
                uri, 
                additional_headers=headers,
                ping_interval=30,
                ping_timeout=15,
                close_timeout=10
            )
            print("✅ Connexion établie!")
            return True
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return False
    
    async def send_session_update(self):
        """Configuration de session pour l'intégration voix-MCP"""
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": """Tu es un assistant vocal français qui exécute des commandes de gestion de fichiers.

Quand tu reçois une transcription de l'utilisateur, tu dois:
1. Confirmer ce que tu as compris
2. Exécuter l'action demandée
3. Confirmer le résultat

Tu NE dois PAS utiliser les outils directement. L'utilisateur va s'en charger.
Réponds simplement de manière naturelle pour confirmer que tu as compris.""",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.3,
                    "prefix_padding_ms": 600,
                    "silence_duration_ms": 700
                }
            }
        }
        
        try:
            await self.ws.send(json.dumps(session_config))
            print("📤 Configuration session envoyée")
        except Exception as e:
            print(f"❌ Erreur config: {e}")
    
    # ========== GESTION DES ÉVÉNEMENTS ==========
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
        """Gérer les événements avec intégration MCP"""
        event_type = event.get("type")
        timestamp = time.strftime("%H:%M:%S")
        
        if event_type == "session.created":
            print(f"[{timestamp}] ✅ Session créée")
            self.session_created = True
            
        elif event_type == "input_audio_buffer.speech_started":
            print(f"[{timestamp}] 🎤 🟢 Écoute en cours...")
            
        elif event_type == "input_audio_buffer.speech_stopped":
            print(f"[{timestamp}] 🔇 🔴 Fin de parole - Traitement...")
            
        elif event_type == "conversation.item.input_audio_transcription.completed":
            transcript = event.get("transcript", "")
            print(f"[{timestamp}] 📝 Transcription: '{transcript}'")
            
            # 🎯 POINT CLÉ: Analyser la transcription et exécuter l'action MCP
            await self.process_voice_command(transcript)
            
        elif event_type == "conversation.item.input_audio_transcription.failed":
            print(f"[{timestamp}] ❌ Échec transcription")
            print("🔧 Essayez de parler plus clairement")
            
        elif event_type == "response.audio.delta":
            # Jouer l'audio de retour
            audio_b64 = event.get("delta", "")
            if audio_b64:
                await self.play_audio_response(audio_b64)
            
        elif event_type == "response.text.delta":
            text = event.get("delta", "")
            print(text, end="", flush=True)
            
        elif event_type == "response.done":
            print(f"\n[{timestamp}] ✅ Réponse terminée")
            
        elif event_type == "error":
            error = event.get("error", {})
            print(f"[{timestamp}] ❌ Erreur: {error}")
    
    async def process_voice_command(self, transcript):
        """Traiter une commande vocale et exécuter l'action MCP correspondante"""
        print(f"\n🎯 TRAITEMENT DE LA COMMANDE VOCALE")
        print("="*50)
        
        # Analyser la commande
        command_info = self.parse_voice_command(transcript)
        
        if command_info:
            action, arguments = command_info
            print(f"🔍 Action identifiée: {action}")
            print(f"📋 Arguments: {arguments}")
            
            # Exécuter l'action MCP
            print(f"⚙️ Exécution de l'action MCP...")
            result = await self.execute_mcp_action(action, arguments)
            print(f"📤 Résultat: {result}")
            
            # Générer une réponse de confirmation
            confirmation = self.generate_confirmation_message(action, arguments, result)
            print(f"🎤 Confirmation: {confirmation}")
            
            # Envoyer la confirmation à OpenAI pour qu'elle soit lue à voix haute
            await self.send_text_response(confirmation)
            
        else:
            print("❌ Commande non reconnue")
            await self.send_text_response("Je n'ai pas compris votre demande. Pouvez-vous répéter ?")
        
        print("="*50)
    
    async def execute_mcp_action(self, action, arguments):
        """Exécuter une action MCP"""
        try:
            if action == "create_folder":
                return self.create_folder(arguments.get("folder_path", ""))
            elif action == "create_file":
                return self.create_file(arguments.get("file_path", ""))
            elif action == "list_contents":
                return self.list_contents(arguments.get("folder_path", ""))
            else:
                return f"Action inconnue: {action}"
        except Exception as e:
            return f"Erreur lors de l'exécution: {e}"
    
    async def send_text_response(self, text):
        """Envoyer un texte à OpenAI pour qu'il soit lu à voix haute"""
        try:
            # Créer un item de conversation avec le texte de réponse
            text_item = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                }
            }
            
            await self.safe_send(json.dumps(text_item))
            
            # Demander une réponse audio
            response_create = {
                "type": "response.create",
                "response": {
                    "modalities": ["audio"]
                }
            }
            
            await self.safe_send(json.dumps(response_create))
            
        except Exception as e:
            print(f"❌ Erreur envoi réponse: {e}")
    
    async def play_audio_response(self, audio_b64):
        """Jouer la réponse audio d'OpenAI"""
        try:
            # Décoder l'audio base64
            audio_bytes = base64.b64decode(audio_b64)
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Jouer l'audio
            sd.play(audio_data.astype(np.float32) / 32768.0, samplerate=24000)
            
        except Exception as e:
            print(f"❌ Erreur lecture audio: {e}")
    
    # ========== PARSING DES COMMANDES ==========
    def parse_voice_command(self, transcript):
        """Analyser la transcription pour identifier les commandes MCP"""
        transcript_lower = transcript.lower().strip()
        
        print(f"🔍 Analyse: '{transcript}'")
        
        # Créer un dossier
        folder_patterns = [
            r"cr[ée]+[r]?\s+(?:un\s+)?dossier\s+([a-zA-Z0-9\s\-_]+)",
            r"fait\s+(?:un\s+)?dossier\s+([a-zA-Z0-9\s\-_]+)",
            r"nouveau\s+dossier\s+([a-zA-Z0-9\s\-_]+)",
            r"dossier\s+([a-zA-Z0-9\s\-_]+)"
        ]
        
        for pattern in folder_patterns:
            match = re.search(pattern, transcript_lower)
            if match:
                folder_name = match.group(1).strip()
                # Nettoyer le nom
                folder_name = re.sub(r'\s+sur\s+le\s+bureau.*', '', folder_name)
                folder_name = re.sub(r'\s+', '-', folder_name)
                folder_name = re.sub(r'[^a-zA-Z0-9\-_]', '', folder_name)
                
                if folder_name:
                    print(f"🎯 Dossier identifié: '{folder_name}'")
                    return ("create_folder", {"folder_path": folder_name})
        
        # Créer un fichier
        file_patterns = [
            r"cr[ée]+[r]?\s+(?:un\s+)?fichier\s+([a-zA-Z0-9\s\-_.]+)",
            r"fait\s+(?:un\s+)?fichier\s+([a-zA-Z0-9\s\-_.]+)",
            r"nouveau\s+fichier\s+([a-zA-Z0-9\s\-_.]+)"
        ]
        
        for pattern in file_patterns:
            match = re.search(pattern, transcript_lower)
            if match:
                file_name = match.group(1).strip()
                file_name = re.sub(r'\s+sur\s+le\s+bureau.*', '', file_name)
                file_name = re.sub(r'\s+', '_', file_name)
                
                # Ajouter extension si manquante
                if '.' not in file_name:
                    file_name += '.txt'
                
                if file_name:
                    print(f"🎯 Fichier identifié: '{file_name}'")
                    return ("create_file", {"file_path": file_name})
        
        # Lister le bureau
        list_patterns = [
            r"list[e]?\s+(?:le\s+)?bureau",
            r"(?:que\s+)?contient\s+le\s+bureau",
            r"montre\s+(?:moi\s+)?le\s+bureau",
            r"affiche\s+le\s+bureau",
            r"voir\s+le\s+bureau"
        ]
        
        for pattern in list_patterns:
            if re.search(pattern, transcript_lower):
                print(f"🎯 Listage bureau identifié")
                return ("list_contents", {"folder_path": ""})
        
        print(f"❌ Aucune commande reconnue dans: '{transcript}'")
        return None
    
    # ========== GESTION AUDIO ==========
    def audio_callback(self, indata, frames, time, status):
        """Callback audio optimisé"""
        if status:
            print(f"⚠️ Status: {status}")
        
        if self.is_recording and self.ws and self.session_created:
            try:
                # Volume pour feedback visuel
                volume_norm = np.linalg.norm(indata[:, 0]) * 10
                self.current_volume = volume_norm
                
                # Conversion PCM16 de haute qualité
                audio_data = (indata[:, 0] * 32767).astype(np.int16)
                max_amplitude = np.max(np.abs(audio_data))
                rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
                
                # Filtrage qualité strict pour la transcription
                if max_amplitude > 200 and rms > 100:  # Seuils élevés pour qualité
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
                print(f"❌ Erreur audio: {e}")
    
    async def process_audio_queue(self):
        """Traiter la queue audio"""
        while self.connection_active:
            try:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.audio_queue.get(timeout=0.1)
                )
                await self.safe_send(message)
            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"❌ Erreur queue: {e}")
    
    async def display_volume_bar(self):
        """Barre de volume en temps réel"""
        while self.show_volume_bar and self.is_recording:
            try:
                bar_length = int(min(self.current_volume, 50))
                
                if bar_length > 30:
                    bar_char = '█'
                    status = "🔊 EXCELLENT"
                elif bar_length > 20:
                    bar_char = '▓'
                    status = "🎤 BON"
                elif bar_length > 10:
                    bar_char = '▒'
                    status = "🔉 FAIBLE"
                else:
                    bar_char = '░'
                    status = "🔈 SILENCE"
                
                bar = bar_char * bar_length
                empty = '·' * (50 - bar_length)
                
                print(f"\r{status} |{bar}{empty}| {self.current_volume:.1f}    ", end='', flush=True)
                await asyncio.sleep(0.05)
                
            except Exception as e:
                print(f"\n❌ Erreur volume: {e}")
                break
    
    async def safe_send(self, message):
        """Envoi sécurisé"""
        try:
            if self.ws and self.connection_active:
                await self.ws.send(message)
                return True
        except Exception as e:
            if "1000" not in str(e):
                print(f"❌ Envoi: {e}")
            return False
        return False
    
    # ========== ENREGISTREMENT ==========
    def wait_for_enter(self):
        """Attendre entrée utilisateur"""
        try:
            input("Appuyez sur Entrée pour arrêter...")
            self.recording_stopped.set()
        except:
            self.recording_stopped.set()
    
    async def start_voice_session(self):
        """Démarrer une session vocale complète"""
        if not self.session_created:
            print("❌ Session non créée")
            return
        
        self.is_recording = True
        self.recording_stopped.clear()
        
        print("\n" + "="*70)
        print("🎤 SESSION VOCALE → MCP")
        print("="*70)
        print("💬 Dites: 'Créer un dossier projet sur le bureau'")
        print("📊 Barre de volume ci-dessous:")
        print("⏹️  Appuyez sur Entrée pour arrêter")
        print("="*70)
        
        # Thread pour attendre l'entrée
        input_thread = threading.Thread(target=self.wait_for_enter)
        input_thread.daemon = True
        input_thread.start()
        
        try:
            with sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=24000,
                dtype=np.float32,
                blocksize=2048,  # Blocs plus grands pour meilleure qualité
                latency='high'   # Privilégier la qualité
            ):
                # Affichage volume
                volume_task = asyncio.create_task(self.display_volume_bar())
                
                while not self.recording_stopped.is_set():
                    await asyncio.sleep(0.1)
                
                volume_task.cancel()
                
        except Exception as e:
            print(f"❌ Erreur enregistrement: {e}")
        
        self.is_recording = False
        print(f"\n🔇 Session vocale terminée")
    
    # ========== INTERFACE ==========
    def show_menu(self):
        """Menu principal"""
        print("\n" + "="*60)
        print("🎤➡️🛠️ CONTRÔLEUR VOCAL → MCP")
        print("="*60)
        print("🔗 1 - Se connecter et configurer")
        print("🎤 2 - Session vocale (Voix → Transcription → MCP → Audio)")
        print("🧪 3 - Test commande manuelle")
        print("📊 4 - Exemples de commandes")
        print("❌ q - Quitter")
        print("="*60)
    
    def show_command_examples(self):
        """Afficher des exemples de commandes"""
        print("\n" + "="*60)
        print("📚 EXEMPLES DE COMMANDES VOCALES")
        print("="*60)
        print("📁 CRÉER DES DOSSIERS:")
        print("   • 'Créer un dossier projet sur le bureau'")
        print("   • 'Fait un dossier mes-documents'")
        print("   • 'Nouveau dossier travail'")
        print()
        print("📄 CRÉER DES FICHIERS:")
        print("   • 'Créer un fichier readme sur le bureau'")
        print("   • 'Fait un fichier notes.txt'")
        print("   • 'Nouveau fichier script.py'")
        print()
        print("📋 LISTER LE CONTENU:")
        print("   • 'Liste le bureau'")
        print("   • 'Que contient le bureau'")
        print("   • 'Montre-moi le bureau'")
        print("   • 'Affiche le bureau'")
        print("="*60)
    
    async def test_manual_command(self):
        """Tester une commande manuellement"""
        print("\n🧪 Test de commande manuelle")
        transcript = input("📝 Entrez votre commande: ").strip()
        
        if transcript:
            await self.process_voice_command(transcript)
        else:
            print("❌ Commande vide")
    
    async def run(self):
        """Fonction principale"""
        print("🎤➡️🛠️ CONTRÔLEUR VOCAL → MCP")
        print("="*40)
        print("🎯 Transforme la voix en actions MCP")
        
        try:
            while True:
                try:
                    self.show_menu()
                    choice = input("\n👉 Votre choix: ").strip()
                    
                    if choice.lower() == 'q':
                        break
                        
                    elif choice == '1':
                        if await self.connect_to_realtime():
                            await self.send_session_update()
                            
                            # Démarrer les tâches
                            event_task = asyncio.create_task(self.listen_to_server_events())
                            audio_task = asyncio.create_task(self.process_audio_queue())
                            
                            print("✅ Système prêt pour les commandes vocales!")
                            input("Appuyez sur Entrée pour continuer...")
                        else:
                            print("❌ Échec connexion")
                            
                    elif choice == '2':
                        if self.session_created:
                            await self.start_voice_session()
                            input("Appuyez sur Entrée pour continuer...")
                        else:
                            print("❌ Connectez-vous d'abord (option 1)")
                            
                    elif choice == '3':
                        await self.test_manual_command()
                        input("Appuyez sur Entrée pour continuer...")
                        
                    elif choice == '4':
                        self.show_command_examples()
                        input("Appuyez sur Entrée pour continuer...")
                        
                    else:
                        print("❌ Choix invalide")
                        
                except EOFError:
                    print("\n👋 Au revoir!")
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
        finally:
            self.connection_active = False
            if self.ws:
                try:
                    await self.ws.close()
                except:
                    pass

if __name__ == "__main__":
    def signal_handler(sig, frame):
        print('\n👋 Arrêt...')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        controller = VoiceToMCPController()
        asyncio.run(controller.run())
    except KeyboardInterrupt:
        print("\n👋 Programme arrêté")
