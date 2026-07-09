import { useAtom, useSetAtom } from 'jotai'
import { inputAtom, isTypingAtom } from '../atoms'
import { useChat, Message } from '../hooks/useChat'

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
    <form onSubmit={handleSubmit} className="border-t p-4 flex gap-2">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask about your retail data..."
        className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        disabled={chat.isPending}
      />
      <button
        type="submit"
        disabled={chat.isPending || !input.trim()}
        className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        {chat.isPending ? 'Sending...' : 'Send'}
      </button>
    </form>
  )
}