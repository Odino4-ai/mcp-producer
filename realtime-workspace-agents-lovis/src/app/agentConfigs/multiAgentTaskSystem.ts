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
        
        // Structure complète du projet Notion
        const projectStructure = {
          projectId: 'notion_proj_' + Date.now(),
          projectName,
          projectDescription,
          createdAt: new Date().toISOString(),
          
          // Main pages
          mainPage: {
            title: `📋 ${projectName} - Main Hub`,
            content: `
# ${projectName}

## 📝 Description
${projectDescription}

## 👥 Team
${teamMembers?.map((member: string) => `- ${member}`).join('\n') || '- To be defined'}

## 🎯 Objectives
- Main objective to define
- Important milestones
- Success criteria

## 📅 Timeline
- Phase 1: Planning
- Phase 2: Development  
- Phase 3: Testing and validation
- Phase 4: Delivery

## 📊 Current Status
🟡 **In planning phase**
            `
          },
          
          // Databases
          databases: {
            tasks: {
              name: `${projectName} - Tasks`,
              properties: {
                'Name': { type: 'title' },
                'Assigned to': { type: 'person' },
                'Status': { type: 'select', options: ['To Do', 'In Progress', 'Done', 'Blocked'] },
                'Priority': { type: 'select', options: ['Low', 'Medium', 'High', 'Urgent'] },
                'Due Date': { type: 'date' },
                'Project': { type: 'relation' }
              }
            },
            meetings: {
              name: `${projectName} - Meetings`,
        properties: {
                'Title': { type: 'title' },
                'Date': { type: 'date' },
                'Participants': { type: 'multi_person' },
                'Notes': { type: 'rich_text' },
                'Actions': { type: 'relation' }
              }
            },
            resources: {
              name: `${projectName} - Resources`,
              properties: {
                'Name': { type: 'title' },
                'Type': { type: 'select', options: ['Document', 'Link', 'File', 'Tool'] },
                'URL': { type: 'url' },
                'Description': { type: 'rich_text' }
              }
            }
          },
          
          // Folders and structure
          folders: [
            '📋 Planning',
            '📝 Documentation', 
            '🔧 Development',
            '🧪 Testing',
            '📊 Reports',
            '💬 Communications'
          ]
        };

        // 🔍 DEBUG: Log to trace creation
        console.log('📝 NotionExpert - Complete Project Created:', {
          projectId: projectStructure.projectId,
          projectName: projectName,
          teamMembers: teamMembers?.length || 0,
          databasesCreated: Object.keys(projectStructure.databases).length,
          foldersCreated: projectStructure.folders.length
        });

        // 📡 Emit event for visualizer
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('agentActivity', {
            detail: {
              agentId: 'notionExpert',
              action: `Project "${projectName}" created with complete structure`,
              status: 'completed',
              data: projectStructure
            }
          }));
        }
        
        return projectStructure;
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
        
        const updateResult = {
          updateId: 'update_' + Date.now(),
          projectId,
          timestamp: new Date().toISOString(),
          changes: {
            tasksAdded: newTasks?.length || 0,
            tasksUpdated: updatedTasks?.length || 0,
            context: conversationContext
          },
          newTasks: newTasks?.map((task: any, index: number) => ({
            id: `task_${Date.now()}_${index}`,
            ...task,
            createdAt: new Date().toISOString(),
            status: 'To Do'
          })) || [],
          status: 'updated'
        };

        // 🔍 DEBUG: Log to trace update
        console.log('📋 NotionExpert - To-Do List Updated:', {
          updateId: updateResult.updateId,
          projectId: projectId,
          tasksAdded: updateResult.changes.tasksAdded,
          tasksUpdated: updateResult.changes.tasksUpdated,
          context: conversationContext
        });

        // 📡 Emit event for visualizer
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('agentActivity', {
            detail: {
              agentId: 'notionExpert',
              action: `To-do list updated: +${updateResult.changes.tasksAdded} tasks`,
              status: 'completed',
              data: updateResult
            }
          }));
        }
        
        return updateResult;
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
        
        const enrichmentResult = {
          enrichmentId: 'enrich_' + Date.now(),
          projectId,
          type: enrichmentType,
          trigger: conversationTrigger,
          timestamp: new Date().toISOString(),
          changes: content,
          status: 'enriched'
        };

        // 🔍 DEBUG: Log to trace enrichment
        console.log('⚡ NotionExpert - Content Enriched:', {
          enrichmentId: enrichmentResult.enrichmentId,
          projectId: projectId,
          type: enrichmentType,
          trigger: conversationTrigger
        });

        // 📡 Emit event for visualizer
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('agentActivity', {
            detail: {
              agentId: 'notionExpert',
              action: `Content enriched: ${enrichmentType.replace('_', ' ')}`,
              status: 'completed',
              data: enrichmentResult
            }
          }));
        }
        
        return enrichmentResult;
      },
    }),
  ],

  handoffs: [], // No handoff - single agent
});

// Export scenario with single agent
export const multiAgentTaskScenario = [
  notionExpertAgent
];

// Export system name (adapted to new context)
export const multiAgentSystemName = 'Notion Expert - Silent Transcriber';