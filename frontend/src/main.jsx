import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#FCFAF6',
            color: '#302E2B',
            border: '1px solid #E9DFD1',
            borderRadius: '0.75rem',
            fontFamily: 'Manrope, sans-serif',
            fontSize: '0.875rem',
          },
          success: {
            iconTheme: { primary: '#788875', secondary: '#FCFAF6' },
          },
          error: {
            iconTheme: { primary: '#B8755D', secondary: '#FCFAF6' },
          },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>,
)
