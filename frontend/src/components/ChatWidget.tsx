import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useLocation } from 'react-router-dom'
import Markdown from 'react-markdown'
import { clearChatHistory, fetchChatHistory, sendChat, type ChatTurn, type Product } from '../api'
import { useAuth } from '../auth'
import { OPEN_CHAT } from '../chatBus'
import Bulldog from './Bulldog'
import { useChatResults } from '../chatResults'
import { RESULTS_ID } from './AssistantResults'

interface Message extends ChatTurn {
  products?: Product[]
  title?: string
}

const greeting = (firstName?: string | null): Message => ({
  role: 'assistant',
  content: firstName
    ? `Welcome back, ${firstName}! Woof. Ask me about hoodies, tees, sizes, or prices.`
    : "Woof! I'm **Dan**, the Campus Customs assistant. Ask me about hoodies, tees, sizes, or prices.",
})

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [messages, setMessages] = useState<Message[]>([greeting()])
  const logRef = useRef<HTMLDivElement>(null)
  const { setResults } = useChatResults()
  const { user } = useAuth()
  const { pathname } = useLocation()
  const productMatch = pathname.match(/^\/products\/([^/]+)/)
  const pageProductId = productMatch ? decodeURIComponent(productMatch[1]) : null

  // Logged in: reload saved conversation from the server. Guest or logout: start fresh.
  useEffect(() => {
    setMessages([greeting(user?.first_name)])
    if (!user) return
    let cancelled = false
    fetchChatHistory().then(saved => {
      if (cancelled || saved.length === 0) return
      setMessages([
        greeting(user.first_name),
        ...saved.map(m => ({ role: m.role, content: m.content, products: m.products, title: 'Earlier picks' })),
      ])
    })
    return () => {
      cancelled = true
    }
  }, [user])

  const suggestions = pageProductId
    ? ['Is this in stock in M?', 'What colors does this come in?', 'Show me similar items']
    : ['What hoodies do you have?', 'Gifts under $40', 'Anything for The Game?']

  // Other components (hero button, product page) can open the chat and optionally ask a question.
  const sendRef = useRef<(q: string) => void>(() => {})
  useEffect(() => {
    const onOpen = (e: Event) => {
      setOpen(true)
      const q = (e as CustomEvent<string | undefined>).detail
      if (q) sendRef.current(q)
    }
    window.addEventListener(OPEN_CHAT, onOpen)
    return () => window.removeEventListener(OPEN_CHAT, onOpen)
  }, [])

  async function onClear() {
    if (user) await clearChatHistory()
    setMessages([greeting(user?.first_name)])
    setResults(null)
  }

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, busy])

  function showOnPage(title: string, products: Product[]) {
    setResults({ title, products })
    // Wait for the section to render, then bring it into view.
    requestAnimationFrame(() => document.getElementById(RESULTS_ID)?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    await send(input)
  }

  sendRef.current = (q: string) => void send(q)

  async function send(raw: string) {
    const text = raw.trim()
    if (!text || busy) return
    // Guests send prior turns (minus the greeting); logged-in history is loaded server-side.
    const history = messages.slice(1).map(({ role, content }) => ({ role, content }))
    setInput('')
    setMessages(m => [...m, { role: 'user', content: text }])
    setBusy(true)
    try {
      const res = await sendChat(text, user ? [] : history, { path: pathname, product_id: pageProductId })
      setMessages(m => [...m, { role: 'assistant', content: res.reply, products: res.products, title: res.results_title ?? 'Matching products' }])
      if (res.products.length > 0) showOnPage(res.results_title ?? 'Matching products', res.products)
    } catch (err) {
      setMessages(m => [...m, { role: 'assistant', content: `Sorry, something went wrong: ${(err as Error).message}` }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="chat">
      {open && (
        <div className="chat-panel" role="dialog" aria-label="Shopping assistant">
          <div className="chat-head">
            <Bulldog size={40} mood={busy ? 'thinking' : 'happy'} />
            <div className="chat-title">
              <strong>Dan · Shopping Assistant</strong>
              <small>{user ? 'History saved to your account' : 'Guest chat · log in to save history'}</small>
            </div>
            <div className="chat-head-actions">
              <button onClick={onClear} title="Start a new conversation" aria-label="Clear conversation">⟲</button>
              <button onClick={() => setOpen(false)} aria-label="Close chat">×</button>
            </div>
          </div>
          <div className="chat-log" ref={logRef}>
            {messages.map((m, i) => (
              <div key={i} className={`msg-wrap ${m.role}`}>
                <div className={`msg ${m.role}`}>
                  {m.role === 'assistant' ? <Markdown>{m.content}</Markdown> : m.content}
                </div>
                {m.products && m.products.length > 0 && (
                  <button className="show-results" onClick={() => showOnPage(m.title ?? 'Matching products', m.products!)}>
                    {m.products.length} {m.products.length === 1 ? 'item' : 'items'} shown on the page ↑
                  </button>
                )}
              </div>
            ))}
            {busy && (
              <div className="msg assistant typing" aria-label="Dan is checking the shelves">
                <span className="dots"><i /><i /><i /></span> Checking the shelves…
              </div>
            )}
          </div>
          {!busy && (
            <div className="suggestions" aria-label="Suggested questions">
              {suggestions.map(q => (
                <button key={q} type="button" onClick={() => send(q)}>{q}</button>
              ))}
            </div>
          )}
          <form className="chat-form" onSubmit={onSubmit}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={pageProductId ? 'Ask about this product…' : 'Ask about products…'}
              maxLength={2000}
            />
            <button type="submit" disabled={busy}>Send</button>
          </form>
        </div>
      )}
      <button className={`chat-toggle ${open ? 'is-open' : ''}`} onClick={() => setOpen(o => !o)} aria-label={open ? 'Close chat' : 'Chat with Dan'}>
        {open ? <span className="close-x">×</span> : <Bulldog size={52} />}
        {!open && <span className="chat-bubble-hint">Ask Dan!</span>}
      </button>
    </div>
  )
}
