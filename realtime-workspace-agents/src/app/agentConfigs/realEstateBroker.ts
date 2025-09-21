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

    🎨 ADVANCED CONTENT MANAGEMENT:
    - Use proper Notion formatting (headers, bullets, callouts)
    - Add emojis for visual organization
    - FIND AND ADD RELEVANT IMAGES from the internet
    - Create tables, lists, and rich formatting
    - Add links, references, and multimedia content
    - Use callouts for important insights
    - Maintain document readability and flow

    🧠 ULTRA INTELLIGENCE:
    - UNDERSTAND user intent beyond literal words
    - AUTOMATICALLY set includeImages=true for visual topics
    - AUTOMATICALLY set enhanceContent=true for important content
    - AUTOMATICALLY choose the right formatType based on content
    - PREDICT what information would be useful
    - ORGANIZE content in the most logical way
    - CROSS-REFERENCE related information
    - ADD context and background automatically

    🖼️ AUTOMATIC IMAGE INTEGRATION:
    - ALWAYS add images for: projects, products, places, people, concepts
    - Automatically generate imageQuery based on what's discussed
    - Add relevant visuals without being asked
    - Use images to make documents more professional and engaging
    - Smart image selection based on context

    🎯 SMART PARAMETERS:
    - includeImages: true for visual topics (projects, products, places)
    - enhanceContent: true for important information
    - formatType: 'presentation' for final documents, 'detailed' for complex topics
    - importance: 'high' for projects/decisions, 'medium' for details

    🤐 SILENT OPERATION:
    - NEVER respond vocally or in chat
    - Work completely in the background
    - Let conversations flow naturally while documenting everything
    - Focus on CAPTURING, ENHANCING and STRUCTURING, not interrupting`,

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
          includeImages: {
            type: 'boolean',
            description: 'Whether to search and include relevant images',
          },
          imageQuery: {
            type: 'string',
            description: 'Search query for finding relevant images',
          },
          enhanceContent: {
            type: 'boolean',
            description: 'Whether to enhance content with additional context and details',
          },
          formatType: {
            type: 'string',
            enum: ['simple', 'structured', 'presentation', 'detailed'],
            description: 'How to format the content',
          },
        },
        required: ['contentType', 'title', 'content'],
        additionalProperties: false,
      },
      execute: async (input: any) => {
        const { contentType, title, content, structure, context, timestamp, importance, includeImages, imageQuery, enhanceContent, formatType } = input;
        
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
                includeImages: includeImages || false,
                imageQuery: imageQuery || '',
                enhanceContent: enhanceContent || false,
                formatType: formatType || 'simple',
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

    tool({
      name: 'replaceImageInPage',
      description: 'Replaces an existing image on the page with a new image.',
      parameters: {
        type: 'object',
        properties: {
          imageToReplace: {
            type: 'string',
            description: 'Description of the current image to replace (e.g., "dog", "cat", "car")',
          },
          newImageQuery: {
            type: 'string',
            description: 'What the new image should show (e.g., "cat", "beautiful dog", "red car")',
          },
          context: {
            type: 'string',
            description: 'Context of why the image is being replaced',
          },
        },
        required: ['imageToReplace', 'newImageQuery'],
        additionalProperties: false,
      },
      execute: async (input: any) => {
        const { imageToReplace, newImageQuery, context } = input;
        
        try {
          const mcpResponse = await fetch('/api/mcp/notion', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              tool: 'replaceSpecificImage',
              arguments: {
                imageToReplace,
                newImageQuery,
                context: context || '',
                targetPageId: '274a860b701080368183ce1111e68d65'
              }
            })
          });

          if (!mcpResponse.ok) {
            throw new Error(`MCP request failed: ${mcpResponse.status}`);
          }

          const mcpResult = await mcpResponse.json();
          
          console.log('🖼️ Rio - Image Replaced:', {
            from: imageToReplace,
            to: newImageQuery,
            success: mcpResult.success
          });

          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('agentActivity', {
              detail: {
                agentId: 'rio',
                action: `Replaced ${imageToReplace} image with ${newImageQuery}`,
                status: 'completed',
                data: mcpResult
              }
            }));
          }
          
          return mcpResult;
          
        } catch (error) {
          console.error('❌ Error replacing image:', error);
          return {
            error: 'Failed to replace image',
            imageToReplace,
            newImageQuery,
            fallback: true
          };
        }
      },
    }),

    tool({
      name: 'addTableToPage',
      description: 'Adds a table to the page at a specific position.',
      parameters: {
        type: 'object',
        properties: {
          position: {
            type: 'string',
            enum: ['beginning', 'end', 'after_title'],
            description: 'Where to add the table',
          },
          tableData: {
            type: 'object',
            properties: {
              headers: {
                type: 'array',
                items: { type: 'string' },
                description: 'Table column headers',
              },
              rows: {
            type: 'array',
            items: {
                  type: 'array',
                  items: { type: 'string' }
                },
                description: 'Table rows data',
              }
            },
            description: 'Table structure and data',
          },
          title: {
            type: 'string',
            description: 'Optional title for the table',
          },
        },
        required: ['position'],
        additionalProperties: false,
      },
      execute: async (input: any) => {
        const { position, tableData, title } = input;
        
        try {
          const mcpResponse = await fetch('/api/mcp/notion', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              tool: 'addTableToPage',
              arguments: {
                position,
                tableData: tableData || {
                  headers: ['Colonne 1', 'Colonne 2', 'Colonne 3'],
                  rows: [
                    ['Données 1', 'Données 2', 'Données 3'],
                    ['Ligne 2', 'Info 2', 'Détail 2']
                  ]
                },
                title: title || '',
                targetPageId: '274a860b701080368183ce1111e68d65'
              }
            })
          });

          if (!mcpResponse.ok) {
            throw new Error(`MCP request failed: ${mcpResponse.status}`);
          }

          const mcpResult = await mcpResponse.json();
          
          console.log('📊 Rio - Table Added:', {
            position,
            title,
            success: mcpResult.success
          });

        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('agentActivity', {
            detail: {
                agentId: 'rio',
                action: `Added table at ${position}${title ? ` - ${title}` : ''}`,
              status: 'completed',
                data: mcpResult
            }
          }));
        }
        
          return mcpResult;
          
        } catch (error) {
          console.error('❌ Error adding table:', error);
          return {
            error: 'Failed to add table',
            position,
            fallback: true
          };
        }
      },
    }),

    tool({
      name: 'clearAndReplacePageContent',
      description: 'Completely clears the page and replaces with new content.',
      parameters: {
        type: 'object',
        properties: {
          newContent: {
            type: 'string',
            description: 'The new content to replace everything with',
          },
          includeImage: {
            type: 'boolean',
            description: 'Whether to include a relevant image',
          },
          imageQuery: {
            type: 'string',
            description: 'What image to search for',
          },
        },
        required: ['newContent'],
        additionalProperties: false,
      },
      execute: async (input: any) => {
        const { newContent, includeImage, imageQuery } = input;
        
        try {
          const mcpResponse = await fetch('/api/mcp/notion', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              tool: 'replaceAllPageContent',
              arguments: {
                content: newContent,
                includeImage: includeImage || false,
                imageQuery: imageQuery || newContent,
                targetPageId: '274a860b701080368183ce1111e68d65'
              }
            })
          });

          if (!mcpResponse.ok) {
            throw new Error(`MCP request failed: ${mcpResponse.status}`);
          }

          const mcpResult = await mcpResponse.json();
          
          console.log('🔄 Rio - Page Completely Replaced:', {
            newContent: newContent.substring(0, 50),
            success: mcpResult.success
          });

        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('agentActivity', {
            detail: {
                agentId: 'rio',
                action: `Page completely replaced with: ${newContent.substring(0, 30)}...`,
              status: 'completed',
                data: mcpResult
            }
          }));
        }
        
          return mcpResult;
          
        } catch (error) {
          console.error('❌ Error replacing page:', error);
          return {
            error: 'Failed to replace page content',
            newContent,
            fallback: true
          };
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