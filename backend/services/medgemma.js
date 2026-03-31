async function analyzeReport(documentData, userQuestion, language = 'English') {

  const prompt = `You are a compassionate medical assistant helping patients understand cancer screening reports.

IMPORTANT RULES:
- Respond ONLY in ${language}
- Use simple, clear, non-technical language that any patient can understand
- Be empathetic and reassuring in tone
- ALWAYS end your response with: "Please consult your doctor or oncologist for professional medical advice about these results."
- Never make a definitive diagnosis — only explain what the report says
- Highlight any values marked as abnormal and explain what they mean in simple terms

REPORT CONTENT:
${documentData.type === 'text' ? documentData.content : '[Image-based report uploaded by patient]'}

PATIENT QUESTION:
${userQuestion}

Please answer clearly and compassionately in ${language}.`;

  const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.MEDGEMMA_API_KEY}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': 'http://localhost:5173',
      'X-Title': 'CancerScreen AI'
    },
    body: JSON.stringify({
      model: 'openrouter/auto',
      messages: [
        {
          role: 'system',
          content: 'You are a helpful, compassionate medical assistant specializing in explaining cancer screening reports to patients in simple language.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      stream: true,
      max_tokens: 1000
    })
  });

  return response;
}

module.exports = { analyzeReport };