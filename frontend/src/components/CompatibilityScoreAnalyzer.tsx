import { STYLING } from "./constants";
import CompatibilityScore from "./CompatibilityScore";
import Typewriter from 'typewriter-effect';
import RadarChart from "./RadarChart";

interface RadarChartData {
  languages: Array<{ language: string; [username: string]: number | string }>
}

export function CompatibilityScoreAnalyzer({ compatibilityScore, compatibilityReasoning, users, radarChartData }: { 
  compatibilityScore: number, 
  compatibilityReasoning: string, 
  users: {avatar_url: string, username: string}[], 
  radarChartData: RadarChartData | null 
}) {
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
            
            <div className="flex flex-row justify-center" style={{ margin: STYLING.SPACING.MEDIUM }}>
                
                {users.map((user) => (
                <div key={user.username} className="flex flex-col justify-center items-center" style={{ margin: STYLING.SPACING.MEDIUM }}>
                  <img
                    src={user.avatar_url}
                    alt={user.username}
                    className="w-10 h-10 rounded-full"
                    style={{
                      height: STYLING.SPACING.XXL,
                      width: STYLING.SPACING.XXL,
                      marginBottom: STYLING.SPACING.SMALL,
                    }}
                  />
                  <span className="text-sm font-bold text-gray-700">{user.username}</span>
                </div>
                ))}
            </div>
            {radarChartData && radarChartData.languages && radarChartData.languages.length > 0 && (
            <RadarChart data={radarChartData} />
               )}
            <div className="flex justify-center">
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