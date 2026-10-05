import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { fetchMe, logout as apiLogout, type User } from './api'

interface AuthState {
  user: User | null
  setUser: (u: User | null) => void
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    fetchMe().then(setUser).catch(() => setUser(null))
  }, [])

  const logout = async () => {
    await apiLogout()
    setUser(null)
  }

  return <AuthContext.Provider value={{ user, setUser, logout }}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
