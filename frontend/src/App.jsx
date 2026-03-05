import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Settings, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [mode, setMode] = useState('explain')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: input,
          mode: mode,
          history: messages
        })
      })

      const data = await response.json()

      const assistantMessage = {
        role: 'assistant',
        content: data.result || "I'm sorry, I couldn't process that."
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

  return (
    <div className="app-container">
      <header>
        <div className="logo-area">
          <h1>SLM Mentor</h1>
        </div>
        <div className="controls">
          <div className="mode-toggle">
            <button
              className={`mode-btn ${mode === 'id_only' ? 'active' : ''}`}
              onClick={() => setMode('id_only')}
            >
              ID Only
            </button>
            <button
              className={`mode-btn ${mode === 'explain' ? 'active' : ''}`}
              onClick={() => setMode('explain')}
            >
              Explain
            </button>
          </div>
        </div>
      </header>

      <main className="chat-window">
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
      </main>
    </div>
  )
}

export default App
