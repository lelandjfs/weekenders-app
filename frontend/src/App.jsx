import React, { useState } from 'react'

const API_URL = 'http://localhost:8000'

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hey! Where are you heading this weekend? Tell me a city and I'll find concerts, restaurants, events, and cool spots for you." }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    // Add thinking message
    setMessages(prev => [...prev, { role: 'assistant', content: '🔍 Searching all sources...', isLoading: true }])

    try {
      const response = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city: userMessage, weekend: 'next' })
      })

      const data = await response.json()
      setResults(data)

      // Remove loading message and add results
      setMessages(prev => {
        const filtered = prev.filter(m => !m.isLoading)
        return [...filtered, {
          role: 'assistant',
          content: formatResults(data),
          data: data
        }]
      })
    } catch (error) {
      setMessages(prev => {
        const filtered = prev.filter(m => !m.isLoading)
        return [...filtered, {
          role: 'assistant',
          content: `❌ Error: ${error.message}. Make sure the backend is running (uvicorn main:app --reload)`
        }]
      })
    }

    setLoading(false)
  }

  const formatResults = (data) => {
    // Use Claude's formatted output if available
    if (data.formatted_output) {
      return data.formatted_output
    }

    const { concerts, dining, events, locations, metadata } = data
    return `Found ${metadata.total_results} results for ${data.city}:

🎵 **Concerts**: ${concerts.count} shows
🍽️ **Dining**: ${dining.count} restaurants
🎭 **Events**: ${events.count} events
📍 **Locations**: ${locations.count} spots

⏱️ Searched in ${metadata.total_run_time_seconds}s`
  }

  return (
    <div className="app">
      <header>
        <h1>🌴 Weekenders</h1>
        <p>Your AI-powered weekend trip planner</p>
      </header>

      <div className="chat-container">
        <div className="messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <div className="message-content">
                {msg.content}
                {msg.data && <ResultsDisplay data={msg.data} />}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <div className="message-content loading">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
              </div>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter a city (e.g., Austin, Nashville, Portland...)"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            {loading ? '...' : 'Search'}
          </button>
        </form>
      </div>

      {results && (
        <div className="json-output">
          <h3>📋 Structured Output (JSON)</h3>
          <pre>{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

function ResultsDisplay({ data }) {
  const [activeTab, setActiveTab] = useState('concerts')

  const tabs = [
    { id: 'concerts', label: '🎵 Concerts', count: data.concerts.count },
    { id: 'dining', label: '🍽️ Dining', count: data.dining.count },
    { id: 'events', label: '🎭 Events', count: data.events.count },
    { id: 'locations', label: '📍 Spots', count: data.locations.count },
  ]

  const getItems = () => {
    switch(activeTab) {
      case 'concerts': return data.concerts.items || []
      case 'dining': return data.dining.items || []
      case 'events': return data.events.items || []
      case 'locations': return data.locations.items || []
      default: return []
    }
  }

  return (
    <div className="results-display">
      <div className="tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      <div className="results-list">
        {getItems().slice(0, 10).map((item, i) => (
          <div key={i} className="result-item">
            <strong>{item.name}</strong>
            {item.venue && <span className="venue">@ {item.venue}</span>}
            {item.date && <span className="date">{item.date}</span>}
            {item.neighborhood && <span className="neighborhood">{item.neighborhood}</span>}
            {item.rating && <span className="rating">⭐ {item.rating}</span>}
            {item.category && <span className="category">{item.category}</span>}
          </div>
        ))}
        {getItems().length === 0 && <p className="no-results">No results found</p>}
        {getItems().length > 10 && <p className="more">+{getItems().length - 10} more...</p>}
      </div>
    </div>
  )
}

export default App
