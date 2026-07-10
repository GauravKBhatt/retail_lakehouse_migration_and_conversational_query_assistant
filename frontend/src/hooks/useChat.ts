import { useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function useChat() {
  const qc = useQueryClient()
  
  return useMutation({
    mutationFn: ({ messages, model }: { messages: Message[], model: string }) => 
      axios.post('http://localhost:8000/chat', { messages, model }).then(r => r.data),
    onSuccess: (data, variables) => {
      qc.setQueryData(['conversation'], (prev: any) => [...(prev || []), variables.messages[variables.messages.length - 1], data])
    }
  })
}