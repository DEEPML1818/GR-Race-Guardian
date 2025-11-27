/**
 * AI Response Templates for All 7 Modes
 * 
 * Comprehensive templates for when Gemini is not available or as fallback
 */

class AIResponseTemplates {
  /**
   * Engineering Mode Template
   */
  engineeringTemplate(driverTwin, raceTwin, lapData, weather) {
    const sections = {
      executive_summary: this._generateExecutiveSummary(driverTwin, raceTwin, lapData),
      key_insights: this._extractKeyInsights(driverTwin, raceTwin, lapData, weather),
      driver_twin_interpretation: this._interpretDriverTwin(driverTwin),
      race_twin_interpretation: this._interpretRaceTwin(raceTwin),
      tire_pace_analysis: this._analyzeTirePace(driverTwin, lapData),
      strategy_recommendation: this._generateStrategyRecommendation(raceTwin, lapData, weather),
      sector_breakdown: this._analyzeSectors(driverTwin, lapData),
      risk_factors: this._assessRisks(driverTwin, raceTwin, lapData, weather),
      action_items: this._generateActionItems(driverTwin, raceTwin, lapData)
    };

    return {
      mode: 'engineering',
      timestamp: new Date().toISOString(),
      sections
    };
  }

  /**
   * Strategy Mode Template
   */
  strategyTemplate(raceTwin, lapData, events, weather) {
    return {
      mode: 'strategy',
      timestamp: new Date().toISOString(),
      recommendation: raceTwin?.pit_recommendations || 'Continue current strategy',
      reasoning: this._explainStrategyDecision(raceTwin, lapData),
      confidence: raceTwin?.confidence || 'medium',
      traffic_impact: raceTwin?.traffic_simulation || {},
      undercut_analysis: raceTwin?.undercut_outcomes || {}
    };
  }

  /**
   * Coach Mode Template
   */
  coachTemplate(driverTwin, lapData) {
    return {
      mode: 'coach',
      timestamp: new Date().toISOString(),
      improvements: this._generateImprovements(driverTwin, lapData),
      strengths: this._identifyStrengths(driverTwin),
      weaknesses: this._identifyWeaknesses(driverTwin),
      consistency_analysis: this._analyzeConsistency(driverTwin)
    };
  }

  /**
   * Fan Mode Template
   */
  fanTemplate(lapData, events) {
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
   * Summary Mode Template
   */
  summaryTemplate(lapData, events) {
    return {
      mode: 'summary',
      timestamp: new Date().toISOString(),
      race_recap: this._generateRaceRecap(lapData, events),
      key_stats: this._extractKeyStats(lapData),
      critical_moments: this._identifyCriticalMoments(events)
    };
  }

  /**
   * Compare Mode Template
   */
  compareTemplate(compareDrivers, lapData) {
    if (!compareDrivers || !Array.isArray(compareDrivers) || compareDrivers.length !== 2) {
      return {
        error: 'compare_drivers must contain exactly 2 drivers',
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
   * Pit Decision Mode Template
   */
  pitDecisionTemplate(raceTwin, lapData, weather) {
    return {
      mode: 'pit-decision',
      timestamp: new Date().toISOString(),
      decision: this._makePitDecision(raceTwin, lapData, weather).decision,
      confidence: this._makePitDecision(raceTwin, lapData, weather).confidence,
      reasoning: this._makePitDecision(raceTwin, lapData, weather).reasoning,
      factors: {
        degradation: this._evaluateDegradation(raceTwin, lapData),
        traffic_window: this._evaluateTrafficWindow(raceTwin),
        tire_age: this._evaluateTireAge(raceTwin),
        undercut_viability: this._evaluateUndercut(raceTwin)
      }
    };
  }

  // Helper methods (simplified versions)
  _generateExecutiveSummary(driverTwin, raceTwin, lapData) {
    const summary = [];
    if (raceTwin?.expected_finishing_positions?.[0]) {
      summary.push(`Expected finishing: P${raceTwin.expected_finishing_positions[0].position}`);
    }
    if (driverTwin?.consistency_index) {
      summary.push(`Consistency: ${(driverTwin.consistency_index * 100).toFixed(1)}%`);
    }
    return summary.join('. ') || 'Analysis in progress...';
  }

  _extractKeyInsights(driverTwin, raceTwin, lapData, weather) {
    const insights = [];
    if (driverTwin?.pace_vector) {
      insights.push(`Pace vector: ${driverTwin.pace_vector.toFixed(3)}`);
    }
    if (raceTwin?.tire_cliff_prediction) {
      insights.push(`Tire cliff predicted at lap ${raceTwin.tire_cliff_prediction.lap}`);
    }
    return insights.length > 0 ? insights : ['Gathering insights...'];
  }

  _interpretDriverTwin(driverTwin) {
    if (!driverTwin) return 'No driver data available';
    return {
      pace: `Pace vector: ${driverTwin.pace_vector || 0}`,
      consistency: `Consistency: ${((driverTwin.consistency_index || 0.7) * 100).toFixed(1)}%`,
      aggression: `Aggression: ${driverTwin.aggression_score || 0.5}`,
      sectors: driverTwin.sector_strengths || { S1: 1.0, S2: 1.0, S3: 1.0 }
    };
  }

  _interpretRaceTwin(raceTwin) {
    if (!raceTwin) return 'No race simulation data available';
    return {
      monte_carlo: raceTwin.monte_carlo_outcomes || {},
      pit_recommendations: raceTwin.pit_recommendations || {},
      traffic: raceTwin.traffic_simulation || {}
    };
  }

  _analyzeTirePace(driverTwin, lapData) {
    return {
      degradation_trend: driverTwin?.degradation_profile?.rate || 0.002,
      pace_dropoff: 'Analyzing...'
    };
  }

  _generateStrategyRecommendation(raceTwin, lapData, weather) {
    return raceTwin?.pit_recommendations || 'Continue current strategy';
  }

  _analyzeSectors(driverTwin, lapData) {
    if (!driverTwin?.sector_strengths) return { message: 'No sector data' };
    const sectors = Object.entries(driverTwin.sector_strengths).sort((a, b) => b[1] - a[1]);
    return {
      strongest: sectors[0]?.[0] || 'N/A',
      weakest: sectors[sectors.length - 1]?.[0] || 'N/A',
      breakdown: driverTwin.sector_strengths
    };
  }

  _assessRisks(driverTwin, raceTwin, lapData, weather) {
    const risks = [];
    if (raceTwin?.tire_cliff_prediction?.critical) {
      risks.push('Tire cliff approaching');
    }
    return {
      identified_risks: risks.length > 0 ? risks : ['No major risks'],
      overall_confidence: 'medium'
    };
  }

  _generateActionItems(driverTwin, raceTwin, lapData) {
    const actions = [];
    if (raceTwin?.pit_recommendations) {
      actions.push('Review pit window recommendations');
    }
    return actions.length > 0 ? actions : ['Continue monitoring'];
  }

  _explainStrategyDecision(raceTwin, lapData) {
    return 'Strategy based on degradation curve and traffic simulation';
  }

  _generateImprovements(driverTwin, lapData) {
    if (!driverTwin) return ['No driver data'];
    const improvements = [];
    if (driverTwin.sector_strengths) {
      const weakest = Object.entries(driverTwin.sector_strengths).sort((a, b) => a[1] - b[1])[0];
      if (weakest) {
        improvements.push(`Focus on ${weakest[0]} - weakest sector`);
      }
    }
    return improvements.length > 0 ? improvements : ['Maintain current performance'];
  }

  _identifyStrengths(driverTwin) {
    if (!driverTwin) return [];
    const strengths = [];
    if (driverTwin.consistency_index > 0.9) {
      strengths.push('Exceptional consistency');
    }
    return strengths;
  }

  _identifyWeaknesses(driverTwin) {
    if (!driverTwin) return [];
    const weaknesses = [];
    if (driverTwin.consistency_index < 0.8) {
      weaknesses.push('Inconsistent lap times');
    }
    return weaknesses;
  }

  _analyzeConsistency(driverTwin) {
    if (!driverTwin?.consistency_index) return 'No consistency data';
    return `Consistency: ${(driverTwin.consistency_index * 100).toFixed(1)}%`;
  }

  _generateHeadline(lapData, events) {
    if (events?.some(e => e.type === 'overtake')) {
      return 'Race Heating Up: Overtakes Recorded!';
    }
    return 'Professional Racing Action Unfolding';
  }

  _generateRaceStory(lapData, events) {
    return `After ${lapData?.length || 0} laps of intense racing...`;
  }

  _extractTopMoments(events, lapData) {
    if (!events) return ['No key moments'];
    return events.filter(e => ['overtake', 'pit_stop'].includes(e.type)).map(e => `${e.type} at lap ${e.lap}`);
  }

  _generateDriverHighlights(lapData) {
    if (!lapData || lapData.length === 0) return ['No highlights'];
    const fastest = lapData.reduce((min, lap) => lap.lap_time < min.lap_time ? lap : min, lapData[0]);
    return [`Fastest lap: ${fastest.lap_time}s at lap ${fastest.lap}`];
  }

  _generateWrapup(lapData, events) {
    return 'An intense race showcasing professional motorsport at its finest.';
  }

  _generateRaceRecap(lapData, events) {
    return `${lapData?.length || 0} laps completed`;
  }

  _extractKeyStats(lapData) {
    if (!lapData || lapData.length === 0) return { message: 'No data' };
    const times = lapData.map(l => l.lap_time).filter(Boolean);
    return {
      total_laps: lapData.length,
      average_lap_time: `${(times.reduce((a, b) => a + b, 0) / times.length).toFixed(3)}s`,
      fastest_lap: `${Math.min(...times).toFixed(3)}s`
    };
  }

  _identifyCriticalMoments(events) {
    if (!events) return [];
    return events.filter(e => ['overtake', 'pit_stop', 'safety_car'].includes(e.type));
  }

  _compareDrivers(driver1, driver2) {
    return {
      pace: driver1.pace_vector > driver2.pace_vector ? 'Driver 1 faster' : 'Driver 2 faster',
      consistency: driver1.consistency_index > driver2.consistency_index ? 'Driver 1 more consistent' : 'Driver 2 more consistent'
    };
  }

  _determineWinner(driver1, driver2, lapData) {
    if (driver1.pace_vector > driver2.pace_vector) {
      return 'Driver 1 favored based on pace';
    }
    return 'Driver 2 favored based on pace';
  }

  _makePitDecision(raceTwin, lapData, weather) {
    const decision = raceTwin?.pit_recommendations?.decision || 'EXTEND_STINT';
    return {
      decision,
      confidence: 'medium',
      reasoning: ['Based on degradation and traffic analysis']
    };
  }

  _evaluateDegradation(raceTwin, lapData) {
    return {
      critical: raceTwin?.tire_cliff_prediction?.critical || false,
      trend: 'stable'
    };
  }

  _evaluateTrafficWindow(raceTwin) {
    return {
      clear: raceTwin?.traffic_simulation?.clear_window || false,
      busy: raceTwin?.traffic_simulation?.busy || false
    };
  }

  _evaluateTireAge(raceTwin) {
    return {
      age: raceTwin?.tire_age || 10,
      critical: (raceTwin?.tire_age || 10) > 20
    };
  }

  _evaluateUndercut(raceTwin) {
    return {
      viable: raceTwin?.undercut_outcomes?.viable || false,
      advantage: raceTwin?.undercut_outcomes?.time_gain || 0
    };
  }
}

module.exports = new AIResponseTemplates();

