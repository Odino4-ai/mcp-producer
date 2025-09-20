#!/usr/bin/env python3
"""
Contrôleur Principal - Voice File Controller
Menu principal pour accéder à tous les outils de test et au contrôleur vocal
"""
import asyncio
import subprocess
import sys
from pathlib import Path

class MainController:
    def __init__(self):
        self.base_path = Path(__file__).parent
        
    def show_main_menu(self):
        """Menu principal unifié"""
        print("\n" + "="*70)
        print("🎤 VOICE FILE CONTROLLER - MENU PRINCIPAL")
        print("="*70)
        print("🧪 TESTS MANUELS:")
        print("  1 - Testeur MCP Manuel (créer dossiers/fichiers à la main)")
        print("  2 - Test audio simple (sans OpenAI)")
        print("  3 - Test connexion OpenAI (avec debug)")
        print()
        print("🎤 CONTRÔLEUR VOCAL:")
        print("  4 - Contrôleur Vocal → MCP (RECOMMANDÉ)")
        print("  5 - Contrôleur Vocal Final (OpenAI Realtime API)")
        print("  6 - Contrôleur avec corrections (version debug)")
        print()
        print("🔧 OUTILS DE DÉVELOPPEMENT:")
        print("  7 - Serveur MCP (pour Claude Desktop)")
        print("  8 - Tests unitaires des fonctions")
        print("  9 - Debugger de transcription")
        print()
        print("📚 AIDE:")
        print("  h - Afficher l'aide et les descriptions")
        print("  q - Quitter")
        print("="*70)
    
    def show_help(self):
        """Afficher l'aide détaillée"""
        print("\n" + "="*70)
        print("📚 AIDE - VOICE FILE CONTROLLER")
        print("="*70)
        
        print("\n🧪 TESTS MANUELS:")
        print("  1 - Testeur MCP Manuel")
        print("      → Testez les fonctions de création de dossiers/fichiers")
        print("      → Interface interactive pour tester toutes les fonctions MCP")
        print("      → Parfait pour vérifier que les fonctions de base marchent")
        
        print("\n  2 - Test Audio Simple") 
        print("      → Teste uniquement la capture audio (sans OpenAI)")
        print("      → Feedback visuel en temps réel")
        print("      → Diagnostic des problèmes de microphone")
        
        print("\n  3 - Test Connexion OpenAI")
        print("      → Teste la connexion WebSocket avec OpenAI")
        print("      → Debug des problèmes de réseau")
        print("      → Test de transcription audio")
        
        print("\n🎤 CONTRÔLEUR VOCAL:")
        print("  4 - Contrôleur Vocal Final")
        print("      → Version finale basée sur la documentation OpenAI")
        print("      → Implémentation correcte des événements WebSocket")
        print("      → Fonctions MCP intégrées (créer dossiers/fichiers)")
        
        print("\n  5 - Contrôleur avec Corrections")
        print("      → Version avec corrections de bugs")
        print("      → Plus de debug et feedback visuel")
        print("      → Utile pour diagnostiquer les problèmes")
        
        print("\n🔧 OUTILS DE DÉVELOPPEMENT:")
        print("  6 - Serveur MCP")
        print("      → Lance le serveur MCP pour Claude Desktop")
        print("      → Permet à Claude d'utiliser les fonctions de fichiers")
        
        print("\n  7 - Tests Unitaires")
        print("      → Tests automatisés des fonctions MCP")
        print("      → Vérification que tout fonctionne correctement")
        
        print("\n💡 RECOMMANDATIONS D'USAGE:")
        print("  • Commencez par le test 1 pour vérifier les fonctions de base")
        print("  • Utilisez le test 2 si vous avez des problèmes de microphone")
        print("  • Le test 3 pour diagnostiquer les problèmes OpenAI")
        print("  • Le contrôleur 4 est la version finale recommandée")
        print("  • Le contrôleur 5 pour déboguer les problèmes audio")
        
        print("="*70)
    
    def run_script(self, script_name, description):
        """Exécuter un script Python"""
        script_path = self.base_path / script_name
        
        if not script_path.exists():
            print(f"❌ Script non trouvé: {script_name}")
            return False
        
        print(f"\n🚀 Lancement: {description}")
        print(f"📁 Script: {script_name}")
        print("-" * 50)
        
        try:
            # Lancer le script dans le même environnement
            result = subprocess.run([
                sys.executable, str(script_path)
            ], cwd=str(self.base_path))
            
            if result.returncode == 0:
                print(f"\n✅ {description} terminé avec succès")
            else:
                print(f"\n⚠️ {description} terminé avec code: {result.returncode}")
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n⏹️ {description} interrompu par l'utilisateur")
            return True
        except Exception as e:
            print(f"\n❌ Erreur lors du lancement: {e}")
            return False
    
    def run_tests(self):
        """Exécuter les tests unitaires"""
        print("\n🧪 Exécution des tests unitaires...")
        
        # Tests basiques des fonctions MCP
        try:
            from pathlib import Path
            import tempfile
            import shutil
            
            print("  ✓ Test d'import des modules")
            
            # Test création dossier temporaire
            with tempfile.TemporaryDirectory() as temp_dir:
                test_folder = Path(temp_dir) / "test_folder"
                test_folder.mkdir()
                assert test_folder.exists()
                print("  ✓ Test création dossier")
                
                # Test création fichier
                test_file = test_folder / "test.txt"
                test_file.touch()
                assert test_file.exists()
                print("  ✓ Test création fichier")
                
                # Test listage
                items = list(test_folder.iterdir())
                assert len(items) == 1
                print("  ✓ Test listage contenu")
            
            print("✅ Tous les tests sont passés!")
            
        except Exception as e:
            print(f"❌ Erreur dans les tests: {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def check_environment(self):
        """Vérifier l'environnement"""
        print("\n🔍 Vérification de l'environnement...")
        
        # Vérifier les fichiers
        scripts = {
            "mcp_manual_tester.py": "Testeur MCP Manuel",
            "test_simple_audio.py": "Test Audio Simple", 
            "test_openai_connection.py": "Test Connexion OpenAI",
            "voice_controller_final.py": "Contrôleur Vocal Final",
            "voice_controller_fixed.py": "Contrôleur avec Corrections",
            "mcp_server.py": "Serveur MCP"
        }
        
        print("\n📁 Scripts disponibles:")
        all_good = True
        for script, desc in scripts.items():
            script_path = self.base_path / script
            if script_path.exists():
                print(f"  ✅ {script} - {desc}")
            else:
                print(f"  ❌ {script} - MANQUANT")
                all_good = False
        
        # Vérifier les dépendances
        print("\n📦 Dépendances Python:")
        deps = ["sounddevice", "numpy", "websockets", "python-dotenv"]
        for dep in deps:
            try:
                __import__(dep.replace("-", "_"))
                print(f"  ✅ {dep}")
            except ImportError:
                print(f"  ❌ {dep} - NON INSTALLÉ")
                all_good = False
        
        # Vérifier .env
        env_file = self.base_path / ".env"
        if env_file.exists():
            print(f"  ✅ Fichier .env trouvé")
        else:
            print(f"  ⚠️ Fichier .env manquant (requis pour OpenAI)")
        
        if all_good:
            print("\n✅ Environnement OK!")
        else:
            print("\n⚠️ Certains éléments manquent")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    async def run(self):
        """Boucle principale"""
        print("🎤 VOICE FILE CONTROLLER")
        print("="*30)
        print("🎯 Menu principal pour tous les outils")
        
        try:
            while True:
                try:
                    self.show_main_menu()
                    choice = input("\n👉 Votre choix: ").strip().lower()
                    
                    if choice == 'q':
                        break
                        
                    elif choice == '1':
                        self.run_script("mcp_manual_tester.py", "Testeur MCP Manuel")
                        
                    elif choice == '2':
                        self.run_script("test_simple_audio.py", "Test Audio Simple")
                        
                    elif choice == '3':
                        self.run_script("test_openai_connection.py", "Test Connexion OpenAI")
                        
                    elif choice == '4':
                        self.run_script("voice_to_mcp_controller.py", "Contrôleur Vocal → MCP")
                        
                    elif choice == '5':
                        self.run_script("voice_controller_final.py", "Contrôleur Vocal Final")
                        
                    elif choice == '6':
                        self.run_script("voice_controller_fixed.py", "Contrôleur avec Corrections")
                        
                    elif choice == '7':
                        self.run_script("mcp_server.py", "Serveur MCP")
                        
                    elif choice == '8':
                        self.run_tests()
                        
                    elif choice == '9':
                        self.run_script("transcription_debugger.py", "Debugger de Transcription")
                        
                    elif choice == 'h':
                        self.show_help()
                        input("\nAppuyez sur Entrée pour continuer...")
                        
                    elif choice == 'env':
                        self.check_environment()
                        
                    else:
                        print("❌ Choix invalide. Utilisez 1-7, h, ou q")
                        
                except EOFError:
                    print("\n👋 Au revoir!")
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")

if __name__ == "__main__":
    import signal
    
    def signal_handler(sig, frame):
        print('\n👋 Arrêt du programme...')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        controller = MainController()
        asyncio.run(controller.run())
    except KeyboardInterrupt:
        print("\n👋 Programme arrêté")
