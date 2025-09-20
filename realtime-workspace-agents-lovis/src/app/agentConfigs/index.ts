import { multiAgentTaskScenario } from './multiAgentTaskSystem';
import type { RealtimeAgent } from '@openai/agents/realtime';

// Map of scenario key -> array of RealtimeAgent objects (single Notion Expert agent)
export const allAgentSets: Record<string, RealtimeAgent[]> = {
  multiAgentTaskManagement: multiAgentTaskScenario, // Contains the single Notion Expert agent
};

export const defaultAgentSetKey = 'multiAgentTaskManagement';
