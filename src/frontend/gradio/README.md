# Gradio Frontend for Hugging Face Spaces

This is a unified Gradio interface for the Recruitment Agent system, designed for deployment on Hugging Face Spaces for the **MCP 1st Birthday Hackathon**.

## 🚀 Features

The Gradio app includes three main tabs:

1. **👤 Candidate Portal**
   - Submit job applications with CV upload
   - Check application status by email
   - View screening results and interview status

2. **🧑‍💼 HR Portal**
   - View and filter candidates by status
   - Trigger voice screening for candidates
   - Schedule interviews
   - Manage recruitment pipeline

3. **🤖 Supervisor Chat**
   - Interactive chat with the HR Supervisor Agent
   - Query candidate information
   - Get help with recruitment tasks
   - Token usage tracking

## 📦 Deployment to Hugging Face Spaces

### Step 1: Create a Hugging Face Space

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. Select:
   - **SDK**: `gradio`
   - **Hardware**: Choose based on your needs (CPU Basic is fine for the frontend)
   - **Visibility**: Public (for hackathon submission)

### Step 2: Upload Files

Upload these files to your Space:

```
app.py                    # Main Gradio application (from src/frontend/gradio/app.py)
requirements.txt          # Python dependencies (from src/frontend/gradio/requirements.txt)
README.md                 # This file (optional, but recommended)
```

**Note**: The app expects the backend API to be accessible. You have two options:

#### Option A: Backend on Same Space (Recommended for Hackathon)
- Deploy the FastAPI backend as a separate Space
- Update API URLs in the Gradio app to point to your backend Space

#### Option B: Backend Running Elsewhere
- Set environment variables in your Space settings:
  - `SUPERVISOR_API_URL`
  - `DATABASE_API_URL`
  - `CV_UPLOAD_API_URL`
  - `VOICE_SCREENER_API_URL`

### Step 3: Configure Environment Variables

In your Space settings, add any required environment variables:

```bash
# API URLs (if backend is separate)
SUPERVISOR_API_URL=https://your-backend-space.hf.space/api/v1/supervisor
DATABASE_API_URL=https://your-backend-space.hf.space/api/v1/db
CV_UPLOAD_API_URL=https://your-backend-space.hf.space/api/v1/cv
VOICE_SCREENER_API_URL=https://your-backend-space.hf.space/api/v1/voice-screener

# OpenAI API Key (if backend needs it)
OPENAI_API_KEY=your_key_here
```

### Step 4: Deploy

1. Push your files to the Space
2. Hugging Face will automatically build and deploy
3. Wait for the build to complete
4. Your app will be live at: `https://your-username-your-space-name.hf.space`

## 🔧 Local Development

To run locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Make sure backend API is running on localhost:8080
# Or set environment variables:
export SUPERVISOR_API_URL=http://localhost:8080/api/v1/supervisor
export DATABASE_API_URL=http://localhost:8080/api/v1/db
export CV_UPLOAD_API_URL=http://localhost:8080/api/v1/cv

# Run Gradio app
python app.py
```

The app will be available at `http://localhost:7860`

## 📝 Differences from Next.js Frontend

This Gradio frontend is a **separate implementation** designed specifically for Hugging Face Spaces deployment. Key differences:

1. **Single Interface**: All features in one Gradio app with tabs
2. **Simplified UI**: Gradio's built-in components instead of custom React
3. **Backend Integration**: Uses the same SDK clients as the Next.js frontend
4. **Deployment**: Optimized for Hugging Face Spaces (no Node.js required)

## 🎯 Hackathon Submission

For the MCP 1st Birthday Hackathon:

1. ✅ Deploy to Hugging Face Spaces (required)
2. ✅ Use Gradio interface (required)
3. ✅ Include all main features (Candidate Portal, HR Portal, Supervisor Chat)
4. ✅ Link to your Space in the hackathon submission

## 🔗 Related Files

- **Next.js Frontend**: `src/frontend/frontend/` (for local development)
- **Streamlit UIs**: `src/frontend/streamlit/` (alternative Python UIs)
- **Backend API**: `src/api/` (FastAPI backend)
- **SDK**: `src/sdk/` (Python SDK used by Gradio app)

## 📚 Documentation

- [Gradio Documentation](https://www.gradio.app/docs/)
- [Hugging Face Spaces Guide](https://huggingface.co/docs/hub/spaces)
- [MCP Hackathon](https://huggingface.co/MCP-1st-Birthday)

