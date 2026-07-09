import { useAtom } from 'jotai'
import { isTypingAtom } from '../atoms'
import { Message } from '../hooks/useChat'

interface ChatWindowProps {
  messages: Message[]
}

export function ChatWindow({ messages }: ChatWindowProps) {
  const [isTyping] = useAtom(isTypingAtom)

  const formatMessage = (content: string) => {
    // Detect SQL in the message and wrap it in a monospace block
    const sqlRegex = /SELECT.*?FROM.*?(?:;|$)/gis
    const parts = content.split(sqlRegex)
    const matches = content.match(sqlRegex) || []
    
    return parts.map((part, i) => (
      <span key={i}>
        {part}
        {matches[i] && (
          <pre className="bg-gray-800 text-green-400 p-2 rounded mt-2 mb-2 overflow-x-auto">
            <code>{matches[i]}</code>
          </pre>
        )}
      </span>
    ))
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[70%] rounded-lg p-3 ${
              msg.role === 'user'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-800'
            }`}
          >
            {msg.role === 'assistant' ? formatMessage(msg.content) : msg.content}
          </div>
        </div>
      ))}
      {isTyping && (
        <div className="flex justify-start">
          <div className="bg-gray-200 text-gray-800 rounded-lg p-3">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100" />
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200" />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}