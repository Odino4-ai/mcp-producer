#!/usr/bin/env python3
"""
Voice Bridge avec reconnaissance vocale native Mac
Solution sans OpenAI pour le hackathon - utilise Google Speech Recognition
"""
import speech_recognition as sr
import pyperclip
import sys
import time
from pathlib import Path

class VoiceBridgeNative:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.desktop_path = Path.home() / "Desktop"
        
        print("🎤 VOICE BRIDGE NATIF")
        print("="*40)
        print("✅ Sans OpenAI - Reconnaissance vocale Google")
        print("🎯 Parfait pour le hackathon!")
        print("="*40)
        
        # Calibrer le microphone
        print("🔧 Calibration du microphone...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("✅ Microphone calibré")
        
    def listen_and_transcribe(self, timeout=10):
        """Écouter et transcrire avec la reconnaissance native"""
        print("\n🎤 🔴 ÉCOUTE EN COURS...")
        print("💬 Parlez maintenant (vous avez 10 secondes)...")
        
        try:
            with self.microphone as source:
                # Écouter avec timeout
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=8)
            
            print("🔄 Transcription en cours...")
            
            # Essayer d'abord avec Google (gratuit)
            try:
                text = self.recognizer.recognize_google(audio, language='fr-FR')
                print(f"📝 ✅ TRANSCRIPTION RÉUSSIE: '{text}'")
                return text
            except sr.UnknownValueError:
                print("❌ Parole non comprise")
                return None
            except sr.RequestError as e:
                print(f"❌ Erreur service Google: {e}")
                # Fallback vers reconnaissance offline si disponible
                try:
                    text = self.recognizer.recognize_sphinx(audio, language='fr-FR')
                    print(f"📝 ✅ TRANSCRIPTION OFFLINE: '{text}'")
                    return text
                except:
                    print("❌ Reconnaissance offline non disponible")
                    return None
                    
        except sr.WaitTimeoutError:
            print("⏰ Timeout - Aucune parole détectée")
            return None
        except Exception as e:
            print(f"❌ Erreur écoute: {e}")
            return None
    
    def parse_voice_command(self, text):
        """Parser simple pour identifier les commandes"""
        text_lower = text.lower().strip()
        
        print(f"🔍 Analyse de: '{text_lower}'")
        
        # Créer dossier
        if "dossier" in text_lower and any(word in text_lower for word in ["crée", "créer", "fait", "faire"]):
            # Extraire le nom
            import re
            patterns = [
                r"dossier\s+([a-zA-Z0-9\s\-_]+)",
                r"cr[ée]+[r]?\s+(?:un\s+)?dossier\s+([a-zA-Z0-9\s\-_]+)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    name = match.group(1).strip()
                    name = re.sub(r'\s+sur.*', '', name)
                    name = re.sub(r'\s+', '-', name)
                    name = re.sub(r'[^a-zA-Z0-9\-_]', '', name)
                    
                    if name:
                        print(f"✅ Commande dossier: '{name}'")
                        return ("create_folder", name)
        
        # Créer fichier
        if "fichier" in text_lower and any(word in text_lower for word in ["crée", "créer", "fait", "faire"]):
            import re
            patterns = [
                r"fichier\s+([a-zA-Z0-9\s\-_.]+)",
                r"cr[ée]+[r]?\s+(?:un\s+)?fichier\s+([a-zA-Z0-9\s\-_.]+)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    name = match.group(1).strip()
                    name = re.sub(r'\s+sur.*', '', name)
                    name = re.sub(r'\s+', '_', name)
                    
                    if '.' not in name:
                        name += '.txt'
                    
                    if name:
                        print(f"✅ Commande fichier: '{name}'")
                        return ("create_file", name)
        
        # Lister
        if any(word in text_lower for word in ["liste", "montre", "affiche", "contient"]) and "bureau" in text_lower:
            print(f"✅ Commande liste")
            return ("list_contents", "")
        
        print(f"❌ Commande non reconnue")
        return None
    
    def execute_mcp_local(self, action, name):
        """Exécuter l'action MCP localement"""
        print(f"\n⚙️ EXÉCUTION MCP: {action}")
        
        if action == "create_folder":
            try:
                folder_path = self.desktop_path / name
                folder_path.mkdir(exist_ok=True)
                print(f"✅ DOSSIER CRÉÉ: {name}")
                return f"J'ai créé le dossier {name} sur votre bureau"
            except Exception as e:
                print(f"❌ Erreur: {e}")
                return f"Erreur lors de la création du dossier: {e}"
                
        elif action == "create_file":
            try:
                file_path = self.desktop_path / name
                file_path.touch()
                print(f"✅ FICHIER CRÉÉ: {name}")
                return f"J'ai créé le fichier {name} sur votre bureau"
            except Exception as e:
                print(f"❌ Erreur: {e}")
                return f"Erreur lors de la création du fichier: {e}"
                
        elif action == "list_contents":
            try:
                items = list(self.desktop_path.iterdir())
                folders = [item.name for item in items if item.is_dir()]
                files = [item.name for item in items if item.is_file() and not item.name.startswith('.')]
                
                print(f"✅ CONTENU LISTÉ: {len(folders)} dossiers, {len(files)} fichiers")
                
                result = f"Sur votre bureau, il y a {len(folders)} dossiers"
                if folders:
                    result += f": {', '.join(folders[:3])}"
                    if len(folders) > 3:
                        result += f" et {len(folders)-3} autres"
                
                result += f" et {len(files)} fichiers"
                if files:
                    result += f": {', '.join(files[:3])}"
                    if len(files) > 3:
                        result += f" et {len(files)-3} autres"
                
                return result
            except Exception as e:
                print(f"❌ Erreur: {e}")
                return f"Erreur lors du listage: {e}"
        
        return "Action inconnue"
    
    def create_claude_prompt(self, voice_command, action_result):
        """Créer un prompt pour Claude Desktop avec le résultat"""
        prompt = f"""🎤 Commande vocale reçue: "{voice_command}"

✅ Action exécutée automatiquement: {action_result}

Utilise maintenant les outils MCP voice-file-controller pour confirmer ou compléter cette action si nécessaire.

Commandes disponibles:
- create_folder: créer des dossiers
- create_file: créer des fichiers
- list_contents: lister le contenu

La commande a déjà été exécutée localement, mais tu peux utiliser les outils MCP pour vérifier ou faire des actions complémentaires."""

        return prompt
    
    def copy_to_clipboard(self, text):
        """Copier dans le presse-papier"""
        try:
            pyperclip.copy(text)
            print("✅ Prompt copié dans le presse-papier!")
            print("👉 Collez dans Claude Desktop (Cmd+V)")
            return True
        except Exception as e:
            print(f"❌ Erreur copie: {e}")
            return False
    
    def run_voice_session(self):
        """Session vocale complète"""
        print("\n" + "="*60)
        print("🎤 SESSION VOCALE NATIVE")
        print("="*60)
        print("💬 Exemples de commandes:")
        print("   • 'Crée un dossier projet-hackathon'")
        print("   • 'Crée un fichier readme'")
        print("   • 'Montre-moi le bureau'")
        print("="*60)
        
        try:
            # 1. Écouter et transcrire
            text = self.listen_and_transcribe()
            
            if not text:
                print("❌ Aucune transcription obtenue")
                return
            
            # 2. Parser la commande
            command = self.parse_voice_command(text)
            
            if not command:
                print("❌ Commande non reconnue")
                # Créer quand même un prompt pour Claude
                prompt = f"""Commande vocale non reconnue: "{text}"

Peux-tu analyser cette commande et utiliser les outils MCP appropriés:
- create_folder: créer des dossiers
- create_file: créer des fichiers
- list_contents: lister le contenu"""
                
                if self.copy_to_clipboard(prompt):
                    print("📋 Prompt envoyé à Claude pour analyse")
                return
            
            # 3. Exécuter l'action MCP localement
            action, name = command
            result = self.execute_mcp_local(action, name)
            
            # 4. Créer le prompt pour Claude
            prompt = self.create_claude_prompt(text, result)
            
            # 5. Copier dans le presse-papier
            if self.copy_to_clipboard(prompt):
                print("\n" + "="*60)
                print("PROMPT GÉNÉRÉ POUR CLAUDE:")
                print("="*60)
                print(prompt)
                print("="*60)
                print("\n🎯 Dans Claude Desktop:")
                print("1. Ouvrez une conversation")
                print("2. Collez avec Cmd+V")
                print("3. Appuyez sur Entrée")
                print("4. Claude utilisera les outils MCP!")
            
        except Exception as e:
            print(f"❌ Erreur session: {e}")
    
    def run_continuous_demo(self):
        """Mode démo continu pour le hackathon"""
        print("\n🔄 MODE DÉMO HACKATHON")
        print("="*40)
        print("Commandes vocales en boucle")
        print("Entrée = nouvelle commande, 'q' = quitter")
        
        session_count = 0
        
        while True:
            try:
                session_count += 1
                print(f"\n🎯 SESSION #{session_count}")
                
                choice = input("👉 Appuyez sur Entrée pour parler (q pour quitter): ").strip()
                if choice.lower() == 'q':
                    break
                
                self.run_voice_session()
                
                print("\n⏳ Prêt pour la prochaine commande...")
                
            except KeyboardInterrupt:
                print("\n👋 Démo terminée!")
                break
    
    def test_microphone_simple(self):
        """Test simple du microphone"""
        print("\n🎤 Test microphone (parlez pendant 3 secondes)...")
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("🔴 Parlez maintenant...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
            
            print("✅ Audio capturé!")
            
            # Test transcription
            try:
                text = self.recognizer.recognize_google(audio, language='fr-FR')
                print(f"📝 Transcription: '{text}'")
                return True
            except Exception as e:
                print(f"❌ Transcription échouée: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur microphone: {e}")
            return False
    
    def show_menu(self):
        """Menu principal"""
        print("\n" + "="*50)
        print("🎤 VOICE BRIDGE NATIF - HACKATHON")
        print("="*50)
        print("🧪 TESTS:")
        print("  1 - Test microphone simple")
        print("  2 - Session vocale unique")
        print("  3 - Mode démo continu (hackathon)")
        print()
        print("📋 COMMANDES SUPPORTÉES:")
        print("  • 'Crée un dossier [nom]'")
        print("  • 'Crée un fichier [nom]'")
        print("  • 'Montre-moi le bureau'")
        print("  • 'Liste le bureau'")
        print()
        print("❌ q - Quitter")
        print("="*50)
    
    def run(self):
        """Fonction principale"""
        print("🎤 VOICE BRIDGE NATIF")
        print("🎯 Reconnaissance vocale sans OpenAI")
        
        try:
            while True:
                try:
                    self.show_menu()
                    choice = input("\n👉 Votre choix: ").strip()
                    
                    if choice.lower() == 'q':
                        break
                        
                    elif choice == '1':
                        self.test_microphone_simple()
                        input("\nAppuyez sur Entrée pour continuer...")
                        
                    elif choice == '2':
                        self.run_voice_session()
                        input("\nAppuyez sur Entrée pour continuer...")
                        
                    elif choice == '3':
                        self.run_continuous_demo()
                        
                    else:
                        print("❌ Choix invalide. Utilisez 1-3 ou 'q'")
                        
                except EOFError:
                    print("\n👋 Au revoir!")
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")

if __name__ == "__main__":
    # Vérifier les dépendances
    try:
        import speech_recognition as sr
        import pyperclip
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("💡 Installez avec: pip install SpeechRecognition pyperclip")
        sys.exit(1)
    
    try:
        bridge = VoiceBridgeNative()
        bridge.run()
    except KeyboardInterrupt:
        print("\n👋 Programme arrêté")
