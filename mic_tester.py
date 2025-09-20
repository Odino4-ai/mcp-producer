#!/usr/bin/env python3
"""
Testeur de Microphone Ultra-Simple
Pour diagnostiquer pourquoi l'audio montre toujours SILENCE
"""
import sounddevice as sd
import numpy as np
import time

class MicTester:
    def __init__(self):
        self.is_recording = False
        
    def test_devices(self):
        """Lister tous les périphériques audio"""
        print("🎤 PÉRIPHÉRIQUES AUDIO DISPONIBLES:")
        print("="*50)
        
        try:
            devices = sd.query_devices()
            
            for i, device in enumerate(devices):
                device_type = []
                if device['max_input_channels'] > 0:
                    device_type.append("INPUT")
                if device['max_output_channels'] > 0:
                    device_type.append("OUTPUT")
                
                status = "🎤" if "INPUT" in device_type else "🔊"
                default_marker = " (DÉFAUT)" if i == sd.default.device[0] else ""
                
                print(f"{status} {i}: {device['name']}{default_marker}")
                print(f"     Canaux IN: {device['max_input_channels']}, OUT: {device['max_output_channels']}")
                print(f"     Fréquence: {device['default_samplerate']} Hz")
                print()
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    def test_realtime_volume(self):
        """Test volume en temps réel"""
        print("\n🎤 TEST VOLUME TEMPS RÉEL")
        print("="*40)
        print("Parlez... (Ctrl+C pour arrêter)")
        print()
        
        self.is_recording = True
        
        def callback(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            
            try:
                # Plusieurs méthodes de calcul du volume
                volume1 = np.linalg.norm(indata) * 10
                volume2 = np.max(np.abs(indata)) * 100
                volume3 = np.sqrt(np.mean(indata**2)) * 100
                
                # Barre visuelle
                bar_length = int(min(volume1, 50))
                bar = '█' * bar_length + '·' * (50 - bar_length)
                
                print(f"\r🔊 |{bar}| Vol1:{volume1:.1f} Vol2:{volume2:.1f} Vol3:{volume3:.1f}", end='', flush=True)
                
            except Exception as e:
                print(f"\nErreur callback: {e}")
        
        try:
            with sd.InputStream(callback=callback, channels=1, samplerate=44100):
                while self.is_recording:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            self.is_recording = False
            print(f"\n✅ Test terminé")
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
    
    def test_specific_device(self):
        """Test d'un périphérique spécifique"""
        self.test_devices()
        
        try:
            device_id = input("\n👉 ID du périphérique à tester (ou Entrée pour défaut): ").strip()
            
            if device_id.isdigit():
                device_id = int(device_id)
            else:
                device_id = None
            
            print(f"\n🎤 Test du périphérique {device_id or 'par défaut'}...")
            
            duration = 3
            sample_rate = 44100
            
            print("Parlez maintenant...")
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype=np.float32,
                device=device_id
            )
            sd.wait()
            
            # Analyser
            max_vol = np.max(np.abs(recording))
            rms = np.sqrt(np.mean(recording**2))
            
            print(f"📊 Résultats:")
            print(f"   Volume max: {max_vol:.6f}")
            print(f"   RMS: {rms:.6f}")
            
            if max_vol > 0.001:
                print("✅ Périphérique fonctionne!")
            else:
                print("❌ Aucun signal détecté")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    def run(self):
        """Menu principal"""
        while True:
            print("\n" + "="*50)
            print("🎤 TESTEUR DE MICROPHONE")
            print("="*50)
            print("1️⃣  - Lister tous les périphériques")
            print("2️⃣  - Test volume temps réel")
            print("3️⃣  - Test périphérique spécifique")
            print("4️⃣  - Test enregistrement simple")
            print("❌ q - Quitter")
            print("="*50)
            
            choice = input("\n👉 Votre choix: ").strip()
            
            if choice.lower() == 'q':
                break
            elif choice == '1':
                self.test_devices()
                input("\nAppuyez sur Entrée...")
            elif choice == '2':
                self.test_realtime_volume()
                input("\nAppuyez sur Entrée...")
            elif choice == '3':
                self.test_specific_device()
                input("\nAppuyez sur Entrée...")
            elif choice == '4':
                print("\n🎤 Enregistrement 3 secondes...")
                try:
                    rec = sd.rec(3*44100, samplerate=44100, channels=1)
                    print("Parlez...")
                    sd.wait()
                    vol = np.max(np.abs(rec))
                    print(f"Volume: {vol:.6f}")
                    if vol > 0.001:
                        print("✅ Enregistrement OK")
                    else:
                        print("❌ Pas d'audio")
                except Exception as e:
                    print(f"❌ Erreur: {e}")
                input("\nAppuyez sur Entrée...")
            else:
                print("❌ Choix invalide")

if __name__ == "__main__":
    try:
        tester = MicTester()
        tester.run()
    except KeyboardInterrupt:
        print("\n👋 Au revoir!")
