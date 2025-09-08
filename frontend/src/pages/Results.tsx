import { useLoaderData } from 'react-router'
import { CompatibilityScoreAnalyzer } from '../components/CompatibilityScoreAnalyzer'

type RadarChartData = {
  languages: Array<{ language: string; [username: string]: number | string }>
}

type User = {
  avatar_url: string
  username: string
}

type ResultsData = {
  score: number
  reasoning: string
  users: User[]
  radarData: RadarChartData
}

export default function Results() {
  const data = useLoaderData() as ResultsData
  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      <div className="fixed inset-0 -z-10 bg-slate h-full w-full">
        <div
          className="absolute inset-0"
          style={{
            background: 'radial-gradient(circle 800px at 50% 50%, #5BC0BE, transparent)',
          }}
        />
      </div>

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-12">
        <div className="w-full max-w-6xl">
          <div className="text-center mb-8">
            <h2 className="text-4xl font-bold text-black mb-4">Analysis Results</h2>
            <p className="text-lg text-gray-600">Here's what we found about your GitHub compatibility</p>
          </div>

          <CompatibilityScoreAnalyzer
            compatibilityScore={data.score}
            compatibilityReasoning={data.reasoning}
            users={data.users}
            radarChartData={data.radarData}
          />
        </div>
      </div>
    </div>
  )
}
