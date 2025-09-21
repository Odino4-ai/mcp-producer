import { RealtimeAgent, tool } from '@openai/agents/realtime';

// Agent Unique : Rio - Documenteur Intelligent qui structure et enrichit en temps réel
export const notionExpertAgent = new RealtimeAgent({
  name: 'rio',
  voice: 'sage',
  handoffDescription:
    "Rio, the intelligent live documenter who captures, structures, and enriches every conversation detail in Notion in real-time, in English.",

  instructions:
    `You are RIO, a helpful assistant who documents conversations in English.

    🎯 SIMPLE MISSION:
    - LISTEN to what people say
    - DO exactly what they're talking about
    - UPDATE the Notion page to reflect the conversation
    - NEVER speak or interrupt

    📝 PRECISE ACTIONS:
    
    When people mention PROJECTS/TOPICS:
    → Use documentConversationContent
    → Set includeImages=true, formatType='presentation'
    
    When people say "REPLACE the image with [X]":
    → Use replaceImageInPage
    → Set imageToReplace='current', newImageQuery='X'
    
    When people say "ADD a table":
    → Use addTableToPage
    → Set position based on context (beginning/end)
    
    When people say "DELETE everything" or "CLEAR the page":
    → Use clearAndReplacePageContent
    → Set newContent='' (empty)
    
    When people say "REPLACE all content with [X]":
    → Use clearAndReplacePageContent
    → Set newContent='X'
    
    When people give NEW info about EXISTING topics:
    → Use documentConversationContent
    → This will update existing sections automatically

    🔧 TOOL SELECTION (EXACT MATCHING):
    - "replace image" → replaceImageInPage
    - "add table" → addTableToPage  
    - "delete all" → clearAndReplacePageContent (empty)
    - "replace all with X" → clearAndReplacePageContent (with X)
    - "clean up" → clearAndReplacePageContent (organized)
    - "reset memory" → resetMemory
    - Everything else → documentConversationContent

    🎯 DEFAULT PARAMETERS:
    - includeImages: true (always)
    - enhanceContent: false (just document what's said)
    - formatType: 'presentation' (clean)
    - importance: 'medium'`,

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

    tool({
      name: 'resetMemory',
      description: 'Completely clears the Notion page to reset the agent memory.',
      parameters: {
        type: 'object',
        properties: {
          confirmation: {
            type: 'string',
            description: 'Confirmation from the user to clear everything.',
          },
        },
        required: [],
        additionalProperties: false,
      },
      execute: async (input: any) => {
        try {
          const mcpResponse = await fetch('/api/mcp/notion', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              tool: 'deleteAllPageContent', // Reuses the existing tool
              arguments: {
                context: 'User requested a memory reset.',
                targetPageId: '274a860b701080368183ce1111e68d65'
              }
            })
          });

          if (!mcpResponse.ok) {
            throw new Error(`MCP request failed: ${mcpResponse.status}`);
          }
          
          const mcpResult = await mcpResponse.json();
          console.log('🧠 Rio - Memory Reset:', { success: mcpResult.success });

          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('agentActivity', {
              detail: {
                agentId: 'rio',
                action: 'Memory completely reset.',
                status: 'completed',
                data: mcpResult
              }
            }));
          }
          
          return mcpResult;
          
        } catch (error) {
          console.error('❌ Error resetting memory:', error);
          return { error: 'Failed to reset memory', fallback: true };
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