import LandingCard from "./LandingCard"
import { LANDING_CARD_TEXT } from "./constants"



export function LandingCardWrapper ({showLandingCards}:{
    showLandingCards: boolean
}){
    return(
        <>{LANDING_CARD_TEXT.map((card, idx) => (
    <LandingCard
      key={idx}
      side={card.side as "left" | "right"}
      topClass={card.topClass}
      show={showLandingCards}
      delayMs={card.delayMs}
      widthClass={card.widthClass}
      title={card.title}
      subtitle={card.subtitle}
      rotateFromDeg={card.rotateFromDeg}
      rotateToDeg={card.rotateToDeg}
      translateShownRem={card.translateShownRem}
    />
  
  ))}
  </>
    )
}