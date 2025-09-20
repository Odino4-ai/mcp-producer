"use client";
import React from 'react';

// Composant pour simuler l'activité des agents (pour les tests)
const AgentSimulator: React.FC = () => {
  const simulateProjectCreation = () => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('agentActivity', {
        detail: {
          agentId: 'notionExpert',
          action: 'New project detected: "Car Project"',
          status: 'processing',
          data: { projectName: 'Car Project' }
        }
      }));

      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('agentActivity', {
          detail: {
            agentId: 'notionExpert',
            action: 'Project "Car Project" created with complete structure',
            status: 'completed',
            data: { 
              projectId: 'proj_' + Date.now(),
              databases: 3,
              folders: 6,
              team: ['Alice', 'Bob', 'Charlie']
            }
          }
        }));
      }, 2000);
    }
  };

  const simulateTodoUpdate = () => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('agentActivity', {
        detail: {
          agentId: 'notionExpert',
          action: 'Updating to-do list...',
          status: 'processing',
          data: {}
        }
      }));

      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('agentActivity', {
          detail: {
            agentId: 'notionExpert',
            action: 'To-do list updated: +3 new tasks',
            status: 'completed',
            data: { tasksAdded: 3, assignees: ['Alice', 'Bob'] }
          }
        }));
      }, 1500);
    }
  };

  const simulateContentEnrichment = () => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('agentActivity', {
        detail: {
          agentId: 'notionExpert',
          action: 'Enriching content...',
          status: 'processing',
          data: {}
        }
      }));

      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('agentActivity', {
          detail: {
            agentId: 'notionExpert',
            action: 'Content enriched: meeting notes added',
            status: 'completed',
            data: { type: 'meeting_notes', pages: 2 }
          }
        }));
      }, 1200);
    }
  };

  const simulateFullFlow = () => {
    simulateProjectCreation();
    setTimeout(() => {
      simulateTodoUpdate();
    }, 3000);
    setTimeout(() => {
      simulateContentEnrichment();
    }, 5000);
  };

  const resetAgent = () => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('agentActivity', {
        detail: {
          agentId: 'notionExpert',
          action: 'Waiting silently...',
          status: 'idle',
          data: {}
        }
      }));
    }
  };

  return (
    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg mb-4">
      <h3 className="text-md font-semibold text-yellow-800 mb-3">
        🧪 Agent Simulator (Test)
      </h3>
      <div className="flex flex-wrap gap-2">
        <button
          onClick={simulateFullFlow}
          className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 text-sm"
        >
          🚀 Full Flow
        </button>
        <button
          onClick={simulateProjectCreation}
          className="px-3 py-1 bg-green-500 text-white rounded-md hover:bg-green-600 text-sm"
        >
          📝 Create Project
        </button>
        <button
          onClick={simulateTodoUpdate}
          className="px-3 py-1 bg-purple-500 text-white rounded-md hover:bg-purple-600 text-sm"
        >
          📋 To-Do List
        </button>
        <button
          onClick={simulateContentEnrichment}
          className="px-3 py-1 bg-orange-500 text-white rounded-md hover:bg-orange-600 text-sm"
        >
          ⚡ Enrich
        </button>
        <button
          onClick={resetAgent}
          className="px-3 py-1 bg-gray-500 text-white rounded-md hover:bg-gray-600 text-sm"
        >
          🔄 Reset
        </button>
      </div>
      <p className="text-xs text-yellow-700 mt-2">
        Test the silent Notion Expert agent - it works in the background!
      </p>
    </div>
  );
};

export default AgentSimulator;
