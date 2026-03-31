# CancerScreen AI
### Medical Document Conversational Framework for Reliable Cancer Screening Assistance

> Final Year Project | Computer Science & IT

---

## Overview

CancerScreen AI is a real-time conversational web application that allows patients to upload hospital cancer screening reports (PDF or image) and ask questions about them in plain, simple language. The AI responds using Google's MedGemma model and supports multiple languages.

---

## Features

- **Document Upload** — PDF, JPG, PNG up to 20MB
- **Real-time Streaming** — AI answers stream word-by-word
- **Multi-language Support** — 13 languages including Hindi, Bengali, Tamil, Telugu
- **Chat History** — Save and reload past sessions (localStorage)
- **Download as PDF** — Export AI summaries as formatted PDF
- **Medical Disclaimer** — Shown on first launch
- **Rate Limiting** — Prevents API abuse
- **Mobile Responsive** — Works on all screen sizes

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite |
| Backend | Node.js, Express |
| AI Model | Google MedGemma (via Gemini API) |
| File Parsing | pdf-parse, multer |
| PDF Export | jsPDF |
| Rate Limiting | express-rate-limit |

---

## Setup Instructions

### Prerequisites
- Node.js v18 or higher
- Google AI API Key (from https://aistudio.google.com)

### Installation

**1. Clone or download the project**
```bash
cd cancer-screening-assistant
```

**2. Setup Backend**
```bash
cd backend
npm install
```

Create `.env` file:
```
MEDGEMMA_API_KEY=your_google_ai_api_key_here
PORT=5000
```

**3. Setup Frontend**
```bash
cd ../frontend
npm install
```

### Running the Project

Open two terminals in VS Code:

**Terminal 1 — Backend:**
```bash
cd backend
node server.js
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open browser at: **http://localhost:5173**

---

## Deployment

- **Backend** → [Render.com](https://render.com) — connect repo, set root to `/backend`, add `MEDGEMMA_API_KEY` env var
- **Frontend** → [Vercel.com](https://vercel.com) — connect repo, set root to `/frontend`, add `VITE_API_URL=https://your-render-url.onrender.com`

---

## Project Structure

```
cancer-screening-assistant/
├── frontend/
│   ├── src/
│   │   ├── App.jsx          ← Main React component (all features)
│   │   ├── api.js           ← API calls (upload + streaming chat)
│   │   ├── index.css        ← Full dark medical theme
│   │   └── main.jsx         ← React entry point
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── backend/
│   ├── routes/
│   │   ├── chat.js          ← Streaming chat endpoint
│   │   └── upload.js        ← File upload + parsing endpoint
│   ├── services/
│   │   ├── medgemma.js      ← Google AI / MedGemma integration
│   │   └── parser.js        ← PDF and image text extraction
│   ├── server.js            ← Express server with rate limiting
│   ├── .env                 ← API keys (never commit this)
│   └── package.json
├── .gitignore
└── README.md
```

---

## Disclaimer

This application is for educational and informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified doctor or oncologist.

---

*Developed as Final Year Project — Computer Science & IT*
