
import { useState } from 'react'
import { ChevronDown, ChevronRight, BarChart3, Code, Star, GitBranch, Activity, Info } from 'lucide-react'
import LineChart from './LineChart'
import CompatibilityScore from './CompatibilityScore'
import Typewriter from 'typewriter-effect'

interface User {
  avatar_url: string
  username: string
}

interface RadarChartData {
  languages: Array<{ language: string; [username: string]: number | string }>
}

interface ComparisonData {
  activity_comparison?: Array<{ label: string; [username: string]: any }>
  repository_comparison?: Array<{ label: string; [username: string]: any }>
  language_comparison?: Array<{ label: string; [username: string]: any }>
  topic_comparison?: Array<{ label: string; [username: string]: any }>
}

interface DashboardProps {
  compatibilityScore: number
  compatibilityReasoning: string
  users: User[]
  radarChartData: RadarChartData | null
  comparisonData?: ComparisonData | null
}

interface MetricCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  onClick?: () => void
  isClickable?: boolean
  tooltip?: string
}

interface TooltipProps {
  children: React.ReactNode
  content: string
}

const Tooltip = ({ children, content }: TooltipProps) => {
  const [isVisible, setIsVisible] = useState(false)

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div
          className="absolute bottom-full left-1/2 transform -translate-x-1/2 
                     bg-white/90 backdrop-blur-sm text-gray-900 rounded-lg shadow-xl z-50 
                     border border-gray-200"
          style={{
            wordWrap: 'break-word',
            padding: '12px 16px',
            lineHeight: '1.5',
            maxWidth: '320px',
            minWidth: '200px',
            fontSize: '13px',
            fontWeight: '500'
          }}
        >
          <div className="text-left leading-relaxed whitespace-normal break-words">
            {content}
          </div>
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 
                          w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-white/90">
          </div>
        </div>
      )}
    </div>
  )
}

const MetricCard = ({ title, value, icon, onClick, isClickable = false, tooltip }: MetricCardProps) => (
  <div 
    className={`bg-white rounded-lg shadow-[8px_10px_0px_#222] border-4 border-gray-900 hover:shadow-md transition-all duration-200 ${
      isClickable ? 'cursor-pointer hover:border-[#FF621F]' : ''
    }`}
    style={{ padding: '12px', ...(window.innerWidth >= 1024 ? { padding: '16px' } : {}) }}
    onClick={onClick}
  >
    <div className="flex items-center justify-between">
      <div className="flex items-center" style={{ gap: window.innerWidth >= 1024 ? '12px' : '8px' }}>
        <div
          className="bg-blue-50 rounded-lg text-blue-600"
          style={{ padding: window.innerWidth >= 1024 ? '8px' : '6px' }}
        >
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs lg:text-sm font-medium text-gray-600 truncate">{title}</p>
          <p className="text-lg lg:text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
      {tooltip && (
        <Tooltip content={tooltip}>
          <Info className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" />
        </Tooltip>
      )}
    </div>
  </div>
)

interface DataTableProps {
  title: string
  data: Array<{ [key: string]: any }>
  users: User[]
  columns: Array<{ key: string; label: string; type?: 'number' | 'text' | 'array'; tooltip?: string }>
  isExpanded: boolean
  onToggle: () => void
}

const DataTable = ({ title, data, users, columns, isExpanded, onToggle }: DataTableProps) => {
  if (!data || data.length === 0) return null

  const tableData = data[0] // Get the first (and only) item from the array

  return (
    <div className="rounded-lg shadow-[6px_8px_0px_#222] hover:shadow-md border-4 border-gray-900" style={{ marginBottom: '16px' }}>
      <div
        className="flex items-center justify-between cursor-pointer hover:"
        style={{ padding: window.innerWidth >= 1024 ? '16px' : '12px' }}
        onClick={onToggle}
      >
        <h3 className="text-base lg:text-lg font-semibold text-gray-800">{title}</h3>
        {isExpanded ? <ChevronDown className="w-4 h-4 lg:w-5 lg:h-5 text-gray-500" /> : <ChevronRight className="w-4 h-4 lg:w-5 lg:h-5 text-gray-500" />}
      </div>
      
      {isExpanded && (
        <div className="border-t border-gray-900">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px]">
              <thead>
                <tr>
                  <th
                    className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    style={{
                      paddingLeft: window.innerWidth >= 1024 ? '16px' : '8px',
                      paddingRight: window.innerWidth >= 1024 ? '16px' : '8px',
                      paddingTop: window.innerWidth >= 1024 ? '12px' : '8px',
                      paddingBottom: window.innerWidth >= 1024 ? '12px' : '8px'
                    }}
                  >
                    User
                  </th>
                  {columns.map((column) => (
                    <th
                      key={column.key}
                      className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      style={{
                        paddingLeft: window.innerWidth >= 1024 ? '16px' : '8px',
                        paddingRight: window.innerWidth >= 1024 ? '16px' : '8px',
                        paddingTop: window.innerWidth >= 1024 ? '12px' : '8px',
                        paddingBottom: window.innerWidth >= 1024 ? '12px' : '8px'
                      }}
                    >
                      <div className="flex items-center gap-1">
                        {column.label}
                        {/* {column.tooltip && (
                          <Tooltip content={column.tooltip}>
                            <Info className="w-3 h-3 text-gray-400 hover:text-gray-600 cursor-help" />
                          </Tooltip>
                        )} */}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {users.map((user) => {
                  const userData = tableData[user.username]
                  if (!userData) return null
                  
                  return (
                    <tr key={user.username} className="hover:">
                      <td
                        className="whitespace-nowrap"
                        style={{
                          paddingLeft: window.innerWidth >= 1024 ? '16px' : '8px',
                          paddingRight: window.innerWidth >= 1024 ? '16px' : '8px',
                          paddingTop: window.innerWidth >= 1024 ? '16px' : '12px',
                          paddingBottom: window.innerWidth >= 1024 ? '16px' : '12px'
                        }}
                      >
                        <div className="flex items-center">
                          <img
                            className="rounded-full"
                            style={{
                              height: window.innerWidth >= 1024 ? '32px' : '24px',
                              width: window.innerWidth >= 1024 ? '32px' : '24px',
                              marginRight: window.innerWidth >= 1024 ? '12px' : '8px'
                            }}
                            src={user.avatar_url}
                            alt={user.username}
                          />
                          <span className="text-xs lg:text-sm font-medium text-gray-900 truncate">{user.username}</span>
                        </div>
                      </td>
                      {columns.map((column) => (
                        <td
                          key={column.key}
                          className="text-xs lg:text-sm text-gray-900"
                          style={{
                            paddingLeft: window.innerWidth >= 1024 ? '16px' : '8px',
                            paddingRight: window.innerWidth >= 1024 ? '16px' : '8px',
                            paddingTop: window.innerWidth >= 1024 ? '16px' : '12px',
                            paddingBottom: window.innerWidth >= 1024 ? '16px' : '12px'
                          }}
                        >
                          {column.type === 'array' && Array.isArray(userData[column.key]) 
                            ? userData[column.key].join(', ')
                            : userData[column.key] || 'N/A'
                          }
                        </td>
                      ))}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default function Dashboard({ 
  compatibilityScore, 
  compatibilityReasoning, 
  users, 
  radarChartData, 
  comparisonData 
}: DashboardProps) {
  const [expandedSections, setExpandedSections] = useState<{ [key: string]: boolean }>({
    activity: false,
    repositories: false,
    languages: false,
    topics: false
  })

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const scrollToSection = (section: string) => {
    // First expand the section if it's not already expanded
    if (!expandedSections[section]) {
      setExpandedSections(prev => ({
        ...prev,
        [section]: true
      }))
    }
    
    // Then scroll to the section after a short delay to allow expansion
    setTimeout(() => {
      const element = document.getElementById(`section-${section}`)
      if (element) {
        element.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start',
          inline: 'nearest'
        })
      }
    }, 100)
  }

  const getSummaryMetrics = () => {
    if (!comparisonData) return []

    const activityData = comparisonData.activity_comparison?.[0]
    const repoData = comparisonData.repository_comparison?.[0]
    const langData = comparisonData.language_comparison?.[0]

    const metrics = []

    if (activityData) {
      const totalPRs = users.reduce((sum, user) => sum + (activityData[user.username]?.pull_requests || 0), 0)
      const totalCommits = users.reduce((sum, user) => sum + (activityData[user.username]?.commits || 0), 0)
      const totalIssues = users.reduce((sum, user) => sum + (activityData[user.username]?.issues || 0), 0)
      const totalReleases = users.reduce((sum, user) => sum + (activityData[user.username]?.releases || 0), 0)
      
      metrics.push(
        { 
          title: 'Total Commits', 
          value: totalCommits, 
          icon: <Activity className="w-5 h-5" />,
          tooltip: 'Total commits across all users',
          onClick: () => scrollToSection('activity'),
          isClickable: true
        },
        { 
          title: 'Pull Requests', 
          value: totalPRs, 
          icon: <GitBranch className="w-5 h-5" />,
          tooltip: 'Total pull requests created',
          onClick: () => scrollToSection('activity'),
          isClickable: true
        },
        { 
          title: 'Issues Created', 
          value: totalIssues, 
          icon: <Activity className="w-5 h-5" />,
          tooltip: 'Total issues created',
          onClick: () => scrollToSection('activity'),
          isClickable: true
        },
        { 
          title: 'Releases', 
          value: totalReleases, 
          icon: <Star className="w-5 h-5" />,
          tooltip: 'Total releases published',
          onClick: () => scrollToSection('activity'),
          isClickable: true
        }
      )
    }

    if (repoData) {
      const totalRepos = users.reduce((sum, user) => sum + (repoData[user.username]?.total_repos || 0), 0)
      const totalStars = users.reduce((sum, user) => sum + (repoData[user.username]?.total_stars || 0), 0)
      const totalForks = users.reduce((sum, user) => sum + (repoData[user.username]?.total_forks || 0), 0)
      const publicRepos = users.reduce((sum, user) => sum + (repoData[user.username]?.public_repos || 0), 0)
      const totalWatchers = users.reduce((sum, user) => sum + (repoData[user.username]?.total_watchers || 0), 0)

      
      metrics.push(
        { 
          title: 'Total Repositories', 
          value: totalRepos, 
          icon: <Code className="w-5 h-5" />,
          tooltip: 'Total repositories across all users',
          onClick: () => scrollToSection('repositories'),
          isClickable: true
        },
        { 
          title: 'Stars Received', 
          value: totalStars, 
          icon: <Star className="w-5 h-5" />,
          tooltip: 'Total stars received on repositories',
          onClick: () => scrollToSection('repositories'),
          isClickable: true
        },
        { 
          title: 'Forks Received', 
          value: totalForks, 
          icon: <GitBranch className="w-5 h-5" />,
          tooltip: 'Total forks of repositories',
          onClick: () => scrollToSection('repositories'),
          isClickable: true
        },
        { 
          title: 'Public Repos', 
          value: publicRepos, 
          icon: <Code className="w-5 h-5" />,
          tooltip: 'Number of public repositories',
          onClick: () => scrollToSection('repositories'),
          isClickable: true
        },
        { 
          title: 'Watchers', 
          value: totalWatchers, 
          icon: <Activity className="w-5 h-5" />,
          tooltip: 'Total watchers across repositories',
          onClick: () => scrollToSection('repositories'),
          isClickable: true
        }
      )
    }

    if (langData) {
      const avgLanguages = users.reduce((sum, user) => sum + (langData[user.username]?.total_languages || 0), 0) / users.length
      const totalCodeBytes = users.reduce((sum, user) => sum + (langData[user.username]?.total_code_bytes || 0), 0)
      const maxLanguages = Math.max(...users.map(user => langData[user.username]?.total_languages || 0))
      
      // Find user with max languages and get their languages
      const userWithMaxLanguages = users.find(user => (langData[user.username]?.total_languages || 0) === maxLanguages)
      const maxLanguagesList = userWithMaxLanguages ? 
        (radarChartData?.languages?.map(lang => lang.language).slice(0, maxLanguages).join(', ') || 'N/A') : 
        'N/A'
      
      metrics.push(
        { 
          title: 'Avg Languages/User', 
          value: avgLanguages.toFixed(1), 
          icon: <BarChart3 className="w-5 h-5" />,
          tooltip: 'Average programming languages per user',
          onClick: () => scrollToSection('languages'),
          isClickable: true
        },
        { 
          title: 'Max Languages', 
          value: maxLanguages, 
          icon: <Code className="w-5 h-5" />,
          tooltip: `languages used: ${maxLanguagesList}`,
          onClick: () => scrollToSection('languages'),
          isClickable: true
        },
        { 
          title: 'Total Code Size', 
          value: (totalCodeBytes / 1024 / 1024).toFixed(1) + ' MB', 
          icon: <Code className="w-5 h-5" />,
          tooltip: 'Total code size across repositories',
          onClick: () => scrollToSection('languages'),
          isClickable: true
        }
      )
    }

    return metrics
  }

  const summaryMetrics = getSummaryMetrics()

  return (
    <div
      className="min-h-screen"
      style={{
        background: 'radial-gradient(circle 800px at 100% 200px, #FF621F, #E6E6E6)',
        transition: 'background 2s',
      }}
    >
      <div className="shadow-[12px_#222] border-b border-gray-900">
        <div className="max-w-7xl mx-auto" style={{ paddingLeft: '16px', paddingRight: '16px' }}>
          <div
            className="flex flex-col lg:flex-row lg:justify-between lg:items-center"
            style={{
              paddingTop: '24px',
              paddingBottom: '24px',
              marginBottom: 0,
              gap: window.innerWidth >= 1024 ? 0 : '16px',
              flexDirection: window.innerWidth >= 1024 ? 'row' : 'column'
            }}
          >
            <div>
              <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">GitHub Compatibility Dashboard</h1>
              <p className="text-sm text-gray-500" style={{ marginTop: '4px' }}>
                Comprehensive analysis of {users.length} developers
              </p>
            </div>
            <div className="flex flex-wrap items-center" style={{ gap: '16px' }}>
              {users.map((user) => (
                <a
                  key={user.username}
                  href={`https://github.com/${user.username}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center"
                  style={{ gap: '8px', textDecoration: 'none' }}
                >
                  <img
                    className="rounded-full border-4 border-[#222] hover:border-gray-600"
                    style={{ height: '48px', width: '48px' }}
                    src={user.avatar_url}
                    alt={user.username}
                  />
                  <span className="text-md font-bold text-gray-900 hover:text-gray-600">
                    {user.username}
                  </span>
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div
        className="max-w-7xl mx-auto"
        style={{
          paddingLeft: '16px',
          paddingRight: '16px',
          paddingTop: '32px',
          paddingBottom: 0
        }}
      >
        {/* Summary Metrics */}
        <div
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4"
          style={{
            gap: window.innerWidth >= 1024 ? '24px' : '16px',
            marginBottom: '32px'
          }}
        >
          {summaryMetrics.map((metric, index) => (
            <MetricCard key={index} {...metric} />
          ))}
        </div>

        {/* Compatibility Score Widget */}
        <div
          className="rounded-lg shadow-[8px_10px_0px_#222] hover:shadow-md border-4 border-gray-900"
          style={{ padding: '24px', marginBottom: '32px' }}
        >
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900" style={{ marginBottom: '16px' }}>
              Compatibility Analysis
            </h2>
            <div className="flex justify-center" style={{ marginBottom: '24px' }}>
              <CompatibilityScore score={compatibilityScore} />
            </div>
            <div className="max-w-3xl mx-auto">
              <div className="rounded-lg text-left" style={{ padding: '16px' }}>
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
              </div>
            </div>
          </div>
        </div>

        {/* Skills Chart */}
        {radarChartData && radarChartData.languages && radarChartData.languages.length > 0 && (
          <div
            className="rounded-lg shadow-[8px_10px_0px_#222] hover:shadow-md border-4 border-gray-900"
            style={{
              padding: window.innerWidth >= 1024 ? '24px' : '16px',
              marginBottom: '32px'
            }}
          >
            <div className="flex items-center justify-between" style={{ gap: '8px' }}>
            <h2
              className="text-lg lg:text-xl font-semibold text-gray-900"
              style={{ marginBottom: '16px' }}
            >
              Programming Language Proficiency
            </h2>
            <Tooltip 
            children={<Info className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" />} 
            content="We score the top 10 most popular languages for each user, ranking their usage from 10 (most used) down to 1. Languages not used by a user receive a score of 0. This provides a clear 0–10 proficiency scale for each language."

            ></Tooltip>
            </div>
            <div className="overflow-x-auto">
              <LineChart
                data={radarChartData.languages
                  .filter(lang => lang.language !== 'language')
                  .map(lang => ({
                    ...lang,
                    label: lang.language
                  }))}
                title=""
                yAxisLabel="Proficiency Level"
                height={300}
              />
            </div>
          </div>
        )}

        {/* Detailed Data Tables */}
        <div style={{ gap: window.innerWidth >= 1024 ? '24px' : '16px', display: 'flex', flexDirection: 'column' }}>
          <h2 className="text-xl lg:text-2xl font-bold text-gray-900">Detailed Metrics</h2>
          
          {/* Activity Metrics */}
          {comparisonData?.activity_comparison && comparisonData.activity_comparison.length > 0 && (
            <div id="section-activity">
            {/* <Typewriter
              options={{
                strings: [
                  radarChartData && radarChartData.languages
                    ? radarChartData.languages.map(lang => lang.language).join(', ')
                    : ''
                ],
                autoStart: true,
                delay: 20,
                deleteSpeed: Infinity,
              }}
            /> */}

              <DataTable
                title="Activity Metrics"
                data={comparisonData.activity_comparison}
                users={users}
                columns={[
                  { key: 'pushes', label: 'Pushes', type: 'number', tooltip: 'Number of code pushes to repositories' },
                  { key: 'commits', label: 'Commits', type: 'number', tooltip: 'Total number of commits made' },
                  { key: 'pull_requests', label: 'Pull Requests', type: 'number', tooltip: 'Number of pull requests created' },
                  { key: 'issues', label: 'Issues', type: 'number', tooltip: 'Number of issues created' },
                  { key: 'releases', label: 'Releases', type: 'number', tooltip: 'Number of releases published' },
                  { key: 'stars', label: 'Stars Given', type: 'number', tooltip: 'Number of repositories starred' }
                ]}
                isExpanded={expandedSections.activity}
                onToggle={() => toggleSection('activity')}
              />
            </div>
          )}

          {/* Repository Metrics */}
          {comparisonData?.repository_comparison && comparisonData.repository_comparison.length > 0 && (
            <div id="section-repositories">
              <DataTable
                title="Repository Statistics"
                data={comparisonData.repository_comparison}
                users={users}
                columns={[
                  { key: 'total_repos', label: 'Total Repos', type: 'number', tooltip: 'Total number of repositories owned' },
                  { key: 'public_repos', label: 'Public', type: 'number', tooltip: 'Number of public repositories' },
                  { key: 'private_repos', label: 'Private', type: 'number', tooltip: 'Number of private repositories' },
                  { key: 'original_repos', label: 'Original', type: 'number', tooltip: 'Number of original (non-forked) repositories' },
                  { key: 'forked_repos', label: 'Forks', type: 'number', tooltip: 'Number of forked repositories' },
                  { key: 'total_stars', label: 'Stars Received', type: 'number', tooltip: 'Total stars received on all repositories' },
                  { key: 'total_forks', label: 'Forks Received', type: 'number', tooltip: 'Total forks received on all repositories' },
                  { key: 'total_watchers', label: 'Watchers', type: 'number', tooltip: 'Total watchers across all repositories' },
                  { key: 'avg_repo_size', label: 'Avg Size (KB)', type: 'number', tooltip: 'Average repository size in kilobytes' }
                ]}
                isExpanded={expandedSections.repositories}
                onToggle={() => toggleSection('repositories')}
              />
            </div>
          )}

          {/* Language Diversity */}
          {comparisonData?.language_comparison && comparisonData.language_comparison.length > 0 && (
            <div id="section-languages">
              <DataTable
                title="Language Diversity"
                data={comparisonData.language_comparison}
                users={users}
                columns={[
                  { key: 'total_languages', label: 'Total Languages', type: 'number', tooltip: 'Number of different programming languages used' },
                  { key: 'primary_language', label: 'Primary Language', type: 'text', tooltip: 'Most frequently used programming language' },
                  { key: 'primary_language_percentage', label: 'Primary %', type: 'number', tooltip: 'Percentage of code written in primary language' },
                  { key: 'language_diversity', label: 'Diversity Score', type: 'number', tooltip: 'Score indicating how evenly distributed languages are (0-1)' },
                  { key: 'total_code_bytes', label: 'Code Bytes', type: 'number', tooltip: 'Total size of code written across all languages' }
                ]}
                isExpanded={expandedSections.languages}
                onToggle={() => toggleSection('languages')}
              />
            </div>
          )}

          {/* Topic Interests */}
          {comparisonData?.topic_comparison && comparisonData.topic_comparison.length > 0 && (
            <div id="section-topics">
              <DataTable
                title="Topic Interests"
                data={comparisonData.topic_comparison}
                users={users}
                columns={[
                  { key: 'total_topics', label: 'Total Topics', type: 'number', tooltip: 'Number of different technology topics/domains' },
                  { key: 'top_topics', label: 'Top Topics', type: 'array', tooltip: 'Most frequently mentioned technology topics' }
                ]}
                isExpanded={expandedSections.topics}
                onToggle={() => toggleSection('topics')}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
