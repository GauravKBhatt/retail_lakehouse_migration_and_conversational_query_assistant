import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChatWindow } from './components/chatWindow'
import { ChatInput } from './components/chatInput'
import { LogsPanel } from './components/LogsPanel'

export default function App() {
  const [logsOpen, setLogsOpen] = useState(false)
  const { data: messages = [] } = useQuery({
    queryKey: ['conversation'],
    initialData: [],
  })

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-[#0D2B36] border-b border-teal-800/30 px-6 py-3 flex items-center gap-3 shrink-0">
        <img src="/ycotek-logo.svg" alt="YCOTEK" className="h-7" />
        <button
          onClick={() => setLogsOpen(true)}
          className="ml-auto text-white/60 hover:text-white text-sm font-light flex items-center gap-1.5 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Logs
        </button>
        <span className="text-white/40 text-sm font-light">Retail Lakehouse AI</span>
      </header>
      <ChatWindow messages={messages} />
      <ChatInput messages={messages} />
      <LogsPanel open={logsOpen} onClose={() => setLogsOpen(false)} />
    </div>
  )
}
