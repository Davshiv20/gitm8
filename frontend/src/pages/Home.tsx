import { useRef, useEffect, useReducer } from 'react'
import { useNavigation } from 'react-router'
import gitm8 from '../assets/gitm8.png'
import GitForm from '../components/GitForm'
import { UI_TEXT, STYLING, CONFIG, COMPONENTS } from '../components/constants'
import { LandingCardWrapper } from '../components/LandingCardWrapper'

type HomeState = {
  showLandingCards: boolean
  initialAnimationComplete: boolean
}

type HomeAction =
  | { type: 'SHOW_LANDING_CARDS' }
  | { type: 'COMPLETE_INITIAL_ANIMATION' }

const initialState: HomeState = {
  showLandingCards: false,
  initialAnimationComplete: false
}

function homeReducer(state: HomeState, action: HomeAction): HomeState {
  switch (action.type) {
    case 'SHOW_LANDING_CARDS': {
      return { ...state, showLandingCards: true }
    }
    case 'COMPLETE_INITIAL_ANIMATION': {
      return { ...state, initialAnimationComplete: true }
    }
    default: {
      return state
    }
  }
}
function getCurrentYear(){
  let currentYear = new Date().getFullYear()
  return currentYear
}

export default function Home() {
  const radialRef = useRef<HTMLDivElement>(null)
  const [state, dispatch] = useReducer(homeReducer, initialState)
  const navigation = useNavigation()
  const isLoading = navigation.state === 'submitting'

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
            zIndex: 1,
          }}
        />
        <div
          className="absolute inset-0"
          style={{
            background: 'radial-gradient(circle 600px at 0% 85%, #6D3D14, transparent)',
            filter: 'blur(40px)',
          }}

        />
         <div
          className="absolute inset-0"
          style={{
            background: 'radial-gradient(circle 600px at 0% 0%, #2D3047, transparent)',
            filter: 'blur(40px)',
          }}
          
        />
         <div
          className="absolute inset-0"
          style={{
            background: 'radial-gradient(circle 600px at 100% 0%, #6D3D14, transparent)',
            filter: 'blur(40px)',
          }}
        />
        {/* Third radial gradient - bottom right for visual balance */}
        <div
          className="absolute inset-0"
          style={{
            background: 'radial-gradient(circle 500px at 100% 90%, #2D3047, transparent)',
            filter: 'blur(32px)',
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
          <h2 className="text-xl text-gray-600 max-w-2xl mx-auto font-mono tracking-tight mb-4">
            {UI_TEXT.APP_SUBTITLE}
          </h2>
          <p className="text-base text-gray-500 max-w-3xl mx-auto leading-relaxed">
            GitM8 is a powerful GitHub compatibility analyzer that helps developers find their perfect coding partners. 
            Compare programming languages, analyze coding styles, and discover collaboration opportunities with AI-powered insights. 
            Whether you're looking for a hackathon teammate, project collaborator, or just want to see how your GitHub profile 
            matches with friends, GitM8 provides detailed compatibility scores and recommendations.
          </p>
        </div>

        <div className="flex justify-center">
          <GitForm isLoading={isLoading} />
        </div>

        <div className="flex justify-between w-full max-w-4xl mt-12">
          <footer className="w-full text-center py-8">
            <div className="max-w-4xl mx-auto px-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">Features</h3>
                  <ul className="space-y-2 text-gray-600">
                    <li><a href="/" className="hover:text-black transition-colors">GitHub Analysis</a></li>
                    <li><a href="/" className="hover:text-black transition-colors">Compatibility Score</a></li>
                    <li><a href="/" className="hover:text-black transition-colors">Language Comparison</a></li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">Use Cases</h3>
                  <ul className="space-y-2 text-gray-600">
                    <li><a href="/" className="hover:text-black transition-colors">Find Coding Partners</a></li>
                    <li><a href="/" className="hover:text-black transition-colors">Hackathon Teams</a></li>
                    <li><a href="/" className="hover:text-black transition-colors">Project Collaboration</a></li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">Resources</h3>
                  <ul className="space-y-2 text-gray-600">
                    <li><a href="https://github.com" target="_blank" rel="noopener noreferrer" className="hover:text-black transition-colors">GitHub</a></li>
                    <li><a href="https://docs.github.com/en/graphql" target="_blank" rel="noopener noreferrer" className="hover:text-black transition-colors">GitHub API</a></li>
                    <li><a href="https://vercel.com" target="_blank" rel="noopener noreferrer" className="hover:text-black transition-colors">Powered by Vercel</a></li>
                  </ul>
                </div>
              </div>
              <div className="border-t border-gray-300 pt-6">
                <p className="text-gray-600 text-sm">
                  © {getCurrentYear()} GitM8. Analyze GitHub profiles and find your perfect coding buddy.
                </p>
              </div>
            </div>
          </footer>
        </div>
      </div>
    </div>
  )
}
