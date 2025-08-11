import React from 'react'
import { UI_TEXT, STYLING, COMPONENTS, CONFIG } from './constants'

interface AnalysisResultsProps {
  data: any
  onReset: () => void
}

const AnalysisResults: React.FC<AnalysisResultsProps> = ({ data, onReset }) => {
  const { llm_analysis, compatibility_metrics, visualization_data } = data

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className={COMPONENTS.ANALYSIS_RESULTS.CONTAINER_MAX_WIDTH + " px-4"}>
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">{UI_TEXT.ANALYSIS_TITLE}</h1>
          <button
            onClick={onReset}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {UI_TEXT.ANALYZE_NEW_BUTTON}
          </button>
        </div>

        {/* Compatibility Score */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">{UI_TEXT.COMPATIBILITY_SCORE_TITLE}</h2>
          <div className="flex items-center justify-center">
            <div className={`relative w-${COMPONENTS.ANALYSIS_RESULTS.CIRCLE_DIMENSIONS.WIDTH} h-${COMPONENTS.ANALYSIS_RESULTS.CIRCLE_DIMENSIONS.HEIGHT}`}>
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx={COMPONENTS.ANALYSIS_RESULTS.CIRCLE_DIMENSIONS.CENTER_X}
                  cy={COMPONENTS.ANALYSIS_RESULTS.CIRCLE_DIMENSIONS.CENTER_Y}
                  r={STYLING.SIZES.CIRCLE.SMALL}
                  stroke="currentColor"
                  strokeWidth={STYLING.SIZES.STROKE_WIDTH.MEDIUM}
                  fill="transparent"
                  className="text-gray-200"
                />
                <circle
                  cx={COMPONENTS.ANALYSIS_RESULTS.CIRCLE_DIMENSIONS.CENTER_X}
                  cy={COMPONENTS.ANALYSIS_RESULTS.CIRCLE_DIMENSIONS.CENTER_Y}
                  r={STYLING.SIZES.CIRCLE.SMALL}
                  stroke="currentColor"
                  strokeWidth={STYLING.SIZES.STROKE_WIDTH.MEDIUM}
                  fill="transparent"
                  strokeDasharray={`${2 * Math.PI * STYLING.SIZES.CIRCLE.SMALL}`}
                  strokeDashoffset={`${2 * Math.PI * STYLING.SIZES.CIRCLE.SMALL * (1 - llm_analysis.analysis.compatibility_score / CONFIG.PROGRESS.MAX_VALUE)}`}
                  className="text-blue-600"
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold text-gray-900">
                  {llm_analysis.analysis.compatibility_score}/{CONFIG.PROGRESS.MAX_VALUE}
                </span>
              </div>
            </div>
          </div>
          <p className="text-center text-gray-600 mt-4">
            {llm_analysis.analysis.compatibility_reasoning}
          </p>
        </div>

        {/* Skills Overlap */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">{UI_TEXT.SKILLS_OVERLAP_TITLE}</h2>
          <div className={COMPONENTS.ANALYSIS_RESULTS.GRID_COLUMNS + " gap-6"}>
            <div>
              <h3 className="font-medium mb-3">{UI_TEXT.SHARED_LANGUAGES_TITLE}</h3>
              <div className="space-y-2">
                {Object.entries(compatibility_metrics.language_overlap).map(([lang, count]) => (
                  <div key={lang} className="flex justify-between items-center p-2 bg-blue-50 rounded">
                    <span className="font-medium">{lang}</span>
                    <span className="text-sm text-gray-600">{String(count)} {UI_TEXT.USERS_COUNT_SUFFIX}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-medium mb-3">{UI_TEXT.SHARED_TECHNOLOGIES_TITLE}</h3>
              <div className="space-y-2">
                {Object.entries(compatibility_metrics.topic_overlap).map(([topic, count]) => (
                  <div key={topic} className="flex justify-between items-center p-2 bg-green-50 rounded">
                    <span className="font-medium">{topic}</span>
                    <span className="text-sm text-gray-600">{String(count)} {UI_TEXT.USERS_COUNT_SUFFIX}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Project Ideas */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">{UI_TEXT.PROJECT_IDEAS_TITLE}</h2>
          <div className="space-y-4">
            {llm_analysis.analysis.collaboration_opportunities.map((opportunity: string, index: number) => (
              <div key={index} className="p-4 border border-gray-200 rounded-lg">
                <p className="text-gray-700">{opportunity}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">{UI_TEXT.RECOMMENDATIONS_TITLE}</h2>
          <div className="space-y-3">
            {llm_analysis.analysis.recommendations.map((rec: string, index: number) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  {index + 1}
                </div>
                <p className="text-gray-700">{rec}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AnalysisResults 