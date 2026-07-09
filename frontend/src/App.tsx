import { useQuery } from '@tanstack/react-query'
import { ChatWindow } from './components/chatWindow'
import { ChatInput } from './components/chatInput'
import './App.css'

function App() {
  const { data: messages = [] } = useQuery({
    queryKey: ['conversation'],
    initialData: [],
  })

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