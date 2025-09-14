import CompatibilityScore from "./CompatibilityScore";
import Typewriter from 'typewriter-effect';
import LineChart from "./LineChart";

interface RadarChartData {
  languages: Array<{ language: string; [username: string]: number | string }>
}

interface ComparisonData {
  activity_comparison?: Array<{ label: string; [username: string]: any }>
  repository_comparison?: Array<{ label: string; [username: string]: any }>
  language_comparison?: Array<{ label: string; [username: string]: any }>
  topic_comparison?: Array<{ label: string; [username: string]: any }>
}

// Patch LineChart to filter out 'languages' from legend
function FilteredLineChart(props: React.ComponentProps<typeof LineChart>) {
  // Filter out 'languages' key from each data object
  const filteredData = props.data.map(item => {
    const newItem: any = { ...item };
    // Remove the 'languages' key if present
    if ('languages' in newItem) {
      delete newItem['languages'];
    }
    return newItem;
  });
  // Also filter out 'languages' from the legend by removing it from the keys
  return <LineChart {...props} data={filteredData} />;
}

export function CompatibilityScoreAnalyzer({
  compatibilityScore,
  compatibilityReasoning,
  users,
  radarChartData,
  comparisonData
}: {
  compatibilityScore: number,
  compatibilityReasoning: string,
  users: {avatar_url: string, username: string}[],
  radarChartData: RadarChartData | null,
  comparisonData?: ComparisonData | null
}) {
    return(
        <div
            className="flex flex-col justify-center space-y-8"
            ref={el => {
              if (el) {
                el.scrollIntoView({ behavior: "smooth", block: "center" });
              }
            }}
          > 

            
            
            {/* User Profiles Section */}
            <div className="  p-6" style={{ padding: "1.5rem" }}>
              <p className="text-center font-bold text-xl text-gray-800 mb-6" style={{ marginBottom: "1.5rem" }}>
                User Profiles
              </p>

              <div className="flex flex-row justify-center gap-8 flex-wrap">
                {users.map((user) => (
                  <div key={user.username} className="flex flex-col justify-center items-center p-4 min-w-[120px]" style={{ padding: "1rem", minWidth: "120px" }}>
                    <img
                      src={user.avatar_url}
                      alt={user.username}
                      className="w-16 h-16 rounded-full mb-3 border-2 border-gray-200"
                      style={{ marginBottom: "0.75rem" }}
                    />
                    <span className="text-sm font-bold text-gray-800 text-center">{user.username}</span>
                  </div>
                ))}
              </div>
              
            </div>

               
              
            <p className="text-center text-xl text-gray-700  font-bold mb-4" style={{ marginBottom: "1rem" }}>Analysis Summary:</p>
                <div className=" p-4  " style={{ padding: "1rem" }}>
                  {/* <Typewriter
                    options={{
                      strings: [compatibilityReasoning],
                      autoStart: true,
                      delay: 20,
                      deleteSpeed: Infinity,
                      cursor: "|",
                      cursorClassName: "text-gray-600",
                    }}
                  /> */}
                  {compatibilityReasoning}
                </div>

            {radarChartData && radarChartData.languages && radarChartData.languages.length > 0 && (
              <div className=" p-6" style={{ padding: "1.5rem" }}>
                <FilteredLineChart
                  data={radarChartData.languages.map(lang => ({
                    ...lang,
                    label: lang.language
                  }))}
                  title="Programming Language Proficiency"
                  yAxisLabel="Proficiency Level"
                  height={400}
                />
              </div>
            )}

            {/* Comparison Parameters Section */}
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-800 text-center mb-6" style={{ marginBottom: "1.5rem" }}>Detailed Comparison Metrics</h2>
              {/* Activity Comparison */}
              {comparisonData?.activity_comparison && comparisonData.activity_comparison.length > 0 && (
                <div className=" p-6" style={{ padding: "1.5rem" }}>
                  <h3 className="text-xl font-bold text-gray-800 mb-4 text-center" style={{ marginBottom: "1rem" }}>Activity Metrics</h3>
                  <div className="space-y-4">
                    {comparisonData.activity_comparison.map((activity, index) => (
                      <div key={index} className="text-sm">
                        {users.map((user) => {
                          const userData = activity[user.username];
                          return userData ? (
                            <div key={user.username} className="mb-2" style={{ marginBottom: "0.5rem" }}>
                              <span className="font-semibold text-gray-700">{user.username}:</span>
                              <div className="ml-4 text-gray-600" style={{ marginLeft: "1rem" }}>
                                <div>Pushes: {userData.pushes}</div>
                                <div>PRs: {userData.pull_requests}</div>
                                <div>Issues: {userData.issues}</div>
                                <div>Stars: {userData.stars}</div>
                              </div>
                            </div>
                          ) : null;
                        })}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Repository Comparison */}
              {comparisonData?.repository_comparison && comparisonData.repository_comparison.length > 0 && (
                <div className=" p-6" style={{ padding: "1.5rem" }}>
                  <h3 className="text-xl font-bold text-gray-800 mb-4 text-center" style={{ marginBottom: "1rem" }}>Repository Statistics</h3>
                  <div className="space-y-4">
                    {comparisonData.repository_comparison.map((repo, index) => (
                      <div key={index} className="text-sm">
                        {users.map((user) => {
                          const userData = repo[user.username];
                          return userData ? (
                            <div key={user.username} className="mb-2" style={{ marginBottom: "0.5rem" }}>
                              <span className="font-semibold text-gray-700">{user.username}:</span>
                              <div className="ml-4 text-gray-600" style={{ marginLeft: "1rem" }}>
                                <div>Total Repos: {userData.total_repos}</div>
                                <div>Original: {userData.original_repos}</div>
                                <div>Forks: {userData.forked_repos}</div>
                                <div>Stars: {userData.total_stars}</div>
                              </div>
                            </div>
                          ) : null;
                        })}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Language Diversity */}
              {comparisonData?.language_comparison && comparisonData.language_comparison.length > 0 && (
                <div className=" p-6" style={{ padding: "1.5rem" }}>
                  <h3 className="text-xl font-bold text-gray-800 mb-4 text-center" style={{ marginBottom: "1rem" }}>Language Diversity</h3>
                  <div className="space-y-4">
                    {comparisonData.language_comparison.map((lang, index) => (
                      <div key={index} className="text-sm">
                        {users.map((user) => {
                          const userData = lang[user.username];
                          return userData ? (
                            <div key={user.username} className="mb-2" style={{ marginBottom: "0.5rem" }}>
                              <span className="font-semibold text-gray-700">{user.username}:</span>
                              <div className="ml-4 text-gray-600" style={{ marginLeft: "1rem" }}>
                                <div>Total Languages: {userData.total_languages}</div>
                                <div>Primary: {userData.primary_language}</div>
                                <div>Diversity Score: {userData.language_diversity}</div>
                              </div>
                            </div>
                          ) : null;
                        })}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {comparisonData?.topic_comparison && comparisonData.topic_comparison.length > 0 && (
                <div className=" p-6" style={{ padding: "1.5rem" }}>
                  <h3 className="text-xl font-bold text-gray-800 mb-4 text-center" style={{ marginBottom: "1rem" }}>Topic Interests</h3>
                  <div className="space-y-4">
                    {comparisonData.topic_comparison.map((topic, index) => (
                      <div key={index} className="text-sm">
                        {users.map((user) => {
                          const userData = topic[user.username];
                          return userData ? (
                            <div key={user.username} className="mb-2" style={{ marginBottom: "0.5rem" }}>
                              <span className="font-semibold text-gray-700">{user.username}:</span>
                              <div className="ml-4 text-gray-600" style={{ marginLeft: "1rem" }}>
                                <div>Total Topics: {userData.total_topics}</div>
                                <div>Top Topics: {userData.top_topics?.join(', ') || 'None'}</div>
                              </div>
                            </div>
                          ) : null;
                        })}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {/* Compatibility Score Section */}
            <div className=" p-8 text-center" style={{ padding: "2rem" }}>
              <h3 className="text-2xl font-bold text-gray-800 mb-6" style={{ marginBottom: "1.5rem" }}>Compatibility Score</h3>
              <div className="flex justify-center mb-6" style={{ marginBottom: "1.5rem" }}>
                <CompatibilityScore score={compatibilityScore} />
              </div>       
            </div>
            
          </div> 
          
    )}