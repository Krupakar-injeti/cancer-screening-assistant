const express = require('express');
const { analyzeReport } = require('../services/medgemma');

const router = express.Router();

router.post('/', async (req, res) => {
  const { documentData, question, language } = req.body;

  if (!documentData || !question) {
    return res.status(400).json({ error: 'Missing document data or question.' });
  }

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');

  try {
    const response = await analyzeReport(documentData, question, language || 'English');

    if (!response.ok) {
      const errText = await response.text();
      console.error('OpenRouter error:', errText);
      res.write(`data: ${JSON.stringify({ error: 'API error: ' + errText })}\n\n`);
      res.end();
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed === 'data: [DONE]') continue;

        if (trimmed.startsWith('data: ')) {
          try {
            const json = JSON.parse(trimmed.slice(6));
            const text = json.choices?.[0]?.delta?.content;
            if (text) {
              res.write(`data: ${JSON.stringify({ text })}\n\n`);
            }
          } catch (e) {
            console.log('Parse skip:', trimmed.slice(0, 50));
          }
        }
      }
    }

    res.write('data: [DONE]\n\n');
    res.end();

  } catch (err) {
    console.error('Chat error:', err.message);
    res.write(`data: ${JSON.stringify({ error: err.message })}\n\n`);
    res.end();
  }
});

module.exports = router;