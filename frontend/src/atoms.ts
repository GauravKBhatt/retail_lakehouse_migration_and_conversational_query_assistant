import { atom } from 'jotai'

export const inputAtom = atom('')
export const isTypingAtom = atom(false)
export const asOfDateAtom = atom<string | null>(null) // time-travel pin

export const modelsAtom = atom([
  { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash", provider: "Gemini" },
  { id: "gemini-1.5-pro", name: "Gemini 1.5 Pro", provider: "Gemini" },
  { id: "groq-llama3-70b", name: "Llama3 70B", provider: "Groq" },
  { id: "groq-llama3-8b", name: "Llama3 8B", provider: "Groq" },
  { id: "groq-mixtral", name: "Mixtral 8x7B", provider: "Groq" },
  { id: "groq-gemma", name: "Gemma 7B", provider: "Groq" },
  { id: "groq/gpt-oss-120b", name: "GPT-OSS 120B", provider: "Groq" },
])
export const selectedModelAtom = atom("gemini-2.5-flash")