import { useQuery } from '@tanstack/react-query'
import { ChatWindow } from './components/chatWindow'
import { ChatInput } from './components/chatInput'

export default function App() {
  const { data: messages = [] } = useQuery({
    queryKey: ['conversation'],
    initialData: [],
  })

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-[#0D2B36] border-b border-teal-800/30 px-6 py-3 flex items-center gap-3 shrink-0">
        <img src="/ycotek-logo.svg" alt="YCOTEK" className="h-7" />
        <span className="text-white/40 text-sm font-light ml-auto">Retail Lakehouse AI</span>
      </header>
      <ChatWindow messages={messages} />
      <ChatInput messages={messages} />
    </div>
  )
}
