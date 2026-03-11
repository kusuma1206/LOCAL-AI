import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles, MessageSquare, Upload, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [view, setView] = useState('chat') // 'chat' or 'ingest'
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  // Ingestion State
  const [file, setFile] = useState(null)
  const [docTitle, setDocTitle] = useState('')
  const [uploadedBy, setUploadedBy] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStatus, setUploadStatus] = useState('idle') // 'idle', 'uploading', 'success', 'error'
  const [errorMessage, setErrorMessage] = useState('')
  const fileInputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    if (view === 'chat') {
      scrollToBottom()
    }
  }, [messages, view])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: input,
          mode: 'explain',
          history: messages
        })
      })

      const data = await response.json()
      let displayContent = ""

      if (data.result.formatted_answer) {
        displayContent = data.result.formatted_answer
      } else if (typeof data.result === 'object' && data.result !== null) {
        if (data.result.retrieved_context) {
          displayContent = "### Retrieval Results (NOLLM)\n\n"
          data.result.retrieved_context.forEach(item => {
            if (item.type === 'global_summary') {
              displayContent += `#### 📄 Document Overview\n${item.content}\n\n`
            } else if (item.type === 'section') {
              displayContent += `#### 📑 Section: ${item.title}\n${item.content}\n\n`
            } else if (item.type === 'chunk') {
              displayContent += `> ${item.content}\n\n`
            }
          })
          if (data.result.primary_doc_id) {
            const filenameStr = data.result.primary_filename ? ` - ${data.result.primary_filename}` : ""
            displayContent += `---\n*Source Document: ID ${data.result.primary_doc_id}${filenameStr}*`
          }
        } else if (typeof data.result === 'object') {
          displayContent = "### Document Information\n" + JSON.stringify(data.result, null, 2)
        }
      } else {
        displayContent = data.result || "I'm sorry, I couldn't process that."
      }

      const assistantMessage = {
        role: 'assistant',
        content: displayContent
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Error: Could not connect to the SLM backend."
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = () => {
    if (!file || !docTitle || !uploadedBy) {
      setUploadStatus('error')
      setErrorMessage('Please fill in all fields and select a file.')
      return
    }

    setUploadStatus('uploading')
    setUploadProgress(0)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_title', docTitle)
    formData.append('uploaded_by', uploadedBy)
    formData.append('timestamp', new Date().toISOString())

    const xhr = new XMLHttpRequest()

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100)
        setUploadProgress(percent)
      }
    }

    xhr.onload = () => {
      if (xhr.status === 200 || xhr.status === 201) {
        setUploadStatus('success')
        setFile(null)
        setDocTitle('')
        setUploadedBy('')
      } else {
        setUploadStatus('error')
        try {
          const errorData = JSON.parse(xhr.responseText)
          setErrorMessage(errorData.detail || `Upload failed: ${xhr.statusText}`)
        } catch {
          setErrorMessage(`Upload failed: ${xhr.statusText}`)
        }
      }
    }

    xhr.onerror = () => {
      setUploadStatus('error')
      setErrorMessage('Network error occurred during upload.')
    }

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    xhr.open('POST', `${API_URL}/upload-document`)
    xhr.send(formData)
  }

  return (
    <div className="app-container">
      <header>
        <div className="logo-area">
          <h1>SLM Mentor <span style={{ fontSize: '0.6rem', opacity: 0.5 }}>v1.1</span></h1>
        </div>
        <div className="nav-tabs">
          <button
            className={`nav-btn ${view === 'chat' ? 'active' : ''}`}
            onClick={() => setView('chat')}
          >
            <MessageSquare size={18} />
            Chat
          </button>
          <button
            className={`nav-btn ${view === 'ingest' ? 'active' : ''}`}
            onClick={() => setView('ingest')}
          >
            <Upload size={18} />
            Ingest
          </button>
        </div>
        <div className="controls">
        </div>
      </header>

      <main className="chat-window">
        {view === 'chat' ? (
          <>
            <div className="messages-container">
              {messages.length === 0 && (
                <div className="empty-state" style={{ textAlign: 'center', marginTop: '100px', color: '#64748b' }}>
                  <Bot size={64} style={{ marginBottom: '20px', opacity: 0.5 }} />
                  <h2>Hello! I'm your SLM Technical Mentor.</h2>
                  <p>Ask me anything about your documents.</p>
                </div>
              )}
              {messages.map((msg, index) => (
                <div key={index} className={`message ${msg.role}`}>
                  <div className="message-header" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', opacity: 0.7, fontSize: '0.8rem' }}>
                    {msg.role === 'user' ? <User size={14} /> : <Sparkles size={14} />}
                    <span>{msg.role === 'user' ? 'You' : 'SLM Assistant'}</span>
                  </div>
                  <div className="markdown-content">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="message assistant loading">
                  <div className="typing-indicator" style={{ display: 'flex', gap: '4px' }}>
                    <div className="dot">.</div>
                    <div className="dot">.</div>
                    <div className="dot">.</div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="input-area">
              <input
                type="text"
                placeholder="Type your technical question..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                disabled={isLoading}
              />
              <button onClick={handleSend} disabled={isLoading || !input.trim()}>
                <Send size={20} />
              </button>
            </div>
          </>
        ) : (
          <div className="ingestion-container animate-fade-in">
            <div className="ingestion-form">
              <div className="form-header" style={{ marginBottom: '20px' }}>
                <h2>Document Ingestion</h2>
                <p style={{ color: '#94a3b8' }}>Upload new documents to the knowledge base for indexing.</p>
              </div>

              <div className="form-group">
                <label>Document Title</label>
                <input
                  type="text"
                  placeholder="e.g., System Architecture Guide"
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Uploaded By</label>
                <input
                  type="text"
                  placeholder="Your Name"
                  value={uploadedBy}
                  onChange={(e) => setUploadedBy(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Document File (PDF, DOCX, MD)</label>
                <div
                  className="file-drop-area"
                  onClick={() => fileInputRef.current.click()}
                >
                  <Upload size={32} color="#3b82f6" />
                  {file ? (
                    <div className="file-info">
                      <FileText size={18} />
                      <span>{file.name}</span>
                    </div>
                  ) : (
                    <p>Click to select or drag and drop file here</p>
                  )}
                  <input
                    type="file"
                    ref={fileInputRef}
                    style={{ display: 'none' }}
                    accept=".pdf,.docx,.md"
                    onChange={(e) => setFile(e.target.files[0])}
                  />
                </div>
              </div>

              {uploadStatus === 'uploading' && (
                <div className="upload-progress-section">
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.9rem' }}>
                    <span>Uploading...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="progress-container">
                    <div className="progress-bar" style={{ width: `${uploadProgress}%` }}></div>
                  </div>
                </div>
              )}

              {uploadStatus === 'success' && (
                <div className="status-message success">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                    <CheckCircle size={18} />
                    <span>Document uploaded and sent for indexing.</span>
                  </div>
                </div>
              )}

              {uploadStatus === 'error' && (
                <div className="status-message error">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                    <AlertCircle size={18} />
                    <span>{errorMessage}</span>
                  </div>
                </div>
              )}

              <button
                className="upload-btn"
                style={{ marginTop: '20px', gap: '8px' }}
                onClick={handleFileUpload}
                disabled={uploadStatus === 'uploading'}
              >
                {uploadStatus === 'uploading' ? <Loader2 className="animate-spin" size={20} /> : <Upload size={20} />}
                Upload Document
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App

