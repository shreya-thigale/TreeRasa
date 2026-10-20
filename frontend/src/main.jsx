import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './app/App'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import './styles/global.css'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider><AuthProvider><BrowserRouter><App /></BrowserRouter></AuthProvider></ThemeProvider>
  </React.StrictMode>
)
