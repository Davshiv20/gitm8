
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js'
import { Chart } from 'react-chartjs-2'

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

interface RadarChartProps {
  data: {
    languages: Array<{ language: string; [username: string]: number | string }>
  }
}

const getRadarChartData = (rawData: RadarChartProps['data']) => {
  if (!rawData || !rawData.languages || rawData.languages.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  // Get all usernames (keys except 'language')
  const usernames = Object.keys(rawData.languages[0]).filter(key => key !== 'language')

  // Labels are all languages
  const labels = rawData.languages.map(item => item.language)

  // Assign colors for up to 6 users, fallback to random if more
  const palette = [
    'rgba(91,120,190,0.6)',
    'rgba(255,99,132,0.5)',
    'rgba(54,162,235,0.5)',
    'rgba(255,206,86,0.5)',
    'rgba(75,192,192,0.5)',
    'rgba(153,102,255,0.5)',
    'rgba(255,159,64,0.5)',
  ]

  const borderPalette = [
    'rgba(91,121,190,1)',
    'rgba(255,99,132,1)',
    'rgba(54,162,235,1)',
    'rgba(255,206,86,1)',
    'rgba(75,192,192,1)',
    'rgba(153,102,255,1)',
    'rgba(255,159,64,1)',
  ]

  // Build datasets for each user
  const datasets = usernames.map((username, idx) => ({
    label: username,
    data: rawData.languages.map(item => typeof item[username] === 'number' ? item[username] : 0),
    backgroundColor: palette[idx % palette.length],
    borderColor: borderPalette[idx % borderPalette.length],
    borderWidth: 2,
    pointBackgroundColor: borderPalette[idx % borderPalette.length],
    pointBorderColor: '#fff',
    pointHoverBackgroundColor: '#fff',
    pointHoverBorderColor: borderPalette[idx % borderPalette.length],
    fill: true,
  }))

  return {
    labels,
    datasets,
  }
}

const RadarChart = ({ data }: RadarChartProps) => {
  const chartData = getRadarChartData(data)

  return (
    <div>
      <Chart
        type="radar"
        data={chartData}
        options={{
          plugins: {
            legend: {
              display: true,
              position: 'top',
            },
            tooltip: {
              enabled: true,
            },
          },
          scales: {
            r: {
              angleLines: { display: true },
              suggestedMin: 0,
              // You can adjust max if you want, or let Chart.js auto-scale
              suggestedMax: 10,
              pointLabels: {
                font: {
                  size: 14,
                },
              },
              ticks: {
                stepSize: 5,
                // callback: (value) => value + '%',
                font: {
                  size: 8,
                },
                backdropColor: '#A6E3E9',
                textStrokeColor: '#252A34'
              },
            },
          },
          responsive: true,
          maintainAspectRatio: false,
        }}
        height={350}
      />
    </div>
  )
}

export default RadarChart