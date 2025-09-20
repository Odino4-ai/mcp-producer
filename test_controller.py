#!/usr/bin/env python3
"""
Contrôleur de test simple sans connexion OpenAI
Permet de tester les fonctions de gestion de fichiers directement
"""
import asyncio
import os
from pathlib import Path

class TestController:
    def __init__(self):
        self.desktop_path = Path.home() / "Desktop"
        
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
    
    def show_test_menu(self):
        """Affiche le menu des commandes de test"""
        print("\n" + "="*50)
        print("🧪 CONTRÔLEUR DE TEST SIMPLE (HORS LIGNE)")
        print("="*50)
        print("1️⃣  - Créer un dossier 'test-dossier'")
        print("2️⃣  - Créer 3 dossiers (dossier-1, dossier-2, dossier-3)")
        print("3️⃣  - Créer un fichier 'test.txt'")
        print("4️⃣  - Créer plusieurs fichiers (.txt, .py, .md)")
        print("5️⃣  - Lister le contenu du bureau")
        print("6️⃣  - Créer une structure projet complète")
        print("7️⃣  - Nettoyer (supprimer les fichiers de test)")
        print("🎤 8 - Tester OpenAI et enregistrement vocal")
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
                await asyncio.sleep(0.2)
                
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
                await asyncio.sleep(0.1)
                
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
                await asyncio.sleep(0.1)
            
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
                await asyncio.sleep(0.1)
                
            print("✅ Structure de projet créée avec succès!")
            
        elif command == "7":
            # Test: nettoyer les fichiers de test
            print("🧹 Nettoyage des fichiers de test...")
            import shutil
            
            test_items = [
                "test-dossier", "dossier-1", "dossier-2", "dossier-3",
                "test.txt", "readme.txt", "script.py", "documentation.md", 
                "config.json", "mon-projet"
            ]
            
            cleaned = 0
            for item_name in test_items:
                item_path = self.desktop_path / item_name
                try:
                    if item_path.exists():
                        if item_path.is_dir():
                            shutil.rmtree(item_path)
                            print(f"🗑️ Dossier supprimé: {item_name}")
                        else:
                            item_path.unlink()
                            print(f"🗑️ Fichier supprimé: {item_name}")
                        cleaned += 1
                except Exception as e:
                    print(f"❌ Erreur suppression {item_name}: {e}")
            
            print(f"✅ Nettoyage terminé: {cleaned} éléments supprimés")
            
        elif command == "8":
            # Test: lancer le testeur OpenAI
            print("🎤 Lancement du testeur de connexion OpenAI...")
            print("📋 Ceci va lancer un programme séparé pour tester l'audio et OpenAI")
            
            import subprocess
            import sys
            
            try:
                # Lancer le testeur OpenAI dans un nouveau processus
                subprocess.run([sys.executable, "test_openai_connection.py"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ Erreur lors du lancement du testeur: {e}")
            except FileNotFoundError:
                print("❌ Fichier test_openai_connection.py non trouvé")
                print("💡 Lancez directement: python test_openai_connection.py")
        
        else:
            print("❌ Commande inconnue")
    
    async def run(self):
        """Fonction principale"""
        print("🧪 CONTRÔLEUR DE TEST SIMPLE")
        print("="*40)
        print(f"📁 Bureau: {self.desktop_path}")
        print("🔧 Mode test sans connexion OpenAI")
        
        try:
            while True:
                try:
                    self.show_test_menu()
                    user_input = input("\n👉 Votre choix: ").strip()
                    
                    if user_input.lower() == 'q':
                        break
                    elif user_input in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                        await self.execute_test_command(user_input)
                        input("\nAppuyez sur Entrée pour continuer...")
                    else:
                        print("❌ Choix invalide. Utilisez 1-8 ou 'q' (quitter)")
                        
                except EOFError:
                    print("\n👋 Au revoir!")
                    break
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")

if __name__ == "__main__":
    try:
        asyncio.run(TestController().run())
    except KeyboardInterrupt:
        print("\n👋 Programme arrêté")
