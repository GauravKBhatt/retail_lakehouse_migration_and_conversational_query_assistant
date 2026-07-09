import { useAtom, useSetAtom } from 'jotai'
import { inputAtom, isTypingAtom } from '../atoms'
import { useChat } from '../hooks/useChat'
import type { Message } from '../hooks/useChat'

interface ChatInputProps {
  messages: Message[]
}

export function ChatInput({ messages }: ChatInputProps) {
  const [input, setInput] = useAtom(inputAtom)
  const setIsTyping = useSetAtom(isTypingAtom)
  const chat = useChat()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage: Message = { role: 'user', content: input }
    const newMessages = [...messages, userMessage]

    setIsTyping(true)
    setInput('')

    try {
      await chat.mutateAsync(newMessages)
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-200 bg-white px-4 py-3 shrink-0">
      <div className="flex gap-2 items-center max-w-4xl mx-auto">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your retail data..."
          className="flex-1 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-shadow placeholder:text-gray-400"
          disabled={chat.isPending}
        />
        <button
          type="submit"
          disabled={chat.isPending || !input.trim()}
          className="bg-teal-600 text-white px-5 py-2.5 rounded-xl hover:bg-teal-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-sm font-medium flex items-center gap-1.5"
        >
          {chat.isPending ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Sending
            </>
          ) : (
            <>
              Send
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </>
          )}
        </button>
      </div>
    </form>
  )
}
