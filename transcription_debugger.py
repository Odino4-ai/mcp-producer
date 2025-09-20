#!/usr/bin/env python3
"""
Debugger de Transcription OpenAI
Outil spécialisé pour diagnostiquer les problèmes de transcription audio
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
import base64
import time

load_dotenv()

class TranscriptionDebugger:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview-2024-10-01')
        self.ws = None
        self.is_recording = False
        self.recording_stopped = threading.Event()
        
        # Statistiques de debug
        self.audio_stats = {
            "chunks_sent": 0,
            "chunks_filtered": 0,
            "total_bytes": 0,
            "recording_duration": 0,
            "transcription_attempts": 0,
            "transcription_successes": 0,
            "transcription_failures": 0
        }
        
        self.audio_queue = queue.Queue(maxsize=200)
        self.connection_active = True
        self.session_created = False
        
    async def connect_to_realtime(self):
        """Connexion optimisée pour la transcription"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'OpenAI-Beta': 'realtime=v1'
        }
        
        uri = f"wss://api.openai.com/v1/realtime?model={self.model}"
        
        try:
            print("🔗 Connexion à OpenAI pour debug transcription...")
            self.ws = await websockets.connect(
                uri, 
                additional_headers=headers,
                ping_interval=30,
                ping_timeout=15,
                close_timeout=10
            )
            print("✅ Connexion établie")
            return True
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return False
    
    async def send_optimized_session_config(self):
        """Configuration optimisée pour la transcription"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "instructions": "Tu es un assistant de test. Répète simplement ce que tu entends pour confirmer la transcription.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.2,  # Seuil très bas
                    "prefix_padding_ms": 800,  # Beaucoup de padding
                    "silence_duration_ms": 800  # Attendre longtemps
                }
            }
        }
        
        try:
            await self.ws.send(json.dumps(config))
            print("📤 Configuration optimisée envoyée")
        except Exception as e:
            print(f"❌ Erreur config: {e}")
    
    async def listen_to_events(self):
        """Écouter et analyser tous les événements"""
        try:
            async for message in self.ws:
                try:
                    event = json.loads(message)
                    await self.analyze_event(event)
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
    
    async def analyze_event(self, event):
        """Analyser les événements pour le debug"""
        event_type = event.get("type")
        timestamp = time.strftime("%H:%M:%S")
        
        if event_type == "session.created":
            print(f"[{timestamp}] ✅ Session créée")
            self.session_created = True
            
        elif event_type == "session.updated":
            print(f"[{timestamp}] ✅ Session mise à jour")
            
        elif event_type == "input_audio_buffer.speech_started":
            print(f"[{timestamp}] 🎤 🟢 VAD: Début de parole")
            
        elif event_type == "input_audio_buffer.speech_stopped":
            print(f"[{timestamp}] 🔇 🔴 VAD: Fin de parole")
            
        elif event_type == "input_audio_buffer.committed":
            print(f"[{timestamp}] 📦 Buffer audio committé")
            self.audio_stats["transcription_attempts"] += 1
            
        elif event_type == "conversation.item.created":
            print(f"[{timestamp}] 📝 Item de conversation créé")
            
        elif event_type == "conversation.item.input_audio_transcription.completed":
            transcript = event.get("transcript", "")
            print(f"[{timestamp}] ✅ TRANSCRIPTION RÉUSSIE: '{transcript}'")
            self.audio_stats["transcription_successes"] += 1
            
        elif event_type == "conversation.item.input_audio_transcription.failed":
            error = event.get("error", {})
            print(f"[{timestamp}] ❌ TRANSCRIPTION ÉCHOUÉE: {error}")
            self.audio_stats["transcription_failures"] += 1
            
            # Analyser la cause
            if "too short" in str(error).lower():
                print("   💡 Cause: Audio trop court")
            elif "quality" in str(error).lower():
                print("   💡 Cause: Qualité audio insuffisante")
            elif "format" in str(error).lower():
                print("   💡 Cause: Problème de format")
            else:
                print("   💡 Cause: Inconnue")
            
        elif event_type == "response.created":
            print(f"[{timestamp}] 🤖 Réponse en cours de génération")
            
        elif event_type == "response.done":
            print(f"[{timestamp}] ✅ Réponse terminée")
            
        elif event_type == "error":
            error_details = event.get("error", {})
            print(f"[{timestamp}] ❌ ERREUR SERVEUR: {error_details}")
    
    def audio_callback_debug(self, indata, frames, time, status):
        """Callback audio avec debug détaillé"""
        if status:
            print(f"⚠️ Status: {status}")
        
        if self.is_recording and self.ws and self.session_created:
            try:
                # Analyser la qualité audio
                audio_float = indata[:, 0]
                volume_norm = np.linalg.norm(audio_float) * 10
                
                # Convertir en PCM16
                audio_data = (audio_float * 32767).astype(np.int16)
                max_amplitude = np.max(np.abs(audio_data))
                rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
                
                # Statistiques
                chunk_size = len(audio_data.tobytes())
                self.audio_stats["total_bytes"] += chunk_size
                
                # Critères de qualité améliorés
                quality_ok = (
                    max_amplitude > 100 and  # Amplitude minimum
                    rms > 50 and           # RMS minimum
                    volume_norm > 5        # Volume visuel minimum
                )
                
                if quality_ok:
                    # Encoder et envoyer
                    audio_b64 = base64.b64encode(audio_data.tobytes()).decode('utf-8')
                    
                    audio_event = {
                        "type": "input_audio_buffer.append",
                        "audio": audio_b64
                    }
                    
                    try:
                        self.audio_queue.put_nowait(json.dumps(audio_event))
                        self.audio_stats["chunks_sent"] += 1
                        
                        # Debug visuel
                        if max_amplitude > 1000:
                            print(f" [✅ ENVOYÉ: {max_amplitude:.0f}]", end="")
                    except queue.Full:
                        pass
                else:
                    self.audio_stats["chunks_filtered"] += 1
                    # Debug: pourquoi filtré
                    if volume_norm > 10:  # Volume visuel fort mais qualité faible
                        print(f" [❌ FILTRÉ: amp={max_amplitude:.0f}, rms={rms:.0f}]", end="")
                    
            except Exception as e:
                print(f"❌ Erreur callback: {e}")
    
    async def process_audio_queue(self):
        """Traiter la queue avec statistiques"""
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
    
    def wait_for_enter(self):
        """Attendre entrée utilisateur"""
        try:
            input("Appuyez sur Entrée pour arrêter...")
            self.recording_stopped.set()
        except:
            self.recording_stopped.set()
    
    async def debug_recording_session(self):
        """Session d'enregistrement avec debug complet"""
        print("\n" + "="*60)
        print("🔍 SESSION DE DEBUG TRANSCRIPTION")
        print("="*60)
        print("💬 Parlez CLAIREMENT et DISTINCTEMENT")
        print("⏰ Parlez pendant au moins 3-4 secondes")
        print("🔊 Évitez les bruits de fond")
        print("⏹️  Appuyez sur Entrée pour arrêter")
        print("="*60)
        
        # Reset des stats
        self.audio_stats = {
            "chunks_sent": 0,
            "chunks_filtered": 0,
            "total_bytes": 0,
            "recording_duration": 0,
            "transcription_attempts": 0,
            "transcription_successes": 0,
            "transcription_failures": 0
        }
        
        self.is_recording = True
        self.recording_stopped.clear()
        
        # Thread pour attendre l'entrée
        input_thread = threading.Thread(target=self.wait_for_enter)
        input_thread.daemon = True
        input_thread.start()
        
        start_time = time.time()
        
        try:
            # Configuration audio optimisée pour la transcription
            with sd.InputStream(
                callback=self.audio_callback_debug,
                channels=1,
                samplerate=24000,  # Fréquence recommandée par OpenAI
                dtype=np.float32,
                blocksize=2048,   # Blocs plus grands pour meilleure qualité
                latency='high'    # Latence plus élevée pour meilleure qualité
            ):
                while not self.recording_stopped.is_set():
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            print(f"❌ Erreur enregistrement: {e}")
        
        self.is_recording = False
        end_time = time.time()
        self.audio_stats["recording_duration"] = end_time - start_time
        
        print(f"\n🔇 Enregistrement terminé")
        
        # Attendre un peu pour les événements de transcription
        print("⏳ Attente des résultats de transcription...")
        await asyncio.sleep(3)
        
        # Afficher les statistiques
        self.show_debug_stats()
    
    def show_debug_stats(self):
        """Afficher les statistiques de debug"""
        stats = self.audio_stats
        
        print("\n" + "="*50)
        print("📊 STATISTIQUES DE DEBUG")
        print("="*50)
        print(f"⏱️  Durée d'enregistrement: {stats['recording_duration']:.2f}s")
        print(f"📦 Chunks audio envoyés: {stats['chunks_sent']}")
        print(f"🚫 Chunks filtrés: {stats['chunks_filtered']}")
        print(f"💾 Total bytes audio: {stats['total_bytes']}")
        
        if stats['recording_duration'] > 0:
            bytes_per_sec = stats['total_bytes'] / stats['recording_duration']
            print(f"📈 Débit audio: {bytes_per_sec:.0f} bytes/sec")
        
        print(f"\n📝 Tentatives de transcription: {stats['transcription_attempts']}")
        print(f"✅ Transcriptions réussies: {stats['transcription_successes']}")
        print(f"❌ Transcriptions échouées: {stats['transcription_failures']}")
        
        if stats['transcription_attempts'] > 0:
            success_rate = (stats['transcription_successes'] / stats['transcription_attempts']) * 100
            print(f"📊 Taux de réussite: {success_rate:.1f}%")
        
        # Diagnostic
        print(f"\n🔍 DIAGNOSTIC:")
        if stats['chunks_sent'] == 0:
            print("❌ Aucun audio envoyé - Problème de capture ou qualité")
        elif stats['chunks_sent'] < 10:
            print("⚠️ Peu d'audio envoyé - Parlez plus fort ou plus longtemps")
        elif stats['transcription_failures'] > stats['transcription_successes']:
            print("⚠️ Beaucoup d'échecs - Problème de qualité audio")
        elif stats['transcription_successes'] > 0:
            print("✅ Transcription fonctionne - Audio de bonne qualité")
        else:
            print("🤔 Audio envoyé mais pas de tentative de transcription")
        
        print("="*50)
    
    def show_menu(self):
        """Menu du debugger"""
        print("\n" + "="*60)
        print("🔍 DEBUGGER DE TRANSCRIPTION OPENAI")
        print("="*60)
        print("1️⃣  - Test de transcription avec debug complet")
        print("2️⃣  - Test qualité audio (sans OpenAI)")
        print("3️⃣  - Afficher les dernières statistiques")
        print("4️⃣  - Reset des statistiques")
        print("❌ q - Quitter")
        print("="*60)
    
    def test_audio_quality(self):
        """Test de qualité audio local"""
        print("\n🎤 Test de qualité audio (5 secondes)")
        print("Parlez maintenant...")
        
        # Enregistrer 5 secondes
        duration = 5
        sample_rate = 24000
        
        recording = sd.rec(int(duration * sample_rate), 
                          samplerate=sample_rate, 
                          channels=1, 
                          dtype=np.float32)
        sd.wait()
        
        # Analyser la qualité
        audio_data = (recording[:, 0] * 32767).astype(np.int16)
        max_amplitude = np.max(np.abs(audio_data))
        rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
        volume_norm = np.linalg.norm(recording[:, 0]) * 10
        
        print(f"\n📊 Analyse de qualité:")
        print(f"   Amplitude max: {max_amplitude:.0f}")
        print(f"   RMS: {rms:.0f}")
        print(f"   Volume visuel moyen: {volume_norm:.1f}")
        
        # Critères de qualité
        print(f"\n🎯 Critères de qualité:")
        print(f"   Amplitude > 100: {'✅' if max_amplitude > 100 else '❌'} ({max_amplitude:.0f})")
        print(f"   RMS > 50: {'✅' if rms > 50 else '❌'} ({rms:.0f})")
        print(f"   Volume > 5: {'✅' if volume_norm > 5 else '❌'} ({volume_norm:.1f})")
        
        if max_amplitude > 100 and rms > 50:
            print("✅ Qualité suffisante pour la transcription")
        else:
            print("❌ Qualité insuffisante - parlez plus fort")
    
    async def run(self):
        """Fonction principale"""
        print("🔍 DEBUGGER DE TRANSCRIPTION")
        print("="*40)
        print("🎯 Diagnostiquer les problèmes de transcription OpenAI")
        
        try:
            while True:
                try:
                    self.show_menu()
                    choice = input("\n👉 Votre choix: ").strip()
                    
                    if choice.lower() == 'q':
                        break
                        
                    elif choice == '1':
                        if await self.connect_to_realtime():
                            await self.send_optimized_session_config()
                            
                            # Démarrer les tâches
                            event_task = asyncio.create_task(self.listen_to_events())
                            audio_task = asyncio.create_task(self.process_audio_queue())
                            
                            await self.debug_recording_session()
                            
                            event_task.cancel()
                            audio_task.cancel()
                            
                            try:
                                await self.ws.close()
                            except:
                                pass
                        else:
                            print("❌ Impossible de se connecter")
                            
                    elif choice == '2':
                        self.test_audio_quality()
                        input("\nAppuyez sur Entrée pour continuer...")
                        
                    elif choice == '3':
                        self.show_debug_stats()
                        input("\nAppuyez sur Entrée pour continuer...")
                        
                    elif choice == '4':
                        self.audio_stats = {
                            "chunks_sent": 0,
                            "chunks_filtered": 0,
                            "total_bytes": 0,
                            "recording_duration": 0,
                            "transcription_attempts": 0,
                            "transcription_successes": 0,
                            "transcription_failures": 0
                        }
                        print("✅ Statistiques réinitialisées")
                        
                    else:
                        print("❌ Choix invalide")
                        
                except EOFError:
                    print("\n👋 Au revoir!")
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
        finally:
            self.connection_active = False

if __name__ == "__main__":
    def signal_handler(sig, frame):
        print('\n👋 Arrêt...')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        debugger = TranscriptionDebugger()
        asyncio.run(debugger.run())
    except KeyboardInterrupt:
        print("\n👋 Programme arrêté")
