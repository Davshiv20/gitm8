# Environment Setup Guide

## Required Environment Variables

Create a `.env.development` file in the backend directory with the following variables:

```bash
# Environment
ENV=development

# GitHub Configuration (REQUIRED)
GITHUB_TOKEN=your_github_token_here

# Google Gemini Configuration (OPTIONAL - for LLM fallback)
GOOGLE_API_KEY=your_google_api_key_here

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8000

# Server Configuration
HOST=0.0.0.0
PORT=8180
DEBUG=true
RELOAD=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
```

## Environment Files

The application supports environment-specific configuration files:

- `.env.development` - Development environment
- `.env.stag` - Staging environment  
- `.env.production` - Production environment

The active environment is determined by the `ENV` variable.

## Installation

1. Install dependencies:
```bash
cd backend
poetry install
```

2. Test the configuration:
```bash
poetry run python test_settings.py
```

## Getting Your GitHub Token

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Click "Generate new token (classic)"
3. Select the following scopes:
   - `public_repo` - Access public repositories
   - `read:user` - Read user profile data
   - `read:org` - Read organization data
4. Copy the generated token and set it as `GITHUB_TOKEN`

## Getting Your Google API Key (Optional)

1. Go to Google Cloud Console
2. Enable the Gemini API
3. Create credentials (API Key)
4. Copy the key and set it as `GOOGLE_API_KEY`

## Debugger Configuration

The debugger is configured to run from the project root. Environment variables are set in `.cursor/launch.json`:

1. **Update the debugger configuration**:
   - Open `.cursor/launch.json`
   - Replace `"your_github_token_here"` with your actual GitHub token
   - The debugger will use these environment variables

2. **Alternative: Create .env.development in project root**:
   ```bash
   # From project root
   python backend/setup_env.py create
   # Then edit the created file with your actual token
   ```

## Validation

The application will validate all required environment variables on startup and log any missing variables. Check the console output for validation results.

## Quick Setup

Run the setup helper:
```bash
cd backend
python setup_env.py create
# Edit the created .env.development file with your GitHub token
```
