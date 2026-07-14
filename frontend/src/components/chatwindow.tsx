import { useAtom } from 'jotai'
import { isTypingAtom } from '../atoms'
import type { Message } from '../hooks/useChat'

interface ChatWindowProps {
  messages: Message[]
}

export function ChatWindow({ messages }: ChatWindowProps) {
  const [isTyping] = useAtom(isTypingAtom)

  const formatMessage = (content: string) => {
    const sqlRegex = /SELECT.*?FROM.*?(?:;|$)/gis
    const parts = content.split(sqlRegex)
    const matches = content.match(sqlRegex) || []
    
    const renderTable = (text: string) => {
      const lines = text.trim().split('\n').filter(line => line.trim())
      if (lines.length < 2) return <p className="whitespace-pre-wrap">{text}</p>
      
      // Check if it looks like a table (has pipe separators)
      const hasPipes = lines.some(line => line.includes('|'))
      if (!hasPipes) return <p className="whitespace-pre-wrap">{text}</p>
      
      const rows = lines.map(line => 
        line.split('|').map(cell => cell.trim()).filter(cell => cell)
      )
      
      if (rows.length < 2 || rows.some(row => row.length === 0)) {
        return <p className="whitespace-pre-wrap">{text}</p>
      }
      
      return (
        <div className="overflow-x-auto mt-3 mb-3">
          <table className="min-w-full border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-gray-50">
              <tr>
                {rows[0].map((cell, i) => (
                  <th key={i} className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b">
                    {cell}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {rows.slice(1).map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-gray-50">
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )
    }
    
    return parts.map((part, i) => (
      <span key={i}>
        {renderTable(part)}
        {matches[i] && (
          <pre className="bg-gray-900 text-[#FFA62B] p-3 rounded-lg mt-2 mb-2 overflow-x-auto text-sm leading-relaxed">
            <code>{matches[i]}</code>
          </pre>
        )}
      </span>
    ))
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
      {messages.length === 0 && !isTyping && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-teal-50 flex items-center justify-center">
              <svg className="w-8 h-8 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-gray-700 mb-1">Ask your retail data</h2>
            <p className="text-sm text-gray-400">Ask questions about sales, products, stores, and more using natural language.</p>
          </div>
        </div>
      )}
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} items-end gap-2`}
        >
          {msg.role === 'assistant' && (
            <div className="w-7 h-7 rounded-full bg-teal-600 flex items-center justify-center shrink-0">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          )}
          <div
            className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${
              msg.role === 'user'
                ? 'bg-teal-600 text-white rounded-br-sm'
                : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm shadow-sm'
            }`}
          >
            {msg.role === 'assistant' ? formatMessage(msg.content) : msg.content}
          </div>
        </div>
      ))}
      {isTyping && (
        <div className="flex justify-start items-end gap-2">
          <div className="w-7 h-7 rounded-full bg-teal-600 flex items-center justify-center shrink-0">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-teal-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce [animation-delay:0.15s]" />
              <div className="w-2 h-2 bg-teal-600 rounded-full animate-bounce [animation-delay:0.3s]" />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
