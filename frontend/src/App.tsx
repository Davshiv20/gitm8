import './App.css'
import gitm8 from './assets/gitm8.png'
import React, { useRef, useEffect, useState } from 'react'
import GitForm from './components/GitForm'
import { UI_TEXT, STYLING, CONFIG, API, COMPONENTS } from './components/constants'
import { CompatibilityScoreAnalyzer } from './components/CompatibilityScoreAnalyzer'

function App() {
  const radialRef = useRef<HTMLDivElement>(null)
  const [isLoading, setIsLoading]= useState(false)
  const [users, setUsers]= useState<{avatar_url: string, username: string}[]>([])
  const [compatibilityScore, setCompatibilityScore]= useState<number | null>(null)
  const [compatibilityReasoning, setCompatibilityReasoning]= useState('no analysis yet')
  const [error, setError]= useState('')

  const handleSubmit = async (data: { users: string[] }) => {
    setIsLoading(true)
    setError('')
    try {
      // First, get quick compatibility score
      const quickRes = await fetch(`${API.BASE_URL}/api/quick-compatibility`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ usernames: data.users }),
      })
      
      if (!quickRes.ok) {
        throw new Error(UI_TEXT.ERROR_MESSAGES.USER_NOT_FOUND)
      }
      
      const quickResult = await quickRes.json()
      console.log('Quick result:', quickResult)
      
      // Set the compatibility score immediately
      setCompatibilityScore(quickResult.compatibility_score)
      setCompatibilityReasoning(quickResult.compatibility_reasoning)
      setUsers(quickResult.users)
      
      // Now fetch detailed analysis in background (optional)
     
      
      setIsLoading(false)
    } catch (err: any) {
      setError(err.message || UI_TEXT.ERROR_MESSAGES.GENERAL_ERROR)
      setIsLoading(false)
    }
  }

  useEffect(() => {
    let animationFrame: number

    let x: number = CONFIG.RADIAL_GRADIENT.INITIAL_X
    let y: number = CONFIG.RADIAL_GRADIENT.INITIAL_Y
    let vx = (Math.random() - 0.5) * CONFIG.RADIAL_GRADIENT.VELOCITY_X
    let vy = (Math.random() - 0.5) * CONFIG.RADIAL_GRADIENT.VELOCITY_Y
    
    const minX = CONFIG.RADIAL_GRADIENT.MIN_X
    const maxX = CONFIG.RADIAL_GRADIENT.MAX_X
    const minY = CONFIG.RADIAL_GRADIENT.MIN_Y
    const maxY = CONFIG.RADIAL_GRADIENT.MAX_Y

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
      if (Math.random() < CONFIG.RADIAL_GRADIENT.RANDOM_CHANCE) {
        vx += (Math.random() - 0.5) * 0.1
        vy += (Math.random() - 0.5) * 0.1
        // Clamp velocity to a reasonable range
        vx = Math.max(-CONFIG.RADIAL_GRADIENT.VELOCITY_CLAMP, Math.min(CONFIG.RADIAL_GRADIENT.VELOCITY_CLAMP, vx))
        vy = Math.max(-CONFIG.RADIAL_GRADIENT.VELOCITY_CLAMP, Math.min(CONFIG.RADIAL_GRADIENT.VELOCITY_CLAMP, vy))
      }

      if (radialRef.current) {
        radialRef.current.style.background = `radial-gradient(circle ${CONFIG.RADIAL_GRADIENT.SIZE}px at ${x}% ${y}px, ${STYLING.COLORS.ACCENT}, transparent)`
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

        <div className="flex justify-center" style={{ marginBottom: STYLING.SPACING.MEDIUM }}>
          <img src={gitm8} alt="gitm8 logo" height={COMPONENTS.APP.LOGO_DIMENSIONS.HEIGHT} width={COMPONENTS.APP.LOGO_DIMENSIONS.WIDTH} />
        </div>
        <h1 className="text-5xl font-bold text-black relative" style={{ marginBottom: STYLING.SPACING.MEDIUM }}>
          {UI_TEXT.APP_TITLE}
          <span className="absolute -bottom-1 left-0 w-full h-0.5 bg-black"></span>
        </h1>
        
        <div className="text-center" style={{ marginBottom: STYLING.SPACING.XL }}>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto font-mono tracking-tight">
            {UI_TEXT.APP_SUBTITLE}
          </p>
        </div>
        
        <div className="flex justify-center">
          <GitForm onsubmit={handleSubmit} isLoading={isLoading}  />
        </div>
        {compatibilityScore && (
          <CompatibilityScoreAnalyzer compatibilityScore={compatibilityScore} compatibilityReasoning={compatibilityReasoning} users={users} />
        )}
      </div>
      
    </div>
  )
}

export default App
  