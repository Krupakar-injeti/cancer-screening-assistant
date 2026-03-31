import { useState, useRef, useEffect } from 'react'
import { uploadReport, streamChat } from './api'
import jsPDF from 'jspdf'

const STORAGE_KEY = 'cancerscreen_chat_history'
const DISCLAIMER_KEY = 'cancerscreen_disclaimer_accepted'

const LANGUAGES = [
  'English', 'Hindi', 'Bengali', 'Tamil', 'Telugu',
  'Marathi', 'Gujarati', 'Kannada', 'Malayalam',
  'Spanish', 'French', 'Arabic', 'Portuguese'
]

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []
  } catch {
    return []
  }
}

export default function App() {
  const [showDisclaimer, setShowDisclaimer] = useState(
    !localStorage.getItem(DISCLAIMER_KEY)
  )
  const [documentData, setDocumentData] = useState(null)
  const [fileName, setFileName] = useState('')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [language, setLanguage] = useState('English')
  const [sessions, setSessions] = useState(loadHistory)
  const [showHistory, setShowHistory] = useState(false)
  const [activeSession, setActiveSession] = useState(null)

  const fileRef = useRef()
  const chatEndRef = useRef()
  const inputRef = useRef()

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const acceptDisclaimer = () => {
    localStorage.setItem(DISCLAIMER_KEY, 'true')
    setShowDisclaimer(false)
  }

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setUploadError('')
    setUploading(true)
    setMessages([])
    setDocumentData(null)

    try {
      const result = await uploadReport(file)
      setDocumentData(result.documentData)
      setFileName(file.name)
      setMessages([{
        role: 'assistant',
        text: `Report loaded successfully: **${file.name}**\n\nI have read your medical report. You can now ask me anything about it — I will explain it in simple, easy-to-understand language in ${language}.\n\nSome questions you could ask:\n• What does this report mean overall?\n• Are there any abnormal values?\n• What type of cancer screening is this?\n• What should I do next?`
      }])
    } catch (err) {
      setUploadError(err.message || 'Failed to upload file. Please try again.')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const handleSend = async () => {
    if (!input.trim() || !documentData || loading) return

    const question = input.trim()
    setInput('')
    setLoading(true)

    const userMsg = { role: 'user', text: question }
    setMessages(prev => [...prev, userMsg, { role: 'assistant', text: '' }])

    try {
      let response = ''
      for await (const chunk of streamChat(documentData, question, language)) {
        response += chunk
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = { role: 'assistant', text: response }
          return updated
        })
      }
    } catch (err) {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          text: 'Sorry, something went wrong. Please check your API key or try again.'
        }
        return updated
      })
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const saveSession = () => {
    if (messages.length === 0) return
    const session = {
      id: Date.now(),
      name: fileName || `Session ${new Date().toLocaleDateString()}`,
      language,
      messages,
      date: new Date().toISOString()
    }
    const updated = [session, ...sessions].slice(0, 15)
    setSessions(updated)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    setActiveSession(session.id)
    alert('Session saved!')
  }

  const loadSession = (session) => {
    setMessages(session.messages)
    setActiveSession(session.id)
    setLanguage(session.language || 'English')
    setFileName(session.name)
    setShowHistory(false)
  }

  const deleteSession = (id, e) => {
    e.stopPropagation()
    const updated = sessions.filter(s => s.id !== id)
    setSessions(updated)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    if (activeSession === id) setActiveSession(null)
  }

  const clearAllHistory = () => {
    if (confirm('Delete all saved sessions?')) {
      setSessions([])
      localStorage.removeItem(STORAGE_KEY)
      setActiveSession(null)
    }
  }

  const downloadPDF = () => {
    const doc = new jsPDF()
    const aiMessages = messages.filter(m => m.role === 'assistant')
    const userMessages = messages.filter(m => m.role === 'user')

    doc.setFillColor(15, 25, 20)
    doc.rect(0, 0, 210, 40, 'F')

    doc.setTextColor(127, 221, 186)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(18)
    doc.text('CancerScreen AI — Report Summary', 20, 18)

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    doc.setTextColor(200, 200, 200)
    doc.text(`Report: ${fileName}`, 20, 27)
    doc.text(`Date: ${new Date().toLocaleDateString()}   Language: ${language}`, 20, 33)

    doc.setFillColor(255, 243, 205)
    doc.rect(15, 44, 180, 12, 'F')
    doc.setTextColor(120, 80, 0)
    doc.setFontSize(8)
    doc.text('DISCLAIMER: This is an AI-generated summary for informational purposes only. Always consult a qualified doctor.', 20, 52)

    let y = 65
    doc.setTextColor(0, 0, 0)

    messages.forEach((msg, i) => {
      if (y > 270) { doc.addPage(); y = 20 }

      if (msg.role === 'user') {
        doc.setFillColor(230, 245, 255)
        doc.setDrawColor(100, 160, 220)
        doc.setFont('helvetica', 'bold')
        doc.setFontSize(10)
        doc.setTextColor(20, 60, 120)
        const lines = doc.splitTextToSize(`Question: ${msg.text}`, 170)
        const boxH = lines.length * 6 + 8
        doc.roundedRect(15, y - 4, 180, boxH, 2, 2, 'FD')
        lines.forEach(line => {
          if (y > 270) { doc.addPage(); y = 20 }
          doc.text(line, 20, y)
          y += 6
        })
        y += 6
      } else {
        doc.setFont('helvetica', 'normal')
        doc.setFontSize(10)
        doc.setTextColor(30, 30, 30)
        const lines = doc.splitTextToSize(msg.text, 170)
        lines.forEach(line => {
          if (y > 270) { doc.addPage(); y = 20 }
          doc.text(line, 20, y)
          y += 6
        })
        y += 8
      }
    })

    doc.save(`cancerscreen-summary-${Date.now()}.pdf`)
  }

  const formatMessage = (text) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br/>')
  }

  return (
    <div className="app">

      {showDisclaimer && (
        <div className="overlay">
          <div className="disclaimer-modal">
            <div className="disclaimer-icon">⚕️</div>
            <h2>Medical Disclaimer</h2>
            <p>
              This tool uses AI to help you <strong>understand</strong> your cancer
              screening reports in plain, simple language.
            </p>
            <p>
              It is <strong>not a substitute</strong> for professional medical advice,
              diagnosis, or treatment. Always consult a qualified doctor or oncologist
              about your results.
            </p>
            <p className="disclaimer-small">
              Your documents are processed securely and not stored permanently.
            </p>
            <button className="btn-accept" onClick={acceptDisclaimer}>
              I Understand — Continue
            </button>
          </div>
        </div>
      )}

      <header className="header">
        <div className="header-left">
          <div className="logo">🧬 CancerScreen AI</div>
          <div className="logo-sub">Medical Report Assistant</div>
        </div>
        <div className="header-right">
          <select
            className="lang-select"
            value={language}
            onChange={e => setLanguage(e.target.value)}
            title="Response language"
          >
            {LANGUAGES.map(l => <option key={l}>{l}</option>)}
          </select>
          <button
            className="btn-icon"
            onClick={() => setShowHistory(!showHistory)}
            title="Chat history"
          >
            🕘 History {sessions.length > 0 && <span className="badge">{sessions.length}</span>}
          </button>
          {messages.some(m => m.role === 'assistant' && m.text) && (
            <>
              <button className="btn-icon" onClick={saveSession} title="Save session">
                💾 Save
              </button>
              <button className="btn-icon btn-download" onClick={downloadPDF} title="Download PDF">
                ⬇ PDF
              </button>
            </>
          )}
        </div>
      </header>

      {showHistory && (
        <div className="history-panel">
          <div className="history-header">
            <span>Saved sessions ({sessions.length})</span>
            {sessions.length > 0 && (
              <button className="btn-text-danger" onClick={clearAllHistory}>Clear all</button>
            )}
          </div>
          {sessions.length === 0 ? (
            <div className="history-empty">No saved sessions yet. Start a chat and click Save.</div>
          ) : (
            sessions.map(s => (
              <div
                key={s.id}
                className={`history-item ${activeSession === s.id ? 'active' : ''}`}
                onClick={() => loadSession(s)}
              >
                <div className="history-item-info">
                  <div className="history-name">📋 {s.name}</div>
                  <div className="history-meta">
                    {new Date(s.date).toLocaleDateString()} · {s.language || 'English'} · {s.messages.length} messages
                  </div>
                </div>
                <button
                  className="btn-delete"
                  onClick={(e) => deleteSession(s.id, e)}
                  title="Delete session"
                >✕</button>
              </div>
            ))
          )}
        </div>
      )}

      <div className="main">
        <div
          className={`upload-zone ${uploading ? 'uploading' : ''} ${documentData ? 'uploaded' : ''}`}
          onClick={() => !uploading && fileRef.current.click()}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,image/jpeg,image/jpg,image/png,image/webp"
            hidden
            onChange={handleUpload}
          />
          {uploading ? (
            <span>⏳ Reading your report...</span>
          ) : documentData ? (
            <span>📋 {fileName} <em>(click to upload a different report)</em></span>
          ) : (
            <span>📎 Click here to upload your hospital report <em>(PDF, JPG, PNG — up to 20MB)</em></span>
          )}
        </div>

        {uploadError && (
          <div className="error-bar">⚠️ {uploadError}</div>
        )}

        <div className="chat-area">
          {messages.length === 0 && !uploading && (
            <div className="empty-state">
              <div className="empty-icon">🏥</div>
              <div className="empty-title">Upload your report to begin</div>
              <div className="empty-sub">
                Upload any cancer screening report — mammogram, PSA, biopsy, CBC, or any hospital document.
                I will explain it to you in simple {language}.
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              {msg.role === 'assistant' && (
                <div className="avatar">🧬</div>
              )}
              <div
                className="bubble"
                dangerouslySetInnerHTML={{ __html: formatMessage(msg.text || '▌') }}
              />
              {msg.role === 'user' && (
                <div className="avatar user-avatar">👤</div>
              )}
            </div>
          ))}

          <div ref={chatEndRef} />
        </div>

        <div className="input-area">
          <input
            ref={inputRef}
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder={
              documentData
                ? `Ask about your report in ${language}...`
                : 'Upload a report first to start asking questions'
            }
            disabled={!documentData || loading}
          />
          <button
            className="btn-send"
            onClick={handleSend}
            disabled={!documentData || loading || !input.trim()}
          >
            {loading ? '⏳' : 'Send ➤'}
          </button>
        </div>

        <div className="footer-note">
          ⚕️ AI explanations only · Always consult your doctor for medical decisions
        </div>
      </div>
    </div>
  )
}
