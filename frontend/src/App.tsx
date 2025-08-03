import './App.css'
import gitm8 from './assets/gitm8.png'
import React, { useRef, useEffect, useState } from 'react'
import GitForm from './components/GitForm'

function App() {
  const radialRef = useRef<HTMLDivElement>(null)
  const [isLoading, setIsLoading]= useState(false)
  const [error, setError]= useState('')

  const handleSubmit = async (data: { users: string[] }) => {
    setIsLoading(true)
    setError('')
    try {

      const API_BASE = 'http://localhost:8000';

      const [user1Res, user2Res] = await Promise.all([
        fetch(`${API_BASE}/users/${encodeURIComponent(data.users[0])}`),
        fetch(`${API_BASE}/users/${encodeURIComponent(data.users[1])}`)
      ])
      if (!user1Res.ok || !user2Res.ok) {
        throw new Error('One or both users not found on GitHub')
      }
      
      setIsLoading(false)
    } catch (err: any) {
      setError(err.message || 'An error occurred while fetching user data.')
      setIsLoading(false)
    }
  }

  useEffect(() => {
    let animationFrame: number

    // Initial position (in % for x, px for y)
    let x = 50 // percent of width
    let y = 200 // px from top
    // Velocity in % per frame for x, px per frame for y
    let vx = (Math.random() - 0.5) * 0.9 // slower, random direction
    let vy = (Math.random() - 0.5) * 0.3

    // Boundaries for the center of the radial
    const minX = 10
    const maxX = 90
    const minY = 100
    const maxY = 400

    const animate = () => {
      // Move position
      x += vx
      y += vy

      // Deflect if out of bounds
      if (x < minX) {
        x = minX
        vx = Math.abs(vx) * (0.7 + Math.random() * 0.6) // randomize speed a bit
      } else if (x > maxX) {
        x = maxX
        vx = -Math.abs(vx) * (0.7 + Math.random() * 0.6)
      }
      if (y < minY) {
        y = minY
        vy = Math.abs(vy) * (0.7 + Math.random() * 0.6)
      } else if (y > maxY) {
        y = maxY
        vy = -Math.abs(vy) * (0.7 + Math.random() * 0.6)
      }

      // Occasionally randomize direction slightly for more "random" movement
      if (Math.random() < 0.01) {
        vx += (Math.random() - 0.5) * 0.1
        vy += (Math.random() - 0.5) * 0.1
        // Clamp velocity to a reasonable range
        vx = Math.max(-0.4, Math.min(0.4, vx))
        vy = Math.max(-0.4, Math.min(0.4, vy))
      }

      if (radialRef.current) {
        radialRef.current.style.background = `radial-gradient(circle 800px at ${x}% ${y}px, #5BC0BE, transparent)`
      }
      animationFrame = requestAnimationFrame(animate)
    }

    animate()
    return () => cancelAnimationFrame(animationFrame)
  }, [])

  return (
    <div className="relative min-h-screen w-full">
      <div className="fixed inset-0 -z-10 bg-slate h-full w-full">
        <div
          ref={radialRef}
          className="absolute inset-0"
          style={{
            background: 'radial-gradient(circle 800px at 100% 200px, #5BC0BE, transparent)',
            transition: 'background 2s',
          }}
        ></div>
      </div>

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4">

        <div className="flex justify-center" style={{ marginBottom: '1rem' }}>
          <img src={gitm8} alt="gitm8 logo" height={100} width={100} />
        </div>
        <h1 className="text-5xl font-bold text-black relative" style={{ marginBottom: '1rem' }}>
          GitM8
          <span className="absolute -bottom-1 left-0 w-full h-0.5 bg-black"></span>
        </h1>
        
        <div className="text-center" style={{ marginBottom: '4rem' }}>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto font-mono tracking-tight">
            Discover how your Github vibe matches with your friends
          </p>
        </div>
        
        <div className="flex justify-center">
          <GitForm onsubmit={handleSubmit} isLoading={isLoading}  />
        </div>
      </div>
      
    </div>
  )
}

export default App
