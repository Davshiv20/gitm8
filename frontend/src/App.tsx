import './App.css'
import gitm8 from './assets/gitm8.png'
import { useRef, useEffect, useReducer } from 'react'
import GitForm from './components/GitForm'
import { UI_TEXT, STYLING, CONFIG, API, COMPONENTS} from './components/constants'
import { CompatibilityScoreAnalyzer } from './components/CompatibilityScoreAnalyzer'
import { LandingCardWrapper } from './components/LandingCardWrapper'

type RadarChartData = {
  languages: Array<{ language: string; [username: string]: number | string }>
}

type User = {
  avatar_url: string
  username: string
}

type SetCompatibilityDataPayload = {
  score: number
  reasoning: string
  users: User[]
  radarData: RadarChartData
}

type AppState = {
  isLoading: boolean
  users: User[]
  compatibilityScore: number | null
  compatibilityReasoning: string
  error: string
  radarChartData: RadarChartData | null
  showLandingCards: boolean
  initialAnimationComplete: boolean
}

type AppAction = 
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_COMPATIBILITY_DATA'; payload: SetCompatibilityDataPayload }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'SHOW_LANDING_CARDS' }
  | { type: 'COMPLETE_INITIAL_ANIMATION' }

const initialState: AppState = {
  isLoading: false,
  users: [],
  compatibilityScore: null,
  compatibilityReasoning: 'no analysis yet',
  error: '',
  radarChartData: null,
  showLandingCards: false,
  initialAnimationComplete: false
}

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_LOADING': {
      const newState: AppState = { ...state, isLoading: action.payload, error: '' }
      return newState
    }
    case 'SET_COMPATIBILITY_DATA': {
      const newState: AppState = {
        ...state,
        compatibilityScore: action.payload.score,
        compatibilityReasoning: action.payload.reasoning,
        users: action.payload.users,
        radarChartData: action.payload.radarData,
        isLoading: false
      }
      return newState
    }
    case 'SET_ERROR': {
      const newState: AppState = { ...state, error: action.payload, isLoading: false }
      return newState
    }
    case 'SHOW_LANDING_CARDS': {
      const newState: AppState = { ...state, showLandingCards: true }
      return newState
    }
    case 'COMPLETE_INITIAL_ANIMATION': {
      const newState: AppState = { ...state, initialAnimationComplete: true }
      return newState
    }
    default: {
      return state
    }
  }
}

function App() {
  const radialRef = useRef<HTMLDivElement>(null)
  const [state, dispatch] = useReducer(appReducer, initialState)

  const handleSubmit = async (data: { users: string[] }) => {
    dispatch({ type: 'SET_LOADING', payload: true })
    
    try {
      const quickRes = await fetch(`${API.BASE_URL}/api/quick-compatibility`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ usernames: data.users }),
      })
      
      if (!quickRes.ok) {
        throw new Error(UI_TEXT.ERROR_MESSAGES.USER_NOT_FOUND)
      }
      
      type QuickResult = {
        compatibility_score: number
        compatibility_reasoning: string
        users: User[]
        radar_chart_data: RadarChartData
      }
      const quickResult: QuickResult = await quickRes.json()
      console.log('Quick result:', quickResult)
      
      const payload: SetCompatibilityDataPayload = {
        score: quickResult.compatibility_score,
        reasoning: quickResult.compatibility_reasoning,
        users: quickResult.users,
        radarData: quickResult.radar_chart_data
      }
      dispatch({
        type: 'SET_COMPATIBILITY_DATA',
        payload
      })
    } catch (err: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: err.message || UI_TEXT.ERROR_MESSAGES.GENERAL_ERROR 
      })
    }
  }

  // Radial gradient animation
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
      x += vx
      y += vy

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

  // Initial animations
  useEffect(() => {
    const landingTimer = setTimeout(() => dispatch({ type: 'SHOW_LANDING_CARDS' }), 1000)
    const blurTimer = setTimeout(() => dispatch({ type: 'COMPLETE_INITIAL_ANIMATION' }), 2000)
    
    return () => {
      clearTimeout(landingTimer)
      clearTimeout(blurTimer)
    }
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
        />
      </div>
      
      <div className="pointer-events-none hidden md:block" aria-hidden>
        <LandingCardWrapper showLandingCards={state.showLandingCards} />
      </div>

      <div className={`relative z-10 flex transition duration-1000 delay-1000 flex-col items-center justify-center min-h-screen px-4 ${
        !state.initialAnimationComplete ? 'blur-sm' : ''
      }`}>
        <div className="flex justify-center" style={{ marginBottom: STYLING.SPACING.MEDIUM }}>
          <img src={gitm8} alt="gitm8 logo" height={COMPONENTS.APP.LOGO_DIMENSIONS.HEIGHT} width={COMPONENTS.APP.LOGO_DIMENSIONS.WIDTH} />
        </div>
        
        <h1 className="text-5xl font-bold text-black relative" style={{ marginBottom: STYLING.SPACING.MEDIUM }}>
          {UI_TEXT.APP_TITLE}
          <span className="absolute -bottom-1 left-0 w-full h-0.5 bg-black" />
        </h1>
        
        <div className="text-center" style={{ marginBottom: STYLING.SPACING.LARGE }}>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto font-mono tracking-tight">
            {UI_TEXT.APP_SUBTITLE}
          </p>
        </div>
        
        <div className="flex justify-center">
          <GitForm isLoading={state.isLoading} />
        </div>
        
        <div className="flex justify-between w-full max-w-4xl mt-12" />
        
        {state.compatibilityScore && (
          <CompatibilityScoreAnalyzer 
            compatibilityScore={state.compatibilityScore} 
            compatibilityReasoning={state.compatibilityReasoning} 
            users={state.users}   
            radarChartData={state.radarChartData}
          />
        )}
      </div>
    </div>
  )
}

export default App