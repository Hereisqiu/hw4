import { createContext, useContext, useState, type ReactNode } from 'react'
import type { Product } from './api'

export interface ChatResults {
  title: string
  products: Product[]
}

interface ChatResultsState {
  results: ChatResults | null
  setResults: (r: ChatResults | null) => void
}

const ChatResultsContext = createContext<ChatResultsState | null>(null)

// Holds the latest product matches from the assistant so any page can show them.
export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ChatResults | null>(null)
  return <ChatResultsContext.Provider value={{ results, setResults }}>{children}</ChatResultsContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useChatResults() {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside ChatResultsProvider')
  return ctx
}
