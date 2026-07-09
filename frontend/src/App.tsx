import { useState } from 'react'
import { ChatWindow } from './components/chatWindow'
import { ChatInput } from './components/chatInput'
import { Message } from './hooks/useChat'
import './App.css'

function App() {
  const [messages, setMessages] = useState<Message[]>([])

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b p-4">
        <h1 className="text-xl font-bold text-gray-800">Retail Lakehouse Chat</h1>
      </header>
      <ChatWindow messages={messages} />
      <ChatInput messages={messages} />
    </div>
  )
}

export default App