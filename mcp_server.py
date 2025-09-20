#!/usr/bin/env python3
"""
Serveur MCP pour la gestion de fichiers par voix
Implémente des outils pour créer des dossiers, fichiers et lister le contenu
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    INTERNAL_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    JSONRPCError,
)


class VoiceFileControllerServer:
    """Serveur MCP pour le contrôle de fichiers par voix"""
    
    def __init__(self):
        """Initialise le serveur MCP"""
        self.server = Server("voice-file-controller")
        self.base_path = Path.home() / "Desktop"  # Chemin de base par défaut
        self.setup_handlers()
    
    def sanitize_path(self, path_string: str) -> str:
        """
        Nettoie et sécurise un chemin de fichier
        
        Args:
            path_string: Chemin à nettoyer
            
        Returns:
            str: Chemin nettoyé et sécurisé
        """
        # Remplace les caractères non autorisés par des underscores
        safe_path = "".join(c if c.isalnum() or c in "/._-" else "_" for c in path_string)
        # Supprime les doubles slashes
        safe_path = "/".join(part for part in safe_path.split("/") if part)
        return safe_path
    
    def resolve_path(self, relative_path: str = "") -> Path:
        """
        Résout un chemin relatif vers un chemin absolu sécurisé
        
        Args:
            relative_path: Chemin relatif depuis le base_path
            
        Returns:
            Path: Chemin absolu résolu
        """
        if not relative_path:
            return self.base_path
        
        # Nettoie le chemin
        clean_path = self.sanitize_path(relative_path)
        
        # Construit le chemin complet
        full_path = self.base_path / clean_path
        
        # Vérifie que le chemin résolu est bien dans le base_path (sécurité)
        try:
            full_path.resolve().relative_to(self.base_path.resolve())
        except ValueError:
            raise JSONRPCError(
                INVALID_PARAMS,
                "Le chemin spécifié sort du répertoire autorisé"
            )
        
        return full_path
        
    def setup_handlers(self):
        """Configure les handlers pour les différentes méthodes MCP"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """
            Handler pour la méthode tools/list
            Retourne la liste des outils disponibles
            """
            return [
                Tool(
                    name="create_folder",
                    description="Crée un nouveau dossier (peut inclure des sous-chemins comme 'projet/sous-dossier')",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "folder_path": {
                                "type": "string",
                                "description": "Chemin du dossier à créer (ex: 'mon-projet' ou 'projet/sous-dossier')"
                            }
                        },
                        "required": ["folder_path"]
                    }
                ),
                Tool(
                    name="create_file",
                    description="Crée un fichier vide dans un dossier spécifié",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Chemin du fichier à créer (ex: 'mon-fichier.txt' ou 'projet/fichier.txt')"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="list_contents",
                    description="Liste le contenu d'un dossier",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "folder_path": {
                                "type": "string",
                                "description": "Chemin du dossier à lister (vide pour lister le Desktop)"
                            }
                        },
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """
            Handler pour la méthode tools/call
            Exécute l'outil demandé avec les arguments fournis
            """
            try:
                if name == "create_folder":
                    return await self.create_folder(arguments)
                elif name == "create_file":
                    return await self.create_file(arguments)
                elif name == "list_contents":
                    return await self.list_contents(arguments)
                else:
                    raise JSONRPCError(
                        METHOD_NOT_FOUND,
                        f"Outil '{name}' non trouvé"
                    )
            except JSONRPCError:
                # Re-raise les erreurs MCP
                raise
            except Exception as e:
                # Convertit les autres erreurs en erreurs MCP
                raise JSONRPCError(
                    INTERNAL_ERROR,
                    f"Erreur interne lors de l'exécution de l'outil: {str(e)}"
                )
    
    async def create_folder(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Crée un nouveau dossier (peut inclure des sous-chemins)
        
        Args:
            arguments: Dictionnaire contenant les arguments de l'outil
                - folder_path (str): Chemin du dossier à créer
        
        Returns:
            List[TextContent]: Résultat de l'opération
            
        Raises:
            JSONRPCError: Si le chemin est invalide ou si la création échoue
        """
        # Validation des arguments
        if "folder_path" not in arguments:
            raise JSONRPCError(
                INVALID_PARAMS,
                "Le paramètre 'folder_path' est requis"
            )
        
        folder_path_str = arguments["folder_path"]
        if not isinstance(folder_path_str, str) or not folder_path_str.strip():
            raise JSONRPCError(
                INVALID_PARAMS,
                "Le chemin du dossier doit être une chaîne non vide"
            )
        
        try:
            # Résolution du chemin
            folder_path = self.resolve_path(folder_path_str.strip())
            
            # Vérification si le dossier existe déjà
            if folder_path.exists():
                return [TextContent(
                    type="text",
                    text=f"Le dossier '{folder_path_str}' existe déjà à l'emplacement: {folder_path}"
                )]
            
            # Création du dossier (avec parents si nécessaire)
            folder_path.mkdir(parents=True, exist_ok=True)
            
            return [TextContent(
                type="text",
                text=f"Dossier '{folder_path_str}' créé avec succès à l'emplacement: {folder_path}"
            )]
            
        except PermissionError:
            raise JSONRPCError(
                INTERNAL_ERROR,
                f"Permission refusée pour créer le dossier"
            )
        except OSError as e:
            raise JSONRPCError(
                INTERNAL_ERROR,
                f"Erreur lors de la création du dossier: {str(e)}"
            )
    
    async def create_file(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Crée un fichier vide dans un dossier spécifié
        
        Args:
            arguments: Dictionnaire contenant les arguments de l'outil
                - file_path (str): Chemin du fichier à créer
        
        Returns:
            List[TextContent]: Résultat de l'opération
            
        Raises:
            JSONRPCError: Si le chemin est invalide ou si la création échoue
        """
        # Validation des arguments
        if "file_path" not in arguments:
            raise JSONRPCError(
                INVALID_PARAMS,
                "Le paramètre 'file_path' est requis"
            )
        
        file_path_str = arguments["file_path"]
        if not isinstance(file_path_str, str) or not file_path_str.strip():
            raise JSONRPCError(
                INVALID_PARAMS,
                "Le chemin du fichier doit être une chaîne non vide"
            )
        
        try:
            # Résolution du chemin
            file_path = self.resolve_path(file_path_str.strip())
            
            # Vérification si le fichier existe déjà
            if file_path.exists():
                return [TextContent(
                    type="text",
                    text=f"Le fichier '{file_path_str}' existe déjà à l'emplacement: {file_path}"
                )]
            
            # Création du répertoire parent si nécessaire
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Création du fichier vide
            file_path.touch()
            
            return [TextContent(
                type="text",
                text=f"Fichier '{file_path_str}' créé avec succès à l'emplacement: {file_path}"
            )]
            
        except PermissionError:
            raise JSONRPCError(
                INTERNAL_ERROR,
                f"Permission refusée pour créer le fichier"
            )
        except OSError as e:
            raise JSONRPCError(
                INTERNAL_ERROR,
                f"Erreur lors de la création du fichier: {str(e)}"
            )
    
    async def list_contents(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Liste le contenu d'un dossier
        
        Args:
            arguments: Dictionnaire contenant les arguments de l'outil
                - folder_path (str, optionnel): Chemin du dossier à lister
        
        Returns:
            List[TextContent]: Liste du contenu du dossier
            
        Raises:
            JSONRPCError: Si le chemin est invalide ou si la lecture échoue
        """
        try:
            # Résolution du chemin (vide = Desktop par défaut)
            folder_path_str = arguments.get("folder_path", "").strip()
            folder_path = self.resolve_path(folder_path_str)
            
            # Vérification que le chemin existe et est un dossier
            if not folder_path.exists():
                return [TextContent(
                    type="text",
                    text=f"Le dossier '{folder_path_str or 'Desktop'}' n'existe pas"
                )]
            
            if not folder_path.is_dir():
                return [TextContent(
                    type="text",
                    text=f"Le chemin '{folder_path_str}' n'est pas un dossier"
                )]
            
            # Lecture du contenu du dossier
            try:
                items = list(folder_path.iterdir())
                items.sort(key=lambda x: (x.is_file(), x.name.lower()))
                
                if not items:
                    return [TextContent(
                        type="text",
                        text=f"Le dossier '{folder_path_str or 'Desktop'}' est vide"
                    )]
                
                # Formatage de la liste
                result_lines = [f"Contenu du dossier '{folder_path_str or 'Desktop'}':\n"]
                
                for item in items:
                    if item.is_dir():
                        result_lines.append(f"📁 {item.name}/")
                    else:
                        size = item.stat().st_size
                        size_str = f"{size} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                        result_lines.append(f"📄 {item.name} ({size_str})")
                
                return [TextContent(
                    type="text",
                    text="\n".join(result_lines)
                )]
                
            except PermissionError:
                raise JSONRPCError(
                    INTERNAL_ERROR,
                    f"Permission refusée pour lire le contenu du dossier"
                )
                
        except JSONRPCError:
            raise
        except Exception as e:
            raise JSONRPCError(
                INTERNAL_ERROR,
                f"Erreur lors de la lecture du dossier: {str(e)}"
            )


async def main():
    """Point d'entrée principal du serveur MCP"""
    try:
        # Création de l'instance du serveur
        voice_server = VoiceFileControllerServer()
        
        # Configuration des options d'initialisation
        options = InitializationOptions(
            server_name="voice-file-controller",
            server_version="1.0.0",
            capabilities={
                "tools": {}
            }
        )
        
        # Démarrage du serveur avec stdio
        async with stdio_server() as (read_stream, write_stream):
            await voice_server.server.run(
                read_stream,
                write_stream,
                options
            )
            
    except KeyboardInterrupt:
        print("Serveur MCP arrêté par l'utilisateur", file=sys.stderr)
    except Exception as e:
        print(f"Erreur fatale du serveur MCP: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
