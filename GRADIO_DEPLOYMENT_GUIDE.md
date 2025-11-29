# 🚀 Gradio Frontend Deployment Guide

## Overview

This guide explains the changes made to create a Gradio frontend for Hugging Face Spaces deployment, as required for the **MCP 1st Birthday Hackathon**.

## ✅ What Was Created

### New Files

1. **`src/frontend/gradio/app.py`**
   - Main Gradio application
   - Combines all features from Next.js frontend into a single Gradio interface
   - Three tabs: Candidate Portal, HR Portal, Supervisor Chat

2. **`src/frontend/gradio/requirements.txt`**
   - Python dependencies for Gradio app
   - Includes: gradio, requests, python-dotenv

3. **`src/frontend/gradio/README.md`**
   - Deployment instructions for Hugging Face Spaces
   - Local development guide
   - Configuration options

## 🔄 Changes Made

### 1. Created Unified Gradio Interface

The Gradio app replicates the key functionality from your Next.js frontend:

#### **Tab 1: Candidate Portal** 👤
- ✅ CV upload form (mirrors `app/candidate/page.tsx`)
- ✅ Application status checker
- ✅ Uses `CVUploadClient` and `DatabaseClient` from SDK

#### **Tab 2: HR Portal** 🧑‍💼
- ✅ Candidate list with filtering (mirrors `app/hr/page.tsx`)
- ✅ Voice screening trigger
- ✅ Interview scheduling
- ✅ Uses `DatabaseClient` and `SupervisorClient` from SDK

#### **Tab 3: Supervisor Chat** 🤖
- ✅ Interactive chat interface (mirrors `app/chat/page.tsx`)
- ✅ Thread management
- ✅ Token usage tracking
- ✅ Uses `SupervisorClient` from SDK

### 2. API Integration

The Gradio app uses the **same SDK clients** as your Next.js frontend:
- `SupervisorClient` - for supervisor agent chat
- `DatabaseClient` - for candidate queries
- `CVUploadClient` - for CV submissions

This means:
- ✅ **No backend changes needed** - works with existing API
- ✅ **Same functionality** - all features available
- ✅ **Consistent behavior** - same SDK = same results

### 3. Configuration

The app automatically detects:
- **Hugging Face Spaces**: Uses Space URL for API calls
- **Local Development**: Uses `localhost:8080` by default
- **Environment Variables**: Supports custom API URLs

## 📋 What You DON'T Need to Change

### ✅ Keep Your Next.js Frontend

**You do NOT need to remove or change your Next.js frontend!**

- Next.js frontend: Keep for local development and production
- Gradio frontend: Use specifically for Hugging Face Spaces deployment
- Both can coexist - they use the same backend API

### ✅ No Backend Changes

- Your FastAPI backend (`src/api/`) remains unchanged
- All existing endpoints work with both frontends
- No API modifications needed

## 🎯 Deployment Options

### Option 1: Separate Spaces (Recommended)

1. **Backend Space**: Deploy FastAPI backend to one Space
2. **Frontend Space**: Deploy Gradio app to another Space
3. **Connect**: Set environment variables in Gradio Space to point to backend

**Pros:**
- Clear separation of concerns
- Easier to debug
- Can scale independently

### Option 2: Combined Deployment

Deploy both backend and frontend in the same Space (more complex, requires custom Docker setup).

## 📝 Step-by-Step Deployment

### For Hugging Face Spaces:

1. **Create New Space**
   ```
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Choose: SDK = Gradio, Hardware = CPU Basic
   ```

2. **Upload Files**
   ```
   - Copy src/frontend/gradio/app.py → app.py
   - Copy src/frontend/gradio/requirements.txt → requirements.txt
   - Copy src/frontend/gradio/README.md → README.md (optional)
   ```

3. **Set Environment Variables** (if backend is separate)
   ```
   SUPERVISOR_API_URL=https://your-backend.hf.space/api/v1/supervisor
   DATABASE_API_URL=https://your-backend.hf.space/api/v1/db
   CV_UPLOAD_API_URL=https://your-backend.hf.space/api/v1/cv
   ```

4. **Deploy**
   - Push files to Space
   - Wait for build to complete
   - Your app is live!

## 🔍 Testing Locally

```bash
# 1. Make sure backend is running
# (from project root)
docker compose up supervisor_api

# 2. Run Gradio app
cd src/frontend/gradio
pip install -r requirements.txt
python app.py

# 3. Open http://localhost:7860
```

## 📊 Feature Comparison

| Feature | Next.js Frontend | Gradio Frontend |
|---------|-----------------|-----------------|
| Candidate Application | ✅ | ✅ |
| HR Portal | ✅ | ✅ |
| Supervisor Chat | ✅ | ✅ |
| Voice Screening UI | ✅ (separate) | ⚠️ (via API) |
| Dashboard View | ✅ | ⚠️ (simplified) |
| Deployment | Vercel/Netlify | Hugging Face Spaces |
| Custom Styling | ✅ Full control | ⚠️ Limited |
| Mobile Responsive | ✅ | ⚠️ Basic |

## 🎨 Customization

To customize the Gradio app:

1. **Change Theme**: Edit `theme=gr.themes.Soft()` in `app.py`
2. **Add Features**: Add new tabs or components
3. **Modify Layout**: Adjust `gr.Column()` and `gr.Row()` arrangements
4. **Styling**: Use Gradio's theming system or custom CSS

## 🐛 Troubleshooting

### Issue: "SDK not available"
- **Solution**: Make sure `src/sdk` is in Python path
- The app adds `src/` to path automatically, but check if structure is correct

### Issue: API connection errors
- **Solution**: Check environment variables are set correctly
- Verify backend is running and accessible

### Issue: Import errors
- **Solution**: Install all requirements: `pip install -r requirements.txt`
- Make sure you're in the correct directory

## 📚 Next Steps

1. ✅ Test Gradio app locally
2. ✅ Create Hugging Face Space
3. ✅ Deploy and test on Spaces
4. ✅ Submit to hackathon!

## 💡 Tips

- **Keep both frontends**: Use Next.js for production, Gradio for hackathon
- **Share backend**: Both frontends can use the same API
- **Test thoroughly**: Make sure all features work on Spaces
- **Document well**: Add screenshots and descriptions to your Space

## 🎉 Summary

**What you have now:**
- ✅ Next.js frontend (unchanged) - for production use
- ✅ Gradio frontend (new) - for Hugging Face Spaces
- ✅ Same backend API - works with both
- ✅ Same SDK - consistent functionality

**You don't need to:**
- ❌ Remove Next.js frontend
- ❌ Change backend API
- ❌ Modify existing code
- ❌ Choose one or the other

**Both frontends can coexist and serve different purposes!**

