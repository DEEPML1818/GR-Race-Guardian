/**
 * Gemini 2.0 Flash Integration for GR Race Guardian AI
 * 
 * Provides intelligent AI responses using Google Gemini 2.0 Flash
 */

const { GoogleGenerativeAI } = require('@google/generative-ai');

class GeminiAIService {
  constructor() {
    this.apiKey = process.env.GEMINI_API_KEY || '';
    this.model = null;
    this.genAI = null;
    this.initialized = false;
    
    if (this.apiKey) {
      try {
        this.genAI = new GoogleGenerativeAI(this.apiKey);
        this.model = this.genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });
        this.initialized = true;
        console.log('[Gemini] AI service initialized successfully with tool-calling support');
      } catch (error) {
        console.warn('[Gemini] Failed to initialize:', error.message);
        this.initialized = false;
      }
    } else {
      console.warn('[Gemini] GEMINI_API_KEY not set. AI will use template-based responses.');
    }
  }

  /**
   * Generate AI response for race engineering analysis
   * Supports tool-calling for advanced AI agent functionality
   */
  async generateResponse(mode, data, userQuery = null, enableToolCalling = true) {
    if (!this.initialized || !this.model) {
      return null; // Fall back to template-based responses
    }

    try {
      const prompt = this._buildPrompt(mode, data, userQuery);
      
      // Configure tool-calling if enabled
      const tools = enableToolCalling ? this._getToolDefinitions() : undefined;
      
      const generationConfig = {
        temperature: 0.7,
        topK: 40,
        topP: 0.95,
        maxOutputTokens: 2048,
      };
      
      // Create model with tools if available
      const modelWithTools = tools ? 
        this.genAI.getGenerativeModel({ 
          model: 'gemini-2.0-flash-exp',
          tools: tools,
          generationConfig: generationConfig
        }) :
        this.model;
      
      const result = await modelWithTools.generateContent(prompt);
      const response = await result.response;
      
      // Check if response contains function calls
      const functionCalls = response.functionCalls();
      if (functionCalls && functionCalls.length > 0) {
        // Handle function calls
        return {
          text: response.text(),
          functionCalls: functionCalls,
          hasToolCalls: true
        };
      }
      
      return response.text();
    } catch (error) {
      console.error('[Gemini] Error generating response:', error.message);
      return null; // Fall back to template-based
    }
  }
  
  /**
   * Get tool definitions for Gemini function calling
   */
  _getToolDefinitions() {
    return [
      {
        functionDeclarations: [
          {
            name: 'getDriverTwin',
            description: 'Fetches the Digital Driver Twin data for a specific driver. Returns pace vector, consistency index, aggression score, sector strengths, and degradation profile.',
            parameters: {
              type: 'object',
              properties: {
                driverId: {
                  type: 'string',
                  description: 'The unique identifier of the driver (e.g., "driver_1", "HAM")'
                }
              },
              required: ['driverId']
            }
          },
          {
            name: 'getRaceTwin',
            description: 'Fetches the Digital Race Twin (Monte Carlo simulation) data. Returns expected finishing positions, pit recommendations, tire cliff predictions, traffic simulation, and undercut outcomes.',
            parameters: {
              type: 'object',
              properties: {
                raceId: {
                  type: 'string',
                  description: 'The unique identifier of the race (e.g., "race_1", "monaco_2024")'
                }
              },
              required: ['raceId']
            }
          },
          {
            name: 'getPitDecision',
            description: 'Gets an advanced AI pit decision recommendation with multi-factor analysis. Returns decision (PIT_NOW/PIT_LATER/EXTEND_STINT), confidence score, factor breakdown, and reasoning.',
            parameters: {
              type: 'object',
              properties: {
                driverId: {
                  type: 'string',
                  description: 'The unique identifier of the driver'
                },
                currentLap: {
                  type: 'number',
                  description: 'Current lap number in the race'
                },
                tireAge: {
                  type: 'number',
                  description: 'Current tire age in laps'
                },
                tireCompound: {
                  type: 'string',
                  description: 'Current tire compound (SOFT, MEDIUM, HARD)',
                  enum: ['SOFT', 'MEDIUM', 'HARD']
                },
                position: {
                  type: 'number',
                  description: 'Current race position'
                },
                raceId: {
                  type: 'string',
                  description: 'The unique identifier of the race'
                }
              },
              required: ['driverId', 'currentLap', 'tireAge', 'tireCompound', 'position', 'raceId']
            }
          },
          {
            name: 'runMonteCarlo',
            description: 'Runs a Monte Carlo race simulation to predict race outcomes. Returns expected finishing positions, win probabilities, pit strategy recommendations, and tire cliff predictions.',
            parameters: {
              type: 'object',
              properties: {
                raceId: {
                  type: 'string',
                  description: 'The unique identifier of the race'
                },
                drivers: {
                  type: 'array',
                  description: 'Array of driver data with positions, lap times, tire ages, etc.',
                  items: {
                    type: 'object'
                  }
                },
                totalLaps: {
                  type: 'number',
                  description: 'Total number of laps in the race'
                },
                currentLap: {
                  type: 'number',
                  description: 'Current lap number'
                },
                numSimulations: {
                  type: 'number',
                  description: 'Number of Monte Carlo simulations to run (100-500)',
                  default: 500
                }
              },
              required: ['raceId', 'drivers', 'totalLaps', 'currentLap']
            }
          },
          {
            name: 'evaluateSectors',
            description: 'Evaluates sector-by-sector performance for a driver. Returns sector strengths, weaknesses, average sector times, and improvement recommendations.',
            parameters: {
              type: 'object',
              properties: {
                driverId: {
                  type: 'string',
                  description: 'The unique identifier of the driver'
                },
                sectorTimes: {
                  type: 'array',
                  description: 'Array of sector time objects with S1, S2, S3 values',
                  items: {
                    type: 'object',
                    properties: {
                      S1: { type: 'number' },
                      S2: { type: 'number' },
                      S3: { type: 'number' }
                    }
                  }
                }
              },
              required: ['driverId']
            }
          }
        ]
      }
    ];
  }
  
  /**
   * Check if Gemini supports tool-calling
   */
  supportsToolCalling() {
    return this.initialized && this.model !== null;
  }

  /**
   * Build prompt for Gemini based on mode and data
   */
  _buildPrompt(mode, data, userQuery) {
    const { driver_twin, race_twin, lap_data, events, weather, compare_drivers } = data;

    let prompt = `You are GR-RACE-GUARDIAN-AI, a professional motorsport race engineer AI assistant. `;
    prompt += `You analyze real-time race data and provide actionable insights. `;
    prompt += `NEVER hallucinate data - only analyze what's provided. Use professional motorsport terminology.\n\n`;

    // Mode-specific instructions
    switch (mode.toLowerCase()) {
      case 'engineering':
        prompt += `MODE: Engineering Analysis\n`;
        prompt += `Provide a comprehensive race engineering analysis with:\n`;
        prompt += `1. Executive Summary (2-3 sentences)\n`;
        prompt += `2. Key Insights (bullet points)\n`;
        prompt += `3. Driver Twin Interpretation (pace, consistency, aggression, sectors)\n`;
        prompt += `4. Race Twin Interpretation (Monte Carlo predictions, pit recommendations)\n`;
        prompt += `5. Tire & Pace Analysis (degradation trends, pace dropoff)\n`;
        prompt += `6. Strategy Recommendation (pit windows, tire compounds)\n`;
        prompt += `7. Sector Breakdown (strengths and weaknesses)\n`;
        prompt += `8. Risk Factors & Confidence\n`;
        prompt += `9. Action Items (specific recommendations)\n\n`;
        break;

      case 'strategy':
        prompt += `MODE: Strategy Analysis\n`;
        prompt += `Provide real-time tactical strategy recommendations:\n`;
        prompt += `- Pit window analysis\n`;
        prompt += `- Undercut vs overcut opportunities\n`;
        prompt += `- Tire degradation impact\n`;
        prompt += `- Traffic window analysis\n`;
        prompt += `- Risk assessment\n\n`;
        break;

      case 'coach':
        prompt += `MODE: Driver Coaching\n`;
        prompt += `Provide driver improvement analysis:\n`;
        prompt += `- Sector-by-sector strengths and weaknesses\n`;
        prompt += `- Consistency improvements\n`;
        prompt += `- Specific technical recommendations\n`;
        prompt += `- Lap time optimization opportunities\n\n`;
        break;

      case 'fan':
        prompt += `MODE: Fan Commentary\n`;
        prompt += `Provide exciting, engaging race commentary:\n`;
        prompt += `- Headline moment\n`;
        prompt += `- Race story narrative\n`;
        prompt += `- Top moments highlight\n`;
        prompt += `- Driver highlights\n`;
        prompt += `- Final wrap-up\n\n`;
        break;

      case 'summary':
        prompt += `MODE: Race Summary\n`;
        prompt += `Provide a comprehensive race recap:\n`;
        prompt += `- Race overview\n`;
        prompt += `- Key statistics\n`;
        prompt += `- Critical moments\n`;
        prompt += `- Final results analysis\n\n`;
        break;

      case 'compare':
        prompt += `MODE: Driver Comparison\n`;
        prompt += `Provide side-by-side driver comparison:\n`;
        prompt += `- Pace comparison\n`;
        prompt += `- Consistency comparison\n`;
        prompt += `- Sector strengths comparison\n`;
        prompt += `- Overall assessment\n\n`;
        break;

      case 'pit-decision':
        prompt += `MODE: Pit Decision Analysis\n`;
        prompt += `Provide pit stop decision recommendation:\n`;
        prompt += `- Decision: PIT_NOW, PIT_LATER, or EXTEND_STINT\n`;
        prompt += `- Confidence level (high/medium/low)\n`;
        prompt += `- Detailed reasoning\n`;
        prompt += `- Factor analysis (degradation, traffic, tire age)\n\n`;
        break;
    }

    // Add data context
    prompt += `RACE DATA:\n`;
    
    if (driver_twin) {
      prompt += `Driver Twin:\n`;
      prompt += `- Pace Vector: ${driver_twin.pace_vector || 'N/A'}\n`;
      prompt += `- Consistency Index: ${driver_twin.consistency_index || 'N/A'}\n`;
      prompt += `- Aggression Score: ${driver_twin.aggression_score || 'N/A'}\n`;
      if (driver_twin.sector_strengths) {
        prompt += `- Sector Strengths: S1=${driver_twin.sector_strengths.S1 || 'N/A'}, S2=${driver_twin.sector_strengths.S2 || 'N/A'}, S3=${driver_twin.sector_strengths.S3 || 'N/A'}\n`;
      }
      prompt += `\n`;
    }

    if (race_twin) {
      prompt += `Race Twin (Monte Carlo Simulation):\n`;
      if (race_twin.expected_finishing_positions) {
        prompt += `- Expected Finishing Positions: ${JSON.stringify(race_twin.expected_finishing_positions)}\n`;
      }
      if (race_twin.pit_recommendations) {
        prompt += `- Pit Recommendations: ${JSON.stringify(race_twin.pit_recommendations)}\n`;
      }
      if (race_twin.tire_cliff_prediction) {
        prompt += `- Tire Cliff Prediction: Lap ${race_twin.tire_cliff_prediction.lap || 'N/A'}\n`;
      }
      prompt += `\n`;
    }

    if (lap_data && Array.isArray(lap_data) && lap_data.length > 0) {
      prompt += `Recent Lap Data:\n`;
      const recentLaps = lap_data.slice(-5);
      recentLaps.forEach((lap, idx) => {
        prompt += `- Lap ${lap.lap || idx + 1}: ${lap.lap_time || 'N/A'}s\n`;
      });
      prompt += `\n`;
    }

    if (weather) {
      prompt += `Weather Conditions:\n`;
      prompt += `- Temperature: ${weather.temperature || 'N/A'}°C\n`;
      prompt += `- Condition: ${weather.condition || 'N/A'}\n`;
      prompt += `\n`;
    }

    if (compare_drivers && Array.isArray(compare_drivers) && compare_drivers.length === 2) {
      prompt += `Driver Comparison:\n`;
      prompt += `Driver 1: ${JSON.stringify(compare_drivers[0])}\n`;
      prompt += `Driver 2: ${JSON.stringify(compare_drivers[1])}\n`;
      prompt += `\n`;
    }

    if (userQuery) {
      prompt += `USER QUESTION: ${userQuery}\n\n`;
    }

    prompt += `Provide a detailed, professional analysis based on the above data. `;
    prompt += `Be specific, actionable, and use motorsport terminology. `;
    prompt += `Format your response clearly with sections and bullet points where appropriate.`;

    return prompt;
  }

  /**
   * Check if Gemini is available
   */
  isAvailable() {
    return this.initialized && this.model !== null;
  }
}

module.exports = new GeminiAIService();

