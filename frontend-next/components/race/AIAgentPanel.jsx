'use client';

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';

const MODES = [
  { id: 'engineering', label: 'Engineering', icon: '🔧' },
  { id: 'strategy', label: 'Strategy', icon: '🎯' },
  { id: 'coach', label: 'Coach', icon: '👨‍🏫' },
  { id: 'fan', label: 'Fan', icon: '🎉' },
  { id: 'summary', label: 'Summary', icon: '📊' },
  { id: 'compare', label: 'Compare', icon: '⚖️' },
  { id: 'pit-decision', label: 'Pit Decision', icon: '🚨' }
];

export default function AIAgentPanel({ raceId, driverId, liveData }) {
  const [mode, setMode] = useState('engineering');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastLapData, setLastLapData] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (liveData) {
      setLastLapData(liveData);
    }
  }, [liveData]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post('http://localhost:3001/api/ai/analyze', {
        mode: mode,
        driver_twin: liveData?.driverTwin?.[driverId],
        race_twin: liveData?.raceTwin,
        lap_data: liveData?.liveData,
        events: [],
        user_query: input
      });

      // Format the analysis response based on mode
      let formattedContent = 'No response';
      const analysis = response.data.analysis;
      
      if (analysis) {
        if (typeof analysis === 'string') {
          formattedContent = analysis;
        } else if (typeof analysis === 'object') {
          // Format based on mode
          switch (mode) {
            case 'engineering':
              if (analysis.sections) {
                formattedContent = `🔧 ENGINEERING ANALYSIS\n\n` +
                  `📊 Executive Summary:\n${analysis.sections.executive_summary || 'N/A'}\n\n` +
                  `💡 Key Insights:\n${Array.isArray(analysis.sections.key_insights) ? analysis.sections.key_insights.join('\n') : analysis.sections.key_insights || 'N/A'}\n\n` +
                  `👤 Driver Twin:\n${typeof analysis.sections.driver_twin_interpretation === 'object' ? JSON.stringify(analysis.sections.driver_twin_interpretation, null, 2) : analysis.sections.driver_twin_interpretation || 'N/A'}\n\n` +
                  `🏁 Race Twin:\n${typeof analysis.sections.race_twin_interpretation === 'object' ? JSON.stringify(analysis.sections.race_twin_interpretation, null, 2) : analysis.sections.race_twin_interpretation || 'N/A'}\n\n` +
                  `🎯 Strategy Recommendations:\n${Array.isArray(analysis.sections.strategy_recommendation) ? analysis.sections.strategy_recommendation.join('\n') : analysis.sections.strategy_recommendation || 'N/A'}\n\n` +
                  `⚡ Action Items:\n${Array.isArray(analysis.sections.action_items) ? analysis.sections.action_items.join('\n') : analysis.sections.action_items || 'N/A'}`;
              } else {
                formattedContent = JSON.stringify(analysis, null, 2);
              }
              break;
            case 'strategy':
              formattedContent = `🎯 STRATEGY ANALYSIS\n\n` +
                `Recommendation: ${analysis.recommendation || 'N/A'}\n` +
                `Confidence: ${analysis.confidence || 'medium'}\n` +
                `Reasoning: ${typeof analysis.reasoning === 'string' ? analysis.reasoning : (Array.isArray(analysis.reasoning) ? analysis.reasoning.join('\n') : JSON.stringify(analysis.reasoning, null, 2))}\n` +
                (analysis.traffic_impact ? `\nTraffic Impact: ${JSON.stringify(analysis.traffic_impact, null, 2)}` : '') +
                (analysis.undercut_analysis ? `\nUndercut Analysis: ${JSON.stringify(analysis.undercut_analysis, null, 2)}` : '');
              break;
            case 'coach':
              formattedContent = `👨‍🏫 COACHING ANALYSIS\n\n` +
                `Strengths:\n${Array.isArray(analysis.strengths) ? analysis.strengths.join('\n') : analysis.strengths || 'N/A'}\n\n` +
                `Weaknesses:\n${Array.isArray(analysis.weaknesses) ? analysis.weaknesses.join('\n') : analysis.weaknesses || 'N/A'}\n\n` +
                `Improvements:\n${Array.isArray(analysis.improvements) ? analysis.improvements.join('\n') : analysis.improvements || 'N/A'}\n\n` +
                (analysis.consistency_analysis ? `Consistency: ${analysis.consistency_analysis}\n` : '');
              break;
            case 'fan':
              formattedContent = `🎉 FAN MODE\n\n` +
                `📰 ${analysis.headline || 'N/A'}\n\n` +
                `📖 Race Story:\n${analysis.race_story || 'N/A'}\n\n` +
                `⭐ Top Moments:\n${Array.isArray(analysis.top_moments) ? analysis.top_moments.join('\n') : analysis.top_moments || 'N/A'}\n\n` +
                `🏆 Driver Highlights:\n${Array.isArray(analysis.driver_highlights) ? analysis.driver_highlights.join('\n') : analysis.driver_highlights || 'N/A'}\n\n` +
                `📝 Wrap-up: ${analysis.final_wrapup || 'N/A'}`;
              break;
            case 'summary':
              formattedContent = `📊 RACE SUMMARY\n\n` +
                `Race Recap: ${analysis.race_recap || 'N/A'}\n\n` +
                `Key Stats:\n${typeof analysis.key_stats === 'object' ? JSON.stringify(analysis.key_stats, null, 2) : analysis.key_stats || 'N/A'}\n\n` +
                `Critical Moments:\n${Array.isArray(analysis.critical_moments) ? analysis.critical_moments.map(m => typeof m === 'object' ? JSON.stringify(m) : m).join('\n') : analysis.critical_moments || 'N/A'}`;
              break;
            case 'compare':
              formattedContent = `⚖️ DRIVER COMPARISON\n\n` +
                `Driver 1:\n${typeof analysis.driver_1 === 'object' ? JSON.stringify(analysis.driver_1, null, 2) : analysis.driver_1 || 'N/A'}\n\n` +
                `Driver 2:\n${typeof analysis.driver_2 === 'object' ? JSON.stringify(analysis.driver_2, null, 2) : analysis.driver_2 || 'N/A'}\n\n` +
                `Comparison:\n${typeof analysis.comparison === 'object' ? JSON.stringify(analysis.comparison, null, 2) : analysis.comparison || 'N/A'}\n\n` +
                `Winner Analysis: ${analysis.winner_analysis || 'N/A'}`;
              break;
            case 'pit-decision':
              formattedContent = `🚨 PIT DECISION\n\n` +
                `Decision: ${analysis.decision || 'N/A'}\n` +
                `Confidence: ${analysis.confidence || 'medium'}\n\n` +
                `Reasoning:\n${Array.isArray(analysis.reasoning) ? analysis.reasoning.join('\n') : analysis.reasoning || 'N/A'}\n\n` +
                (analysis.factors ? `Factors:\n${JSON.stringify(analysis.factors, null, 2)}` : '');
              break;
            default:
              formattedContent = JSON.stringify(analysis, null, 2);
          }
        }
      } else if (response.data.message) {
        formattedContent = response.data.message;
      }

      const aiMessage = {
        role: 'assistant',
        content: formattedContent,
        timestamp: new Date(),
        mode: mode
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('AI request failed:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const autoInsertData = () => {
    if (lastLapData) {
      const dataText = `Current lap: ${lastLapData.lap || 'N/A'}, ` +
        `Position: ${lastLapData.liveData?.positions?.[0] || 'N/A'}, ` +
        `Lap time: ${lastLapData.liveData?.lap_times?.[0] || 'N/A'}s`;
      setInput(dataText);
    }
  };

  const inspectLastLap = () => {
    if (lastLapData) {
      const inspection = {
        role: 'system',
        content: `Last Lap Data:\n${JSON.stringify(lastLapData, null, 2)}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, inspection]);
    }
  };

  return (
    <div style={{
      border: '2px solid #ddd',
      borderRadius: 8,
      padding: 20,
      backgroundColor: 'white',
      height: '100%',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <h2 style={{ marginTop: 0, color: '#333', marginBottom: 15 }}>🤖 AI Race Engineer</h2>

      {/* Mode Selector */}
      <div style={{ marginBottom: 15 }}>
        <div style={{ fontSize: '14px', color: '#666', marginBottom: 8 }}>Mode:</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {MODES.map(m => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              style={{
                padding: '8px 12px',
                border: `2px solid ${mode === m.id ? '#4CAF50' : '#ddd'}`,
                borderRadius: 6,
                backgroundColor: mode === m.id ? '#e8f5e9' : 'white',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: mode === m.id ? 'bold' : 'normal'
              }}
            >
              {m.icon} {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div style={{ marginBottom: 15, display: 'flex', gap: 10 }}>
        <button
          onClick={autoInsertData}
          style={{
            padding: '6px 12px',
            border: '1px solid #4CAF50',
            borderRadius: 4,
            backgroundColor: '#e8f5e9',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          📋 Auto-Insert Data
        </button>
        <button
          onClick={inspectLastLap}
          style={{
            padding: '6px 12px',
            border: '1px solid #2196F3',
            borderRadius: 4,
            backgroundColor: '#e3f2fd',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          🔍 Inspect Last Lap
        </button>
      </div>

      {/* Chat Window */}
      <div style={{
        flex: 1,
        border: '1px solid #ddd',
        borderRadius: 6,
        padding: 15,
        marginBottom: 15,
        overflowY: 'auto',
        backgroundColor: '#fafafa',
        minHeight: 300
      }}>
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#999', padding: 20 }}>
            Start a conversation with the AI Race Engineer...
          </div>
        ) : (
          messages.map((msg, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                marginBottom: 15,
                padding: 10,
                borderRadius: 6,
                backgroundColor: msg.role === 'user' ? '#e3f2fd' : 
                                msg.error ? '#ffebee' : 'white',
                border: msg.error ? '1px solid #f44336' : '1px solid #ddd'
              }}
            >
              <div style={{ fontSize: '12px', color: '#666', marginBottom: 5 }}>
                {msg.role === 'user' ? 'You' : 'AI Race Engineer'} 
                {msg.mode && ` (${msg.mode})`}
                {' - '}
                {msg.timestamp.toLocaleTimeString()}
              </div>
              <div style={{ 
                whiteSpace: 'pre-wrap', 
                wordBreak: 'break-word',
                color: msg.error ? '#d32f2f' : '#333'
              }}>
                {msg.content}
              </div>
            </motion.div>
          ))
        )}
        {loading && (
          <div style={{ textAlign: 'center', color: '#999', padding: 10 }}>
            AI is thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{ display: 'flex', gap: 10 }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask the AI Race Engineer..."
          style={{
            flex: 1,
            padding: '10px 15px',
            border: '1px solid #ddd',
            borderRadius: 6,
            fontSize: '14px'
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          style={{
            padding: '10px 20px',
            border: 'none',
            borderRadius: 6,
            backgroundColor: loading || !input.trim() ? '#ccc' : '#4CAF50',
            color: 'white',
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            fontWeight: 'bold'
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}

