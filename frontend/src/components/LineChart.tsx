import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

interface LineChartProps {
  data: Array<{ label: string; [username: string]: string | number }>
  title: string
  yAxisLabel?: string
  height?: number
}

const getLineChartData = (rawData: LineChartProps['data']) => {
  if (!rawData || rawData.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  // Get all usernames (keys except 'label')
  const usernames = Object.keys(rawData[0]).filter(key => key !== 'label')

  // Labels are the data points
  const labels = rawData.map(item => item.label)

  // Color palette for different users
  const palette = [
    'rgba(91,120,190,0.8)', // Blue
    'rgba(255,99,132,0.8)', // Red
    'rgba(54,162,235,0.8)', // Light Blue
    'rgba(255,206,86,0.8)', // Yellow
    'rgba(75,192,192,0.8)', // Teal
    'rgba(153,102,255,0.8)', // Purple
    'rgba(255,159,64,0.8)', // Orange
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
    data: rawData.map(item => typeof item[username] === 'number' ? item[username] : 0),
    borderColor: borderPalette[idx % borderPalette.length],
    backgroundColor: palette[idx % palette.length],
    borderWidth: 3,
    fill: false,
    tension: 0.4,
    pointRadius: 6,
    pointHoverRadius: 8,
    pointBackgroundColor: borderPalette[idx % borderPalette.length],
    pointBorderColor: '#fff',
    pointBorderWidth: 2,
  }))

  return {
    labels,
    datasets,
  }
}

const LineChart = ({ data, title, yAxisLabel = 'Value', height = 300 }: LineChartProps) => {
  const chartData = getLineChartData(data)

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          font: {
            size: 14,
            weight: 'bold' as const,
          },
          padding: 20,
        },
      },
      title: {
        display: true,
        text: title,
        font: {
          size: 18,
          weight: 'bold' as const,
        },
        padding: {
          top: 10,
          bottom: 30,
        },
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0,0,0,0.8)',
        titleFont: {
          size: 14,
          weight: 'bold' as const,
        },
        bodyFont: {
          size: 13,
        },
        padding: 12,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: yAxisLabel,
          font: {
            size: 14,
            weight: 'bold' as const,
          },
        },
        ticks: {
          font: {
            size: 12,
          },
        },
        grid: {
          color: 'rgba(0,0,0,0.1)',
        },
      },
      x: {
        title: {
          display: true,
          text: 'Languages',
          font: {
            size: 14,
            weight: 'bold' as const,
            color: '#000',
          },
        },
        ticks: {
          font: {
            size: 12,
          },
          maxRotation: 45,
        },
        grid: {
          color: 'rgba(0,0,0,0.1)',
        },
      },
    },
    elements: {
      point: {
        hoverBorderWidth: 3,
      },
    },
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
  }

  return (
    <div className="w-full" style={{ height: `${height}px` }}>
      <Line data={chartData} options={options} />
    </div>
  )
}

export default LineChart
