#!/usr/bin/env python3
"""
Démo Simple Voice → MCP
Version ultra-simplifiée qui fonctionne étape par étape
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
import base64
import re

load_dotenv()

class SimpleVoiceDemo:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.desktop_path = Path.home() / "Desktop"
        self.ws = None
        
    # ========== FONCTIONS MCP LOCALES ==========
    def mcp_create_folder(self, name):
        """Créer un dossier - version locale simple"""
        try:
            folder_path = self.desktop_path / name
            folder_path.mkdir(exist_ok=True)
            print(f"✅ DOSSIER CRÉÉ: {folder_path}")
            return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def mcp_create_file(self, name):
        """Créer un fichier - version locale simple"""
        try:
            if '.' not in name:
                name += '.txt'
            file_path = self.desktop_path / name
            file_path.touch()
            print(f"✅ FICHIER CRÉÉ: {file_path}")
            return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def mcp_list_desktop(self):
        """Lister le bureau - version locale simple"""
        try:
            items = list(self.desktop_path.iterdir())
            folders = [item.name for item in items if item.is_dir()]
            files = [item.name for item in items if item.is_file() and not item.name.startswith('.')]
            
            print(f"✅ CONTENU DU BUREAU:")
            print(f"   📁 {len(folders)} dossiers: {folders[:3]}")
            print(f"   📄 {len(files)} fichiers: {files[:3]}")
            return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    # ========== PARSING SIMPLE ==========
    def parse_simple_command(self, text):
        """Parser ultra-simple"""
        text_lower = text.lower()
        
        print(f"\n🔍 PARSING: '{text}'")
        
        # Dossier
        if "dossier" in text_lower and ("crée" in text_lower or "créer" in text_lower):
            # Extraire le nom après "dossier"
            match = re.search(r'dossier\s+([a-zA-Z0-9\s\-_]+)', text_lower)
            if match:
                name = match.group(1).strip()
                name = re.sub(r'\s+', '-', name)
                name = re.sub(r'[^a-zA-Z0-9\-_]', '', name)
                if name:
                    print(f"✅ Commande dossier: '{name}'")
                    return ("folder", name)
        
        # Fichier
        if "fichier" in text_lower and ("crée" in text_lower or "créer" in text_lower):
            match = re.search(r'fichier\s+([a-zA-Z0-9\s\-_.]+)', text_lower)
            if match:
                name = match.group(1).strip()
                name = re.sub(r'\s+', '_', name)
                if name:
                    print(f"✅ Commande fichier: '{name}'")
                    return ("file", name)
        
        # Liste
        if any(word in text_lower for word in ["liste", "montre", "affiche", "contient"]) and "bureau" in text_lower:
            print(f"✅ Commande liste")
            return ("list", "")
        
        print(f"❌ Commande non reconnue")
        return None
    
    # ========== TEST AUDIO SIMPLE ==========
    async def test_microphone(self):
        """Test simple du microphone"""
        print("\n🎤 TEST MICROPHONE (3 secondes)")
        print("Parlez maintenant...")
        
        # Enregistrer
        duration = 3
        sample_rate = 44100
        
        try:
            recording = sd.rec(int(duration * sample_rate), 
                              samplerate=sample_rate, 
                              channels=1, 
                              dtype=np.float32)
            sd.wait()
            
            # Analyser
            max_vol = np.max(np.abs(recording))
            rms = np.sqrt(np.mean(recording**2))
            
            print(f"📊 Volume max: {max_vol:.4f}")
            print(f"📊 RMS: {rms:.4f}")
            
            if max_vol > 0.01:
                print("✅ Microphone fonctionne!")
                
                # Sauvegarder pour test
                import wave
                test_file = "test_audio.wav"
                
                # Convertir en int16
                audio_int = (recording * 32767).astype(np.int16)
                
                with wave.open(test_file, 'w') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_int.tobytes())
                
                print(f"💾 Audio sauvé dans {test_file}")
                return True
            else:
                print("❌ Pas d'audio détecté")
                return False
                
        except Exception as e:
            print(f"❌ Erreur test micro: {e}")
            return False
    
    # ========== TRANSCRIPTION OPENAI SIMPLE ==========
    async def test_transcription_simple(self):
        """Test de transcription avec OpenAI simple"""
        if not await self.test_microphone():
            print("❌ Test microphone échoué")
            return
        
        print("\n🔗 Test transcription OpenAI...")
        
        # Lire le fichier audio de test
        try:
            import wave
            with wave.open("test_audio.wav", 'rb') as wf:
                audio_data = wf.readframes(wf.getnframes())
            
            # Connecter à OpenAI
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'OpenAI-Beta': 'realtime=v1'
            }
            
            uri = f"wss://api.openai.com/v1/realtime?model={self.model}"
            
            try:
                self.ws = await websockets.connect(uri, additional_headers=headers)
                print("✅ Connexion OpenAI OK")
                
                # Configuration simple
                config = {
                    "type": "session.update",
                    "session": {
                        "modalities": ["audio"],
                        "input_audio_transcription": {"model": "whisper-1"}
                    }
                }
                
                await self.ws.send(json.dumps(config))
                
                # Envoyer l'audio
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                
                # Créer item audio
                audio_item = {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "audio": audio_b64
                            }
                        ]
                    }
                }
                
                await self.ws.send(json.dumps(audio_item))
                print("📤 Audio envoyé pour transcription")
                
                # Écouter la réponse
                timeout = 10
                start_time = asyncio.get_event_loop().time()
                
                async for message in self.ws:
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        print("⏰ Timeout")
                        break
                    
                    try:
                        event = json.loads(message)
                        event_type = event.get("type")
                        
                        if event_type == "conversation.item.input_audio_transcription.completed":
                            transcript = event.get("transcript", "")
                            print(f"📝 ✅ TRANSCRIPTION: '{transcript}'")
                            
                            # TEST DU PARSING
                            command = self.parse_simple_command(transcript)
                            if command:
                                action, name = command
                                print(f"🎯 COMMANDE IDENTIFIÉE: {action} -> {name}")
                                
                                # EXÉCUTION MCP
                                if action == "folder":
                                    success = self.mcp_create_folder(name)
                                elif action == "file":
                                    success = self.mcp_create_file(name)
                                elif action == "list":
                                    success = self.mcp_list_desktop()
                                
                                if success:
                                    print("🎉 SUCCÈS COMPLET! Voix → Transcription → Parsing → MCP ✅")
                                else:
                                    print("❌ Échec MCP")
                            else:
                                print("❌ Commande non reconnue")
                            
                            break
                            
                        elif event_type == "conversation.item.input_audio_transcription.failed":
                            error = event.get("error", {})
                            print(f"❌ TRANSCRIPTION ÉCHOUÉE: {error}")
                            break
                            
                    except Exception as e:
                        print(f"❌ Erreur événement: {e}")
                
                await self.ws.close()
                
            except Exception as e:
                print(f"❌ Erreur WebSocket: {e}")
                
        except Exception as e:
            print(f"❌ Erreur lecture audio: {e}")
    
    # ========== TEST COMPLET ÉTAPE PAR ÉTAPE ==========
    async def demo_step_by_step(self):
        """Démo complète étape par étape"""
        print("\n" + "="*60)
        print("🎯 DÉMO ÉTAPE PAR ÉTAPE: VOIX → MCP")
        print("="*60)
        
        # Étape 1: Test microphone
        print("\n📍 ÉTAPE 1: Test du microphone")
        print("-" * 30)
        input("Appuyez sur Entrée pour tester votre microphone...")
        
        if not await self.test_microphone():
            print("❌ Microphone ne fonctionne pas - Arrêt")
            return
        
        print("✅ Microphone OK!")
        
        # Étape 2: Test transcription
        print("\n📍 ÉTAPE 2: Test transcription + parsing + MCP")
        print("-" * 30)
        print("🎤 Dites: 'Crée un dossier test-demo'")
        input("Appuyez sur Entrée quand vous êtes prêt...")
        
        await self.test_transcription_simple()
        
        # Étape 3: Vérification
        print("\n📍 ÉTAPE 3: Vérification")
        print("-" * 30)
        
        test_folder = self.desktop_path / "test-demo"
        if test_folder.exists():
            print("🎉 SUCCÈS TOTAL! Le dossier a été créé!")
            print(f"📁 Vérifiez votre bureau: {test_folder}")
        else:
            print("❌ Le dossier n'a pas été créé")
        
        print("\n✅ Démo terminée")
    
    # ========== INTERFACE ==========
    def show_menu(self):
        print("\n" + "="*50)
        print("🎯 DÉMO SIMPLE VOICE → MCP")
        print("="*50)
        print("1️⃣  - Test microphone seulement")
        print("2️⃣  - Test transcription + MCP")
        print("3️⃣  - Démo complète étape par étape")
        print("4️⃣  - Test parsing manuel")
        print("❌ q - Quitter")
        print("="*50)
    
    async def test_parsing_manual(self):
        """Test du parsing manuellement"""
        print("\n🧪 Test parsing manuel")
        
        examples = [
            "Crée un dossier projet",
            "Crée un dossier test-demo", 
            "Crée un fichier readme.txt",
            "Liste le bureau",
            "Montre-moi le bureau"
        ]
        
        print("Exemples:")
        for i, ex in enumerate(examples, 1):
            print(f"  {i}. {ex}")
        
        text = input("\nTapez une commande ou choisissez (1-5): ").strip()
        
        if text.isdigit() and 1 <= int(text) <= 5:
            text = examples[int(text) - 1]
        
        if text:
            command = self.parse_simple_command(text)
            if command:
                action, name = command
                print(f"✅ Parsing réussi: {action} -> {name}")
                
                # Exécuter directement
                if action == "folder":
                    self.mcp_create_folder(name)
                elif action == "file":
                    self.mcp_create_file(name)
                elif action == "list":
                    self.mcp_list_desktop()
            else:
                print("❌ Parsing échoué")
    
    async def run(self):
        """Fonction principale"""
        print("🎯 DÉMO SIMPLE VOICE → MCP")
        print("="*30)
        print("🎯 Test chaque étape individuellement")
        
        try:
            while True:
                try:
                    self.show_menu()
                    choice = input("\n👉 Votre choix: ").strip()
                    
                    if choice.lower() == 'q':
                        break
                        
                    elif choice == '1':
                        await self.test_microphone()
                        input("\nAppuyez sur Entrée pour continuer...")
                        
                    elif choice == '2':
                        await self.test_transcription_simple()
                        input("\nAppuyez sur Entrée pour continuer...")
                        
                    elif choice == '3':
                        await self.demo_step_by_step()
                        input("\nAppuyez sur Entrée pour continuer...")
                        
                    elif choice == '4':
                        await self.test_parsing_manual()
                        input("\nAppuyez sur Entrée pour continuer...")
                        
                    else:
                        print("❌ Choix invalide")
                        
                except EOFError:
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")

if __name__ == "__main__":
    try:
        demo = SimpleVoiceDemo()
        asyncio.run(demo.run())
    except KeyboardInterrupt:
        print("\n👋 Programme arrêté")
