import { useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

export interface Message {
  role: 'user' | 'assistant'
  content: string
}

function getSessionId(): string {
  let id = localStorage.getItem('chat_session_id')
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem('chat_session_id', id)
  }
  return id
}

export function useChat() {
  const qc = useQueryClient()
  
  return useMutation({
    mutationFn: ({ messages, model }: { messages: Message[], model: string }) => 
      axios.post('http://localhost:8000/chat', {
        messages,
        model,
        session_id: getSessionId(),
      }).then(r => r.data),
    onSuccess: (data, variables) => {
      qc.setQueryData(['conversation'], (prev: any) => [...(prev || []), variables.messages[variables.messages.length - 1], data])
    }
  })
}
