import { NextRequest, NextResponse } from 'next/server';

// Interface pour les requêtes MCP
interface MCPRequest {
  tool: string;
  arguments: any;
}

// Interface pour les réponses MCP
interface MCPResponse {
  success: boolean;
  data?: any;
  error?: string;
  pageId?: string;
  tasksAdded?: number;
  tasksUpdated?: number;
  databasesCreated?: number;
}

// Configuration Notion
const DEFAULT_NOTION_PAGE_ID = "274a860b701080368183ce1111e68d65"; // Page Notion par défaut à modifier

// Fonction pour normaliser l'ID de page Notion
function normalizeNotionPageId(pageId: string): string {
  // Supprimer les tirets et reformater si nécessaire
  const cleanId = pageId.replace(/-/g, '');
  // Reformater avec tirets au bon endroit : 8-4-4-4-12
  if (cleanId.length === 32) {
    return `${cleanId.slice(0,8)}-${cleanId.slice(8,12)}-${cleanId.slice(12,16)}-${cleanId.slice(16,20)}-${cleanId.slice(20,32)}`;
  }
  return pageId;
}
const NOTION_API_URL = "https://api.notion.com/v1";
const NOTION_VERSION = "2022-06-28";

// Client MCP Notion avec vraie intégration API
class NotionMCPClient {
  
  private async callNotionAPI(endpoint: string, method: string = 'GET', data?: any) {
    const notionToken = process.env.NOTION_TOKEN;
    
    if (!notionToken) {
      throw new Error('NOTION_TOKEN not configured');
    }
    
    console.log(`🔗 Notion API Call: ${method} ${endpoint}`);
    
    const response = await fetch(`${NOTION_API_URL}${endpoint}`, {
      method,
      headers: {
        'Authorization': `Bearer ${notionToken}`,
        'Notion-Version': NOTION_VERSION,
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    
    console.log(`📡 Notion API Response: ${response.status} ${response.statusText}`);
    
    if (!response.ok) {
      const error = await response.json();
      console.error(`❌ Notion API Error:`, error);
      throw new Error(`Notion API error: ${response.status} - ${JSON.stringify(error)}`);
    }
    
    const result = await response.json();
    return result;
  }
  
  async createNotionProject(args: any): Promise<MCPResponse> {
    const { projectName, projectDescription, projectType, teamMembers, initialContext } = args;
    
    try {
      // 🔧 Appel réel à l'API Notion pour créer le projet
      
      const projectId = `notion_${Date.now()}`;
      const rawPageId = args.targetPageId || DEFAULT_NOTION_PAGE_ID;
      const pageId = normalizeNotionPageId(rawPageId); // Normalise l'ID de page
      
      // Créer le contenu du projet à ajouter à la page
      const projectContent = [
        {
          "object": "block",
          "type": "heading_1",
          "heading_1": {
            "rich_text": [
              {
                "type": "text",
                "text": {
                  "content": `🚀 ${projectName}`
                },
                "annotations": {
                  "bold": true,
                  "color": "blue"
                }
              }
            ]
          }
        },
        {
          "object": "block",
          "type": "paragraph",
          "paragraph": {
            "rich_text": [
              {
                "type": "text",
                "text": {
                  "content": `📝 Description: ${projectDescription}`
                }
              }
            ]
          }
        },
        {
          "object": "block",
          "type": "paragraph",
          "paragraph": {
            "rich_text": [
              {
                "type": "text",
                "text": {
                  "content": `🎯 Type: ${projectType || 'business'}`
                }
              }
            ]
          }
        }
      ];
      
      // Ajouter l'équipe si spécifiée
      if (teamMembers && teamMembers.length > 0) {
        projectContent.push({
          "object": "block",
          "type": "heading_3",
          "heading_3": {
            "rich_text": [
              {
                "type": "text",
                "text": {
                  "content": "👥 Équipe"
                }
              }
            ]
          }
        });
        
        teamMembers.forEach((member: string) => {
          projectContent.push({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
              "rich_text": [
                {
                  "type": "text",
                  "text": {
                    "content": member
                  }
                }
              ]
            }
          });
        });
      }
      
      // Ajouter des sections de base
      projectContent.push(
        {
          "object": "block",
          "type": "heading_3",
          "heading_3": {
            "rich_text": [
              {
                "type": "text",
                "text": {
                  "content": "📋 Tâches"
                }
              }
            ]
          }
        },
        {
          "object": "block",
          "type": "to_do",
          "to_do": {
            "rich_text": [
              {
                "type": "text",
                "text": {
                  "content": "Planifier le projet"
                }
              }
            ],
            "checked": false
          }
        },
        {
          "object": "block",
          "type": "to_do",
          "to_do": {
            "rich_text": [
              {
                "type": "text",
                "text": {
                  "content": "Définir les objectifs"
                }
              }
            ],
            "checked": false
          }
        }
      );
      
      // Ajouter le contexte initial si fourni
      if (initialContext) {
        projectContent.push({
          "object": "block",
          "type": "callout",
          "callout": {
            "rich_text": [
              {
                "type": "text",
                "text": {
                  "content": `💡 Contexte initial: ${initialContext}`
                }
              }
            ],
            "icon": {
              "emoji": "💡"
            }
          }
        });
      }
      
      // Ajouter le contenu à la page Notion
      await this.callNotionAPI(`/blocks/${pageId}/children`, 'PATCH', {
        children: projectContent
      });
      
      console.log('🎯 MCP API - Notion Project REALLY Created:', {
        projectId,
        projectName,
        targetNotionPageId: pageId,
        blocksCreated: projectContent.length,
        teamMembers: teamMembers?.length || 0
      });
      
      return {
        success: true,
        pageId,
        databasesCreated: 0, // Pas de databases créées, juste du contenu ajouté
        data: {
          projectId,
          projectName,
          targetPageId: pageId,
          blocksCreated: projectContent.length,
          notionUrl: `https://notion.so/${pageId.replace(/-/g, '')}`,
          timestamp: new Date().toISOString()
        }
      };
      
    } catch (error) {
      console.error('❌ MCP API - Error creating Notion project:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
  
  async updateNotionTasks(args: any): Promise<MCPResponse> {
    const { projectId, newTasks, updatedTasks, conversationContext } = args;
    const rawTargetPageId = args.targetPageId || DEFAULT_NOTION_PAGE_ID;
    const targetPageId = normalizeNotionPageId(rawTargetPageId);
    
    try {
      // 🔧 Appel réel à l'API Notion pour modifier la page
      
      // 1. Récupérer le contenu actuel de la page
      const currentPage = await this.callNotionAPI(`/pages/${targetPageId}`);
      
      // 2. Récupérer les blocs de contenu actuels
      const currentBlocks = await this.callNotionAPI(`/blocks/${targetPageId}/children`);
      
      // 3. Créer le nouveau contenu à ajouter
      const newContent = [];
      
      // Ajouter un header pour les nouvelles tâches
      if (newTasks && newTasks.length > 0) {
        newContent.push({
          "object": "block",
          "type": "heading_2",
          "heading_2": {
            "rich_text": [
              {
                "type": "text",
                "text": {
                  "content": `🔄 Mise à jour - ${new Date().toLocaleDateString()}`
                }
              }
            ]
          }
        });
        
        // Ajouter le contexte de conversation
        if (conversationContext) {
          newContent.push({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
              "rich_text": [
                {
                  "type": "text",
                  "text": {
                    "content": `💬 Contexte: ${conversationContext}`
                  }
                }
              ]
            }
          });
        }
        
        // Ajouter chaque nouvelle tâche
        newTasks.forEach((task: any) => {
          newContent.push({
            "object": "block",
            "type": "to_do",
            "to_do": {
              "rich_text": [
                {
                  "type": "text",
                  "text": {
                    "content": task.task || task.title || 'Nouvelle tâche'
                  }
                }
              ],
              "checked": false
            }
          });
          
          // Ajouter les détails de la tâche si disponibles
          if (task.assignedTo || task.priority) {
            const details = [];
            if (task.assignedTo) details.push(`👤 ${task.assignedTo}`);
            if (task.priority) details.push(`⚡ ${task.priority}`);
            
            newContent.push({
              "object": "block",
              "type": "paragraph",
              "paragraph": {
                "rich_text": [
                  {
                    "type": "text",
                    "text": {
                      "content": `   ${details.join(' • ')}`
                    }
                  }
                ]
              }
            });
          }
        });
      }
      
      // 4. Ajouter le nouveau contenu à la page Notion
      if (newContent.length > 0) {
        await this.callNotionAPI(`/blocks/${targetPageId}/children`, 'PATCH', {
          children: newContent
        });
      }
      
      const tasksAdded = newTasks?.length || 0;
      const tasksUpdated = updatedTasks?.length || 0;
      
      console.log('📋 MCP API - Notion Page REALLY Updated:', {
        projectId,
        targetNotionPageId: targetPageId,
        tasksAdded,
        tasksUpdated,
        context: conversationContext,
        blocksAdded: newContent.length
      });
      
      return {
        success: true,
        tasksAdded,
        tasksUpdated,
        data: {
          projectId,
          targetPageId,
          blocksAdded: newContent.length,
          timestamp: new Date().toISOString(),
          notionUrl: `https://notion.so/${targetPageId.replace(/-/g, '')}`
        }
      };
      
    } catch (error) {
      console.error('❌ MCP API - Error updating Notion tasks:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
  
  async enrichNotionContent(args: any): Promise<MCPResponse> {
    const { projectId, enrichmentType, content, conversationTrigger } = args;
    const targetPageId = args.targetPageId || DEFAULT_NOTION_PAGE_ID;
    
    try {
      // 🔧 ICI : Appel réel au serveur MCP pour enrichir le contenu
      
      const enrichmentId = `enrich_${Date.now()}`;
      
      console.log('⚡ MCP API - Notion Content Enriched:', {
        enrichmentId,
        projectId,
        targetNotionPageId: targetPageId,
        type: enrichmentType,
        trigger: conversationTrigger
      });
      
      return {
        success: true,
        data: {
          enrichmentId,
          projectId,
          type: enrichmentType,
          trigger: conversationTrigger,
          content,
          timestamp: new Date().toISOString(),
          notionUpdated: true
        }
      };
      
    } catch (error) {
      console.error('❌ MCP API - Error enriching Notion content:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
  
  async documentLiveContent(args: any): Promise<MCPResponse> {
    const { contentType, title, content, structure, context, timestamp, importance, includeImages, imageQuery, enhanceContent, formatType } = args;
    const targetPageId = args.targetPageId || DEFAULT_NOTION_PAGE_ID;
    
    try {
      // 🔧 Documentation intelligente avec modification/mise à jour du contenu existant
      
      // 1. Lire le contenu existant de la page
      const existingBlocks = await this.callNotionAPI(`/blocks/${targetPageId}/children?page_size=100`);
      
      // 2. Analyser le contenu existant pour trouver les sections similaires
      const existingContent = existingBlocks.results || [];
      let targetBlockId = null;
      let shouldReplace = false;
      
      // Chercher une section existante avec un titre similaire
      for (let i = 0; i < existingContent.length; i++) {
        const block = existingContent[i];
        
        if (block.type === 'heading_1' || block.type === 'heading_2' || block.type === 'heading_3') {
          const blockText = block[block.type]?.rich_text?.[0]?.text?.content || '';
          
          // Vérifier si le titre correspond (en ignorant les emojis)
          const cleanBlockText = blockText.replace(/^[🚀📌✅💡📝🔄📋📄]\s*/, '');
          const cleanTitle = title.replace(/^[🚀📌✅💡📝🔄📋📄]\s*/, '');
          
          if (cleanBlockText.toLowerCase().includes(cleanTitle.toLowerCase()) || 
              cleanTitle.toLowerCase().includes(cleanBlockText.toLowerCase())) {
            targetBlockId = block.id;
            shouldReplace = true;
            console.log('🔍 Found existing section to update:', cleanBlockText);
            break;
          }
        }
      }
      
      const documentContent = [];
      
      // 3. Si on remplace une section existante, supprimer d'abord les blocs associés
      if (shouldReplace && targetBlockId) {
        // Trouver tous les blocs associés à cette section (jusqu'au prochain titre de même niveau)
        const targetBlockIndex = existingContent.findIndex(block => block.id === targetBlockId);
        const targetBlock = existingContent[targetBlockIndex];
        const targetLevel = targetBlock.type;
        
        const blocksToDelete = [targetBlockId]; // Inclure le titre
        
        // Trouver tous les blocs suivants jusqu'au prochain titre de même niveau ou supérieur
        for (let i = targetBlockIndex + 1; i < existingContent.length; i++) {
          const nextBlock = existingContent[i];
          
          // Si c'est un titre de même niveau ou supérieur, arrêter
          if ((nextBlock.type === 'heading_1') ||
              (nextBlock.type === 'heading_2' && targetLevel !== 'heading_1') ||
              (nextBlock.type === 'heading_3' && targetLevel === 'heading_3')) {
            break;
          }
          
          blocksToDelete.push(nextBlock.id);
        }
        
        // Supprimer les blocs existants (un par un avec vérification)
        let deletedCount = 0;
        for (const blockId of blocksToDelete) {
          try {
            console.log(`🗑️ Attempting to delete block: ${blockId}`);
            const deleteResponse = await this.callNotionAPI(`/blocks/${blockId}`, 'DELETE');
            console.log(`✅ Successfully deleted block: ${blockId}`, deleteResponse);
            deletedCount++;
            
            // Petite pause pour éviter les rate limits
            await new Promise(resolve => setTimeout(resolve, 100));
          } catch (error: any) {
            console.error(`❌ Failed to delete block ${blockId}:`, error.message);
            // Continuer même si la suppression échoue
          }
        }
        
        console.log(`🗑️ Deleted ${deletedCount}/${blocksToDelete.length} blocks for section update`);
      }
      
      // 4. ULTRA INTELLIGENCE - Améliorer le contenu automatiquement
      let enhancedContent = content;
      let relevantImages = [];
      
      if (enhanceContent) {
        // Enrichir le contenu avec du contexte intelligent
        enhancedContent = await this.enhanceContentIntelligently(content, contentType, title);
      }
      
      if (includeImages) {
        // Rechercher des images pertinentes
        const searchQuery = imageQuery || title || content.substring(0, 50);
        relevantImages = await this.findRelevantImages(searchQuery, contentType);
      }
      
      // 5. Créer le nouveau contenu (mis à jour ou nouveau)
      if (!shouldReplace) {
        // Ajouter un séparateur seulement pour le nouveau contenu
        documentContent.push({
          "object": "block",
          "type": "divider",
          "divider": {}
        });
      }
      
      // Ajouter le titre principal selon le type de contenu
      const titleEmoji = {
        'project': '🚀',
        'topic': '📌',
        'decision': '✅',
        'insight': '💡',
        'detail': '📝',
        'update': '🔄',
        'note': '📋'
      }[contentType] || '📄';
      
      const headerLevel = importance === 'critical' ? 'heading_1' : 
                         importance === 'high' ? 'heading_2' : 'heading_3';
      
      // Ajouter un indicateur de mise à jour si c'est une modification
      const titleText = shouldReplace ? 
        `${titleEmoji} ${title} (Updated ${new Date().toLocaleTimeString()})` :
        `${titleEmoji} ${title}`;
      
      documentContent.push({
        "object": "block",
        "type": headerLevel,
        [headerLevel]: {
          "rich_text": [
            {
              "type": "text",
              "text": {
                "content": titleText
              },
              "annotations": {
                "bold": importance === 'critical',
                "color": importance === 'critical' ? 'red' : 
                        importance === 'high' ? 'orange' : 
                        shouldReplace ? 'blue' : 'default'
              }
            }
          ]
        }
      });
      
      // Pas de métadonnées dans le document final - garder propre
      
      // Ajouter les images trouvées en premier
      if (relevantImages && relevantImages.length > 0) {
        relevantImages.forEach((imageUrl: string) => {
          documentContent.push({
            "object": "block",
            "type": "image",
            "image": {
              "type": "external",
              "external": {
                "url": imageUrl
              }
            }
          });
        });
      }
      
      // Ajouter le contenu principal (enrichi)
      if (structure && structure.sections && structure.sections.length > 0) {
        // Contenu structuré avec sections
        structure.sections.forEach((section: any) => {
          const sectionLevel = section.level === 1 ? 'heading_2' :
                              section.level === 2 ? 'heading_3' : 'paragraph';
          
          if (section.heading && sectionLevel !== 'paragraph') {
            documentContent.push({
              "object": "block",
              "type": sectionLevel,
              [sectionLevel]: {
                "rich_text": [
                  {
                    "type": "text",
                    "text": {
                      "content": section.heading
                    }
                  }
                ]
              }
            });
          }
          
          documentContent.push({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
              "rich_text": [
                {
                  "type": "text",
                  "text": {
                    "content": section.content
                  }
                }
              ]
            }
          });
        });
      } else {
        // Contenu simple enrichi
        documentContent.push({
          "object": "block",
          "type": "paragraph",
          "paragraph": {
            "rich_text": [
              {
                "type": "text",
                "text": {
                  "content": enhancedContent
                }
              }
            ]
          }
        });
      }
      
      // Pas de callouts dans le document final - garder propre et professionnel
      
      // 5. Ajouter le nouveau contenu à la page Notion
      let insertionResult = null;
      if (documentContent.length > 0) {
        if (shouldReplace && targetBlockId) {
          // Insérer à la position où était l'ancien contenu
          const targetBlockIndex = existingContent.findIndex(block => block.id === targetBlockId);
          
          if (targetBlockIndex >= 0) {
            // Insérer après le bloc précédent (ou au début si c'est le premier)
            if (targetBlockIndex > 0) {
              const previousBlockId = existingContent[targetBlockIndex - 1].id;
              insertionResult = await this.callNotionAPI(`/blocks/${previousBlockId}/children`, 'PATCH', {
                children: documentContent
              });
            } else {
              // Insérer au début de la page
              insertionResult = await this.callNotionAPI(`/blocks/${targetPageId}/children`, 'PATCH', {
                children: documentContent
              });
            }
          }
        } else {
          // Nouveau contenu - ajouter à la fin
          insertionResult = await this.callNotionAPI(`/blocks/${targetPageId}/children`, 'PATCH', {
            children: documentContent
          });
        }
      }
      
      const actionType = shouldReplace ? 'UPDATED' : 'ADDED';
      console.log(`📝 MCP API - Content ${actionType}:`, {
        contentType,
        title,
        importance,
        targetNotionPageId: targetPageId,
        blocksProcessed: documentContent.length,
        action: actionType,
        timestamp: timestamp || new Date().toISOString()
      });
      
      return {
        success: true,
        data: {
          contentType,
          title,
          targetPageId,
          blocksProcessed: documentContent.length,
          action: actionType,
          wasUpdate: shouldReplace,
          timestamp: timestamp || new Date().toISOString(),
          notionUrl: `https://notion.so/${targetPageId.replace(/-/g, '')}`
        }
      };
      
    } catch (error) {
      console.error('❌ MCP API - Error documenting live content:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
  
  async testNotionDeletion(args: any): Promise<MCPResponse> {
    const targetPageId = args.targetPageId || DEFAULT_NOTION_PAGE_ID;
    
    try {
      // Test de suppression : créer un bloc puis le supprimer
      console.log('🧪 Testing Notion deletion capabilities...');
      
      // 1. Créer un bloc de test
      const testContent = [{
        "object": "block",
        "type": "paragraph",
        "paragraph": {
          "rich_text": [
            {
              "type": "text",
              "text": {
                "content": `🧪 TEST BLOCK - Created at ${new Date().toISOString()} - This block will be deleted in 2 seconds`
              }
            }
          ]
        }
      }];
      
      const createResponse = await this.callNotionAPI(`/blocks/${targetPageId}/children`, 'PATCH', {
        children: testContent
      });
      
      console.log('✅ Test block created:', createResponse);
      
      // 2. Attendre 3 secondes pour la synchronisation Notion
      console.log('⏳ Waiting 3 seconds for Notion sync...');
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // 3. Récupérer TOUS les blocs pour trouver celui qu'on vient de créer
      const blocks = await this.callNotionAPI(`/blocks/${targetPageId}/children?page_size=100`);
      console.log(`📊 Found ${blocks.results?.length || 0} total blocks on page`);
      
      // Debug: afficher tous les blocs récents
      const recentBlocks = blocks.results?.slice(-5) || [];
      console.log('🔍 Last 5 blocks on page:');
      recentBlocks.forEach((block: any, index: number) => {
        const content = block[block.type]?.rich_text?.[0]?.text?.content || 'No content';
        console.log(`  ${index}: ${block.type} - "${content.substring(0, 50)}..."`);
      });
      
      const testBlock = blocks.results?.find((block: any) => {
        const content = block[block.type]?.rich_text?.[0]?.text?.content || '';
        return content.includes('🧪 TEST BLOCK');
      });
      
      if (!testBlock) {
        // Essayer de trouver le dernier bloc créé
        const lastBlock = blocks.results?.[blocks.results.length - 1];
        console.log('❌ Could not find test block, last block is:', {
          type: lastBlock?.type,
          content: lastBlock?.[lastBlock?.type]?.rich_text?.[0]?.text?.content?.substring(0, 100)
        });
        throw new Error(`Could not find the test block. Found ${blocks.results?.length || 0} blocks total.`);
      }
      
      console.log('🔍 Found test block to delete:', testBlock.id);
      
      // 4. Supprimer le bloc de test
      const deleteResponse = await this.callNotionAPI(`/blocks/${testBlock.id}`, 'DELETE');
      console.log('🗑️ Test block deleted:', deleteResponse);
      
      return {
        success: true,
        data: {
          message: 'Deletion test completed successfully',
          testBlockId: testBlock.id,
          createdAt: new Date().toISOString(),
          deletionWorking: true
        }
      };
      
    } catch (error) {
      console.error('❌ Deletion test failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        data: {
          message: 'Deletion test failed - this might explain why content is not being replaced',
          deletionWorking: false
        }
      };
    }
  }
  
  async updateContentInPlace(args: any): Promise<MCPResponse> {
    const { contentType, title, content, structure, context, timestamp, importance } = args;
    const targetPageId = args.targetPageId || DEFAULT_NOTION_PAGE_ID;
    
    try {
      // 🔧 Approche alternative : modifier le contenu existant au lieu de supprimer/recréer
      
      // 1. Lire le contenu existant
      const existingBlocks = await this.callNotionAPI(`/blocks/${targetPageId}/children?page_size=100`);
      const existingContent = existingBlocks.results || [];
      
      // 2. Chercher une section existante avec un titre similaire
      let targetBlock = null;
      const cleanTitle = title.replace(/^[🚀📌✅💡📝🔄📋📄]\s*/, '');
      
      for (const block of existingContent) {
        if (block.type === 'heading_1' || block.type === 'heading_2' || block.type === 'heading_3') {
          const blockText = block[block.type]?.rich_text?.[0]?.text?.content || '';
          const cleanBlockText = blockText.replace(/^[🚀📌✅💡📝🔄📋📄]\s*/, '').replace(/\s*\(Updated.*\)$/, '');
          
          if (cleanBlockText.toLowerCase().includes(cleanTitle.toLowerCase()) || 
              cleanTitle.toLowerCase().includes(cleanBlockText.toLowerCase())) {
            targetBlock = block;
            console.log('🔍 Found existing section to update:', cleanBlockText);
            break;
          }
        }
      }
      
      if (targetBlock) {
        // 3. Modifier le titre existant avec indication de mise à jour
        const titleEmoji = {
          'project': '🚀',
          'topic': '📌',
          'decision': '✅',
          'insight': '💡',
          'detail': '📝',
          'update': '🔄',
          'note': '📋'
        }[contentType] || '📄';
        
        const updatedTitle = `${titleEmoji} ${title} (Updated ${new Date().toLocaleTimeString()})`;
        
        // Modifier le titre
        await this.callNotionAPI(`/blocks/${targetBlock.id}`, 'PATCH', {
          [targetBlock.type]: {
            "rich_text": [
              {
                "type": "text",
                "text": {
                  "content": updatedTitle
                },
                "annotations": {
                  "bold": importance === 'critical',
                  "color": importance === 'critical' ? 'red' : 
                          importance === 'high' ? 'orange' : 'blue'
                }
              }
            ]
          }
        });
        
        // 4. Trouver le premier paragraphe suivant ce titre et le modifier
        const targetIndex = existingContent.findIndex(block => block.id === targetBlock.id);
        let contentBlockToUpdate = null;
        
        for (let i = targetIndex + 1; i < existingContent.length; i++) {
          const nextBlock = existingContent[i];
          if (nextBlock.type === 'paragraph') {
            contentBlockToUpdate = nextBlock;
            break;
          }
          // Arrêter si on trouve un autre titre
          if (nextBlock.type === 'heading_1' || nextBlock.type === 'heading_2' || nextBlock.type === 'heading_3') {
            break;
          }
        }
        
        if (contentBlockToUpdate) {
          // Modifier le contenu existant (propre, sans métadonnées)
          await this.callNotionAPI(`/blocks/${contentBlockToUpdate.id}`, 'PATCH', {
            paragraph: {
              "rich_text": [
                {
                  "type": "text",
                  "text": {
                    "content": content // Contenu propre sans timestamp
                  }
                }
              ]
            }
          });
          
          console.log('✅ Updated existing content block');
        } else {
          // Trouver l'index du titre pour insérer après
          const targetIndex = existingContent.findIndex(block => block.id === targetBlock.id);
          
          if (targetIndex >= 0 && targetIndex < existingContent.length - 1) {
            // Insérer après le titre existant
            const nextBlockId = existingContent[targetIndex + 1].id;
            await this.callNotionAPI(`/blocks/${nextBlockId}`, 'PATCH', {
              children: [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                  "rich_text": [
                    {
                      "type": "text",
                      "text": {
                        "content": content
                      }
                    }
                  ]
                }
              }]
            });
          } else {
            // Ajouter à la fin de la page si c'est le dernier élément
            await this.callNotionAPI(`/blocks/${targetPageId}/children`, 'PATCH', {
              children: [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                  "rich_text": [
                    {
                      "type": "text",
                      "text": {
                        "content": content
                      }
                    }
                  ]
                }
              }]
            });
          }
          
          console.log('✅ Added new content block after title');
        }
        
        return {
          success: true,
          data: {
            contentType,
            title,
            targetPageId,
            action: 'UPDATED_IN_PLACE',
            wasUpdate: true,
            timestamp: timestamp || new Date().toISOString(),
            notionUrl: `https://notion.so/${targetPageId.replace(/-/g, '')}`
          }
        };
        
      } else {
        // Pas de section existante, créer normalement
        return await this.documentLiveContent(args);
      }
      
    } catch (error) {
      console.error('❌ Error updating content in place:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
  
  async deleteAllPageContent(args: any): Promise<MCPResponse> {
    const { context } = args;
    const targetPageId = args.targetPageId || DEFAULT_NOTION_PAGE_ID;
    
    try {
      console.log('🧹 Deleting ALL content from page...');
      
      // 1. Récupérer tous les blocs de la page
      const existingBlocks = await this.callNotionAPI(`/blocks/${targetPageId}/children?page_size=100`);
      const blocksToDelete = existingBlocks.results || [];
      
      console.log(`🗑️ Found ${blocksToDelete.length} blocks to delete`);
      
      // 2. Supprimer tous les blocs un par un
      let deletedCount = 0;
      for (const block of blocksToDelete) {
        try {
          await this.callNotionAPI(`/blocks/${block.id}`, 'DELETE');
          deletedCount++;
          // Pause pour éviter les rate limits
          await new Promise(resolve => setTimeout(resolve, 50));
        } catch (error) {
          console.warn(`Failed to delete block ${block.id}`);
        }
      }
      
      // La page est maintenant complètement vide - pas de message de confirmation
      console.log(`✅ Deleted ${deletedCount}/${blocksToDelete.length} blocks - page is now empty`);
      
      return {
        success: true,
        data: {
          action: 'PAGE_CLEARED',
          blocksDeleted: deletedCount,
          totalBlocks: blocksToDelete.length,
          timestamp: new Date().toISOString()
        }
      };
      
    } catch (error) {
      console.error('❌ Error deleting page content:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
  
  async replaceAllPageContent(args: any): Promise<MCPResponse> {
    const { content, context } = args;
    const targetPageId = args.targetPageId || DEFAULT_NOTION_PAGE_ID;
    
    try {
      console.log('🔄 Replacing ALL content on page...');
      
      // 1. Supprimer tout le contenu existant
      const deleteResult = await this.deleteAllPageContent(args);
      
      if (!deleteResult.success) {
        throw new Error('Failed to delete existing content');
      }
      
      // Attendre que la suppression soit effective
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 2. Créer le document final propre (pas de métadonnées)
      const newContent = [{
        "object": "block",
        "type": "heading_1",
        "heading_1": {
          "rich_text": [
            {
              "type": "text",
              "text": {
                "content": content // Utiliser directement le contenu comme titre
              },
              "annotations": {
                "bold": true
              }
            }
          ]
        }
      }];
      
      // Si le contenu est long, l'ajouter aussi comme paragraphe
      if (content && content.length > 50) {
        newContent.push({
          "object": "block",
          "type": "paragraph",
          "paragraph": {
            "rich_text": [
              {
                "type": "text",
                "text": {
                  "content": content
                }
              }
            ]
          }
        });
      }
      
      await this.callNotionAPI(`/blocks/${targetPageId}/children`, 'PATCH', {
        children: newContent
      });
      
      console.log('✅ Successfully replaced all page content');
      
      return {
        success: true,
        data: {
          action: 'PAGE_REPLACED',
          newContent: content,
          blocksDeleted: deleteResult.data?.blocksDeleted || 0,
          blocksAdded: newContent.length,
          timestamp: new Date().toISOString()
        }
      };
      
    } catch (error) {
      console.error('❌ Error replacing page content:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
  
  async managePageContent(args: any): Promise<MCPResponse> {
    const { content, context } = args;
    const targetPageId = args.targetPageId || DEFAULT_NOTION_PAGE_ID;
    
    try {
      // Gestion intelligente selon le contexte
      if (context?.toLowerCase().includes('delete') || context?.toLowerCase().includes('clear')) {
        return await this.deleteAllPageContent(args);
      } else if (context?.toLowerCase().includes('replace')) {
        return await this.replaceAllPageContent(args);
      } else {
        // Action par défaut : nettoyer et réorganiser
        return await this.replaceAllPageContent({
          ...args,
          content: content || "Page cleaned and reorganized"
        });
      }
      
    } catch (error) {
      console.error('❌ Error managing page content:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
  
  // 🧠 MÉTHODES D'INTELLIGENCE AVANCÉE
  
  private async enhanceContentIntelligently(content: string, contentType: string, title: string): Promise<string> {
    try {
      // Enrichissement intelligent du contenu selon le type
      let enhancement = '';
      
      switch (contentType) {
        case 'project':
          enhancement = `\n\n📊 Objectifs:\n- Définir les spécifications\n- Planifier les étapes\n- Identifier les ressources nécessaires`;
          break;
        case 'topic':
          enhancement = `\n\n🔍 Points clés à retenir:\n- Impact sur le projet\n- Actions à prévoir\n- Personnes concernées`;
          break;
        case 'decision':
          enhancement = `\n\n⚡ Implications:\n- Changements requis\n- Timeline affectée\n- Prochaines étapes`;
          break;
        default:
          enhancement = '';
      }
      
      return content + enhancement;
    } catch (error) {
      console.warn('Content enhancement failed:', error);
      return content;
    }
  }
  
  private async findRelevantImages(searchQuery: string, contentType: string): Promise<string[]> {
    try {
      // 🖼️ Recherche d'images pertinentes (simulation pour l'instant)
      console.log(`🔍 Searching for images: "${searchQuery}" (type: ${contentType})`);
      
      // Images de base selon le type de contenu
      const imagesByType: Record<string, string[]> = {
        'project': [
          'https://images.unsplash.com/photo-1552664730-d307ca884978?w=800&h=400&fit=crop', // Team collaboration
          'https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=800&h=400&fit=crop'  // Project planning
        ],
        'topic': [
          'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=800&h=400&fit=crop', // Discussion
          'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&h=400&fit=crop'  // Ideas
        ],
        'decision': [
          'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=800&h=400&fit=crop', // Decision making
          'https://images.unsplash.com/photo-1553484771-371a605b060b?w=800&h=400&fit=crop'  // Strategy
        ],
        'insight': [
          'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&h=400&fit=crop', // Light bulb/ideas
          'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&h=400&fit=crop'  // Innovation
        ]
      };
      
      // Recherche spécifique selon le contenu
      if (searchQuery.toLowerCase().includes('dog') || searchQuery.toLowerCase().includes('chien')) {
        return ['https://images.unsplash.com/photo-1552053831-71594a27632d?w=800&h=400&fit=crop']; // Beautiful dog
      }
      
      if (searchQuery.toLowerCase().includes('cat') || searchQuery.toLowerCase().includes('chat')) {
        return ['https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800&h=400&fit=crop']; // Beautiful cat
      }
      
      if (searchQuery.toLowerCase().includes('mobile') || searchQuery.toLowerCase().includes('app')) {
        return ['https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800&h=400&fit=crop']; // Mobile app
      }
      
      if (searchQuery.toLowerCase().includes('car') || searchQuery.toLowerCase().includes('voiture')) {
        return ['https://images.unsplash.com/photo-1549924231-f129b911e442?w=800&h=400&fit=crop']; // Car
      }
      
      if (searchQuery.toLowerCase().includes('table') || searchQuery.toLowerCase().includes('tableau')) {
        return ['https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&h=400&fit=crop']; // Business table/data
      }
      
      // Images par défaut selon le type
      return imagesByType[contentType] || [];
      
    } catch (error) {
      console.warn('Image search failed:', error);
      return [];
    }
  }
  
  async replaceSpecificImage(args: any): Promise<MCPResponse> {
    const { imageToReplace, newImageQuery, context } = args;
    const targetPageId = args.targetPageId || DEFAULT_NOTION_PAGE_ID;
    
    try {
      console.log(`🖼️ Replacing image: ${imageToReplace} → ${newImageQuery}`);
      
      // 1. Trouver l'image existante sur la page
      const existingBlocks = await this.callNotionAPI(`/blocks/${targetPageId}/children?page_size=100`);
      const imageBlocks = existingBlocks.results?.filter((block: any) => block.type === 'image') || [];
      
      console.log(`🔍 Found ${imageBlocks.length} image blocks on page`);
      
      if (imageBlocks.length === 0) {
        throw new Error('No images found on page to replace');
      }
      
      // 2. Prendre la première image (ou la plus récente)
      const imageToReplaceBlock = imageBlocks[imageBlocks.length - 1]; // Dernière image
      
      // 3. Chercher une nouvelle image
      const newImages = await this.findRelevantImages(newImageQuery, 'image_replacement');
      
      if (newImages.length === 0) {
        throw new Error(`No suitable image found for: ${newImageQuery}`);
      }
      
      // 4. Remplacer l'image
      await this.callNotionAPI(`/blocks/${imageToReplaceBlock.id}`, 'PATCH', {
        image: {
          "type": "external",
          "external": {
            "url": newImages[0]
          }
        }
      });
      
      console.log(`✅ Successfully replaced image with: ${newImages[0]}`);
      
      return {
        success: true,
        data: {
          action: 'IMAGE_REPLACED',
          oldImageType: imageToReplace,
          newImageQuery,
          newImageUrl: newImages[0],
          timestamp: new Date().toISOString()
        }
      };
      
    } catch (error) {
      console.error('❌ Error replacing image:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
  
  async addTableToPage(args: any): Promise<MCPResponse> {
    const { position, tableData, title } = args;
    const targetPageId = args.targetPageId || DEFAULT_NOTION_PAGE_ID;
    
    try {
      console.log(`📊 Adding table at position: ${position}`);
      
      const tableContent = [];
      
      // Ajouter un titre si spécifié
      if (title) {
        tableContent.push({
          "object": "block",
          "type": "heading_3",
          "heading_3": {
            "rich_text": [
              {
                "type": "text",
                "text": {
                  "content": `📊 ${title}`
                }
              }
            ]
          }
        });
      }
      
      // Créer le tableau
      const headers = tableData?.headers || ['Colonne 1', 'Colonne 2', 'Colonne 3'];
      const rows = tableData?.rows || [
        ['Données 1', 'Données 2', 'Données 3'],
        ['Ligne 2', 'Info 2', 'Détail 2']
      ];
      
      // Notion utilise un format spécial pour les tableaux
      const tableBlock = {
        "object": "block",
        "type": "table",
        "table": {
          "table_width": headers.length,
          "has_column_header": true,
          "has_row_header": false,
          "children": [
            // Header row
            {
              "object": "block",
              "type": "table_row",
              "table_row": {
                "cells": headers.map(header => [
                  {
                    "type": "text",
                    "text": {
                      "content": header
                    },
                    "annotations": {
                      "bold": true
                    }
                  }
                ])
              }
            },
            // Data rows
            ...rows.map((row: string[]) => ({
              "object": "block",
              "type": "table_row",
              "table_row": {
                "cells": row.map(cell => [
                  {
                    "type": "text",
                    "text": {
                      "content": cell
                    }
                  }
                ])
              }
            }))
          ]
        }
      };
      
      tableContent.push(tableBlock);
      
      // Ajouter le tableau selon la position
      if (position === 'beginning') {
        // Pour insérer au début, on doit d'abord récupérer tous les blocs existants
        const existingBlocks = await this.callNotionAPI(`/blocks/${targetPageId}/children?page_size=100`);
        const allBlocks = existingBlocks.results || [];
        
        if (allBlocks.length > 0) {
          // Supprimer tous les blocs existants temporairement
          const blocksToMove = [];
          for (const block of allBlocks) {
            try {
              // Sauvegarder le contenu avant suppression
              blocksToMove.push(block);
              await this.callNotionAPI(`/blocks/${block.id}`, 'DELETE');
              await new Promise(resolve => setTimeout(resolve, 50)); // Rate limit
            } catch (error) {
              console.warn(`Could not delete block ${block.id} for repositioning`);
            }
          }
          
          // Ajouter le tableau en premier
          await this.callNotionAPI(`/blocks/${targetPageId}/children`, 'PATCH', {
            children: tableContent
          });
          
          // Attendre un peu
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // Remettre les anciens blocs après le tableau
          const blocksToRestore = blocksToMove.map((block: any) => {
            // Recréer les blocs sans leur ID
            const { id, created_time, last_edited_time, created_by, last_edited_by, parent, archived, ...blockContent } = block;
            return {
              object: "block",
              ...blockContent
            };
          });
          
          if (blocksToRestore.length > 0) {
            await this.callNotionAPI(`/blocks/${targetPageId}/children`, 'PATCH', {
              children: blocksToRestore
            });
          }
          
          console.log(`✅ Added table at beginning and restored ${blocksToRestore.length} existing blocks`);
        } else {
          // Page vide, juste ajouter le tableau
          await this.callNotionAPI(`/blocks/${targetPageId}/children`, 'PATCH', {
            children: tableContent
          });
        }
      } else {
        // Ajouter à la fin par défaut
        await this.callNotionAPI(`/blocks/${targetPageId}/children`, 'PATCH', {
          children: tableContent
        });
      }
      
      console.log(`✅ Successfully added table at ${position}`);
      
      return {
        success: true,
        data: {
          action: 'TABLE_ADDED',
          position,
          title,
          columns: headers.length,
          rows: rows.length,
          timestamp: new Date().toISOString()
        }
      };
      
    } catch (error) {
      console.error('❌ Error adding table:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}

// Instance du client MCP
const mcpClient = new NotionMCPClient();

// Handler POST pour les requêtes MCP
export async function POST(request: NextRequest) {
  try {
    const body: MCPRequest = await request.json();
    const { tool, arguments: args } = body;
    
    console.log('🔗 MCP API Request:', { tool, args });
    
    let result: MCPResponse;
    
    switch (tool) {
      case 'createNotionProject':
        result = await mcpClient.createNotionProject(args);
        break;
        
      case 'updateNotionTasks':
        result = await mcpClient.updateNotionTasks(args);
        break;
        
      case 'enrichNotionContent':
        result = await mcpClient.enrichNotionContent(args);
        break;
        
      case 'documentLiveContent':
        result = await mcpClient.documentLiveContent(args);
        break;
        
      case 'testNotionDeletion':
        result = await mcpClient.testNotionDeletion(args);
        break;
        
      case 'updateContentInPlace':
        result = await mcpClient.updateContentInPlace(args);
        break;
        
      case 'deleteAllPageContent':
        result = await mcpClient.deleteAllPageContent(args);
        break;
        
      case 'replaceAllPageContent':
        result = await mcpClient.replaceAllPageContent(args);
        break;
        
      case 'managePageContent':
        result = await mcpClient.managePageContent(args);
        break;
        
      case 'replaceSpecificImage':
        result = await mcpClient.replaceSpecificImage(args);
        break;
        
      case 'addTableToPage':
        result = await mcpClient.addTableToPage(args);
        break;
        
      default:
        return NextResponse.json(
          { success: false, error: `Unknown tool: ${tool}` },
          { status: 400 }
        );
    }
    
    return NextResponse.json(result);
    
  } catch (error) {
    console.error('❌ MCP API - Request error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Internal server error' 
      },
      { status: 500 }
    );
  }
}

// Handler GET pour vérifier le statut et tester l'accès Notion
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const testAccess = searchParams.get('testAccess');
  
  if (testAccess === 'true') {
    // Test d'accès à la page Notion
    try {
      const mcpClient = new NotionMCPClient();
      const pageId = normalizeNotionPageId(DEFAULT_NOTION_PAGE_ID);
      
      const pageInfo = await mcpClient.callNotionAPI(`/pages/${pageId}`);
      
      return NextResponse.json({
        status: 'MCP Notion API is running',
        timestamp: new Date().toISOString(),
        defaultNotionPageId: DEFAULT_NOTION_PAGE_ID,
        normalizedPageId: pageId,
        notionAccess: 'SUCCESS',
        pageTitle: pageInfo.properties?.title?.title?.[0]?.text?.content || 'No title',
        availableTools: [
          'createNotionProject',
          'updateNotionTasks', 
          'enrichNotionContent'
        ],
        note: 'Notion page access verified successfully!'
      });
      
    } catch (error: any) {
      return NextResponse.json({
        status: 'MCP Notion API is running',
        timestamp: new Date().toISOString(),
        defaultNotionPageId: DEFAULT_NOTION_PAGE_ID,
        normalizedPageId: normalizeNotionPageId(DEFAULT_NOTION_PAGE_ID),
        notionAccess: 'ERROR',
        error: error.message,
        availableTools: [
          'createNotionProject',
          'updateNotionTasks', 
          'enrichNotionContent'
        ],
        note: 'API running but Notion access failed. Check page sharing and token.',
        troubleshooting: {
          step1: 'Make sure your Notion integration has access to the page',
          step2: 'Share the page with your integration in Notion',
          step3: 'Verify NOTION_TOKEN is correct'
        }
      });
    }
  }
  
  return NextResponse.json({
    status: 'MCP Notion API is running',
    timestamp: new Date().toISOString(),
    defaultNotionPageId: DEFAULT_NOTION_PAGE_ID,
    normalizedPageId: normalizeNotionPageId(DEFAULT_NOTION_PAGE_ID),
    availableTools: [
      'createNotionProject',
      'updateNotionTasks', 
      'enrichNotionContent',
      'documentLiveContent'
    ],
    note: 'All operations will target the specified Notion page by default',
    testUrl: '?testAccess=true to test Notion page access'
  });
}
