#!/usr/bin/env python3
"""
Testeur MCP Manuel
Permet de tester les fonctions MCP de gestion de fichiers manuellement
"""
import asyncio
import os
from pathlib import Path
import shutil

class MCPManualTester:
    def __init__(self):
        self.desktop_path = Path.home() / "Desktop"
        
    # ========== FONCTIONS MCP ==========
    def create_folder(self, folder_path):
        """Créer un dossier (fonction MCP)"""
        try:
            full_path = self.desktop_path / folder_path
            full_path.mkdir(parents=True, exist_ok=True)
            return f"✅ Dossier créé: {full_path}"
        except Exception as e:
            return f"❌ Erreur création dossier: {e}"
    
    def create_file(self, file_path, content=""):
        """Créer un fichier (fonction MCP)"""
        try:
            full_path = self.desktop_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if content:
                full_path.write_text(content, encoding='utf-8')
            else:
                full_path.touch()
                
            return f"✅ Fichier créé: {full_path}"
        except Exception as e:
            return f"❌ Erreur création fichier: {e}"
    
    def list_contents(self, folder_path=""):
        """Lister le contenu d'un dossier (fonction MCP)"""
        try:
            if folder_path:
                target_path = self.desktop_path / folder_path
            else:
                target_path = self.desktop_path
            
            if not target_path.exists():
                return f"❌ Dossier introuvable: {target_path}"
            
            if not target_path.is_dir():
                return f"❌ Ce n'est pas un dossier: {target_path}"
            
            items = list(target_path.iterdir())
            if not items:
                return f"📁 Dossier vide: {target_path.name}"
            
            result = f"📁 Contenu de {target_path.name}:\n"
            for item in sorted(items):
                if item.is_dir():
                    result += f"  📁 {item.name}/\n"
                else:
                    size = item.stat().st_size
                    size_str = f"{size} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                    result += f"  📄 {item.name} ({size_str})\n"
            return result
        except Exception as e:
            return f"❌ Erreur lecture dossier: {e}"
    
    def delete_item(self, item_path):
        """Supprimer un fichier ou dossier"""
        try:
            full_path = self.desktop_path / item_path
            if not full_path.exists():
                return f"❌ Élément introuvable: {item_path}"
            
            if full_path.is_dir():
                shutil.rmtree(full_path)
                return f"✅ Dossier supprimé: {item_path}"
            else:
                full_path.unlink()
                return f"✅ Fichier supprimé: {item_path}"
        except Exception as e:
            return f"❌ Erreur suppression: {e}"
    
    # ========== SCENARIOS DE TEST ==========
    def test_create_project_structure(self):
        """Créer une structure de projet complète"""
        print("\n🏗️ Création d'une structure de projet...")
        
        # Créer les dossiers
        folders = [
            "MonProjet",
            "MonProjet/src",
            "MonProjet/docs", 
            "MonProjet/tests",
            "MonProjet/assets",
            "MonProjet/config"
        ]
        
        for folder in folders:
            result = self.create_folder(folder)
            print(f"  {result}")
        
        # Créer les fichiers
        files = [
            ("MonProjet/README.md", "# Mon Projet\n\nDescription du projet..."),
            ("MonProjet/requirements.txt", "# Dépendances Python\nnumpy>=1.21.0\npandas>=1.3.0"),
            ("MonProjet/.gitignore", "__pycache__/\n*.pyc\n.env\nnode_modules/"),
            ("MonProjet/src/main.py", "#!/usr/bin/env python3\n\ndef main():\n    print('Hello World!')\n\nif __name__ == '__main__':\n    main()"),
            ("MonProjet/src/utils.py", "# Fonctions utilitaires\n\ndef helper_function():\n    pass"),
            ("MonProjet/tests/test_main.py", "import unittest\n\nclass TestMain(unittest.TestCase):\n    def test_example(self):\n        self.assertTrue(True)"),
            ("MonProjet/docs/guide.md", "# Guide d'utilisation\n\n## Installation\n\n## Usage"),
            ("MonProjet/config/settings.json", '{\n  "app_name": "MonProjet",\n  "version": "1.0.0"\n}')
        ]
        
        for file_path, content in files:
            result = self.create_file(file_path, content)
            print(f"  {result}")
        
        print("✅ Structure de projet créée!")
        return self.list_contents("MonProjet")
    
    def test_create_multiple_folders(self):
        """Créer plusieurs dossiers d'un coup"""
        print("\n📁 Création de plusieurs dossiers...")
        
        folders = ["Dossier1", "Dossier2", "Dossier3", "TestFolder", "Documents/Sous-Dossier"]
        
        for folder in folders:
            result = self.create_folder(folder)
            print(f"  {result}")
        
        return "✅ Dossiers créés!"
    
    def test_create_multiple_files(self):
        """Créer plusieurs fichiers d'un coup"""
        print("\n📄 Création de plusieurs fichiers...")
        
        files = [
            ("test1.txt", "Contenu du fichier 1"),
            ("test2.py", "# Script Python\nprint('Hello')"),
            ("data.json", '{"name": "test", "value": 123}'),
            ("notes.md", "# Mes Notes\n\n- Point 1\n- Point 2"),
            ("config.ini", "[settings]\nname=app\nversion=1.0")
        ]
        
        for file_path, content in files:
            result = self.create_file(file_path, content)
            print(f"  {result}")
        
        return "✅ Fichiers créés!"
    
    def cleanup_test_files(self):
        """Nettoyer les fichiers de test"""
        print("\n🧹 Nettoyage des fichiers de test...")
        
        test_items = [
            "MonProjet", "Dossier1", "Dossier2", "Dossier3", "TestFolder", "Documents",
            "test1.txt", "test2.py", "data.json", "notes.md", "config.ini",
            "test-dossier", "dossier-1", "dossier-2", "dossier-3",
            "test.txt", "readme.txt", "script.py", "documentation.md", "config.json"
        ]
        
        cleaned = 0
        for item in test_items:
            try:
                full_path = self.desktop_path / item
                if full_path.exists():
                    if full_path.is_dir():
                        shutil.rmtree(full_path)
                        print(f"  🗑️ Dossier supprimé: {item}")
                    else:
                        full_path.unlink()
                        print(f"  🗑️ Fichier supprimé: {item}")
                    cleaned += 1
            except Exception as e:
                print(f"  ❌ Erreur suppression {item}: {e}")
        
        return f"✅ Nettoyage terminé: {cleaned} éléments supprimés"
    
    # ========== INTERFACE UTILISATEUR ==========
    def show_main_menu(self):
        """Menu principal"""
        print("\n" + "="*60)
        print("🧪 TESTEUR MCP MANUEL")
        print("="*60)
        print("📁 GESTION DE DOSSIERS:")
        print("  1 - Créer un dossier")
        print("  2 - Créer plusieurs dossiers")
        print("  3 - Créer structure de projet complète")
        print()
        print("📄 GESTION DE FICHIERS:")
        print("  4 - Créer un fichier")
        print("  5 - Créer plusieurs fichiers")
        print()
        print("📋 CONSULTATION:")
        print("  6 - Lister le contenu du bureau")
        print("  7 - Lister le contenu d'un dossier")
        print()
        print("🗑️ NETTOYAGE:")
        print("  8 - Supprimer un élément")
        print("  9 - Nettoyer tous les fichiers de test")
        print()
        print("❌ q - Quitter")
        print("="*60)
    
    async def interactive_mode(self):
        """Mode interactif"""
        print("🧪 TESTEUR MCP MANUEL")
        print("="*30)
        print(f"📁 Bureau: {self.desktop_path}")
        print("🎯 Testez les fonctions MCP manuellement")
        
        try:
            while True:
                try:
                    self.show_main_menu()
                    choice = input("\n👉 Votre choix: ").strip()
                    
                    if choice.lower() == 'q':
                        break
                    elif choice == '1':
                        folder_name = input("📁 Nom du dossier à créer: ").strip()
                        if folder_name:
                            result = self.create_folder(folder_name)
                            print(result)
                        else:
                            print("❌ Nom de dossier requis")
                            
                    elif choice == '2':
                        result = self.test_create_multiple_folders()
                        print(result)
                        
                    elif choice == '3':
                        result = self.test_create_project_structure()
                        print(result)
                        
                    elif choice == '4':
                        file_name = input("📄 Nom du fichier à créer: ").strip()
                        if file_name:
                            content = input("💬 Contenu (optionnel): ").strip()
                            result = self.create_file(file_name, content)
                            print(result)
                        else:
                            print("❌ Nom de fichier requis")
                            
                    elif choice == '5':
                        result = self.test_create_multiple_files()
                        print(result)
                        
                    elif choice == '6':
                        result = self.list_contents()
                        print(result)
                        
                    elif choice == '7':
                        folder_name = input("📁 Nom du dossier à lister: ").strip()
                        result = self.list_contents(folder_name)
                        print(result)
                        
                    elif choice == '8':
                        item_name = input("🗑️ Nom de l'élément à supprimer: ").strip()
                        if item_name:
                            confirm = input(f"⚠️ Confirmer la suppression de '{item_name}' ? (y/N): ").strip().lower()
                            if confirm == 'y':
                                result = self.delete_item(item_name)
                                print(result)
                            else:
                                print("❌ Suppression annulée")
                        else:
                            print("❌ Nom d'élément requis")
                            
                    elif choice == '9':
                        confirm = input("⚠️ Supprimer TOUS les fichiers de test ? (y/N): ").strip().lower()
                        if confirm == 'y':
                            result = self.cleanup_test_files()
                            print(result)
                        else:
                            print("❌ Nettoyage annulé")
                            
                    else:
                        print("❌ Choix invalide. Utilisez 1-9 ou 'q'")
                    
                    if choice != 'q':
                        input("\nAppuyez sur Entrée pour continuer...")
                        
                except EOFError:
                    print("\n👋 Au revoir!")
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")

if __name__ == "__main__":
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print('\n👋 Arrêt du programme...')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        tester = MCPManualTester()
        asyncio.run(tester.interactive_mode())
    except KeyboardInterrupt:
        print("\n👋 Programme arrêté")
