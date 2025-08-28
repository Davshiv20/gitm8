import './App.css'
import gitm8 from './assets/gitm8.png'
import { useRef, useEffect, useState } from 'react'
import GitForm from './components/GitForm'
import { UI_TEXT, STYLING, CONFIG, API, COMPONENTS} from './components/constants'
import { CompatibilityScoreAnalyzer } from './components/CompatibilityScoreAnalyzer'
import { LandingCardWrapper } from './components/LandingCardWrapper'

interface RadarChartData {
  languages: Array<{ language: string; [username: string]: number | string }>
}

function App() {
  const radialRef = useRef<HTMLDivElement>(null)
  const [isLoading, setIsLoading]= useState(false)
  const [users, setUsers]= useState<{avatar_url: string, username: string}[]>([])
  const [compatibilityScore, setCompatibilityScore]= useState<number | null>(null)
  const [compatibilityReasoning, setCompatibilityReasoning]= useState('no analysis yet')
  const [, setError]= useState('')
  const [isRadarChartData, setRadarChartData]= useState<RadarChartData | null>(null)
  const [showLandingCards, setShowLandingCards] = useState(false)

  const handleSubmit = async (data: { users: string[] }) => {
    setIsLoading(true)
    setError('')
    try {
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
      setRadarChartData(quickResult.radar_chart_data)
      
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
        vx = Math.abs(vx) * (0.7 + Math.random() * 0.6)
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

      if (radialRef.current) {
        radialRef.current.style.background = `radial-gradient(circle ${CONFIG.RADIAL_GRADIENT.SIZE}px at ${x}% ${y}px, ${STYLING.COLORS.ACCENT}, transparent)`
      }
      animationFrame = requestAnimationFrame(animate)
    }

    animate()
    return () => cancelAnimationFrame(animationFrame)
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => setShowLandingCards(true), 1000)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="relative min-h-screen w-full overflow-hidden">
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
      
      <div className="pointer-events-none hidden md:block" aria-hidden>
        <LandingCardWrapper showLandingCards= {showLandingCards}/>
      </div>

      <div className="relative z-10 flex blur-sm transition duration-1000 delay-1000 hover:blur-none flex-col items-center justify-center min-h-screen px-4">

        <div className="flex justify-center" style={{ marginBottom: STYLING.SPACING.MEDIUM }}>
          <img src={gitm8} alt="gitm8 logo" height={COMPONENTS.APP.LOGO_DIMENSIONS.HEIGHT} width={COMPONENTS.APP.LOGO_DIMENSIONS.WIDTH} />
        </div>
        <h1 className="text-5xl font-bold  text-black relative" style={{ marginBottom: STYLING.SPACING.MEDIUM }}>
          {UI_TEXT.APP_TITLE}
          <span className="absolute -bottom-1 left-0 w-full h-0.5 bg-black"></span>
        </h1>
        
        <div className="text-center" style={{ marginBottom: STYLING.SPACING.LARGE }}>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto font-mono tracking-tight">
            {UI_TEXT.APP_SUBTITLE}
          </p>
        </div>
        
        <div className="flex justify-center">
          <GitForm onsubmit={handleSubmit} isLoading={isLoading}  />
        </div>
        <div className="flex justify-between w-full max-w-4xl mt-12"></div>
        {compatibilityScore && (
          <CompatibilityScoreAnalyzer compatibilityScore={compatibilityScore} compatibilityReasoning={compatibilityReasoning} users={users}   radarChartData={isRadarChartData}/>
        )}
      </div>
      
    </div>
  )
}

export default App
  