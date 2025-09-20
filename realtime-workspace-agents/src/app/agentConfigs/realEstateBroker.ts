import { RealtimeAgent, tool } from '@openai/agents/realtime';

// Agent Unique : NotionExpert - Expert Notion silencieux qui écoute et met à jour automatiquement
export const notionExpertAgent = new RealtimeAgent({
  name: 'notionExpert',
  voice: 'sage',
  handoffDescription:
    "Silent Notion expert that listens to conversations and automatically updates Notion with complete projects, folders and to-do lists.",

  instructions:
    `You are a SILENT and PROACTIVE NOTION EXPERT.

    🎯 ABSOLUTE RULES:
    - You NEVER write responses or messages to the user
    - You listen to EVERYTHING in silence
    - You act IMMEDIATELY when information is mentioned
    - You create COMPLETE and ANTICIPATORY projects

    🏗️ PROJECT CREATION:
    As soon as a new project is mentioned (e.g., "car project"), you IMMEDIATELY create:
    - Main project page with complete description
    - Complete and logical folder structure
    - Databases for tasks, team, resources
    - Initial to-do list with anticipated tasks
    - Provisional planning
    - Sections for meeting notes

    📋 AUTOMATIC TO-DO LISTS:
    - Create and update to-do lists in real time
    - Automatically add mentioned tasks
    - Assign to the right people
    - Define priorities and deadlines
    - Organize by project and person

    🔄 CONTINUOUS UPDATES:
    - Update Notion in real time during conversation
    - Adapt structure based on new information
    - Automatically enrich content
    - Anticipate future project needs

    ⚡ REACTIVITY:
    - Act from the first mention of an element
    - Create complete structures, not just drafts
    - Think about details the team hasn't mentioned yet
    - Be proactive in organization

    🤐 TOTAL SILENCE:
    - No vocal or textual responses
    - Work in the background
    - Let the conversation flow naturally`,

  tools: [
    tool({
      name: 'createCompleteNotionProject',
      description: 'Immediately creates a complete Notion project with all necessary structure as soon as a project is mentioned.',
      parameters: {
        type: 'object',
        properties: {
          projectName: {
            type: 'string',
            description: 'Project name (e.g., "Car Project")',
          },
          projectDescription: {
            type: 'string',
            description: 'Detailed project description',
          },
          projectType: {
            type: 'string',
            enum: ['development', 'marketing', 'research', 'design', 'business', 'other'],
            description: 'Project type to adapt the structure',
          },
          teamMembers: {
            type: 'array',
            items: { type: 'string' },
            description: 'Team members mentioned',
          },
          initialContext: {
            type: 'string',
            description: 'Initial conversation context',
          },
        },
        required: ['projectName', 'projectDescription'],
        additionalProperties: false,
      },
      execute: async (input: any) => {
        const { projectName, projectDescription, projectType, teamMembers, initialContext } = input;
        
        try {
          // Call actual Notion MCP server to create project
          const mcpResponse = await fetch('/api/mcp/notion', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              tool: 'createNotionProject',
              arguments: {
                projectName,
                projectDescription,
                projectType: projectType || 'business',
                teamMembers: teamMembers || [],
                initialContext: initialContext || ''
              }
            })
          });

          if (!mcpResponse.ok) {
            throw new Error(`MCP request failed: ${mcpResponse.status}`);
          }

          const mcpResult = await mcpResponse.json();
          
          // 🔍 DEBUG: Log to trace creation
          console.log('📝 NotionExpert - Real Project Created:', {
            projectName: projectName,
            notionPageId: mcpResult.pageId,
            databasesCreated: mcpResult.databasesCreated || 0,
            success: mcpResult.success
          });

          // 📡 Emit event for visualizer
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('agentActivity', {
              detail: {
                agentId: 'notionExpert',
                action: `Real Notion project "${projectName}" created successfully`,
                status: 'completed',
                data: mcpResult
              }
            }));
          }
          
          return mcpResult;
          
        } catch (error) {
          console.error('❌ Error creating Notion project:', error);
          
          // Fallback to mock data if MCP server is not available
          const fallbackStructure = {
            error: 'MCP server not available',
            projectName,
            projectDescription,
            fallback: true,
            message: 'Project structure created locally (MCP server connection failed)'
          };

          // 📡 Emit error event
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('agentActivity', {
              detail: {
                agentId: 'notionExpert',
                action: `Failed to create Notion project "${projectName}" - using fallback`,
                status: 'error',
                data: { error: error.message }
              }
            }));
          }
          
          return fallbackStructure;
        }
      },
    }),

    tool({
      name: 'updateNotionTodoList',
      description: 'Automatically updates Notion to-do lists in real time during conversation.',
      parameters: {
        type: 'object',
        properties: {
          projectId: {
            type: 'string',
            description: 'Notion project ID',
          },
          newTasks: {
            type: 'array',
            items: {
        type: 'object',
        properties: {
                task: { type: 'string' },
                assignedTo: { type: 'string' },
                priority: { type: 'string', enum: ['Low', 'Medium', 'High', 'Urgent'] },
                dueDate: { type: 'string' },
                context: { type: 'string' }
              }
            },
            description: 'New tasks to add',
          },
          updatedTasks: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                taskId: { type: 'string' },
                newStatus: { type: 'string' },
                updates: { type: 'object' }
              }
            },
            description: 'Tasks to update',
          },
          conversationContext: {
            type: 'string',
            description: 'Current conversation context',
          },
        },
        required: ['projectId'],
        additionalProperties: false,
      },
      execute: async (input: any) => {
        const { projectId, newTasks, updatedTasks, conversationContext } = input;
        
        try {
          // Call actual Notion MCP server to update tasks
          const mcpResponse = await fetch('/api/mcp/notion', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              tool: 'updateNotionTasks',
              arguments: {
                projectId,
                newTasks: newTasks || [],
                updatedTasks: updatedTasks || [],
                conversationContext: conversationContext || ''
              }
            })
          });

          if (!mcpResponse.ok) {
            throw new Error(`MCP request failed: ${mcpResponse.status}`);
          }

          const mcpResult = await mcpResponse.json();
          
          // 🔍 DEBUG: Log to trace update
          console.log('📋 NotionExpert - Real Tasks Updated:', {
            projectId: projectId,
            tasksAdded: mcpResult.tasksAdded || 0,
            tasksUpdated: mcpResult.tasksUpdated || 0,
            success: mcpResult.success
          });

          // 📡 Emit event for visualizer
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('agentActivity', {
              detail: {
                agentId: 'notionExpert',
                action: `Real Notion tasks updated: +${mcpResult.tasksAdded || 0} tasks`,
                status: 'completed',
                data: mcpResult
              }
            }));
          }
          
          return mcpResult;
          
        } catch (error) {
          console.error('❌ Error updating Notion tasks:', error);
          
          // Fallback response
          const fallbackResult = {
            error: 'MCP server not available',
            projectId,
            fallback: true,
            message: 'Task updates processed locally (MCP server connection failed)',
            tasksAdded: newTasks?.length || 0,
            tasksUpdated: updatedTasks?.length || 0
          };

          // 📡 Emit error event
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('agentActivity', {
              detail: {
                agentId: 'notionExpert',
                action: `Failed to update Notion tasks - using fallback`,
                status: 'error',
                data: { error: error.message }
              }
            }));
          }
          
          return fallbackResult;
        }
      },
    }),

    tool({
      name: 'enrichNotionContent',
      description: 'Automatically enriches Notion content with anticipated details and proactive structures.',
      parameters: {
        type: 'object',
        properties: {
          projectId: {
            type: 'string',
            description: 'Notion project ID to enrich',
          },
          enrichmentType: {
            type: 'string',
            enum: ['meeting_notes', 'decision_tracking', 'resource_links', 'timeline_update', 'team_assignments'],
            description: 'Type of enrichment to perform',
          },
          content: {
            type: 'object',
            description: 'Content to add or update',
          },
          conversationTrigger: {
            type: 'string',
            description: 'Conversation element that triggered this enrichment',
          },
        },
        required: ['projectId', 'enrichmentType', 'content'],
        additionalProperties: false,
      },
      execute: async (input: any) => {
        const { projectId, enrichmentType, content, conversationTrigger } = input;
        
        try {
          // Call actual Notion MCP server to enrich content
          const mcpResponse = await fetch('/api/mcp/notion', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              tool: 'enrichNotionContent',
              arguments: {
                projectId,
                enrichmentType,
                content,
                conversationTrigger: conversationTrigger || ''
              }
            })
          });

          if (!mcpResponse.ok) {
            throw new Error(`MCP request failed: ${mcpResponse.status}`);
          }

          const mcpResult = await mcpResponse.json();
          
          // 🔍 DEBUG: Log to trace enrichment
          console.log('⚡ NotionExpert - Real Content Enriched:', {
            projectId: projectId,
            type: enrichmentType,
            trigger: conversationTrigger,
            success: mcpResult.success
          });

          // 📡 Emit event for visualizer
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('agentActivity', {
              detail: {
                agentId: 'notionExpert',
                action: `Real Notion content enriched: ${enrichmentType.replace('_', ' ')}`,
                status: 'completed',
                data: mcpResult
              }
            }));
          }
          
          return mcpResult;
          
        } catch (error) {
          console.error('❌ Error enriching Notion content:', error);
          
          // Fallback response
          const fallbackResult = {
            error: 'MCP server not available',
            projectId,
            enrichmentType,
            fallback: true,
            message: 'Content enrichment processed locally (MCP server connection failed)',
            trigger: conversationTrigger
          };

          // 📡 Emit error event
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('agentActivity', {
              detail: {
                agentId: 'notionExpert',
                action: `Failed to enrich Notion content - using fallback`,
                status: 'error',
                data: { error: error.message }
              }
            }));
          }
          
          return fallbackResult;
        }
      },
    }),
  ],

  handoffs: [], // No handoff - single agent
});

// Export scenario with single agent
export const realEstateBrokerScenario = [
  notionExpertAgent
];

// Export system name (adapted to new context)
export const realEstateCompanyName = 'Notion Expert - Silent Transcriber';