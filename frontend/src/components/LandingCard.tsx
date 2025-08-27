import React from 'react'

type Side = 'left' | 'right'

interface LandingCardProps {
  side: Side
  topClass: string
  offsetClass?: string
  show: boolean
  delayMs?: number
  widthClass?: string
  title: string
  subtitle?: string
  tag?: string
  rotateFromDeg?: number
  rotateToDeg?: number
  translateShownRem?: number
}

const LandingCard: React.FC<LandingCardProps> = ({
  side,
  topClass,
  offsetClass = side === 'left' ? '-left-10' : '-right-10',
  show,
  delayMs = 0,
  widthClass = 'w-56',
  title,
  subtitle,
  tag,
  rotateFromDeg,
  rotateToDeg,
  translateShownRem,
}) => {
  const defaultFrom = side === 'left' ? -12 : 12
  const defaultTo = side === 'left' ? -6 : 6
  const rotateFrom = typeof rotateFromDeg === 'number' ? rotateFromDeg : defaultFrom
  const rotateTo = typeof rotateToDeg === 'number' ? rotateToDeg : defaultTo
  const translateShown = typeof translateShownRem === 'number' ? translateShownRem : 2.5

  const hiddenTranslate = side === 'left' ? '-100%' : '100%'
  const shownTranslate = side === 'left' ? `${translateShown}rem` : `-${translateShown}rem`

  const transformStyle = {
    transform: show
      ? `translateX(${shownTranslate}) rotate(${rotateTo}deg)`
      : `translateX(${hiddenTranslate}) rotate(${rotateFrom}deg)`
  } as React.CSSProperties

  return (
    <div
      className={`absolute ${topClass} ${offsetClass} transform-gpu will-change-transform transition duration-700 ease-out ${show ? 'opacity-100' : 'opacity-0'}`}
      style={{ transitionDelay: `${delayMs}ms`, ...transformStyle }}
      aria-hidden
    >

      <div className="relative">

        <div
          className="absolute bg-white/70 backdrop-blur shadow-md border"
          style={{
            borderColor: '#BBDCE5',
            borderWidth: '4px',
            borderRadius: '0.375rem',
            width: '100%',
            height: '100%',
            transform: `translate(${side === 'left' ? '6px' : '-6px'}, 4px) rotate(${side === 'left' ? '2deg' : '-2deg'})`
          }}
        />
        <div className="relative">
          <div
            className={`bg-white/90 backdrop-blur shadow-lg p-10 ${widthClass} border`}
            style={{
              borderColor: '#BBDCE5',
              borderWidth: '4px',
               padding: '6px 8px' ,
              borderRadius: '0.375rem',
            }}
          >
            {tag && <div className="text-xs text-slate-500">{tag}</div>}
            <div className="mt-1 font-semibold" >{title}</div>
            {subtitle && <div className="mt-2 text-xs text-slate-500">{subtitle}</div>}
          </div>
          

          <div 
            className="absolute inset-0 pointer-events-none rounded-md"
            style={{
              zIndex: 10,
              borderRadius: '0.375rem',
              // background: side === 'left' 
              //   ? 'linear-gradient(to left, transparent 0%, transparent 25%, rgba(248, 250, 252, 0.8) 85%, white 100%)'
              //   : 'linear-gradient(to right, transparent 0%, transparent 25%, rgba(248, 250, 252, 0.8) 85%, white 100%)'
            }}
          />
        </div>
      </div>
    </div>
  )
}

export default LandingCard