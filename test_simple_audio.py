#!/usr/bin/env python3
"""
Test simple d'enregistrement audio sans WebSocket
Pour vérifier que la capture audio fonctionne correctement
"""
import asyncio
import os
import sys
import sounddevice as sd
import numpy as np
from dotenv import load_dotenv
import threading
import signal
import queue
import json
import base64

load_dotenv()

class SimpleAudioTester:
    def __init__(self):
        self.is_recording = False
        self.recording_stopped = threading.Event()
        self.audio_chunks = []
        self.current_volume = 0.0
        
    def audio_callback(self, indata, frames, time, status):
        """Callback pour l'audio en temps réel"""
        if status:
            print(f"⚠️ Statut audio: {status}")
        
        if self.is_recording:
            try:
                # Calculer le volume pour le feedback visuel
                volume_norm = np.linalg.norm(indata[:, 0]) * 10
                self.current_volume = volume_norm
                
                # Convertir en PCM16
                audio_data = (indata[:, 0] * 32767).astype(np.int16)
                max_amplitude = np.max(np.abs(audio_data))
                
                # Vérifier que les données ne sont pas silencieuses
                if max_amplitude > 10:  # Même seuil que le vrai système
                    # Encoder en base64 comme le vrai système
                    audio_b64 = base64.b64encode(audio_data.tobytes()).decode('utf-8')
                    
                    # Stocker le chunk
                    chunk_info = {
                        "amplitude": max_amplitude,
                        "volume_visual": volume_norm,
                        "size_bytes": len(audio_data.tobytes()),
                        "size_b64": len(audio_b64)
                    }
                    self.audio_chunks.append(chunk_info)
                    
                    # Debug en temps réel
                    if max_amplitude > 1000:
                        print(f" [CAPTURE: {max_amplitude:.0f}]", end="")
                
            except Exception as e:
                print(f"❌ Erreur callback audio: {e}")
    
    async def display_volume_bar(self):
        """Affiche la barre de volume en temps réel"""
        while self.is_recording:
            try:
                # Créer la barre de volume
                bar_length = int(self.current_volume)
                bar_length = min(bar_length, 50)
                
                # Choisir le style selon le niveau
                if bar_length > 30:
                    bar_char = '█'
                    status = "🔊 FORT"
                elif bar_length > 15:
                    bar_char = '▓'
                    status = "🎤 MOYEN"
                elif bar_length > 5:
                    bar_char = '▒'
                    status = "🔉 FAIBLE"
                else:
                    bar_char = '░'
                    status = "🔈 SILENCE"
                
                bar = bar_char * bar_length
                empty = '·' * (50 - bar_length)
                
                # Afficher avec le nombre de chunks capturés
                chunks_count = len(self.audio_chunks)
                print(f"\r{status} |{bar}{empty}| {self.current_volume:.1f} | Chunks: {chunks_count}    ", end='', flush=True)
                
                await asyncio.sleep(0.05)
                
            except Exception as e:
                print(f"\n❌ Erreur affichage volume: {e}")
                break
    
    def wait_for_enter(self):
        """Attendre l'entrée utilisateur"""
        try:
            input("Appuyez sur Entrée pour arrêter l'enregistrement...")
            self.recording_stopped.set()
        except:
            self.recording_stopped.set()
    
    async def test_audio_capture(self):
        """Test de capture audio simple"""
        print("\n" + "="*60)
        print("🧪 TEST SIMPLE DE CAPTURE AUDIO")
        print("="*60)
        print("💬 Parlez FORT et CLAIREMENT...")
        print("📊 Barre de volume et compteur de chunks ci-dessous:")
        print("⏹️  Appuyez sur Entrée pour arrêter")
        print("="*60)
        
        self.is_recording = True
        self.recording_stopped.clear()
        self.audio_chunks = []
        
        # Démarrer l'attente d'entrée dans un thread
        input_thread = threading.Thread(target=self.wait_for_enter)
        input_thread.daemon = True
        input_thread.start()
        
        try:
            # Configuration audio identique au vrai système
            with sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=24000,
                dtype=np.float32,
                blocksize=1024,
                latency='low'
            ):
                # Démarrer l'affichage de la barre de volume
                volume_task = asyncio.create_task(self.display_volume_bar())
                
                # Attendre l'arrêt
                while not self.recording_stopped.is_set():
                    await asyncio.sleep(0.1)
                
                volume_task.cancel()
                
        except Exception as e:
            print(f"❌ Erreur enregistrement: {e}")
        
        self.is_recording = False
        
        # Analyser les résultats
        print(f"\n\n📊 RÉSULTATS DU TEST:")
        print("="*40)
        print(f"🎵 Chunks audio capturés: {len(self.audio_chunks)}")
        
        if self.audio_chunks:
            amplitudes = [chunk["amplitude"] for chunk in self.audio_chunks]
            volumes = [chunk["volume_visual"] for chunk in self.audio_chunks]
            sizes = [chunk["size_bytes"] for chunk in self.audio_chunks]
            
            print(f"📈 Amplitude min/max: {min(amplitudes):.0f} / {max(amplitudes):.0f}")
            print(f"🔊 Volume visuel min/max: {min(volumes):.1f} / {max(volumes):.1f}")
            print(f"📦 Taille chunk min/max: {min(sizes)} / {max(sizes)} bytes")
            print(f"💾 Total données audio: {sum(sizes)} bytes")
            
            # Estimation de la durée
            sample_rate = 24000
            samples_per_chunk = 1024
            duration_estimate = len(self.audio_chunks) * samples_per_chunk / sample_rate
            print(f"⏱️ Durée estimée: {duration_estimate:.2f} secondes")
            
            if len(self.audio_chunks) >= 10:
                print("✅ SUCCÈS: Assez d'audio capturé pour OpenAI")
            else:
                print("⚠️ ATTENTION: Peu d'audio capturé")
        else:
            print("❌ ÉCHEC: Aucun audio capturé")
        
        print("="*40)
    
    def show_menu(self):
        """Menu principal"""
        print("\n" + "="*50)
        print("🧪 TESTEUR AUDIO SIMPLE")
        print("="*50)
        print("1️⃣  - Test capture audio avec feedback visuel")
        print("2️⃣  - Test périphériques audio")
        print("❌ - Quitter (q)")
        print("="*50)
    
    def test_audio_devices(self):
        """Test des périphériques audio"""
        print("\n📊 Test des périphériques audio:")
        print("="*40)
        
        try:
            devices = sd.query_devices()
            input_device_id = sd.default.device[0]
            input_device = devices[input_device_id]
            
            print(f"📥 Périphérique d'entrée: {input_device['name']}")
            print(f"   Canaux max: {input_device['max_input_channels']}")
            print(f"   Fréquence: {input_device['default_samplerate']} Hz")
            
            # Test rapide
            print("\n🧪 Test rapide (2 secondes)...")
            print("🎤 Parlez maintenant...")
            
            recording = sd.rec(int(2 * 24000), samplerate=24000, channels=1, dtype=np.float32)
            sd.wait()
            
            max_amplitude = np.max(np.abs(recording))
            rms = np.sqrt(np.mean(recording**2))
            
            print(f"📊 Amplitude max: {max_amplitude:.4f}")
            print(f"📊 RMS: {rms:.4f}")
            
            if max_amplitude > 0.01:
                print("✅ Microphone fonctionne bien")
            else:
                print("❌ Signal très faible ou inexistant")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        print("="*40)
    
    async def run(self):
        """Fonction principale"""
        print("🧪 TESTEUR AUDIO SIMPLE")
        print("="*30)
        print("🎯 Test la capture audio sans WebSocket")
        
        try:
            while True:
                try:
                    self.show_menu()
                    user_input = input("\n👉 Votre choix: ").strip()
                    
                    if user_input.lower() == 'q':
                        break
                    elif user_input == "1":
                        await self.test_audio_capture()
                        input("\nAppuyez sur Entrée pour continuer...")
                    elif user_input == "2":
                        self.test_audio_devices()
                        input("\nAppuyez sur Entrée pour continuer...")
                    else:
                        print("❌ Choix invalide. Utilisez 1-2 ou 'q'")
                        
                except EOFError:
                    print("\n👋 Au revoir!")
                    break
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")

if __name__ == "__main__":
    def signal_handler(sig, frame):
        print('\n👋 Arrêt du programme...')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(SimpleAudioTester().run())
    except KeyboardInterrupt:
        print("\n👋 Programme arrêté")
