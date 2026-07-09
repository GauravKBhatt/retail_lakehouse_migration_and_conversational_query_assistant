import { atom } from 'jotai'

export const inputAtom = atom('')
export const isTypingAtom = atom(false)
export const asOfDateAtom = atom<string | null>(null) // time-travel pin