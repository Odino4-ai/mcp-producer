import { RealtimeAgent, tool } from '@openai/agents/realtime';

// Agent Unique : Rio - Documenteur Intelligent qui structure et enrichit en temps réel
export const notionExpertAgent = new RealtimeAgent({
  name: 'rio',
  voice: 'sage',
  handoffDescription:
    "Rio, the intelligent live documenter who captures, structures and enriches every conversation detail in Notion in real-time.",

  instructions:
    `You are RIO, an INTELLIGENT LIVE DOCUMENTER speaking in english.

    🎯 YOUR MISSION:
    - You DOCUMENT EVERYTHING that is said in REAL-TIME
    - You STRUCTURE content intelligently with proper hierarchy
    - You SYNTHESIZE and ANALYZE information as it flows
    - You can MODIFY, ADD, or DELETE content on the same Notion page
    - You work SILENTLY in the background

    📝 LIVE DOCUMENTATION RULES:
    - IMMEDIATELY document every piece of information mentioned
    - Create LOGICAL STRUCTURE: titles, subtitles, categories, sections
    - SYNTHESIZE conversations into coherent, organized content
    - ADD content where it makes sense in the document structure
    - MODIFY existing content when new information updates it
    - DELETE outdated or incorrect information
    
    🧹 PAGE MANAGEMENT COMMANDS:
    When users say things like:
    - "delete all text" / "clear the page" / "remove everything" → Use contentType: 'delete_all'
    - "replace all text with X" / "change everything to X" → Use contentType: 'replace_all'
    - "clean up the page" / "start fresh" → Use contentType: 'page_management'

    🏗️ INTELLIGENT STRUCTURING:
    When someone mentions a project or topic:
    - Create clear TITLE and SUBTITLE hierarchy
    - Organize information in LOGICAL CATEGORIES
    - Add CONTEXT and BACKGROUND information
    - Create sections for: Overview, Details, Team, Timeline, Notes
    - Keep ANALYTICAL perspective - what are the implications?
    - Maintain THINGS TO REMEMBER for future reference

    🔄 REAL-TIME UPDATES:
    - Every sentence spoken gets processed and documented
    - Update existing sections when new info comes in
    - Reorganize content structure as topics evolve
    - Add timestamps and conversation flow markers
    - Cross-reference related information

    📊 ANALYTICAL APPROACH:
    - Identify KEY INSIGHTS and highlight them
    - Note DECISIONS made during conversation
    - Track CHANGES in project scope or direction
    - Capture IMPORTANT DETAILS that might be forgotten
    - Synthesize ACTIONABLE INFORMATION

    🎨 CONTENT MANAGEMENT:
    - Use proper Notion formatting (headers, bullets, callouts)
    - Add emojis for visual organization
    - Create clear sections and subsections
    - Use callouts for important insights
    - Maintain document readability and flow

    🤐 SILENT OPERATION:
    - NEVER respond vocally or in chat
    - Work completely in the background
    - Let conversations flow naturally while documenting everything
    - Focus on CAPTURING and STRUCTURING, not interrupting`,

  tools: [
    tool({
      name: 'documentConversationContent',
      description: 'Documents any conversation content in real-time with intelligent structure and formatting.',
      parameters: {
        type: 'object',
        properties: {
          contentType: {
            type: 'string',
            enum: ['project', 'topic', 'decision', 'insight', 'detail', 'update', 'note', 'page_management', 'replace_all', 'delete_all'],
            description: 'Type of content being documented or page management action',
          },
          title: {
            type: 'string',
            description: 'Main title or heading for this content',
          },
          content: {
            type: 'string',
            description: 'The actual content to document',
          },
          structure: {
            type: 'object',
            properties: {
              sections: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    heading: { type: 'string' },
                    content: { type: 'string' },
                    level: { type: 'number', description: 'Heading level 1-3' }
                  }
                }
              }
            },
            description: 'Structured sections for complex content',
          },
          context: {
            type: 'string',
            description: 'Conversation context that triggered this documentation',
          },
          timestamp: {
            type: 'string',
            description: 'When this was mentioned in conversation',
          },
          importance: {
            type: 'string',
            enum: ['low', 'medium', 'high', 'critical'],
            description: 'Importance level of this information',
          },
        },
        required: ['contentType', 'title', 'content'],
        additionalProperties: false,
      },
      execute: async (input: any) => {
        const { contentType, title, content, structure, context, timestamp, importance } = input;
        
        try {
          // Choisir l'outil MCP selon le type de contenu
          let toolName = 'updateContentInPlace';
          
          if (contentType === 'delete_all') {
            toolName = 'deleteAllPageContent';
          } else if (contentType === 'replace_all') {
            toolName = 'replaceAllPageContent';
          } else if (contentType === 'page_management') {
            toolName = 'managePageContent';
          }
          
          // Call MCP server with appropriate tool
          const mcpResponse = await fetch('/api/mcp/notion', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              tool: toolName,
              arguments: {
                contentType,
                title,
                content,
                structure: structure || null,
                context: context || '',
                timestamp: timestamp || new Date().toISOString(),
                importance: importance || 'medium',
                targetPageId: '274a860b701080368183ce1111e68d65' // Votre page Notion spécifique
              }
            })
          });

          if (!mcpResponse.ok) {
            throw new Error(`MCP request failed: ${mcpResponse.status}`);
          }

          const mcpResult = await mcpResponse.json();
          
          // 🔍 DEBUG: Log to trace documentation
          console.log('📝 Rio - Content Documented:', {
            contentType: contentType,
            title: title,
            importance: importance,
            notionPageId: mcpResult.pageId,
            success: mcpResult.success
          });

          // 📡 Emit event for visualizer
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('agentActivity', {
              detail: {
                agentId: 'rio',
                action: `Content "${title}" documented in real-time`,
                status: 'completed',
                data: mcpResult
              }
            }));
          }
          
          return mcpResult;
          
        } catch (error) {
          console.error('❌ Error documenting content:', error);
          
          // Fallback response
          const fallbackResult = {
            error: 'MCP server not available',
            title,
            contentType,
            fallback: true,
            message: 'Content documented locally (MCP server connection failed)'
          };

          // 📡 Emit error event
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('agentActivity', {
              detail: {
                agentId: 'rio',
                action: `Failed to document "${title}" - using fallback`,
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
export const realEstateCompanyName = 'Rio - Intelligent Live Documenter';