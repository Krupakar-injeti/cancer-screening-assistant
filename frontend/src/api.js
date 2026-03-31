const BASE_URL = import.meta.env.VITE_API_URL || '';

export async function uploadReport(file) {
  const formData = new FormData();
  formData.append('report', file);

  const res = await fetch(`${BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || 'Upload failed');
  }

  return data;
}

export async function* streamChat(documentData, question, language = 'English') {
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ documentData, question, language })
  });

  if (!res.ok) {
    throw new Error('Chat request failed');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const lines = decoder.decode(value, { stream: true }).split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ') && line !== 'data: [DONE]') {
        try {
          const json = JSON.parse(line.slice(6));
          if (json.error) throw new Error(json.error);
          if (json.text) yield json.text;
        } catch (e) {
          if (e.message && !e.message.includes('JSON')) throw e;
        }
      }
    }
  }
}
