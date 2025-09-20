#!/usr/bin/env python3
"""
Debugger du Pipeline Vocal → MCP
Montre chaque étape du processus: Audio → Transcription → Parsing → MCP → Retour
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

class PipelineDebugger:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview-2024-10-01')
        self.ws = None
        self.desktop_path = Path.home() / "Desktop"
        
        # État du pipeline
        self.pipeline_state = {
            "step": "idle",
            "audio_captured": False,
            "transcription_received": False,
            "command_parsed": False,
            "mcp_executed": False,
            "response_sent": False
        }
        
        # Audio
        self.is_recording = False
        self.recording_stopped = threading.Event()
        self.audio_queue = queue.Queue(maxsize=200)
        self.audio_chunks_count = 0
        self.current_volume = 0.0
        
        # Connection
        self.connection_active = True
        self.session_created = False
        
    def reset_pipeline_state(self):
        """Reset l'état du pipeline"""
        self.pipeline_state = {
            "step": "waiting_for_audio",
            "audio_captured": False,
            "transcription_received": False,
            "command_parsed": False,
            "mcp_executed": False,
            "response_sent": False
        }
        self.audio_chunks_count = 0
        print("🔄 Pipeline reset - Prêt pour une nouvelle commande")
    
    def show_pipeline_status(self):
        """Afficher l'état du pipeline en temps réel"""
        state = self.pipeline_state
        
        print(f"\n📊 ÉTAT DU PIPELINE:")
        print("="*50)
        print(f"🎤 1. Capture audio: {'✅' if state['audio_captured'] else '⏳'} ({self.audio_chunks_count} chunks)")
        print(f"📝 2. Transcription: {'✅' if state['transcription_received'] else '⏳'}")
        print(f"🔍 3. Parsing commande: {'✅' if state['command_parsed'] else '⏳'}")
        print(f"⚙️ 4. Exécution MCP: {'✅' if state['mcp_executed'] else '⏳'}")
        print(f"🎤 5. Retour audio: {'✅' if state['response_sent'] else '⏳'}")
        print(f"📍 Étape actuelle: {state['step']}")
        print("="*50)
    
    # ========== FONCTIONS MCP ==========
    def create_folder(self, folder_path):
        """Créer un dossier avec feedback détaillé"""
        try:
            full_path = self.desktop_path / folder_path
            
            if full_path.exists():
                return f"Le dossier {folder_path} existe déjà sur le bureau"
            
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ MCP EXÉCUTÉ: Dossier {folder_path} créé à {full_path}")
            return f"J'ai créé le dossier {folder_path} sur votre bureau"
            
        except Exception as e:
            print(f"❌ MCP ÉCHEC: {e}")
            return f"Je n'ai pas pu créer le dossier {folder_path}: {e}"
    
    def create_file(self, file_path):
        """Créer un fichier avec feedback détaillé"""
        try:
            full_path = self.desktop_path / file_path
            
            if full_path.exists():
                return f"Le fichier {file_path} existe déjà sur le bureau"
            
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()
            print(f"✅ MCP EXÉCUTÉ: Fichier {file_path} créé à {full_path}")
            return f"J'ai créé le fichier {file_path} sur votre bureau"
            
        except Exception as e:
            print(f"❌ MCP ÉCHEC: {e}")
            return f"Je n'ai pas pu créer le fichier {file_path}: {e}"
    
    def list_contents(self, folder_path=""):
        """Lister avec feedback détaillé"""
        try:
            if folder_path:
                target_path = self.desktop_path / folder_path
                location = f"dossier {folder_path}"
            else:
                target_path = self.desktop_path
                location = "bureau"
            
            if not target_path.exists():
                return f"Le {location} n'existe pas"
            
            items = list(target_path.iterdir())
            if not items:
                return f"Le {location} est vide"
            
            folders = [item.name for item in items if item.is_dir()]
            files = [item.name for item in items if item.is_file()]
            
            print(f"✅ MCP EXÉCUTÉ: Listage de {target_path}")
            
            result = f"Sur votre {location}, il y a "
            if folders:
                result += f"{len(folders)} dossier(s)"
                if len(folders) <= 3:
                    result += f": {', '.join(folders)}"
            if files:
                if folders:
                    result += " et "
                result += f"{len(files)} fichier(s)"
                if len(files) <= 3:
                    result += f": {', '.join(files)}"
            
            return result
            
        except Exception as e:
            print(f"❌ MCP ÉCHEC: {e}")
            return f"Je n'ai pas pu lire le contenu: {e}"
    
    # ========== PARSING DES COMMANDES ==========
    def parse_voice_command(self, transcript):
        """Parser vocal amélioré avec debug"""
        transcript_lower = transcript.lower().strip()
        
        print(f"\n🔍 PARSING DE LA COMMANDE:")
        print(f"📝 Transcription brute: '{transcript}'")
        print(f"🔤 Version lowercase: '{transcript_lower}'")
        
        # Créer un dossier - patterns étendus
        folder_patterns = [
            r"cr[ée]+[r]?\s+(?:un\s+)?dossier\s+([a-zA-Z0-9\s\-_]+)",
            r"fait\s+(?:un\s+)?dossier\s+([a-zA-Z0-9\s\-_]+)",
            r"nouveau\s+dossier\s+([a-zA-Z0-9\s\-_]+)",
            r"dossier\s+([a-zA-Z0-9\s\-_]+)",
            r"cr[ée]+[r]?\s+([a-zA-Z0-9\s\-_]+)\s+(?:dossier|sur\s+le\s+bureau)"
        ]
        
        for i, pattern in enumerate(folder_patterns):
            print(f"   🔍 Test pattern {i+1}: {pattern}")
            match = re.search(pattern, transcript_lower)
            if match:
                folder_name = match.group(1).strip()
                # Nettoyer le nom
                folder_name = re.sub(r'\s+sur\s+le\s+bureau.*', '', folder_name)
                folder_name = re.sub(r'\s+', '-', folder_name)
                folder_name = re.sub(r'[^a-zA-Z0-9\-_]', '', folder_name)
                
                if folder_name:
                    print(f"✅ MATCH! Dossier: '{folder_name}'")
                    return ("create_folder", {"folder_path": folder_name})
                else:
                    print(f"❌ Nom vide après nettoyage")
            else:
                print(f"   ❌ Pas de match")
        
        # Créer un fichier
        file_patterns = [
            r"cr[ée]+[r]?\s+(?:un\s+)?fichier\s+([a-zA-Z0-9\s\-_.]+)",
            r"fait\s+(?:un\s+)?fichier\s+([a-zA-Z0-9\s\-_.]+)",
            r"nouveau\s+fichier\s+([a-zA-Z0-9\s\-_.]+)"
        ]
        
        print(f"\n   🔍 Test patterns fichiers...")
        for pattern in file_patterns:
            match = re.search(pattern, transcript_lower)
            if match:
                file_name = match.group(1).strip()
                file_name = re.sub(r'\s+sur\s+le\s+bureau.*', '', file_name)
                file_name = re.sub(r'\s+', '_', file_name)
                
                if '.' not in file_name:
                    file_name += '.txt'
                
                if file_name:
                    print(f"✅ MATCH! Fichier: '{file_name}'")
                    return ("create_file", {"file_path": file_name})
        
        # Lister le bureau
        list_patterns = [
            r"list[e]?\s+(?:le\s+)?bureau",
            r"(?:que\s+)?contient\s+le\s+bureau",
            r"montre\s+(?:moi\s+)?le\s+bureau",
            r"affiche\s+le\s+bureau",
            r"voir\s+le\s+bureau"
        ]
        
        print(f"\n   🔍 Test patterns listage...")
        for pattern in list_patterns:
            if re.search(pattern, transcript_lower):
                print(f"✅ MATCH! Listage bureau")
                return ("list_contents", {"folder_path": ""})
        
        print(f"❌ AUCUN MATCH trouvé")
        return None
    
    # ========== CONNEXION ==========
    async def connect_to_realtime(self):
        """Connexion à OpenAI"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'OpenAI-Beta': 'realtime=v1'
        }
        
        uri = f"wss://api.openai.com/v1/realtime?model={self.model}"
        
        try:
            self.ws = await websockets.connect(uri, additional_headers=headers)
            print("✅ Connexion WebSocket établie")
            return True
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return False
    
    async def send_session_config(self):
        """Configuration session minimaliste"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["audio"],
                "instructions": "Tu es un assistant qui confirme les actions de gestion de fichiers.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1"},
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.3,
                    "prefix_padding_ms": 500,
                    "silence_duration_ms": 800
                }
            }
        }
        
        await self.ws.send(json.dumps(config))
        print("📤 Configuration envoyée")
    
    # ========== GESTION DES ÉVÉNEMENTS ==========
    async def listen_to_events(self):
        """Écouter avec debug détaillé"""
        try:
            async for message in self.ws:
                try:
                    event = json.loads(message)
                    await self.handle_event_with_debug(event)
                except Exception as e:
                    print(f"❌ Erreur événement: {e}")
        except Exception as e:
            print(f"❌ Erreur écoute: {e}")
            self.connection_active = False
    
    async def handle_event_with_debug(self, event):
        """Gérer les événements avec debug complet"""
        event_type = event.get("type")
        timestamp = time.strftime("%H:%M:%S")
        
        print(f"\n[{timestamp}] 📨 ÉVÉNEMENT: {event_type}")
        
        if event_type == "session.created":
            self.session_created = True
            print("   ✅ Session prête")
            
        elif event_type == "input_audio_buffer.speech_started":
            self.pipeline_state["step"] = "recording"
            print("   🎤 VAD: Début de parole")
            self.show_pipeline_status()
            
        elif event_type == "input_audio_buffer.speech_stopped":
            self.pipeline_state["step"] = "processing_audio"
            print("   🔇 VAD: Fin de parole")
            self.show_pipeline_status()
            
        elif event_type == "input_audio_buffer.committed":
            self.pipeline_state["audio_captured"] = True
            self.pipeline_state["step"] = "transcribing"
            print("   📦 Audio committé pour transcription")
            self.show_pipeline_status()
            
        elif event_type == "conversation.item.input_audio_transcription.completed":
            transcript = event.get("transcript", "")
            self.pipeline_state["transcription_received"] = True
            self.pipeline_state["step"] = "parsing_command"
            
            print(f"   📝 ✅ TRANSCRIPTION RÉUSSIE: '{transcript}'")
            self.show_pipeline_status()
            
            # 🎯 ÉTAPE CRITIQUE: Parser et exécuter
            await self.process_transcription(transcript)
            
        elif event_type == "conversation.item.input_audio_transcription.failed":
            error = event.get("error", {})
            print(f"   ❌ TRANSCRIPTION ÉCHOUÉE: {error}")
            print("   💡 Le pipeline s'arrête ici - pas de transcription = pas de MCP")
            self.show_pipeline_status()
            
        elif event_type == "response.audio.delta":
            # Audio de retour
            print("   🔊 Retour audio reçu")
            
        elif event_type == "response.done":
            self.pipeline_state["response_sent"] = True
            self.pipeline_state["step"] = "completed"
            print("   ✅ PIPELINE TERMINÉ")
            self.show_pipeline_status()
            
        elif event_type == "error":
            error = event.get("error", {})
            print(f"   ❌ ERREUR SERVEUR: {error}")
    
    async def process_transcription(self, transcript):
        """Traiter la transcription et exécuter MCP"""
        print(f"\n🎯 TRAITEMENT DE LA TRANSCRIPTION")
        print("="*60)
        
        # Étape 1: Parser la commande
        command_info = self.parse_voice_command(transcript)
        
        if command_info:
            action, arguments = command_info
            self.pipeline_state["command_parsed"] = True
            self.pipeline_state["step"] = "executing_mcp"
            
            print(f"✅ Commande parsée: {action} avec {arguments}")
            self.show_pipeline_status()
            
            # Étape 2: Exécuter l'action MCP
            print(f"\n⚙️ EXÉCUTION MCP...")
            result = await self.execute_mcp_action(action, arguments)
            
            self.pipeline_state["mcp_executed"] = True
            self.pipeline_state["step"] = "generating_response"
            
            print(f"📤 Résultat MCP: {result}")
            self.show_pipeline_status()
            
            # Étape 3: Envoyer la confirmation audio
            confirmation = self.generate_confirmation(action, arguments, result)
            print(f"🎤 Confirmation à lire: '{confirmation}'")
            
            await self.send_audio_response(confirmation)
            
        else:
            print(f"❌ Commande non reconnue dans: '{transcript}'")
            await self.send_audio_response("Je n'ai pas compris votre demande. Pouvez-vous répéter ?")
    
    def parse_voice_command(self, transcript):
        """Parser avec debug détaillé"""
        transcript_lower = transcript.lower().strip()
        
        print(f"🔍 Analyse de: '{transcript_lower}'")
        
        # Test dossier
        if "dossier" in transcript_lower and ("créer" in transcript_lower or "crée" in transcript_lower or "fait" in transcript_lower):
            # Extraire le nom du dossier
            patterns = [
                r"dossier\s+([a-zA-Z0-9\s\-_]+)",
                r"cr[ée]+[r]?\s+(?:un\s+)?dossier\s+([a-zA-Z0-9\s\-_]+)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, transcript_lower)
                if match:
                    folder_name = match.group(1).strip()
                    folder_name = re.sub(r'\s+sur.*', '', folder_name)
                    folder_name = re.sub(r'\s+', '-', folder_name)
                    folder_name = re.sub(r'[^a-zA-Z0-9\-_]', '', folder_name)
                    
                    if folder_name:
                        print(f"✅ Dossier identifié: '{folder_name}'")
                        return ("create_folder", {"folder_path": folder_name})
        
        # Test fichier
        if "fichier" in transcript_lower and ("créer" in transcript_lower or "crée" in transcript_lower):
            patterns = [
                r"fichier\s+([a-zA-Z0-9\s\-_.]+)",
                r"cr[ée]+[r]?\s+(?:un\s+)?fichier\s+([a-zA-Z0-9\s\-_.]+)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, transcript_lower)
                if match:
                    file_name = match.group(1).strip()
                    file_name = re.sub(r'\s+sur.*', '', file_name)
                    file_name = re.sub(r'\s+', '_', file_name)
                    
                    if '.' not in file_name:
                        file_name += '.txt'
                    
                    if file_name:
                        print(f"✅ Fichier identifié: '{file_name}'")
                        return ("create_file", {"file_path": file_name})
        
        # Test listage
        if any(word in transcript_lower for word in ["liste", "contient", "montre", "affiche", "voir"]) and "bureau" in transcript_lower:
            print(f"✅ Listage bureau identifié")
            return ("list_contents", {"folder_path": ""})
        
        print(f"❌ Aucune commande identifiée")
        return None
    
    async def execute_mcp_action(self, action, arguments):
        """Exécuter action MCP"""
        if action == "create_folder":
            return self.create_folder(arguments.get("folder_path", ""))
        elif action == "create_file":
            return self.create_file(arguments.get("file_path", ""))
        elif action == "list_contents":
            return self.list_contents(arguments.get("folder_path", ""))
        else:
            return f"Action inconnue: {action}"
    
    def generate_confirmation(self, action, arguments, result):
        """Générer confirmation naturelle"""
        if "créé avec succès" in result or "J'ai créé" in result:
            return result
        elif "existe déjà" in result:
            return result
        elif "Il y a" in result or "Sur votre" in result:
            return result
        else:
            return f"Désolé, il y a eu un problème: {result}"
    
    async def send_audio_response(self, text):
        """Envoyer texte pour conversion audio"""
        try:
            # Créer item de conversation
            text_item = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "text", "text": text}]
                }
            }
            
            await self.safe_send(json.dumps(text_item))
            
            # Demander réponse audio
            response_create = {
                "type": "response.create",
                "response": {"modalities": ["audio"]}
            }
            
            await self.safe_send(json.dumps(response_create))
            print(f"📤 Demande de lecture audio envoyée")
            
        except Exception as e:
            print(f"❌ Erreur réponse audio: {e}")
    
    # ========== AUDIO ==========
    def audio_callback(self, indata, frames, time, status):
        """Callback audio avec comptage"""
        if self.is_recording and self.ws and self.session_created:
            try:
                volume_norm = np.linalg.norm(indata[:, 0]) * 10
                self.current_volume = volume_norm
                
                audio_data = (indata[:, 0] * 32767).astype(np.int16)
                max_amplitude = np.max(np.abs(audio_data))
                
                if max_amplitude > 100:  # Seuil pour qualité
                    audio_b64 = base64.b64encode(audio_data.tobytes()).decode('utf-8')
                    
                    audio_event = {
                        "type": "input_audio_buffer.append",
                        "audio": audio_b64
                    }
                    
                    try:
                        self.audio_queue.put_nowait(json.dumps(audio_event))
                        self.audio_chunks_count += 1
                        
                        if self.audio_chunks_count == 1:
                            self.pipeline_state["audio_captured"] = True
                            print(f"\n✅ Premier chunk audio capturé!")
                            
                    except queue.Full:
                        pass
                    
            except Exception as e:
                print(f"❌ Erreur audio: {e}")
    
    async def process_audio_queue(self):
        """Traiter queue audio"""
        while self.connection_active:
            try:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.audio_queue.get(timeout=0.1)
                )
                await self.safe_send(message)
            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"❌ Erreur queue: {e}")
    
    async def safe_send(self, message):
        """Envoi sécurisé"""
        try:
            if self.ws and self.connection_active:
                await self.ws.send(message)
                return True
        except Exception as e:
            print(f"❌ Envoi: {e}")
            return False
        return False
    
    # ========== ENREGISTREMENT ==========
    def wait_for_enter(self):
        try:
            input("Appuyez sur Entrée pour arrêter...")
            self.recording_stopped.set()
        except:
            self.recording_stopped.set()
    
    async def debug_voice_session(self):
        """Session vocale avec debug complet"""
        self.reset_pipeline_state()
        
        print("\n" + "="*70)
        print("🔍 SESSION DE DEBUG PIPELINE VOCAL → MCP")
        print("="*70)
        print("💬 Dites clairement: 'Créer un dossier projet sur le bureau'")
        print("📊 Suivez le pipeline ci-dessous:")
        print("="*70)
        
        self.is_recording = True
        self.recording_stopped.clear()
        
        input_thread = threading.Thread(target=self.wait_for_enter)
        input_thread.daemon = True
        input_thread.start()
        
        try:
            with sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=24000,
                dtype=np.float32,
                blocksize=2048
            ):
                while not self.recording_stopped.is_set():
                    await asyncio.sleep(0.2)
                    
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        self.is_recording = False
        print(f"\n🔇 Enregistrement terminé")
        
        # Attendre les événements
        print("⏳ Attente des événements de transcription...")
        await asyncio.sleep(5)
        
        print(f"\n📊 RÉSUMÉ FINAL:")
        self.show_pipeline_status()
    
    # ========== INTERFACE ==========
    def show_menu(self):
        print("\n" + "="*60)
        print("🔍 DEBUGGER PIPELINE VOCAL → MCP")
        print("="*60)
        print("🔗 1 - Connecter et configurer")
        print("🎤 2 - Session debug complète")
        print("🧪 3 - Test parsing manuel")
        print("📊 4 - État du pipeline")
        print("❌ q - Quitter")
        print("="*60)
    
    async def test_manual_parsing(self):
        """Test manuel du parsing"""
        print("\n🧪 Test de parsing manuel")
        
        examples = [
            "Créer un dossier projet sur le bureau",
            "Crée un dossier mes-documents", 
            "Fait un fichier readme.txt",
            "Liste le bureau",
            "Que contient le bureau"
        ]
        
        print("📝 Exemples à tester:")
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")
        
        choice = input("\nChoisissez un exemple (1-5) ou tapez votre phrase: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= 5:
            transcript = examples[int(choice) - 1]
        else:
            transcript = choice
        
        if transcript:
            print(f"\n🔍 Test de parsing pour: '{transcript}'")
            result = self.parse_voice_command(transcript)
            
            if result:
                action, args = result
                print(f"✅ Parsing réussi: {action} avec {args}")
                
                # Simuler l'exécution MCP
                mcp_result = await self.execute_mcp_action(action, args)
                print(f"📤 Résultat MCP: {mcp_result}")
                
                confirmation = self.generate_confirmation(action, args, mcp_result)
                print(f"🎤 Confirmation: '{confirmation}'")
            else:
                print("❌ Parsing échoué")
    
    async def run(self):
        """Fonction principale"""
        print("🔍 DEBUGGER PIPELINE VOCAL → MCP")
        print("="*40)
        
        try:
            while True:
                try:
                    self.show_menu()
                    choice = input("\n👉 Votre choix: ").strip()
                    
                    if choice.lower() == 'q':
                        break
                        
                    elif choice == '1':
                        if await self.connect_to_realtime():
                            await self.send_session_config()
                            
                            event_task = asyncio.create_task(self.listen_to_events())
                            audio_task = asyncio.create_task(self.process_audio_queue())
                            
                            print("✅ Système connecté et prêt!")
                            input("Appuyez sur Entrée pour continuer...")
                        
                    elif choice == '2':
                        if self.session_created:
                            await self.debug_voice_session()
                            input("Appuyez sur Entrée pour continuer...")
                        else:
                            print("❌ Connectez-vous d'abord (option 1)")
                            
                    elif choice == '3':
                        await self.test_manual_parsing()
                        input("Appuyez sur Entrée pour continuer...")
                        
                    elif choice == '4':
                        self.show_pipeline_status()
                        input("Appuyez sur Entrée pour continuer...")
                        
                    else:
                        print("❌ Choix invalide")
                        
                except EOFError:
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
        finally:
            self.connection_active = False

if __name__ == "__main__":
    try:
        debugger = PipelineDebugger()
        asyncio.run(debugger.run())
    except KeyboardInterrupt:
        print("\n👋 Programme arrêté")
