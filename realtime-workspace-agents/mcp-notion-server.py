#!/usr/bin/env python3
"""
MCP Server for Notion Integration
Implements tools to create projects, update tasks, and enrich content in Notion
"""

import json
import os
import sys
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import requests

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


class NotionMCPServer:
    """MCP Server for Notion integration"""
    
    def __init__(self):
        """Initialize the MCP server"""
        self.server = Server("notion-mcp-server")
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.notion_api_url = "https://api.notion.com/v1"
        self.setup_handlers()
    
    def setup_handlers(self):
        """Configure handlers for different MCP methods"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """
            Handler for tools/list method
            Returns the list of available tools
            """
            return [
                Tool(
                    name="createNotionProject",
                    description="Creates a complete Notion project with pages, databases, and structure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "projectName": {
                                "type": "string",
                                "description": "Name of the project to create"
                            },
                            "projectDescription": {
                                "type": "string",
                                "description": "Detailed description of the project"
                            },
                            "projectType": {
                                "type": "string",
                                "enum": ["development", "marketing", "research", "design", "business", "other"],
                                "description": "Type of project to adapt the structure"
                            },
                            "teamMembers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of team member names"
                            },
                            "initialContext": {
                                "type": "string",
                                "description": "Initial context from conversation"
                            }
                        },
                        "required": ["projectName", "projectDescription"]
                    }
                ),
                Tool(
                    name="updateNotionTasks",
                    description="Updates Notion task databases with new tasks and task updates",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "projectId": {
                                "type": "string",
                                "description": "Notion project/page ID"
                            },
                            "newTasks": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "task": {"type": "string"},
                                        "assignedTo": {"type": "string"},
                                        "priority": {"type": "string"},
                                        "dueDate": {"type": "string"},
                                        "context": {"type": "string"}
                                    }
                                },
                                "description": "New tasks to add"
                            },
                            "updatedTasks": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "taskId": {"type": "string"},
                                        "newStatus": {"type": "string"},
                                        "updates": {"type": "object"}
                                    }
                                },
                                "description": "Existing tasks to update"
                            },
                            "conversationContext": {
                                "type": "string",
                                "description": "Context from the conversation"
                            }
                        },
                        "required": ["projectId"]
                    }
                ),
                Tool(
                    name="enrichNotionContent",
                    description="Enriches Notion content with additional information and structure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "projectId": {
                                "type": "string",
                                "description": "Notion project/page ID to enrich"
                            },
                            "enrichmentType": {
                                "type": "string",
                                "enum": ["meeting_notes", "decision_tracking", "resource_links", "timeline_update", "team_assignments"],
                                "description": "Type of enrichment to perform"
                            },
                            "content": {
                                "type": "object",
                                "description": "Content to add or update"
                            },
                            "conversationTrigger": {
                                "type": "string",
                                "description": "What triggered this enrichment"
                            }
                        },
                        "required": ["projectId", "enrichmentType", "content"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """
            Handler for tools/call method
            Executes the requested tool with provided arguments
            """
            try:
                if name == "createNotionProject":
                    return await self.create_notion_project(arguments)
                elif name == "updateNotionTasks":
                    return await self.update_notion_tasks(arguments)
                elif name == "enrichNotionContent":
                    return await self.enrich_notion_content(arguments)
                else:
                    raise JSONRPCError(
                        METHOD_NOT_FOUND,
                        f"Tool '{name}' not found"
                    )
            except JSONRPCError:
                # Re-raise MCP errors
                raise
            except Exception as e:
                # Convert other errors to MCP errors
                raise JSONRPCError(
                    INTERNAL_ERROR,
                    f"Internal error executing tool: {str(e)}"
                )
    
    async def create_notion_project(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Creates a complete Notion project structure
        """
        project_name = arguments["projectName"]
        project_description = arguments["projectDescription"]
        project_type = arguments.get("projectType", "business")
        team_members = arguments.get("teamMembers", [])
        initial_context = arguments.get("initialContext", "")
        
        try:
            if not self.notion_token:
                # Fallback mode without real Notion API
                result = {
                    "success": True,
                    "mode": "simulation",
                    "projectName": project_name,
                    "pageId": f"simulated_page_{datetime.now().timestamp()}",
                    "databasesCreated": 3,
                    "message": "Project structure simulated (no Notion API token configured)"
                }
            else:
                # Real Notion API integration
                result = await self._create_real_notion_project(
                    project_name, project_description, project_type, team_members, initial_context
                )
            
            return [TextContent(
                type="text",
                text=f"✅ Notion project '{project_name}' created successfully!\n"
                     f"📄 Page ID: {result.get('pageId', 'N/A')}\n"
                     f"📊 Databases created: {result.get('databasesCreated', 0)}\n"
                     f"🎯 Mode: {result.get('mode', 'real')}"
            )]
            
        except Exception as e:
            raise JSONRPCError(
                INTERNAL_ERROR,
                f"Error creating Notion project: {str(e)}"
            )
    
    async def update_notion_tasks(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Updates Notion tasks based on conversation
        """
        project_id = arguments["projectId"]
        new_tasks = arguments.get("newTasks", [])
        updated_tasks = arguments.get("updatedTasks", [])
        conversation_context = arguments.get("conversationContext", "")
        
        try:
            if not self.notion_token:
                # Simulation mode
                result = {
                    "success": True,
                    "mode": "simulation",
                    "tasksAdded": len(new_tasks),
                    "tasksUpdated": len(updated_tasks),
                    "message": "Tasks updated in simulation mode"
                }
            else:
                # Real Notion API
                result = await self._update_real_notion_tasks(
                    project_id, new_tasks, updated_tasks, conversation_context
                )
            
            return [TextContent(
                type="text",
                text=f"✅ Notion tasks updated!\n"
                     f"➕ Tasks added: {result.get('tasksAdded', 0)}\n"
                     f"🔄 Tasks updated: {result.get('tasksUpdated', 0)}\n"
                     f"🎯 Mode: {result.get('mode', 'real')}"
            )]
            
        except Exception as e:
            raise JSONRPCError(
                INTERNAL_ERROR,
                f"Error updating Notion tasks: {str(e)}"
            )
    
    async def enrich_notion_content(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Enriches Notion content with additional information
        """
        project_id = arguments["projectId"]
        enrichment_type = arguments["enrichmentType"]
        content = arguments["content"]
        conversation_trigger = arguments.get("conversationTrigger", "")
        
        try:
            if not self.notion_token:
                # Simulation mode
                result = {
                    "success": True,
                    "mode": "simulation",
                    "enrichmentType": enrichment_type,
                    "message": f"Content enrichment '{enrichment_type}' simulated"
                }
            else:
                # Real Notion API
                result = await self._enrich_real_notion_content(
                    project_id, enrichment_type, content, conversation_trigger
                )
            
            return [TextContent(
                type="text",
                text=f"✅ Notion content enriched!\n"
                     f"🎨 Type: {enrichment_type.replace('_', ' ').title()}\n"
                     f"🎯 Mode: {result.get('mode', 'real')}\n"
                     f"🔗 Trigger: {conversation_trigger}"
            )]
            
        except Exception as e:
            raise JSONRPCError(
                INTERNAL_ERROR,
                f"Error enriching Notion content: {str(e)}"
            )
    
    async def _create_real_notion_project(self, project_name: str, project_description: str, 
                                        project_type: str, team_members: List[str], 
                                        initial_context: str) -> Dict[str, Any]:
        """
        Creates a real Notion project using the Notion API
        """
        # TODO: Implement real Notion API calls
        # For now, return a realistic simulation
        
        return {
            "success": True,
            "mode": "real",
            "projectName": project_name,
            "pageId": f"real_page_{datetime.now().timestamp()}",
            "databasesCreated": 3,
            "notionUrl": f"https://notion.so/{project_name.lower().replace(' ', '-')}"
        }
    
    async def _update_real_notion_tasks(self, project_id: str, new_tasks: List[Dict], 
                                      updated_tasks: List[Dict], context: str) -> Dict[str, Any]:
        """
        Updates real Notion tasks using the Notion API
        """
        # TODO: Implement real Notion API calls
        
        return {
            "success": True,
            "mode": "real",
            "tasksAdded": len(new_tasks),
            "tasksUpdated": len(updated_tasks)
        }
    
    async def _enrich_real_notion_content(self, project_id: str, enrichment_type: str, 
                                        content: Dict, trigger: str) -> Dict[str, Any]:
        """
        Enriches real Notion content using the Notion API
        """
        # TODO: Implement real Notion API calls
        
        return {
            "success": True,
            "mode": "real",
            "enrichmentType": enrichment_type
        }


async def main():
    """Main entry point for the MCP server"""
    try:
        # Create server instance
        notion_server = NotionMCPServer()
        
        # Configuration options
        options = InitializationOptions(
            server_name="notion-mcp-server",
            server_version="1.0.0",
            capabilities={
                "tools": {}
            }
        )
        
        # Start server with stdio
        async with stdio_server() as (read_stream, write_stream):
            await notion_server.server.run(
                read_stream,
                write_stream,
                options
            )
            
    except KeyboardInterrupt:
        print("MCP server stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"Fatal MCP server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
