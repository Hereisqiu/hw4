export interface InventoryItem {
  size: string
  quantity: number
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  price: number
  inventory?: InventoryItem[]
  total_stock?: number
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export const fetchProducts = () => getJson<Product[]>('/api/products')
export const fetchProduct = (id: string) => getJson<Product>(`/api/products/${encodeURIComponent(id)}`)

export const formatPrice = (p: number) => `$${p.toFixed(2)}`

export interface User {
  id: number
  name: string
  email: string
  first_name: string | null
  last_name: string | null
  created_at: string
}

async function postJson<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = data.detail
    throw new Error(Array.isArray(detail) ? detail.map((d: { msg: string }) => d.msg).join('; ') : detail || res.statusText)
  }
  return data as T
}

export const register = (b: { first_name: string; last_name: string; email: string; password: string }) =>
  postJson<User>('/api/auth/register', b)
export const login = (email: string, password: string) => postJson<User>('/api/auth/login', { email, password })
export const logout = () => postJson<{ ok: boolean }>('/api/auth/logout')
export const fetchMe = async (): Promise<User | null> => {
  const res = await fetch('/api/auth/me', { credentials: 'include' })
  return res.ok ? res.json() : null
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  reply: string
  results_title: string | null
  products: Product[]
}

export interface PageContext {
  path: string
  product_id: string | null
}

export interface StoredMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  products: Product[]
  created_at: string
}

export const sendChat = (message: string, history: ChatTurn[], page: PageContext) =>
  postJson<ChatResponse>('/api/chat', { message, history: history.slice(-20), page })

export const fetchChatHistory = async (): Promise<StoredMessage[]> => {
  const res = await fetch('/api/chat/history', { credentials: 'include' })
  return res.ok ? res.json() : []
}

export const clearChatHistory = () => fetch('/api/chat/history', { method: 'DELETE', credentials: 'include' })
