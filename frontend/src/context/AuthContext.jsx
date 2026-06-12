import { createContext, useContext, useState, useCallback } from 'react'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(null) // { token, role, userId, distributorId, username }

  const login = useCallback((tokenData) => {
    const state = {
      token:         tokenData.access_token,
      role:          tokenData.role,
      userId:        tokenData.user_id,
      distributorId: tokenData.distributor_id,
      username:      tokenData.username,
    }
    window.__authToken = state.token
    setAuth(state)
  }, [])

  const logout = useCallback(() => {
    window.__authToken = null
    setAuth(null)
  }, [])

  return (
    <AuthCtx.Provider value={{ auth, login, logout, isAdmin: auth?.role === 'org_admin' }}>
      {children}
    </AuthCtx.Provider>
  )
}

export const useAuth = () => useContext(AuthCtx)
