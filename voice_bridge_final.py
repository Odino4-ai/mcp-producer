#!/usr/bin/env python3
"""
VOICE BRIDGE FINAL
Interface vocale qui traduit la parole en commandes pour Claude Desktop MCP
"""
import os
import openai
import sounddevice as sd
import numpy as np
import tempfile
import wave
from dotenv import load_dotenv
import pyperclip
import time
import sys

load_dotenv()

class VoiceBridgeFinal:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        print("🎤 VOICE BRIDGE FINAL")
        print("="*40)
        print("1. Parlez dans le micro")
        print("2. Le texte sera copié dans le presse-papier")
        print("3. Collez dans Claude Desktop pour exécution")
        print("="*40)
    
    def record_audio(self, duration=5, sample_rate=44100):
        """Enregistrer l'audio du microphone"""
        print("🔴 ENREGISTREMENT...")
        print("Parlez maintenant!")
        
        # Affichage du compte à rebours
        for i in range(duration, 0, -1):
            print(f"⏱️  {i}s restantes", end='\r')
            time.sleep(1)
        
        print("\n🎤 Capture audio...")
        audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
        sd.wait()
        return audio, sample_rate
    
    def transcribe_audio(self, audio, sample_rate):
        """Transcrire l'audio via OpenAI Whisper"""
        print("🔄 Transcription en cours...")
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            # Convertir en fichier WAV
            with wave.open(tmp.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes((audio * 32767).astype(np.int16).tobytes())
            
            # Transcription
            with open(tmp.name, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file, 
                    language="fr"
                )
            
            os.unlink(tmp.name)
            return transcript.text
    
    def create_claude_prompt(self, voice_command):
        """Créer un prompt optimisé pour Claude Desktop"""
        prompt = f"""Commande vocale reçue: "{voice_command}"

Utilise les outils MCP voice-file-controller disponibles pour exécuter cette demande:

- create_folder: pour créer des dossiers
- create_file: pour créer des fichiers  
- list_contents: pour lister le contenu

Exemples de traduction:
- "crée un dossier projet" → create_folder avec folder_path="projet"
- "crée 3 dossiers" → créer 3 dossiers avec des noms logiques
- "crée un fichier readme" → create_file avec file_path="readme.txt"
- "montre le bureau" → list_contents

Exécute immédiatement la commande avec les outils appropriés."""

        return prompt
    
    def copy_to_clipboard(self, text):
        """Copier le texte dans le presse-papier"""
        try:
            pyperclip.copy(text)
            print("✅ Prompt copié dans le presse-papier!")
            print("👉 Collez maintenant dans Claude Desktop (Cmd+V)")
            return True
        except Exception as e:
            print(f"❌ Erreur copie: {e}")
            return False
    
    def run_voice_session(self):
        """Session vocale complète"""
        try:
            # 1. Enregistrement
            audio, sr = self.record_audio()
            
            # 2. Transcription
            text = self.transcribe_audio(audio, sr)
            print(f"📝 Vous avez dit: '{text}'")
            
            if not text.strip():
                print("❌ Aucun texte détecté")
                return
            
            # 3. Création du prompt
            prompt = self.create_claude_prompt(text)
            
            # 4. Copie dans le presse-papier
            if self.copy_to_clipboard(prompt):
                print("\n" + "="*50)
                print("PROMPT GÉNÉRÉ:")
                print("="*50)
                print(prompt)
                print("="*50)
                print("\n🎯 Maintenant dans Claude Desktop:")
                print("1. Ouvrez une conversation")
                print("2. Collez avec Cmd+V")
                print("3. Appuyez sur Entrée")
                print("4. Regardez les outils s'exécuter!")
            
        except Exception as e:
            print(f"❌ Erreur session: {e}")
    
    def run_continuous(self):
        """Mode continu pour démo"""
        print("\n🔄 MODE CONTINU")
        print("Entrée = nouvelle commande, 'q' = quitter")
        
        while True:
            try:
                choice = input("\n👉 Appuyez sur Entrée pour parler (q pour quitter): ")
                if choice.lower() == 'q':
                    break
                
                self.run_voice_session()
                
            except KeyboardInterrupt:
                print("\n👋 Au revoir!")
                break

if __name__ == "__main__":
    # Vérifier les dépendances
    try:
        import pyperclip
    except ImportError:
        print("❌ Installez pyperclip: pip install pyperclip")
        sys.exit(1)
    
    # Vérifier la clé API
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY non définie dans .env")
        sys.exit(1)
    
    bridge = VoiceBridgeFinal()
    
    print("\n🎛️ MODES DISPONIBLES:")
    print("1 - Session unique")
    print("2 - Mode continu")
    
    choice = input("👉 Choix: ")
    
    if choice == "1":
        bridge.run_voice_session()
    elif choice == "2":
        bridge.run_continuous()
    else:
        print("Test rapide...")
        bridge.run_voice_session()