#!/usr/bin/env node

/**
 * 🔍 Connection Diagnostic Script
 * 
 * This script helps diagnose connection issues with the Notion Expert agent system.
 */

console.log('🔍 Notion Expert - Connection Diagnostic\n');

// Check environment setup
console.log('1. Environment Check:');
require('dotenv').config({ path: './env' });

if (process.env.OPENAI_API_KEY) {
  if (process.env.OPENAI_API_KEY === 'your_openai_api_key_here') {
    console.log('   ❌ OPENAI_API_KEY is set to placeholder value');
    console.log('   🔧 Please update the "env" file with your real OpenAI API key');
  } else if (process.env.OPENAI_API_KEY.startsWith('sk-')) {
    console.log('   ✅ OPENAI_API_KEY is set and looks valid');
  } else {
    console.log('   ⚠️  OPENAI_API_KEY is set but doesn\'t start with "sk-"');
  }
} else {
  console.log('   ❌ OPENAI_API_KEY is not set');
  console.log('   🔧 Please add your OpenAI API key to the "env" file');
}

console.log('\n2. Configuration Check:');
try {
  const { multiAgentTaskScenario, multiAgentSystemName } = require('./src/app/agentConfigs/multiAgentTaskSystem.ts');
  console.log('   ✅ Agent configuration loaded successfully');
  console.log(`   📝 System name: ${multiAgentSystemName}`);
  console.log(`   🤖 Agents count: ${multiAgentTaskScenario?.length || 0}`);
  
  if (multiAgentTaskScenario && multiAgentTaskScenario[0]) {
    console.log(`   🎯 Agent name: ${multiAgentTaskScenario[0].name}`);
  }
} catch (error) {
  console.log('   ❌ Error loading agent configuration:', error.message);
}

console.log('\n3. API Test:');
if (process.env.OPENAI_API_KEY && process.env.OPENAI_API_KEY !== 'your_openai_api_key_here') {
  console.log('   🧪 Testing OpenAI API connection...');
  
  fetch('https://api.openai.com/v1/realtime/sessions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-4o-realtime-preview-2025-06-03',
    }),
  })
  .then(response => {
    if (response.ok) {
      console.log('   ✅ OpenAI API connection successful');
      return response.json();
    } else {
      console.log(`   ❌ OpenAI API error: ${response.status} ${response.statusText}`);
      return response.text().then(text => {
        console.log(`   📝 Error details: ${text}`);
      });
    }
  })
  .then(data => {
    if (data && data.client_secret) {
      console.log('   ✅ Session created successfully');
    }
  })
  .catch(error => {
    console.log('   ❌ Network error:', error.message);
  });
} else {
  console.log('   ⏭️  Skipping API test (no valid API key)');
}

console.log('\n4. Next Steps:');
console.log('   🔧 If API key is missing: Get it from https://platform.openai.com/account/api-keys');
console.log('   🔧 If API key is invalid: Check it\'s copied correctly and has Realtime API access');
console.log('   🚀 Once fixed: npm run dev and try connecting again');

console.log('\n🎯 The Notion Expert agent should connect silently and work in the background!');
