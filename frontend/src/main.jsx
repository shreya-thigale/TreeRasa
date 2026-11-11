import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './app/App'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import { LanguageProvider } from './context/LanguageContext'
import './styles/global.css'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <LanguageProvider><ThemeProvider><AuthProvider><BrowserRouter><App /></BrowserRouter></AuthProvider></ThemeProvider></LanguageProvider>
  </React.StrictMode>
)
