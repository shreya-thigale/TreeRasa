import { createContext, useContext, useEffect, useState } from 'react'
const ThemeContext = createContext(null)
export function ThemeProvider({children}) {
  const [theme,setTheme] = useState(()=>localStorage.getItem('treerasa_theme') || 'light')
  useEffect(()=>{document.documentElement.classList.toggle('dark',theme==='dark');document.documentElement.dataset.theme=theme;localStorage.setItem('treerasa_theme',theme)},[theme])
  return <ThemeContext.Provider value={{theme,toggleTheme:()=>setTheme(t=>t==='dark'?'light':'dark')}}>{children}</ThemeContext.Provider>
}
export const useTheme = () => useContext(ThemeContext)
