import { useLoaderData } from 'react-router'
import Dashboard from '../components/Dashboard'

type RadarChartData = {
  languages: Array<{ language: string; [username: string]: number | string }>
}

type User = {
  avatar_url: string
  username: string
}

type CompatibilityFactor = {
  label: string
  indicator: string
}

type ResultsData = {
  score: number
  reasoning: string
  users: User[]
  radarData: RadarChartData
  comparisonData?: Record<string, unknown>
  compatibilityFactors: CompatibilityFactor[]
}

export default function Results() {
  const data = useLoaderData() as ResultsData
  return (
    <Dashboard
      compatibilityScore={data.score}
      compatibilityReasoning={data.reasoning}
      users={data.users}
      radarChartData={data.radarData}
      comparisonData={data.comparisonData}
      compatibilityFactors={data.compatibilityFactors}
    />
  )
}
