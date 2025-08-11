import { STYLING } from "./constants";
import CompatibilityScore from "./CompatibilityScore";
import Typewriter from 'typewriter-effect';

export function CompatibilityScoreAnalyzer({ compatibilityScore, compatibilityReasoning }: { compatibilityScore: number, compatibilityReasoning: string }) {
    return(
        <div
            className="flex flex-col justify-center"
            style={{ marginTop: STYLING.SPACING.XL }}
            ref={el => {
              if (el) {
                el.scrollIntoView({ behavior: "smooth", block: "center" });
              }
            }}
          >
            <p className="flex justify-center font-bold text-lg text-gray-600 max-w-2xl mx-auto font-mono tracking-tight mb-2">
              Compatibility Score Analysis
            </p>    
            <div className="flex justify-center" style={{ margin: STYLING.SPACING.MEDIUM }}>
              <CompatibilityScore score={compatibilityScore} />
            </div>
            <p className="flex justify-center text-lg text-gray-600 max-w-2xl mx-auto font-mono tracking-tight mt-2">
              <Typewriter
                options={{
                  strings: [compatibilityReasoning],
                  autoStart: true,
                  delay: 20,
                  deleteSpeed: Infinity,
                  cursor: "|",
                  cursorClassName: "text-gray-600",

                }}
              />
            </p>
          </div>    
    )}