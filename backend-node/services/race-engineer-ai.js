/**
 * GR-RACE-GUARDIAN-AI
 * 
 * Central intelligence agent of the GR Race Guardian platform.
 * Operates as a unified race engineer, data analyst, strategy director, and driver coach.
 * 
 * BEHAVIOR:
 * - NEVER hallucinates data - only analyzes what's provided
 * - Speaks like a real race engineer
 * - Uses professional motorsport terminology
 * - Provides actionable, data-driven insights
 * - Powered by Gemini 2.0 Flash (with template fallback)
 */

const geminiAI = require('./gemini-ai');
const responseTemplates = require('./ai-response-templates');

class RaceEngineerAI {
  constructor() {
    this.name = "GR-RACE-GUARDIAN-AI";
    this.version = "2.0.0";
    this.role = "Race Engineer AI Core";
    this.geminiEnabled = geminiAI.isAvailable();
    this.tools = {
      getDriverTwin: this._toolGetDriverTwin.bind(this),
      getRaceTwin: this._toolGetRaceTwin.bind(this),
      getPitDecision: this._toolGetPitDecision.bind(this),
      runMonteCarlo: this._toolRunMonteCarlo.bind(this),
      evaluateSectors: this._toolEvaluateSectors.bind(this)
    };
    
    if (this.geminiEnabled) {
      console.log('[AI] Gemini 2.0 Flash enabled for intelligent responses');
    } else {
      console.log('[AI] Using template-based responses (Gemini not configured)');
    }
  }

  /**
   * Main analysis function
   * @param {Object} data - Input data containing driver twins, race twins, lap data, etc.
   * @param {string} mode - Analysis mode: engineering, strategy, coach, fan, summary, compare, pit-decision
   * @param {string} userQuery - Optional user query/question
   * @returns {Object} Analysis output
   */
  async analyze(data, mode = 'engineering', userQuery = null) {
    // Validate data exists
    if (!data || Object.keys(data).length === 0) {
      // AI Fallback: Provide helpful message when data is missing
      return this._handleMissingData(mode, userQuery);
    }
    
    // Check data completeness
    const dataCompleteness = this._checkDataCompleteness(data, mode);
    if (dataCompleteness.score < 0.5) {
      // Data is incomplete - use fallback with warning
      return this._handleIncompleteData(data, mode, userQuery, dataCompleteness);
    }

    const {
      driver_twin,
      race_twin,
      lap_data,
      events,
      weather,
      compare_drivers
    } = data;

    // Try Gemini first, fall back to templates
    if (this.geminiEnabled && userQuery) {
      try {
        const geminiResponse = await geminiAI.generateResponse(mode, data, userQuery, true);
        if (geminiResponse) {
          // Check if response contains function calls
          if (geminiResponse.hasToolCalls && geminiResponse.functionCalls) {
            // Execute tool calls
            const toolResults = await this._executeToolCalls(geminiResponse.functionCalls, data);
            
            // Generate follow-up response with tool results
            const followUpResponse = await geminiAI.generateResponse(
              mode, 
              { ...data, toolResults }, 
              userQuery + ' [Tool results provided]',
              false // Disable tool calling for follow-up
            );
            
            return {
              mode,
              timestamp: new Date().toISOString(),
              gemini_powered: true,
              tool_calling_enabled: true,
              tool_calls: geminiResponse.functionCalls,
              tool_results: toolResults,
              response: followUpResponse || geminiResponse.text,
              template_fallback: false
            };
          }
          
          return {
            mode,
            timestamp: new Date().toISOString(),
            gemini_powered: true,
            tool_calling_enabled: true,
            response: typeof geminiResponse === 'string' ? geminiResponse : geminiResponse.text,
            template_fallback: false
          };
        }
      } catch (error) {
        console.warn('[AI] Gemini failed, using template fallback:', error.message);
      }
    }

    // Fall back to template-based analysis
    let templateResult;
    switch (mode.toLowerCase()) {
      case 'engineering':
        templateResult = responseTemplates.engineeringTemplate(driver_twin, race_twin, lap_data, weather);
        break;
      case 'strategy':
        templateResult = responseTemplates.strategyTemplate(race_twin, lap_data, events, weather);
        break;
      case 'coach':
        templateResult = responseTemplates.coachTemplate(driver_twin, lap_data);
        break;
      case 'fan':
        templateResult = responseTemplates.fanTemplate(lap_data, events);
        break;
      case 'summary':
        templateResult = responseTemplates.summaryTemplate(lap_data, events);
        break;
      case 'compare':
        templateResult = responseTemplates.compareTemplate(compare_drivers, lap_data);
        break;
      case 'pit-decision':
        templateResult = responseTemplates.pitDecisionTemplate(race_twin, lap_data, weather);
        break;
      default:
        templateResult = responseTemplates.engineeringTemplate(driver_twin, race_twin, lap_data, weather);
    }

    return {
      ...templateResult,
      gemini_powered: false,
      template_fallback: true
    };
  }

  /**
   * Engineering Mode: Professional race engineer output
   * Structure: Executive Summary, Key Insights, Driver Twin, Race Twin, Tire & Pace, Strategy, Sectors, Risks, Actions
   */
  engineeringAnalysis(driverTwin, raceTwin, lapData, weather) {
    const analysis = {
      mode: 'engineering',
      timestamp: new Date().toISOString(),
      sections: {}
    };

    // 1. Executive Summary
    analysis.sections.executive_summary = this._generateExecutiveSummary(
      driverTwin, raceTwin, lapData
    );

    // 2. Key Insights
    analysis.sections.key_insights = this._extractKeyInsights(
      driverTwin, raceTwin, lapData, weather
    );

    // 3. Driver Twin Interpretation
    if (driverTwin) {
      analysis.sections.driver_twin_interpretation = this._interpretDriverTwin(driverTwin);
    } else {
      analysis.sections.driver_twin_interpretation = 'No Driver Twin data provided';
    }

    // 4. Race Twin Interpretation
    if (raceTwin) {
      analysis.sections.race_twin_interpretation = this._interpretRaceTwin(raceTwin);
    } else {
      analysis.sections.race_twin_interpretation = 'No Race Twin data provided';
    }

    // 5. Tire & Pace Analysis
    analysis.sections.tire_pace_analysis = this._analyzeTirePace(
      driverTwin, lapData
    );

    // 6. Strategy Recommendation
    analysis.sections.strategy_recommendation = this._generateStrategyRecommendation(
      raceTwin, lapData, weather
    );

    // 7. Sector Breakdown
    analysis.sections.sector_breakdown = this._analyzeSectors(
      driverTwin, lapData
    );

    // 8. Risk Factors & Confidence
    analysis.sections.risk_factors = this._assessRisks(
      driverTwin, raceTwin, lapData, weather
    );

    // 9. Action Items
    analysis.sections.action_items = this._generateActionItems(
      driverTwin, raceTwin, lapData
    );

    return analysis;
  }

  /**
   * Strategy Mode: Real-time tactical decisions
   */
  strategyAnalysis(raceTwin, lapData, events, weather) {
    const analysis = {
      mode: 'strategy',
      timestamp: new Date().toISOString(),
      recommendation: null,
      reasoning: null,
      confidence: 'medium'
    };

    if (raceTwin?.pit_recommendations) {
      analysis.recommendation = raceTwin.pit_recommendations;
      analysis.reasoning = this._explainStrategyDecision(raceTwin, lapData);
      analysis.confidence = raceTwin.confidence || 'medium';
    }

    if (raceTwin?.traffic_simulation) {
      analysis.traffic_impact = this._analyzeTraffic(raceTwin.traffic_simulation);
    }

    if (raceTwin?.undercut_outcomes) {
      analysis.undercut_analysis = this._analyzeUndercut(raceTwin.undercut_outcomes);
    }

    return analysis;
  }

  /**
   * Coach Mode: Driver improvement analysis
   */
  coachAnalysis(driverTwin, lapData) {
    const analysis = {
      mode: 'coach',
      timestamp: new Date().toISOString(),
      improvements: [],
      strengths: [],
      weaknesses: []
    };

    if (driverTwin) {
      if (driverTwin.sector_strengths) {
        analysis.strengths = this._identifyStrengths(driverTwin);
        analysis.weaknesses = this._identifyWeaknesses(driverTwin);
      }

      if (driverTwin.consistency_index !== undefined) {
        analysis.consistency_analysis = this._analyzeConsistency(driverTwin);
      }

      analysis.improvements = this._generateImprovements(driverTwin, lapData);
    }

    return analysis;
  }

  /**
   * Fan Mode: Storytelling and excitement
   */
  fanAnalysis(lapData, events) {
    return {
      mode: 'fan',
      timestamp: new Date().toISOString(),
      headline: this._generateHeadline(lapData, events),
      race_story: this._generateRaceStory(lapData, events),
      top_moments: this._extractTopMoments(events, lapData),
      driver_highlights: this._generateDriverHighlights(lapData),
      final_wrapup: this._generateWrapup(lapData, events)
    };
  }

  /**
   * Summary Mode: Race recap
   */
  summaryAnalysis(lapData, events) {
    return {
      mode: 'summary',
      timestamp: new Date().toISOString(),
      race_recap: this._generateRaceRecap(lapData, events),
      key_stats: this._extractKeyStats(lapData),
      critical_moments: this._identifyCriticalMoments(events)
    };
  }

  /**
   * Compare Mode: Side-by-side driver comparison
   */
  compareAnalysis(compareDrivers, lapData) {
    if (!compareDrivers || !Array.isArray(compareDrivers) || compareDrivers.length !== 2) {
      return { 
        error: 'compare_drivers must contain exactly 2 drivers in array format',
        mode: 'compare'
      };
    }

    const [driver1, driver2] = compareDrivers;
    
    return {
      mode: 'compare',
      timestamp: new Date().toISOString(),
      driver_1: {
        name: driver1.name || driver1.id || 'Driver 1',
        metrics: driver1,
        strengths: this._identifyStrengths(driver1),
        weaknesses: this._identifyWeaknesses(driver1)
      },
      driver_2: {
        name: driver2.name || driver2.id || 'Driver 2',
        metrics: driver2,
        strengths: this._identifyStrengths(driver2),
        weaknesses: this._identifyWeaknesses(driver2)
      },
      comparison: this._compareDrivers(driver1, driver2),
      winner_analysis: this._determineWinner(driver1, driver2, lapData)
    };
  }

  /**
   * Pit Decision Mode: Should we pit now?
   * Output: PIT_NOW / PIT_LATER / EXTEND_STINT with justification
   */
  pitDecisionAnalysis(raceTwin, lapData, weather) {
    const analysis = {
      mode: 'pit-decision',
      timestamp: new Date().toISOString(),
      decision: 'EXTEND_STINT', // Default
      confidence: 'medium',
      reasoning: [],
      factors: {}
    };

    // Evaluate degradation curve
    analysis.factors.degradation = this._evaluateDegradation(raceTwin, lapData);

    // Evaluate traffic window
    if (raceTwin?.traffic_simulation) {
      analysis.factors.traffic_window = this._evaluateTrafficWindow(raceTwin);
    }

    // Evaluate tire age
    if (raceTwin?.tire_age !== undefined) {
      analysis.factors.tire_age = this._evaluateTireAge(raceTwin.tire_age);
    }

    // Evaluate undercut viability
    if (raceTwin?.undercut_outcomes) {
      analysis.factors.undercut_viability = this._evaluateUndercut(raceTwin);
    }

    // Make decision
    const decision = this._makePitDecision(analysis.factors);
    analysis.decision = decision.decision;
    analysis.confidence = decision.confidence;
    analysis.reasoning = decision.reasoning;

    return analysis;
  }

  // ========== PRIVATE HELPER METHODS ==========

  _generateExecutiveSummary(driverTwin, raceTwin, lapData) {
    const summary = [];
    
    if (raceTwin?.expected_finishing_positions && Array.isArray(raceTwin.expected_finishing_positions)) {
      const pos = raceTwin.expected_finishing_positions[0];
      if (pos) {
        summary.push(`Expected finishing position: P${pos.position || pos.pos || 'N/A'}`);
      }
    }
    
    if (driverTwin?.consistency_index !== undefined) {
      const consistency = (driverTwin.consistency_index * 100).toFixed(1);
      summary.push(`Consistency index: ${consistency}%`);
    }
    
    if (lapData && Array.isArray(lapData) && lapData.length > 0) {
      const times = lapData.map(l => l.lap_time).filter(t => t !== undefined && t !== null);
      if (times.length > 0) {
        const avgLap = times.reduce((sum, t) => sum + parseFloat(t), 0) / times.length;
        summary.push(`Average lap time: ${avgLap.toFixed(3)}s`);
      }
    }

    return summary.length > 0 ? summary.join('. ') : 'No summary data available from provided inputs.';
  }

  _extractKeyInsights(driverTwin, raceTwin, lapData, weather) {
    const insights = [];
    
    if (driverTwin?.pace_vector !== undefined) {
      const pace = parseFloat(driverTwin.pace_vector);
      insights.push(`Pace vector: ${pace.toFixed(3)} - ${pace > 0 ? 'strong' : pace < 0 ? 'conservative' : 'balanced'} performance`);
    }
    
    if (raceTwin?.tire_cliff_prediction) {
      const cliff = raceTwin.tire_cliff_prediction;
      insights.push(`Tire cliff predicted at lap ${cliff.lap || cliff.estimated_lap || 'unknown'}`);
    }
    
    if (weather?.temperature !== undefined) {
      insights.push(`Track temperature: ${weather.temperature}°C`);
    }

    if (driverTwin?.aggression_score !== undefined) {
      const aggr = parseFloat(driverTwin.aggression_score);
      insights.push(`Driving aggression: ${aggr.toFixed(2)} (${aggr > 0.7 ? 'aggressive' : aggr > 0.5 ? 'balanced' : 'conservative'})`);
    }

    return insights.length > 0 ? insights : ['No key insights available from provided data.'];
  }

  _interpretDriverTwin(driverTwin) {
    const interpretation = {
      pace_analysis: null,
      consistency_analysis: null,
      aggression_analysis: null,
      sector_analysis: null,
      degradation_analysis: null
    };

    if (driverTwin.pace_vector !== undefined) {
      interpretation.pace_analysis = `Pace vector: ${parseFloat(driverTwin.pace_vector).toFixed(3)}`;
    } else {
      interpretation.pace_analysis = 'No pace vector data';
    }

    if (driverTwin.consistency_index !== undefined) {
      const ci = parseFloat(driverTwin.consistency_index);
      const level = ci > 0.9 ? 'exceptional' :
                    ci > 0.8 ? 'good' :
                    ci > 0.7 ? 'moderate' : 'needs improvement';
      interpretation.consistency_analysis = `Consistency: ${(ci * 100).toFixed(1)}% (${level})`;
    } else {
      interpretation.consistency_analysis = 'No consistency data';
    }

    if (driverTwin.aggression_score !== undefined) {
      interpretation.aggression_analysis = `Aggression score: ${parseFloat(driverTwin.aggression_score).toFixed(2)}`;
    } else {
      interpretation.aggression_analysis = 'No aggression data';
    }

    if (driverTwin.sector_strengths) {
      interpretation.sector_analysis = `Sector strengths: ${JSON.stringify(driverTwin.sector_strengths)}`;
    } else {
      interpretation.sector_analysis = 'No sector data';
    }

    if (driverTwin.degradation_curve) {
      interpretation.degradation_analysis = 'Degradation curve data available';
    }

    return interpretation;
  }

  _interpretRaceTwin(raceTwin) {
    return {
      monte_carlo_outcomes: raceTwin.monte_carlo_outcomes || 'No Monte Carlo data provided',
      pit_recommendations: raceTwin.pit_recommendations || 'No pit recommendations provided',
      traffic_simulation: raceTwin.traffic_simulation ? 'Traffic simulation data available' : 'No traffic simulation data',
      tire_cliff_prediction: raceTwin.tire_cliff_prediction || 'No tire cliff prediction',
      expected_finishing_positions: raceTwin.expected_finishing_positions || 'No finishing position predictions'
    };
  }

  _analyzeTirePace(driverTwin, lapData) {
    const analysis = {};
    
    if (driverTwin?.degradation_curve) {
      analysis.degradation_trend = 'Degradation curve available from Driver Twin';
    }
    
    if (lapData && Array.isArray(lapData) && lapData.length > 5) {
      const times = lapData.map(l => l.lap_time).filter(t => t !== undefined && t !== null);
      if (times.length > 5) {
        const firstFive = times.slice(0, 5);
        const lastFive = times.slice(-5);
        const earlyAvg = firstFive.reduce((a, b) => parseFloat(a) + parseFloat(b), 0) / firstFive.length;
        const lateAvg = lastFive.reduce((a, b) => parseFloat(a) + parseFloat(b), 0) / lastFive.length;
        const degradation = lateAvg - earlyAvg;
        analysis.pace_dropoff = `Average pace dropoff: ${degradation.toFixed(3)}s`;
        analysis.degradation_rate = degradation > 0.1 ? 'High' : degradation > 0.05 ? 'Moderate' : 'Low';
      }
    }

    if (Object.keys(analysis).length === 0) {
      analysis.message = 'No tire/pace analysis data available';
    }

    return analysis;
  }

  _generateStrategyRecommendation(raceTwin, lapData, weather) {
    const recommendations = [];
    
    if (raceTwin?.pit_recommendations) {
      recommendations.push(raceTwin.pit_recommendations);
    }
    
    if (raceTwin?.tire_cliff_prediction) {
      const cliff = raceTwin.tire_cliff_prediction;
      recommendations.push(`Monitor tire degradation - cliff predicted around lap ${cliff.lap || cliff.estimated_lap || 'unknown'}`);
    }

    if (weather?.condition && weather.condition.toLowerCase().includes('rain')) {
      recommendations.push('Track conditions changing - consider intermediate or wet tires');
    }

    return recommendations.length > 0 ? recommendations : ['Continue current strategy based on available data'];
  }

  _analyzeSectors(driverTwin, lapData) {
    if (driverTwin?.sector_strengths) {
      const strengths = Object.entries(driverTwin.sector_strengths)
        .sort(([, a], [, b]) => parseFloat(b) - parseFloat(a))
        .map(([sector, value]) => ({ sector, strength: parseFloat(value) }));
      
      return {
        strongest_sector: strengths[0]?.sector || 'Unknown',
        weakest_sector: strengths[strengths.length - 1]?.sector || 'Unknown',
        sector_breakdown: strengths,
        recommendation: strengths[strengths.length - 1] ? 
          `Focus improvement on ${strengths[strengths.length - 1].sector}` : null
      };
    }

    return { message: 'No sector data provided in Driver Twin' };
  }

  _assessRisks(driverTwin, raceTwin, lapData, weather) {
    const risks = [];
    const confidence = [];

    if (raceTwin?.tire_cliff_prediction) {
      risks.push('Tire cliff approaching - significant performance drop expected');
      confidence.push('high');
    }

    if (driverTwin?.consistency_index !== undefined && parseFloat(driverTwin.consistency_index) < 0.8) {
      risks.push('Consistency below optimal threshold - increased lap time variability');
      confidence.push('medium');
    }

    if (weather?.condition && weather.condition.toLowerCase().includes('rain')) {
      risks.push('Wet track conditions detected - increased variability and safety concerns');
      confidence.push('high');
    }

    if (raceTwin?.traffic_simulation?.busy) {
      risks.push('High traffic density - potential time loss in traffic');
      confidence.push('medium');
    }

    return {
      identified_risks: risks.length > 0 ? risks : ['No major risks identified'],
      confidence_levels: confidence.length > 0 ? confidence : ['medium'],
      overall_confidence: confidence.length > 0 ? confidence[0] : 'medium'
    };
  }

  _generateActionItems(driverTwin, raceTwin, lapData) {
    const actions = [];
    
    if (raceTwin?.pit_recommendations) {
      actions.push('Review and execute pit window recommendations');
    }
    
    if (driverTwin?.sector_strengths) {
      const weakest = Object.entries(driverTwin.sector_strengths)
        .sort(([, a], [, b]) => parseFloat(a) - parseFloat(b))[0];
      if (weakest) {
        actions.push(`Focus on improving ${weakest[0]} - weakest sector performance`);
      }
    }

    if (driverTwin?.consistency_index !== undefined && parseFloat(driverTwin.consistency_index) < 0.85) {
      actions.push('Work on lap-to-lap consistency - reduce variability');
    }

    if (raceTwin?.tire_cliff_prediction) {
      actions.push('Monitor tire degradation closely - cliff approaching');
    }

    return actions.length > 0 ? actions : ['Continue monitoring performance and race conditions'];
  }

  _makePitDecision(factors) {
    let decision = 'EXTEND_STINT';
    let confidence = 'medium';
    const reasoning = [];

    // Degradation factor
    if (factors.degradation?.critical) {
      decision = 'PIT_NOW';
      confidence = 'high';
      reasoning.push('Critical degradation detected - tire performance cliff imminent');
    } else if (factors.degradation?.trend === 'increasing') {
      decision = 'PIT_LATER';
      reasoning.push('Degradation increasing but not yet critical');
    }

    // Traffic window
    if (factors.traffic_window?.clear) {
      if (decision === 'EXTEND_STINT') {
        decision = 'PIT_LATER';
        reasoning.push('Clear traffic window available later - extend stint');
      } else if (decision === 'PIT_NOW') {
        reasoning.push('Clear traffic window now - good timing for pit stop');
      }
    } else if (factors.traffic_window?.busy) {
      if (decision === 'PIT_NOW') {
        reasoning.push('Heavy traffic - consider delaying pit stop');
        confidence = 'medium';
      } else {
        reasoning.push('Heavy traffic ahead - wait for clearer window');
      }
    }

    // Undercut opportunity
    if (factors.undercut_viability?.viable) {
      decision = 'PIT_NOW';
      confidence = 'high';
      const gain = factors.undercut_viability.advantage || 0;
      reasoning.push(`Undercut opportunity identified - potential ${gain.toFixed(1)}s gain`);
    }

    // Tire age
    if (factors.tire_age?.critical) {
      decision = 'PIT_NOW';
      confidence = 'high';
      reasoning.push(`Tire age critical (${factors.tire_age.age} laps) - pit required`);
    } else if (factors.tire_age?.optimal) {
      if (decision === 'PIT_NOW') {
        reasoning.push('Tires still optimal - consider extending if degradation allows');
      }
    }

    if (reasoning.length === 0) {
      reasoning.push('Continue current stint - no compelling reason to pit');
    }

    return { decision, confidence, reasoning };
  }

  _generateHeadline(lapData, events) {
    if (events && Array.isArray(events)) {
      const overtakes = events.filter(e => e.type === 'overtake');
      if (overtakes.length > 0) {
        return `Race Heating Up: ${overtakes.length} Overtake${overtakes.length > 1 ? 's' : ''} Recorded!`;
      }
      
      const pitStops = events.filter(e => e.type === 'pit_stop');
      if (pitStops.length > 0) {
        return `Strategy Unfolding: ${pitStops.length} Pit Stop${pitStops.length > 1 ? 's' : ''} Shake Up the Order!`;
      }
    }
    return 'Professional Racing Action Unfolding';
  }

  _generateRaceStory(lapData, events) {
    const story = [];
    
    if (lapData && Array.isArray(lapData) && lapData.length > 0) {
      story.push(`After ${lapData.length} lap${lapData.length > 1 ? 's' : ''} of intense racing action...`);
    }
    
    if (events && Array.isArray(events)) {
      const pitStops = events.filter(e => e.type === 'pit_stop');
      const overtakes = events.filter(e => e.type === 'overtake');
      if (pitStops.length > 0 || overtakes.length > 0) {
        story.push(`${pitStops.length} pit stop${pitStops.length !== 1 ? 's' : ''} and ${overtakes.length} overtake${overtakes.length !== 1 ? 's' : ''} have shaped the race so far.`);
      }
    }

    return story.length > 0 ? story.join(' ') : 'An exciting race is underway with professional motorsport action.';
  }

  _extractTopMoments(events, lapData) {
    const moments = [];
    
    if (events && Array.isArray(events)) {
      events.forEach(event => {
        if (event.type === 'overtake') {
          moments.push(`Overtake at lap ${event.lap || event.lap_number || 'unknown'}`);
        } else if (event.type === 'pit_stop') {
          moments.push(`Pit stop at lap ${event.lap || event.lap_number || 'unknown'}`);
        } else if (event.type === 'safety_car') {
          moments.push(`Safety Car deployed at lap ${event.lap || event.lap_number || 'unknown'}`);
        }
      });
    }

    return moments.length > 0 ? moments : ['No key moments recorded in provided data'];
  }

  _generateDriverHighlights(lapData) {
    if (!lapData || !Array.isArray(lapData) || lapData.length === 0) {
      return ['No driver highlights available'];
    }

    const times = lapData.map(l => l.lap_time).filter(t => t !== undefined && t !== null);
    if (times.length === 0) {
      return ['No lap time data available'];
    }

    const fastestLap = lapData.reduce((min, lap) => {
      if (!min || (lap.lap_time && lap.lap_time < min.lap_time)) {
        return lap;
      }
      return min;
    }, null);

    const highlights = [];
    if (fastestLap) {
      highlights.push(`Fastest lap: ${parseFloat(fastestLap.lap_time).toFixed(3)}s at lap ${fastestLap.lap || fastestLap.lap_number || 'unknown'}`);
    }

    return highlights.length > 0 ? highlights : ['No significant highlights recorded'];
  }

  _generateWrapup(lapData, events) {
    return 'An intense race showcasing professional motorsport at its finest. Every lap counts, every decision matters.';
  }

  _identifyStrengths(driverTwin) {
    if (!driverTwin) return ['No driver data provided'];
    
    const strengths = [];
    
    if (driverTwin.consistency_index !== undefined && parseFloat(driverTwin.consistency_index) > 0.9) {
      strengths.push('Exceptional consistency - very stable lap times');
    }
    
    if (driverTwin.sector_strengths) {
      const bestSector = Object.entries(driverTwin.sector_strengths)
        .sort(([, a], [, b]) => parseFloat(b) - parseFloat(a))[0];
      if (bestSector) {
        strengths.push(`Strong performance in ${bestSector[0]} - sector specialist`);
      }
    }

    if (driverTwin.pace_vector !== undefined && parseFloat(driverTwin.pace_vector) > 0.05) {
      strengths.push('Strong pace vector - fast overall performance');
    }

    return strengths.length > 0 ? strengths : ['No specific strengths identified'];
  }

  _identifyWeaknesses(driverTwin) {
    if (!driverTwin) return ['No driver data provided'];
    
    const weaknesses = [];
    
    if (driverTwin.consistency_index !== undefined && parseFloat(driverTwin.consistency_index) < 0.8) {
      weaknesses.push('Inconsistent lap times - high variability');
    }
    
    if (driverTwin.sector_strengths) {
      const worstSector = Object.entries(driverTwin.sector_strengths)
        .sort(([, a], [, b]) => parseFloat(a) - parseFloat(b))[0];
      if (worstSector) {
        weaknesses.push(`Needs improvement in ${worstSector[0]} - weakest sector`);
      }
    }

    if (driverTwin.pace_vector !== undefined && parseFloat(driverTwin.pace_vector) < -0.05) {
      weaknesses.push('Pace vector below optimal - slower than target');
    }

    return weaknesses.length > 0 ? weaknesses : ['No major weaknesses identified'];
  }

  _analyzeConsistency(driverTwin) {
    if (driverTwin?.consistency_index === undefined) {
      return 'No consistency data available';
    }

    const ci = parseFloat(driverTwin.consistency_index);
    const level = ci > 0.9 ? 'excellent' :
                  ci > 0.8 ? 'good' :
                  ci > 0.7 ? 'acceptable' : 'needs work';

    return `Consistency level: ${level} (${(ci * 100).toFixed(1)}%)`;
  }

  _generateImprovements(driverTwin, lapData) {
    if (!driverTwin) return ['No driver data for improvement analysis'];
    
    const improvements = [];
    
    if (driverTwin.sector_strengths) {
      const worst = Object.entries(driverTwin.sector_strengths)
        .sort(([, a], [, b]) => parseFloat(a) - parseFloat(b))[0];
      if (worst) {
        improvements.push(`Focus on ${worst[0]} - work on sector entry and exit speeds, braking points, and throttle application`);
      }
    }
    
    if (driverTwin.consistency_index !== undefined && parseFloat(driverTwin.consistency_index) < 0.9) {
      improvements.push('Improve lap-to-lap consistency through better throttle and braking modulation - focus on smooth inputs');
    }

    if (driverTwin.aggression_score !== undefined) {
      const aggr = parseFloat(driverTwin.aggression_score);
      if (aggr > 0.7) {
        improvements.push('Consider slightly more conservative approach - reduce aggression to improve tire life and consistency');
      } else if (aggr < 0.3) {
        improvements.push('Increase aggression in overtaking zones - push harder in sector 2 and 3');
      }
    }

    return improvements.length > 0 ? improvements : ['Continue current approach - maintain consistency'];
  }

  _compareDrivers(driver1, driver2) {
    const comparison = {};
    
    if (driver1.consistency_index !== undefined && driver2.consistency_index !== undefined) {
      const d1 = parseFloat(driver1.consistency_index);
      const d2 = parseFloat(driver2.consistency_index);
      comparison.consistency = d1 > d2 
        ? `Driver 1 more consistent (${(d1*100).toFixed(1)}% vs ${(d2*100).toFixed(1)}%)`
        : `Driver 2 more consistent (${(d2*100).toFixed(1)}% vs ${(d1*100).toFixed(1)}%)`;
    }
    
    if (driver1.aggression_score !== undefined && driver2.aggression_score !== undefined) {
      const a1 = parseFloat(driver1.aggression_score);
      const a2 = parseFloat(driver2.aggression_score);
      comparison.aggression = a1 > a2
        ? `Driver 1 more aggressive (${a1.toFixed(2)} vs ${a2.toFixed(2)})`
        : `Driver 2 more aggressive (${a2.toFixed(2)} vs ${a1.toFixed(2)})`;
    }

    if (driver1.pace_vector !== undefined && driver2.pace_vector !== undefined) {
      const p1 = parseFloat(driver1.pace_vector);
      const p2 = parseFloat(driver2.pace_vector);
      comparison.pace = p1 > p2
        ? `Driver 1 faster pace (${p1.toFixed(3)} vs ${p2.toFixed(3)})`
        : `Driver 2 faster pace (${p2.toFixed(3)} vs ${p1.toFixed(3)})`;
    }

    return Object.keys(comparison).length > 0 ? comparison : { message: 'Limited comparison data available' };
  }

  _determineWinner(driver1, driver2, lapData) {
    // Analyze based on available metrics
    let winner = null;
    let reasoning = [];

    if (driver1.pace_vector !== undefined && driver2.pace_vector !== undefined) {
      const p1 = parseFloat(driver1.pace_vector);
      const p2 = parseFloat(driver2.pace_vector);
      if (p1 > p2) {
        winner = 'Driver 1';
        reasoning.push('Faster pace vector');
      } else if (p2 > p1) {
        winner = 'Driver 2';
        reasoning.push('Faster pace vector');
      }
    }

    if (driver1.consistency_index !== undefined && driver2.consistency_index !== undefined) {
      const c1 = parseFloat(driver1.consistency_index);
      const c2 = parseFloat(driver2.consistency_index);
      if (c1 > c2) {
        if (winner === 'Driver 1') {
          reasoning.push('Higher consistency');
        } else if (!winner) {
          winner = 'Driver 1';
          reasoning.push('Higher consistency');
        }
      } else if (c2 > c1) {
        if (winner === 'Driver 2') {
          reasoning.push('Higher consistency');
        } else if (!winner) {
          winner = 'Driver 2';
          reasoning.push('Higher consistency');
        }
      }
    }

    return winner ? 
      `${winner} favored based on: ${reasoning.join(', ')}` :
      'Winner cannot be determined from provided data';
  }

  _evaluateDegradation(raceTwin, lapData) {
    if (raceTwin?.degradation_curve) {
      return {
        critical: raceTwin.degradation_curve.critical || false,
        trend: raceTwin.degradation_curve.trend || 'stable',
        estimated_cliff: raceTwin.degradation_curve.cliff_lap
      };
    }
    return { critical: false, trend: 'unknown' };
  }

  _evaluateTrafficWindow(raceTwin) {
    if (raceTwin?.traffic_simulation) {
      return {
        clear: raceTwin.traffic_simulation.clear_window || false,
        busy: raceTwin.traffic_simulation.busy || false,
        density: raceTwin.traffic_simulation.density || 'unknown'
      };
    }
    return { clear: false, busy: false };
  }

  _evaluateTireAge(tireAge) {
    const age = parseInt(tireAge);
    return {
      age: age,
      critical: age > 20,
      optimal: age < 10,
      warning: age >= 15 && age <= 20
    };
  }

  _evaluateUndercut(raceTwin) {
    if (raceTwin?.undercut_outcomes) {
      return {
        viable: raceTwin.undercut_outcomes.viable || false,
        advantage: raceTwin.undercut_outcomes.time_gain || 0,
        risk: raceTwin.undercut_outcomes.risk || 'medium'
      };
    }
    return { viable: false, advantage: 0 };
  }

  _generateRaceRecap(lapData, events) {
    const recap = [];
    
    if (lapData && Array.isArray(lapData)) {
      recap.push(`${lapData.length} lap${lapData.length !== 1 ? 's' : ''} completed`);
    }
    
    if (events && Array.isArray(events)) {
      const pitStops = events.filter(e => e.type === 'pit_stop').length;
      const overtakes = events.filter(e => e.type === 'overtake').length;
      if (pitStops > 0 || overtakes > 0) {
        recap.push(`${pitStops} pit stop${pitStops !== 1 ? 's' : ''}, ${overtakes} overtake${overtakes !== 1 ? 's' : ''}`);
      }
    }

    return recap.join(' - ') || 'Race recap unavailable from provided data';
  }

  _extractKeyStats(lapData) {
    if (!lapData || !Array.isArray(lapData) || lapData.length === 0) {
      return { message: 'No lap data available' };
    }

    const times = lapData.map(l => l.lap_time).filter(t => t !== undefined && t !== null);
    if (times.length === 0) {
      return { message: 'No lap time data available' };
    }

    const numericTimes = times.map(t => parseFloat(t));
    const total = numericTimes.reduce((a, b) => a + b, 0);
    const avg = total / numericTimes.length;
    const min = Math.min(...numericTimes);
    const max = Math.max(...numericTimes);

    return {
      total_laps: lapData.length,
      average_lap_time: `${avg.toFixed(3)}s`,
      fastest_lap: `${min.toFixed(3)}s`,
      slowest_lap: `${max.toFixed(3)}s`,
      lap_time_variance: `${(max - min).toFixed(3)}s`
    };
  }

  _identifyCriticalMoments(events) {
    if (!events || !Array.isArray(events)) return [];
    
    return events.filter(e => 
      e.type === 'overtake' || 
      e.type === 'pit_stop' || 
      e.type === 'safety_car' ||
      e.type === 'mistake'
    ).map(e => ({
      type: e.type,
      lap: e.lap || e.lap_number || 'unknown',
      description: `${e.type.replace('_', ' ')} at lap ${e.lap || e.lap_number || 'unknown'}`
    }));
  }

  _explainStrategyDecision(raceTwin, lapData) {
    if (raceTwin?.pit_recommendations) {
      return `Based on degradation curve and traffic simulation analysis: ${raceTwin.pit_recommendations}`;
    }
    return 'Strategy decision based on current race conditions, tire degradation, and traffic patterns';
  }

  _analyzeTraffic(trafficSimulation) {
    if (!trafficSimulation) return { message: 'No traffic simulation data' };
    
    return {
      density: trafficSimulation.density || 'unknown',
      impact: trafficSimulation.time_loss || 0,
      recommendation: trafficSimulation.clear_window ? 
        'Clear window available - good time for pit stop' : 
        'Heavy traffic - wait for better window'
    };
  }

  _analyzeUndercut(undercutOutcomes) {
    if (!undercutOutcomes) return { message: 'No undercut analysis data' };
    
    return {
      viable: undercutOutcomes.viable || false,
      time_gain: undercutOutcomes.time_gain || 0,
      recommendation: undercutOutcomes.viable ? 
        `Undercut recommended - potential ${undercutOutcomes.time_gain?.toFixed(1) || 0}s gain` : 
        'Undercut not viable in current conditions'
    };
  }

  // ========== TOOL-CALLING FUNCTIONS ==========

  /**
   * Tool: getDriverTwin
   * Fetches Driver Twin data for a driver
   */
  async _toolGetDriverTwin(driverId, nodeApiUrl = 'http://localhost:3001') {
    try {
      const axios = require('axios');
      const response = await axios.get(`${nodeApiUrl}/api/driver-twin/loop/${driverId}`, {
        timeout: 5000
      });
      
      if (response.data.success && response.data.driver_twin) {
        return {
          success: true,
          driver_twin: response.data.driver_twin
        };
      }
      
      return {
        success: false,
        message: `No Driver Twin found for ${driverId}`
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Tool: getRaceTwin
   * Fetches Race Twin (Monte Carlo simulation) data
   */
  async _toolGetRaceTwin(raceId, nodeApiUrl = 'http://localhost:3001') {
    try {
      const axios = require('axios');
      // In production, this would fetch from cache or trigger new simulation
      return {
        success: true,
        message: `Race Twin data for ${raceId} - use race_twin from input data`
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Tool: getPitDecision
   * Gets advanced AI pit decision recommendation with multi-factor analysis
   */
  async _toolGetPitDecision(raceId, driverId, currentLap, tireAge, position, tireCompound = 'MEDIUM', pythonApiUrl = 'http://localhost:8000') {
    try {
      const axios = require('axios');
      const response = await axios.post(`${pythonApiUrl}/strategy/pit-decision`, {
        race_id: raceId,
        driver_id: driverId,
        current_lap: currentLap,
        total_laps: 50, // Default, should be passed if available
        tire_age: tireAge,
        tire_compound: tireCompound || 'MEDIUM',
        position: position,
        degradation_rate: 0.002, // Default, should be calculated
        traffic_density: 0.5 // Default, should be calculated
      }, {
        timeout: 10000
      });
      
      if (response.data.success) {
        return {
          success: true,
          decision: response.data.decision,
          confidence: response.data.confidence,
          confidence_level: response.data.confidence_level,
          factor_breakdown: response.data.factor_breakdown,
          reasoning: response.data.reasoning,
          recommended_lap: response.data.recommended_lap
        };
      }
      
      return {
        success: false,
        message: 'Failed to get pit decision'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Tool: runMonteCarlo
   * Runs Monte Carlo race simulation
   */
  async _toolRunMonteCarlo(drivers, totalLaps, currentLap, numSimulations = 100, pythonApiUrl = 'http://localhost:8000') {
    try {
      const axios = require('axios');
      const response = await axios.post(`${pythonApiUrl}/race-twin/simulate`, {
        race_id: 'simulation',
        drivers: drivers,
        total_laps: totalLaps,
        current_lap: currentLap,
        num_simulations: numSimulations
      }, {
        timeout: 30000
      });
      
      if (response.data.success && response.data.race_twin) {
        return {
          success: true,
          race_twin: response.data.race_twin
        };
      }
      
      return {
        success: false,
        message: 'Monte Carlo simulation failed'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Tool: evaluateSectors
   * Evaluates sector performance with detailed analysis
   */
  async _toolEvaluateSectors(driverId, sectorTimes, pythonApiUrl = 'http://localhost:8000') {
    try {
      // If sector times provided, analyze directly
      if (sectorTimes && Array.isArray(sectorTimes) && sectorTimes.length > 0) {
        const avgS1 = sectorTimes.reduce((sum, s) => sum + (s.S1 || 0), 0) / sectorTimes.length;
        const avgS2 = sectorTimes.reduce((sum, s) => sum + (s.S2 || 0), 0) / sectorTimes.length;
        const avgS3 = sectorTimes.reduce((sum, s) => sum + (s.S3 || 0), 0) / sectorTimes.length;
        
        const total = avgS1 + avgS2 + avgS3;
        const strengths = [];
        const weaknesses = [];
        
        // Determine strongest and weakest sectors
        if (avgS1 <= avgS2 && avgS1 <= avgS3) {
          strengths.push({ sector: 'S1', time: avgS1, percentage: (avgS1 / total * 100).toFixed(1) });
        }
        if (avgS2 <= avgS1 && avgS2 <= avgS3) {
          strengths.push({ sector: 'S2', time: avgS2, percentage: (avgS2 / total * 100).toFixed(1) });
        }
        if (avgS3 <= avgS1 && avgS3 <= avgS2) {
          strengths.push({ sector: 'S3', time: avgS3, percentage: (avgS3 / total * 100).toFixed(1) });
        }
        
        if (avgS1 >= avgS2 && avgS1 >= avgS3) {
          weaknesses.push({ sector: 'S1', time: avgS1, percentage: (avgS1 / total * 100).toFixed(1) });
        }
        if (avgS2 >= avgS1 && avgS2 >= avgS3) {
          weaknesses.push({ sector: 'S2', time: avgS2, percentage: (avgS2 / total * 100).toFixed(1) });
        }
        if (avgS3 >= avgS1 && avgS3 >= avgS2) {
          weaknesses.push({ sector: 'S3', time: avgS3, percentage: (avgS3 / total * 100).toFixed(1) });
        }
        
        return {
          success: true,
          sector_analysis: {
            average_sectors: { S1: avgS1.toFixed(3), S2: avgS2.toFixed(3), S3: avgS3.toFixed(3) },
            total_lap_time: total.toFixed(3),
            strongest_sector: strengths[0]?.sector || 'N/A',
            weakest_sector: weaknesses[0]?.sector || 'N/A',
            strengths: strengths,
            weaknesses: weaknesses,
            improvement_potential: {
              sector: weaknesses[0]?.sector,
              time_gain: weaknesses[0] ? (weaknesses[0].time - strengths[0]?.time || 0).toFixed(3) : '0.000'
            }
          }
        };
      }
      
      // Try API endpoint as fallback
      const axios = require('axios');
      const response = await axios.post(`${pythonApiUrl}/sectors/analyze`, {
        csv: 'dummy',
        driver_id: driverId
      }, {
        timeout: 10000
      });
      
      if (response.data) {
        return {
          success: true,
          sector_analysis: response.data
        };
      }
      
      return {
        success: false,
        message: 'No sector data available'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Call a tool by name
   */
  async callTool(toolName, ...args) {
    if (this.tools[toolName]) {
      return await this.tools[toolName](...args);
    }
    
    return {
      success: false,
      error: `Unknown tool: ${toolName}`
    };
  }

  /**
   * Get available tools
   */
  getAvailableTools() {
    return Object.keys(this.tools);
  }
  
  /**
   * Handle missing data with AI fallback
   */
  _handleMissingData(mode, userQuery) {
    const fallbackMessage = `No data provided for analysis. `;
    const suggestions = [
      'Please provide driver_twin, race_twin, or lap_data',
      'Use the "Auto-Insert Data" button to load current race data',
      'Or manually provide data in the request'
    ];
    
    return {
      mode,
      timestamp: new Date().toISOString(),
      gemini_powered: false,
      template_fallback: true,
      data_missing: true,
      response: fallbackMessage + suggestions.join('. '),
      suggestions: suggestions
    };
  }
  
  /**
   * Handle incomplete data with AI fallback
   */
  _handleIncompleteData(data, mode, userQuery, completeness) {
    const warnings = completeness.missing.map(item => `Missing: ${item}`).join(', ');
    const fallbackMessage = `Incomplete data provided (completeness: ${(completeness.score * 100).toFixed(0)}%). `;
    const suggestions = completeness.suggestions || [];
    
    // Try to use available data with template fallback
    const { driver_twin, race_twin, lap_data, events, weather } = data;
    
    let templateResult;
    switch (mode.toLowerCase()) {
      case 'engineering':
        templateResult = responseTemplates.engineeringTemplate(driver_twin, race_twin, lap_data, weather);
        break;
      case 'strategy':
        templateResult = responseTemplates.strategyTemplate(race_twin, lap_data, events, weather);
        break;
      case 'coach':
        templateResult = responseTemplates.coachTemplate(driver_twin, lap_data);
        break;
      default:
        templateResult = responseTemplates.engineeringTemplate(driver_twin, race_twin, lap_data, weather);
    }
    
    return {
      ...templateResult,
      gemini_powered: false,
      template_fallback: true,
      data_incomplete: true,
      completeness_score: completeness.score,
      warnings: warnings,
      suggestions: suggestions,
      response: fallbackMessage + (templateResult.response || 'Using available data with reduced accuracy.')
    };
  }
  
  /**
   * Check data completeness for analysis
   */
  _checkDataCompleteness(data, mode) {
    const missing = [];
    const suggestions = [];
    let score = 1.0;
    
    // Check required data based on mode
    switch (mode.toLowerCase()) {
      case 'engineering':
        if (!data.driver_twin) {
          missing.push('driver_twin');
          score -= 0.3;
          suggestions.push('Provide driver_twin for pace and consistency analysis');
        }
        if (!data.race_twin) {
          missing.push('race_twin');
          score -= 0.2;
          suggestions.push('Provide race_twin for race predictions');
        }
        if (!data.lap_data || data.lap_data.length === 0) {
          missing.push('lap_data');
          score -= 0.2;
          suggestions.push('Provide lap_data for recent performance analysis');
        }
        break;
        
      case 'strategy':
        if (!data.race_twin) {
          missing.push('race_twin');
          score -= 0.4;
          suggestions.push('Provide race_twin for strategy recommendations');
        }
        if (!data.lap_data || data.lap_data.length === 0) {
          missing.push('lap_data');
          score -= 0.3;
          suggestions.push('Provide lap_data for current race state');
        }
        break;
        
      case 'coach':
        if (!data.driver_twin) {
          missing.push('driver_twin');
          score -= 0.5;
          suggestions.push('Provide driver_twin for coaching recommendations');
        }
        if (!data.lap_data || data.lap_data.length === 0) {
          missing.push('lap_data');
          score -= 0.3;
          suggestions.push('Provide lap_data for performance analysis');
        }
        break;
        
      case 'pit-decision':
        if (!data.race_twin) {
          missing.push('race_twin');
          score -= 0.4;
          suggestions.push('Provide race_twin for pit decision analysis');
        }
        break;
    }
    
    return {
      score: Math.max(0.0, score),
      missing: missing,
      suggestions: suggestions
    };
  }
  
  /**
   * Execute tool calls from Gemini
   */
  async _executeToolCalls(functionCalls, contextData) {
    const results = [];
    
    for (const call of functionCalls) {
      try {
        const toolName = call.name;
        const args = call.args || {};
        
        let result;
        
        switch (toolName) {
          case 'getDriverTwin':
            result = await this._toolGetDriverTwin(args.driverId);
            break;
            
          case 'getRaceTwin':
            result = await this._toolGetRaceTwin(args.raceId);
            break;
            
          case 'getPitDecision':
            result = await this._toolGetPitDecision(
              args.raceId,
              args.driverId,
              args.currentLap,
              args.tireAge,
              args.position
            );
            break;
            
          case 'runMonteCarlo':
            result = await this._toolRunMonteCarlo(
              args.drivers,
              args.totalLaps,
              args.currentLap,
              args.numSimulations || 500,
              args.raceId
            );
            break;
            
          case 'evaluateSectors':
            result = await this._toolEvaluateSectors(
              args.driverId,
              args.sectorTimes
            );
            break;
            
          default:
            result = {
              success: false,
              error: `Unknown tool: ${toolName}`
            };
        }
        
        results.push({
          tool: toolName,
          success: result.success !== false,
          result: result
        });
      } catch (error) {
        results.push({
          tool: call.name,
          success: false,
          error: error.message
        });
      }
    }
    
    return results;
  }
}

module.exports = RaceEngineerAI;
