import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/report.css'

const mount = document.getElementById('root') || (() => {
  const el = document.createElement('div')
  el.id = 'root'
  document.body.appendChild(el)
  return el
})()

ReactDOM.createRoot(mount).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
