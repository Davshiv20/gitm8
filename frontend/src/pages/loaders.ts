import { redirect } from 'react-router'
import type { ActionFunctionArgs } from 'react-router'
import { API } from '../components/constants'

type RadarChartData = {
  languages: Array<{ language: string; [username: string]: number | string }>
}

type User = {
  avatar_url: string
  username: string
}

type QuickResult = {
  compatibility_score: number
  compatibility_reasoning: string
  users: User[]
  radar_chart_data: RadarChartData
}

// Loader for results page - fetches data based on session storage
export async function resultsLoader() {
  // For now, we'll check if there's data in sessionStorage
  // In a real app, you might use URL params or query strings
  const storedData = sessionStorage.getItem('compatibilityResults')

  if (!storedData) {
    // If no data, redirect to home
    return redirect('/')
  }

  return JSON.parse(storedData)
}

// Action for handling form submission
export async function compatibilityAction({ request }: ActionFunctionArgs) {
  const formData = await request.formData()
  const usernames = formData.get('usernames') as string

  if (!usernames) {
    throw new Error('Usernames are required')
  }

  const usernameArray = usernames.split(',').map(u => u.trim()).filter(u => u)

  if (usernameArray.length < 2) {
    throw new Error('At least 2 usernames are required')
  }

  try {
    const response = await fetch(`${API.BASE_URL}/api/quick-compatibility`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usernames: usernameArray }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to analyze compatibility')
    }

    const result: QuickResult = await response.json()

    // Store the result for the results page to access
    const formattedResult = {
      score: result.compatibility_score,
      reasoning: result.compatibility_reasoning,
      users: result.users,
      radarData: result.radar_chart_data
    }

    sessionStorage.setItem('compatibilityResults', JSON.stringify(formattedResult))

    // Redirect to results page
    return redirect('/results')
  } catch (error) {
    // In a real app, you'd handle this with proper error boundaries
    throw new Error(error instanceof Error ? error.message : 'An unexpected error occurred')
  }
}
