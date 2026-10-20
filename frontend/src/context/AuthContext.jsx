import { createContext, useContext, useEffect, useState } from 'react'
import { authApi } from '../api/auth.api'

const AuthContext = createContext(null)
export function AuthProvider({children}) {
  const [user,setUser] = useState(()=>{ try{return JSON.parse(localStorage.getItem('treerasa_user')||'null')}catch{return null} })
  const [loading,setLoading] = useState(Boolean(localStorage.getItem('treerasa_token')))
  useEffect(()=>{ if(!localStorage.getItem('treerasa_token')){setLoading(false);return} authApi.me().then(saveUser).catch(logout).finally(()=>setLoading(false)) },[])
  function saveUser(u){ setUser(u); localStorage.setItem('treerasa_user',JSON.stringify(u)) }
  function saveSession(data){ localStorage.setItem('treerasa_token',data.access_token); saveUser(data.user) }
  function logout(){localStorage.removeItem('treerasa_token');localStorage.removeItem('treerasa_user');setUser(null)}
  async function login(payload){saveSession(await authApi.login(payload))}
  async function register(payload){saveSession(await authApi.register(payload))}
  return <AuthContext.Provider value={{user,loading,login,register,logout,refreshUser:async()=>saveUser(await authApi.me())}}>{children}</AuthContext.Provider>
}
export const useAuth = () => useContext(AuthContext)
