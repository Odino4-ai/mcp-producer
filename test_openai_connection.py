#!/usr/bin/env python3
"""
Testeur de connexion OpenAI et enregistrement vocal
Permet de tester uniquement la partie audio/transcription sans les fonctions de fichiers
"""
import asyncio
import json
import os
import sys
import sounddevice as sd
import numpy as np
import websockets
from dotenv import load_dotenv
import threading
import signal
import queue

load_dotenv()

class OpenAIConnectionTester:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview')
        self.ws = None
        self.is_recording = False
        self.recording_stopped = threading.Event()
        self.audio_queue = queue.Queue(maxsize=100)
        self.connection_active = True
        # Variables pour le feedback visuel
        self.current_volume = 0.0
        self.show_volume_bar = False
        
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
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10,
                max_size=None,
                compression=None
            )
            print("✅ Connexion établie avec succès!")
            return True
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    async def send_session_config(self):
        """Configuration de session simple pour les tests"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": """Tu es un assistant vocal de test. 
                
Réponds simplement à ce que dit l'utilisateur pour confirmer que tu l'as bien entendu.
Par exemple, si l'utilisateur dit 'Bonjour', réponds 'Bonjour ! Je t'ai bien entendu dire bonjour.'
Sois naturel et confirme toujours ce que tu as compris.""",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1"}
            }
        }
        
        try:
            await self.ws.send(json.dumps(config))
            print("📤 Configuration de test envoyée")
        except Exception as e:
            print(f"❌ Erreur envoi config: {e}")
    
    async def listen_to_responses(self):
        """Écouter les réponses de l'API"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    if message_type == "session.created":
                        print("✅ Session de test créée")
                    elif message_type == "input_audio_buffer.speech_started":
                        print("🎤 🟢 Parole détectée - Je vous écoute...")
                    elif message_type == "input_audio_buffer.speech_stopped":
                        print("🔇 🔴 Fin de parole - Traitement en cours...")
                    elif message_type == "conversation.item.input_audio_transcription.completed":
                        transcript = data.get("transcript", "")
                        print(f"📝 ✅ Transcription: '{transcript}'")
                    elif message_type == "response.text.delta":
                        text = data.get("delta", "")
                        print(text, end="", flush=True)
                    elif message_type == "response.done":
                        print("\n🎯 ✅ Réponse terminée\n")
                    elif message_type == "error":
                        error_details = data.get("error", {})
                        print(f"❌ Erreur API: {error_details}")
                    elif message_type in ["response.audio.delta", "response.audio.done"]:
                        # Ignorer les messages audio pour ce test simple
                        pass
                    else:
                        # Afficher les autres types de messages pour debug
                        print(f"🔍 Message: {message_type}")
                    
                except json.JSONDecodeError:
                    print(f"❌ Erreur parsing JSON: {message}")
                except Exception as e:
                    print(f"❌ Erreur traitement message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connexion fermée")
            self.connection_active = False
        except Exception as e:
            print(f"❌ Erreur écoute: {e}")
            self.connection_active = False
    
    def audio_callback(self, indata, frames, time, status):
        """Callback pour l'audio en temps réel avec feedback visuel"""
        if status:
            print(f"⚠️ Statut audio: {status}")
        
        if self.is_recording and self.ws:
            try:
                # Vérifier que nous avons bien des données audio
                if indata is None or len(indata) == 0:
                    return
                
                # Convertir en PCM16 avec vérification
                if indata.shape[1] > 0:  # Vérifier qu'il y a au moins un canal
                    audio_data = (indata[:, 0] * 32767).astype(np.int16)
                    
                    # Calculer le volume pour le feedback visuel
                    volume_norm = np.linalg.norm(indata[:, 0]) * 10
                    self.current_volume = volume_norm
                    
                    # Vérifier que les données ne sont pas silencieuses
                    max_amplitude = np.max(np.abs(audio_data))
                    
                    # CORRECTION: Seuil beaucoup plus bas et debug
                    if max_amplitude > 10:  # Seuil très bas (était 100)
                        audio_b64 = self.numpy_to_base64(audio_data)
                        
                        message = {
                            "type": "input_audio_buffer.append",
                            "audio": audio_b64
                        }
                        
                        try:
                            # Vérifier que la connexion est toujours active avant d'ajouter à la queue
                            if self.connection_active:
                                self.audio_queue.put_nowait(json.dumps(message))
                                # Debug: afficher quand on capture vraiment
                                if max_amplitude > 1000:
                                    print(f" [CAPTURE: {max_amplitude:.0f}]", end="")
                            else:
                                print(f" [CONNEXION FERMÉE]", end="")
                        except queue.Full:
                            # Si la queue est pleine, on ignore ce chunk
                            pass
                    else:
                        # Debug: montrer pourquoi on ignore
                        if volume_norm > 10:  # Si le volume visuel est fort mais pas capturé
                            print(f" [IGNORÉ: {max_amplitude:.0f}]", end="")
                    
            except Exception as e:
                print(f"❌ Erreur callback audio: {e}")
    
    async def process_audio_queue(self):
        """Traiter la queue d'audio de manière asynchrone avec gestion des échecs"""
        failed_sends = 0
        while self.connection_active:
            try:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.audio_queue.get(timeout=0.1)
                )
                
                # Essayer d'envoyer le message
                success = await self.safe_send(message)
                if success:
                    failed_sends = 0  # Reset le compteur sur succès
                else:
                    failed_sends += 1
                    if failed_sends > 10:  # Trop d'échecs consécutifs
                        print(f"\n⚠️ Trop d'échecs d'envoi ({failed_sends}), arrêt du traitement audio")
                        break
                        
            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"❌ Erreur traitement queue audio: {e}")
                failed_sends += 1
                if failed_sends > 10:
                    break
    
    async def safe_send(self, message):
        """Envoi sécurisé de message avec gestion améliorée des erreurs"""
        try:
            if self.ws:
                await self.ws.send(message)
        except websockets.exceptions.ConnectionClosed as e:
            # La connexion a été fermée - ne pas spammer les logs
            if not hasattr(self, '_connection_closed_logged'):
                print(f"\n🔌 Connexion WebSocket fermée: {e}")
                self._connection_closed_logged = True
            return False
        except Exception as e:
            # Filtrer les erreurs répétitives
            if "keepalive ping timeout" not in str(e) and "sent 1000" not in str(e):
                print(f"❌ Erreur envoi: {e}")
            return False
        return True
    
    def numpy_to_base64(self, audio_data):
        """Convertir numpy array en base64"""
        import base64
        return base64.b64encode(audio_data.tobytes()).decode('utf-8')
    
    def wait_for_enter(self):
        """Attendre l'entrée utilisateur dans un thread séparé"""
        try:
            input("Appuyez sur Entrée pour arrêter l'enregistrement...")
            self.recording_stopped.set()
        except:
            self.recording_stopped.set()
    
    async def start_recording(self, with_visual_feedback=False):
        """Démarrer l'enregistrement avec vérifications améliorées et feedback visuel optionnel"""
        self.is_recording = True
        self.recording_stopped.clear()
        self.show_volume_bar = with_visual_feedback
        
        print("\n" + "="*60)
        print("🎤 🔴 ENREGISTREMENT EN COURS")
        print("="*60)
        print("💬 Parlez FORT et CLAIREMENT pour tester...")
        print("⏰ Minimum 2-3 secondes de parole requises")
        print("⏹️  Appuyez sur Entrée pour arrêter")
        if with_visual_feedback:
            print("📊 Barre de volume en temps réel ci-dessous:")
        print("="*60)
        
        # Démarrer l'attente d'entrée dans un thread
        input_thread = threading.Thread(target=self.wait_for_enter)
        input_thread.daemon = True
        input_thread.start()
        
        # Compteur pour vérifier qu'on capture de l'audio
        audio_chunks_sent = 0
        
        try:
            # Configuration audio optimisée
            with sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=24000,
                dtype=np.float32,
                blocksize=1024,  # Taille de bloc plus petite pour plus de réactivité
                latency='low'     # Latence faible
            ):
                start_time = asyncio.get_event_loop().time()
                
                # Démarrer l'affichage de la barre de volume si demandé
                volume_task = None
                if with_visual_feedback:
                    volume_task = asyncio.create_task(self.display_volume_bar())
                
                while not self.recording_stopped.is_set():
                    await asyncio.sleep(0.1)
                    
                    # Vérifier qu'on capture de l'audio (seulement si pas de feedback visuel)
                    if not with_visual_feedback:
                        current_queue_size = self.audio_queue.qsize()
                        if current_queue_size > audio_chunks_sent:
                            chunks_diff = current_queue_size - audio_chunks_sent
                            print(f"🎵 Audio capturé: {chunks_diff} nouveaux chunks", end='\r')
                            audio_chunks_sent = current_queue_size
                    else:
                        audio_chunks_sent = self.audio_queue.qsize()
                    
                    # Vérifier durée minimum
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed < 1.0 and self.recording_stopped.is_set():
                        if with_visual_feedback:
                            print(f"\n⚠️ Enregistrement trop court ({elapsed:.1f}s). Continuez à parler...")
                        else:
                            print(f"\n⚠️ Enregistrement trop court ({elapsed:.1f}s). Continuez à parler...")
                        self.recording_stopped.clear()
                        input_thread = threading.Thread(target=self.wait_for_enter)
                        input_thread.daemon = True
                        input_thread.start()
                
                # Arrêter l'affichage de la barre de volume
                if volume_task:
                    self.show_volume_bar = False
                    volume_task.cancel()
                    
        except Exception as e:
            print(f"❌ Erreur enregistrement: {e}")
        
        self.is_recording = False
        self.show_volume_bar = False
        
        if with_visual_feedback:
            print(f"\n🔇 🟡 Enregistrement arrêté - {audio_chunks_sent} chunks audio capturés")
        else:
            print(f"\n🔇 🟡 Enregistrement arrêté - {audio_chunks_sent} chunks audio capturés")
        
        # Vérifier qu'on a assez d'audio
        if audio_chunks_sent < 10:  # Minimum de chunks requis
            print("⚠️ ATTENTION: Peu d'audio capturé. Parlez plus fort la prochaine fois!")
        
        # Attendre que la queue soit traitée
        print("⏳ Traitement de l'audio en cours...")
        await asyncio.sleep(1)  # Laisser le temps à la queue de se vider
        
        # Finaliser l'audio
        try:
            await self.ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
            await self.ws.send(json.dumps({"type": "response.create"}))
            print("📤 Audio envoyé pour traitement")
        except Exception as e:
            print(f"❌ Erreur finalisation: {e}")
    
    def show_test_menu(self):
        """Affiche le menu de test"""
        print("\n" + "="*60)
        print("🧪 TESTEUR DE CONNEXION OPENAI & AUDIO")
        print("="*60)
        print("🔗 1 - Tester la connexion OpenAI")
        print("🎤 2 - Tester l'enregistrement vocal (avec connexion)")
        print("🎯 3 - Test complet (connexion + enregistrement)")
        print("📊 4 - Vérifier la configuration et test microphone")
        print("🔊 5 - Test microphone en temps réel")
        print("🔍 6 - Debug conversion audio (pour résoudre les bugs)")
        print("❌ q - Quitter")
        print("="*60)
    
    async def test_connection_only(self):
        """Tester uniquement la connexion"""
        print("\n🔗 Test de connexion OpenAI...")
        if await self.connect_to_realtime():
            await self.send_session_config()
            print("✅ Connexion et configuration réussies!")
            
            # Écouter quelques messages pour confirmer
            print("⏳ Écoute des messages pendant 3 secondes...")
            listen_task = asyncio.create_task(self.listen_to_responses())
            await asyncio.sleep(3)
            listen_task.cancel()
            
            try:
                await self.ws.close()
            except:
                pass
            print("✅ Test de connexion terminé avec succès!")
        else:
            print("❌ Échec du test de connexion")
    
    def check_configuration(self):
        """Vérifier la configuration"""
        print("\n📊 Vérification de la configuration...")
        print("="*50)
        
        # Vérifier la clé API
        if self.api_key:
            print(f"✅ Clé API OpenAI: {'*' * 10}...{self.api_key[-4:]}")
        else:
            print("❌ Clé API OpenAI: Non trouvée")
            print("   → Vérifiez votre fichier .env")
        
        print(f"🤖 Modèle: {self.model}")
        
        # Test détaillé des périphériques audio
        try:
            print("\n🎤 Test des périphériques audio:")
            devices = sd.query_devices()
            
            # Périphérique d'entrée par défaut
            input_device_id = sd.default.device[0]
            input_device = devices[input_device_id]
            print(f"📥 Entrée par défaut: {input_device['name']}")
            print(f"   Canaux max: {input_device['max_input_channels']}")
            print(f"   Fréquence par défaut: {input_device['default_samplerate']} Hz")
            
            # Test de capture audio
            print("\n🧪 Test de capture audio (2 secondes)...")
            try:
                duration = 2  # secondes
                sample_rate = 24000
                
                print("🎤 Parlez maintenant pour tester le microphone...")
                recording = sd.rec(int(duration * sample_rate), 
                                 samplerate=sample_rate, 
                                 channels=1, 
                                 dtype=np.float32)
                sd.wait()  # Attendre la fin de l'enregistrement
                
                # Analyser l'enregistrement
                max_amplitude = np.max(np.abs(recording))
                rms = np.sqrt(np.mean(recording**2))
                
                print(f"📊 Amplitude max: {max_amplitude:.4f}")
                print(f"📊 RMS: {rms:.4f}")
                
                if max_amplitude > 0.01:
                    print("✅ Microphone fonctionne correctement")
                elif max_amplitude > 0.001:
                    print("⚠️ Signal faible - parlez plus fort ou rapprochez-vous")
                else:
                    print("❌ Aucun signal détecté - vérifiez votre microphone")
                    
            except Exception as e:
                print(f"❌ Erreur test microphone: {e}")
            
            print("✅ Test audio terminé")
            
        except Exception as e:
            print(f"❌ Erreur périphériques audio: {e}")
        
        print("="*50)
    
    async def test_microphone_live(self):
        """Test en temps réel du microphone"""
        print("\n🎤 TEST MICROPHONE EN TEMPS RÉEL")
        print("="*40)
        print("Parlez... (Ctrl+C pour arrêter)")
        
        def audio_monitor(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            
            # Calculer le niveau audio
            volume_norm = np.linalg.norm(indata) * 10
            bar_length = int(volume_norm)
            bar = '█' * min(bar_length, 50)
            print(f"\r🔊 {bar:<50} {volume_norm:.1f}", end='', flush=True)
        
        try:
            with sd.InputStream(callback=audio_monitor, channels=1, samplerate=24000):
                await asyncio.sleep(10)  # Test pendant 10 secondes
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
        
        print(f"\n✅ Test microphone terminé")
    
    async def debug_audio_conversion(self):
        """Test de debug pour comprendre la conversion audio"""
        print("\n🔍 DEBUG: Test de conversion audio")
        print("="*50)
        
        def debug_callback(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            
            # Analyser les données brutes
            volume_norm = np.linalg.norm(indata[:, 0]) * 10
            audio_data = (indata[:, 0] * 32767).astype(np.int16)
            max_amplitude = np.max(np.abs(audio_data))
            
            print(f"\rVolume visuel: {volume_norm:.1f} | Amplitude PCM16: {max_amplitude:.0f} | Seuil: 10", end="")
            
            if max_amplitude > 10:
                print(" ✅ CAPTURÉ", end="")
            else:
                print(" ❌ IGNORÉ", end="")
        
        print("Parlez pendant 5 secondes pour voir la conversion...")
        try:
            with sd.InputStream(callback=debug_callback, channels=1, samplerate=24000, dtype=np.float32):
                await asyncio.sleep(5)
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
        
        print(f"\n✅ Debug terminé")
    
    async def display_volume_bar(self):
        """Affiche la barre de volume en temps réel pendant l'enregistrement"""
        while self.show_volume_bar and self.is_recording:
            try:
                # Créer la barre de volume
                bar_length = int(self.current_volume)
                bar_length = min(bar_length, 50)  # Maximum 50 caractères
                
                # Choisir la couleur/style selon le niveau
                if bar_length > 30:
                    bar_char = '█'  # Fort
                    status = "🔊 FORT"
                elif bar_length > 15:
                    bar_char = '▓'  # Moyen
                    status = "🎤 MOYEN"
                elif bar_length > 5:
                    bar_char = '▒'  # Faible
                    status = "🔉 FAIBLE"
                else:
                    bar_char = '░'  # Très faible
                    status = "🔈 SILENCE"
                
                bar = bar_char * bar_length
                empty = '·' * (50 - bar_length)
                
                # Afficher la barre avec le statut
                print(f"\r{status} |{bar}{empty}| {self.current_volume:.1f}    ", end='', flush=True)
                
                await asyncio.sleep(0.05)  # Mise à jour 20 fois par seconde
                
            except Exception as e:
                print(f"\n❌ Erreur affichage volume: {e}")
                break
    
    async def run(self):
        """Fonction principale"""
        print("🧪 TESTEUR DE CONNEXION OPENAI")
        print("="*40)
        print("🎯 Outil pour tester la connexion et l'audio")
        
        try:
            while True:
                try:
                    self.show_test_menu()
                    user_input = input("\n👉 Votre choix: ").strip()
                    
                    if user_input.lower() == 'q':
                        break
                    elif user_input == "1":
                        await self.test_connection_only()
                        input("\nAppuyez sur Entrée pour continuer...")
                    elif user_input == "2":
                        if not self.ws:
                            print("⚠️ Connexion requise. Connexion en cours...")
                            if not await self.connect_to_realtime():
                                print("❌ Impossible de se connecter")
                                continue
                            await self.send_session_config()
                        
                        # Démarrer les tâches d'écoute
                        response_task = asyncio.create_task(self.listen_to_responses())
                        audio_queue_task = asyncio.create_task(self.process_audio_queue())
                        
                        await self.start_recording(with_visual_feedback=False)
                        
                        # Attendre un peu pour la réponse
                        await asyncio.sleep(3)
                        
                        response_task.cancel()
                        audio_queue_task.cancel()
                        
                        input("\nAppuyez sur Entrée pour continuer...")
                        
                    elif user_input == "3":
                        print("\n🎯 Test complet: connexion + enregistrement")
                        if await self.connect_to_realtime():
                            await self.send_session_config()
                            
                            response_task = asyncio.create_task(self.listen_to_responses())
                            audio_queue_task = asyncio.create_task(self.process_audio_queue())
                            
                            print("✅ Connexion établie. Prêt pour l'enregistrement avec feedback visuel!")
                            await self.start_recording(with_visual_feedback=True)
                            
                            # Attendre la réponse
                            await asyncio.sleep(5)
                            
                            response_task.cancel()
                            audio_queue_task.cancel()
                            
                            try:
                                await self.ws.close()
                            except:
                                pass
                            
                            print("✅ Test complet terminé!")
                        
                        input("\nAppuyez sur Entrée pour continuer...")
                        
                    elif user_input == "4":
                        self.check_configuration()
                        input("\nAppuyez sur Entrée pour continuer...")
                    elif user_input == "5":
                        await self.test_microphone_live()
                        input("\nAppuyez sur Entrée pour continuer...")
                    elif user_input == "6":
                        await self.debug_audio_conversion()
                        input("\nAppuyez sur Entrée pour continuer...")
                    else:
                        print("❌ Choix invalide. Utilisez 1-6 ou 'q'")
                        
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
        print('\n👋 Arrêt du programme...')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(OpenAIConnectionTester().run())
    except KeyboardInterrupt:
        print("\n👋 Programme arrêté")
