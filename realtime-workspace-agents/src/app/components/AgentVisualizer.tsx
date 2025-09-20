"use client";
import React, { useState, useEffect } from 'react';
import AgentSimulator from './AgentSimulator';

// Types pour le visualisateur
interface AgentActivity {
  agentId: string;
  agentName: string;
  status: 'idle' | 'listening' | 'processing' | 'transmitting' | 'completed';
  lastAction: string;
  timestamp: string;
  data?: any;
}

interface DataTransmission {
  id: string;
  from: string;
  to: string[];
  data: any;
  timestamp: string;
  status: 'pending' | 'transmitted' | 'received' | 'processed';
}

interface AgentVisualizerProps {
  isVisible: boolean;
}

const AgentVisualizer: React.FC<AgentVisualizerProps> = ({ isVisible }) => {
  const [agents, setAgents] = useState<AgentActivity[]>([
    {
      agentId: 'notionExpert',
      agentName: 'Notion Expert',
      status: 'idle',
      lastAction: 'Waiting silently...',
      timestamp: new Date().toISOString()
    }
  ]);

  const [transmissions, setTransmissions] = useState<DataTransmission[]>([]);
  const [logs, setLogs] = useState<string[]>([]);

  // Écouter les événements du système
  useEffect(() => {
    const handleAgentEvent = (event: CustomEvent) => {
      const { agentId, action, status, data } = event.detail;
      
      setAgents(prev => prev.map(agent => 
        agent.agentId === agentId 
          ? {
              ...agent,
              status: status || agent.status,
              lastAction: action,
              timestamp: new Date().toISOString(),
              data: data
            }
          : agent
      ));

      // Ajouter au log
      const logEntry = `[${new Date().toLocaleTimeString()}] ${agentId}: ${action}`;
      setLogs(prev => [logEntry, ...prev.slice(0, 19)]); // Garder les 20 derniers logs
    };

    const handleTransmissionEvent = (event: CustomEvent) => {
      const transmission = event.detail;
      setTransmissions(prev => [transmission, ...prev.slice(0, 9)]); // Garder les 10 dernières transmissions
    };

    window.addEventListener('agentActivity', handleAgentEvent as EventListener);
    window.addEventListener('dataTransmission', handleTransmissionEvent as EventListener);

    return () => {
      window.removeEventListener('agentActivity', handleAgentEvent as EventListener);
      window.removeEventListener('dataTransmission', handleTransmissionEvent as EventListener);
    };
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'listening': return 'bg-blue-500';
      case 'processing': return 'bg-yellow-500';
      case 'transmitting': return 'bg-purple-500';
      case 'completed': return 'bg-green-500';
      default: return 'bg-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'listening': return '👂';
      case 'processing': return '⚙️';
      case 'transmitting': return '📤';
      case 'completed': return '✅';
      default: return '⏸️';
    }
  };

  if (!isVisible) return null;

  return (
    <div className="bg-white border-l border-gray-200 w-96 h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-800">
          🔍 Agent Monitor
        </h2>
        <p className="text-sm text-gray-600">Real-time activity</p>
      </div>

      {/* Simulateur pour tests */}
      <div className="p-4 border-b border-gray-200">
        <AgentSimulator />
      </div>

      {/* Agents Status */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-md font-medium text-gray-700 mb-3">Agent Status</h3>
        <div className="space-y-3">
          {agents.map((agent) => (
            <div key={agent.agentId} className="flex items-start space-x-3">
              <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)} mt-1 flex-shrink-0`}></div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-800">
                    {getStatusIcon(agent.status)} {agent.agentName}
                  </span>
                  <span className="text-xs text-gray-500 capitalize">
                    {agent.status}
                  </span>
                </div>
                <p className="text-xs text-gray-600 truncate">
                  {agent.lastAction}
                </p>
                <p className="text-xs text-gray-400">
                  {new Date(agent.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Data Flow Visualization */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-md font-medium text-gray-700 mb-3">Data Flow</h3>
        <div className="space-y-2">
          {transmissions.slice(0, 3).map((transmission) => (
            <div key={transmission.id} className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium">{transmission.from}</span>
                  <span className="text-gray-400">→</span>
                  <span className="text-sm">{transmission.to.join(', ')}</span>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs ${
                  transmission.status === 'processed' ? 'bg-green-100 text-green-800' :
                  transmission.status === 'transmitted' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {transmission.status}
                </span>
              </div>
              <p className="text-xs text-gray-600 mt-1">
                {new Date(transmission.timestamp).toLocaleTimeString()}
              </p>
            </div>
          ))}
          {transmissions.length === 0 && (
            <p className="text-sm text-gray-500 italic">No recent transmissions</p>
          )}
        </div>
      </div>

      {/* Live Logs */}
      <div className="flex-1 p-4 overflow-hidden flex flex-col">
        <h3 className="text-md font-medium text-gray-700 mb-3">Live Logs</h3>
        <div className="flex-1 bg-gray-900 rounded-lg p-3 overflow-y-auto">
          <div className="space-y-1">
            {logs.length === 0 ? (
              <p className="text-gray-400 text-sm">Waiting for activity...</p>
            ) : (
              logs.map((log, index) => (
                <div key={index} className="text-sm font-mono text-green-400">
                  {log}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <div className="text-lg font-bold text-gray-800">
              {agents.filter(a => a.status !== 'idle').length}
            </div>
            <div className="text-xs text-gray-600">Active Agents</div>
          </div>
          <div>
            <div className="text-lg font-bold text-gray-800">
              {transmissions.length}
            </div>
            <div className="text-xs text-gray-600">Transmissions</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentVisualizer;
