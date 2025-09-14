// UI Text Constants

export const LANDING_CARD_TEXT = [
  {
    side: "left",
    topClass: "top-[12rem]",
    delayMs: 0,
    widthClass: "w-48",
    title: "Real Insights",
    subtitle: "Find your code buddy",
    rotateFromDeg: -14,
    rotateToDeg: -8,
    translateShownRem: 2,
  },
  {
    side: "left",
    topClass: "top-[18rem]",
    delayMs: 150,
    widthClass: "w-48",
    title: "Real Charts",
    subtitle: "Score your compatibility!",
    rotateFromDeg: -10,
    rotateToDeg: 0,
    translateShownRem: 2,
  },
  {
    side: "right",
    topClass: "top-[12rem]",
    delayMs: 300,
    widthClass: "w-56",
    title: "Need code buddy?",
    subtitle: "Connect instantly",
    rotateFromDeg: 14,
    rotateToDeg: 6,
    translateShownRem: 2,
  },
  {
    side: "right",
    topClass: "top-[18rem]",
    delayMs: 450,
    widthClass: "w-48",
    title: "Find New Skills! 🔥",
    subtitle: "Collab Request",
    rotateFromDeg: 10,
    rotateToDeg: 0,
    translateShownRem: 2,
  },
  {
    side: "left",
    topClass: "top-[24rem]",
    delayMs: 600,
    widthClass: "w-52",
    title: "Project Matchmaking",
    subtitle: "Discover ideal teammates",
    rotateFromDeg: -14,
    rotateToDeg: 8,
    translateShownRem: 2,
  },
  {
    side: "right",
    topClass: "top-[24rem]",
    delayMs: 750,
    widthClass: "w-60",
    title: "Find Your Hackathon Team ",
    subtitle: "Make new friends",
    rotateFromDeg: 14,
    rotateToDeg: -2,
    translateShownRem: 2,
  },
]
export const UI_TEXT = {
  // App Header
  APP_TITLE: 'GitM8',
  APP_SUBTITLE: "Discover how your Github vibe matches with your friends",
  
  // GitForm
  FORM_TITLE: "Let's find your compatibility",
  GITHUB_PREFIX: "github.com/",
  USERNAME_PLACEHOLDER: "username",
  
  // User Labels
  USER_LABELS: {
    YOUR_USERNAME: "Your GitHub username",
    FRIEND_USERNAME: "Friend's GitHub username",
    FRIEND_NTH: "Friend {n}'s GitHub username"
  },
  
  // Analysis Results
  ANALYSIS_TITLE: "Compatibility Analysis",
  ANALYZE_NEW_BUTTON: "Analyze New Users",
  COMPATIBILITY_SCORE_TITLE: "Compatibility Score",
  SKILLS_OVERLAP_TITLE: "Skills Overlap",
  SHARED_LANGUAGES_TITLE: "Shared Languages",
  SHARED_TECHNOLOGIES_TITLE: "Shared Technologies",
  PROJECT_IDEAS_TITLE: "Project Ideas",
  RECOMMENDATIONS_TITLE: "Recommendations",
  USERS_COUNT_SUFFIX: " users",
  
  // Error Messages
  ERROR_MESSAGES: {
    USER_COUNT_RANGE: "Please enter between {min} and {max} usernames",
    USER_NOT_FOUND: "User not found on GitHub",
    SERVER_ERROR: "An error occurred while fetching user data.",
    GENERAL_ERROR: "An error occurred while fetching user data.",
    FETCH_FAIL: "Failed to fetch GitHub user. Please check the username.",
    USERNAME_EXISTS : "This User has already been added"
  },
  
  // Button Text
  BUTTON_TEXT: {
    ADD_USER: "Add another user",
    REMOVE_USER: "Remove user",
    SUBMIT_LOADING: "GitM8ing...",
    SUBMIT: "GitM8"
  }
} as const;

// Styling Constants
export const STYLING = {
  // Colors
  COLORS: {
    PRIMARY: "#1C2541",
    SECONDARY: "#7189FF",
    ACCENT: "#5BC0BE",
    BLACK: "#000000",
    WHITE: "#FFFFFF",
    GRAY: {
      50: "#F9FAFB",
      100: "#F3F4F6",
      200: "#E5E7EB",
      300: "#D1D5DB",
      400: "#9CA3AF",
      500: "#6B7280",
      600: "#4B5563",
      700: "#374151",
      800: "#1F2937",
      900: "#111827"
    },
    BLUE: {
      50: "#EFF6FF",
      600: "#2563EB",
      700: "#1D4ED8"
    },
    RED: {
      50: "#FEF2F2",
      300: "#FCA5A5",
      500: "#EF4444",
      700: "#B91C1C"
    },
    GREEN: {
      50: "#F0FDF4"
    }
  },
  
  // Sizes
  SIZES: {
    CIRCLE: {
      SMALL: 56,
      MEDIUM: 64,
      LARGE: 90
    },
    STROKE_WIDTH: {
      THIN: 2,
      MEDIUM: 8,
      THICK: 10
    }
  },
  
  // Spacing
  SPACING: {
    SMALL: "0.5rem",
    MEDIUM: "1rem",
    LARGE: "2rem",
    XL: "4rem",
    XXL: "8rem"
  },
  
  // Padding
  PADDING: {
    FORM_CONTAINER: "2rem",
    FORM_HEADER: "2rem",
    INPUT_LEFT: "6.5rem",
    INPUT_TOP: "0.45rem",
    INPUT_BOTTOM: "0.5rem"
  },
  
  // Margins
  MARGINS: {
    FORM_HEADER: "2rem",
    REMOVE_BUTTON: "1rem",
    ADD_BUTTON_TOP: "1rem",
    ADD_BUTTON_BOTTOM: "1rem",
    SUBMIT_BUTTON_TOP: "1rem",
    SUBMIT_BUTTON_BOTTOM: "1rem"
  },
  
  // Border Radius
  BORDER_RADIUS: {
    SMALL: "0.5rem",
    MEDIUM: "0.75rem",
    LARGE: "1rem"
  }
} as const;

// Configuration Constants
export const CONFIG = {
  // User Limits
  USER_LIMITS: {
    MIN_USERS: 2,
    MAX_USERS: 5
  },
  
  // Animation
  ANIMATION: {
    DELAY: 100,
    TRANSITION_DURATION: "200ms",
    TRANSITION_LENGTH: "1s",
    TRANSITION_STEP: "200ms"
  },
  
  // Progress Bar
  PROGRESS: {
    MIN_VALUE: 0,
    MAX_VALUE: 10,
    GAP_PERCENT: 5,
    OFFSET_FACTOR: 0
  },
  
  // Radial Gradient
  RADIAL_GRADIENT: {
    SIZE: 800,
    MIN_X: 10,
    MAX_X: 90,
    MIN_Y: 100,
    MAX_Y: 400,
    VELOCITY_X: 0.9,
    VELOCITY_Y: 0.3,
    RANDOM_CHANCE: 0.01,
    VELOCITY_CLAMP: 0.4,
    INITIAL_X: 50,
    INITIAL_Y: 200,
    BOUNCE_FACTOR: 0.7,
    RANDOM_SPEED_FACTOR: 0.6
  }
} as const;

// API Constants
const getBaseURL = () => {
  // If VITE_API_URL is explicitly set, use it
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  
  // In production (Vercel), use the backend URL
  if (import.meta.env.PROD) {
    return 'https://gitm8-be.vercel.app'
  }
  
  // In development, use localhost
  return 'http://localhost:8000'
}

export const API = {
  BASE_URL: getBaseURL(),
  ENDPOINTS: {
    ANALYZE_COMPATIBILITY: '/api/analyze-compatibility'
  }
} as const;

// CSS Variables
export const CSS_VARS = {
  CIRCLE_SIZE: "100px",
  PERCENT_TO_DEG: "3.6deg",
  TRANSFORM_ORIGIN: "calc(var(--circle-size) / 2) calc(var(--circle-size) / 2)"
} as const;


export const COMPATIBILITY_LABELS = {
  PERFECT_MATCH: "Perfect Match! 👌",
  GREAT_MATCH: "Great Match! 🔥",
  GOOD_POTENTIAL: "Good Potential! 🤝",
  LOW_COMPATIBILITY: "Low Compatibility 😔",
  VERY_LOW: "Very Low 😢"
} as const;
// Component-specific Constants
export const COMPONENTS = {
  // App
  APP: {
    LOGO_DIMENSIONS: {
      WIDTH: 100,
      HEIGHT: 100
    }
  },
  
  // CompatibilityScore
  COMPATIBILITY_SCORE: {
    DEFAULT_SCORE: 7,
    CIRCLE_SIZE: 40,
    STROKE_WIDTH: 10,
    VIEWBOX: "0 0 100 100",
    CIRCLE_RADIUS: 45,
    CIRCLE_CENTER: 50
  },
  
  // AnalysisResults
  ANALYSIS_RESULTS: {
    CONTAINER_MAX_WIDTH: "container mx-auto",
    GRID_COLUMNS: "grid grid-cols-1 md:grid-cols-2",
    CIRCLE_DIMENSIONS: {
      WIDTH: 32,
      HEIGHT: 32,
      CENTER_X: 64,
      CENTER_Y: 64
    }
  }
} as const;
