import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { router } from './router.tsx'
import { RouterProvider } from 'react-router/dom'
import { Analytics } from '@vercel/analytics/react'


createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
    <Analytics />
  </StrictMode>,
)
