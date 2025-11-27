/**
 * AI Race Engineer Routes
 * 
 * Endpoints for GR-RACE-GUARDIAN-AI analysis
 */

const express = require('express');
const router = express.Router();
const RaceEngineerAI = require('../services/race-engineer-ai');

const ai = new RaceEngineerAI();

/**
 * POST /api/ai/analyze
 * Main AI analysis endpoint
 * 
 * Body:
 * {
 *   mode: "engineering" | "strategy" | "coach" | "fan" | "summary" | "compare" | "pit-decision",
 *   driver_twin: {...},
 *   race_twin: {...},
 *   lap_data: [...],
 *   events: [...],
 *   weather: {...},
 *   compare_drivers: [...]
 * }
 */
router.post('/analyze', async (req, res) => {
  try {
    const { mode = 'engineering', user_query, ...data } = req.body;
    
    if (!mode || typeof mode !== 'string') {
      return res.status(400).json({ 
        error: 'Invalid mode. Must be: engineering, strategy, coach, fan, summary, compare, or pit-decision' 
      });
    }

    const analysis = await ai.analyze(data, mode, user_query);
    
    res.json({
      success: true,
      mode,
      analysis,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('AI analysis error:', error);
    res.status(500).json({ 
      error: 'Failed to perform analysis', 
      message: error.message 
    });
  }
});

/**
 * POST /api/ai/engineering
 * Engineering mode analysis
 */
router.post('/engineering', async (req, res) => {
  try {
    const analysis = await ai.analyze(req.body, 'engineering');
    res.json({
      success: true,
      mode: 'engineering',
      analysis,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/ai/strategy
 * Strategy mode analysis
 */
router.post('/strategy', async (req, res) => {
  try {
    const analysis = await ai.analyze(req.body, 'strategy');
    res.json({
      success: true,
      mode: 'strategy',
      analysis,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/ai/coach
 * Coach mode analysis
 */
router.post('/coach', async (req, res) => {
  try {
    const analysis = await ai.analyze(req.body, 'coach');
    res.json({
      success: true,
      mode: 'coach',
      analysis,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/ai/fan
 * Fan mode analysis (storytelling)
 */
router.post('/fan', async (req, res) => {
  try {
    const analysis = await ai.analyze(req.body, 'fan');
    res.json({
      success: true,
      mode: 'fan',
      analysis,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/ai/pit-decision
 * Pit decision analysis
 */
router.post('/pit-decision', async (req, res) => {
  try {
    const analysis = await ai.analyze(req.body, 'pit-decision');
    res.json({
      success: true,
      mode: 'pit-decision',
      analysis,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/ai/tool
 * Call an AI tool
 */
router.post('/tool', async (req, res) => {
  try {
    const { tool_name, ...args } = req.body;
    
    if (!tool_name) {
      return res.status(400).json({ error: 'tool_name is required' });
    }
    
    const result = await ai.callTool(tool_name, ...Object.values(args));
    res.json({
      success: result.success,
      result,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/ai/tools
 * Get available AI tools
 */
router.get('/tools', (req, res) => {
  try {
    const tools = ai.getAvailableTools();
    res.json({
      success: true,
      tools,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;

