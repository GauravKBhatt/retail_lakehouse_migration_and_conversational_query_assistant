import { useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function useChat() {
  const qc = useQueryClient()
  
  return useMutation({
    mutationFn: (messages: Message[]) => 
      axios.post('http://localhost:8000/chat', { messages }).then(r => r.data),
    onSuccess: (data, variables) => {
      // qc.setQueryData(['conversation'], (prev: any) => [...(prev || []), ...variables, data])
      // the problem was thay variables contained the entire message array (including previous messages), so spreading it suplicates the conversation history. 
      qc.setQueryData(['conversation'], (prev: any) => [...(prev || []), variables[variables.length - 1], data])
      // qc.setQueryData(['conversation'], (prev: any) => [...(prev || []), variables[variables.length - 1], data])
    }
  })
}