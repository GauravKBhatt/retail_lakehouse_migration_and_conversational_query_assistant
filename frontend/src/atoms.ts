import { atom } from 'jotai'

export const inputAtom = atom('')
export const isTypingAtom = atom(false)
export const asOfDateAtom = atom<string | null>(null) // time-travel pin

export const modelsAtom = atom([
  { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash", provider: "Gemini" },
  { id: "gemini-1.5-pro", name: "Gemini 1.5 Pro", provider: "Gemini" },
  { id: "meta-llama/llama-4-scout-17b-16e-instruct", name: "Llama 4 Scout 17B", provider: "Groq" },
  { id: "qwen/qwen3-32b", name: "Qwen 3 32B", provider: "Groq" },
  { id: "openai/gpt-oss-20b", name: "GPT-OSS 20B", provider: "Groq" },
  { id: "qwen/qwen3.6-27b", name: "Qwen 3.6 27B", provider: "Groq" },
  { id: "groq/gpt-oss-120b", name: "GPT-OSS 120B", provider: "Groq" },
])

export const selectedModelAtom = atom("gemini-2.5-flash")