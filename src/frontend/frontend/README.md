# CV UI Frontend

Next.js frontend for the CV Upload Stage of the Recruitment Agent system.

## Overview

This frontend provides a candidate-friendly interface for submitting job applications. It connects to the Gradio backend using Gradio's JavaScript client.

## Features

- **Candidate Application Form**: Collects full name, email, phone, and CV file
- **Job Description Display**: Expandable job description section
- **Real-time Status**: Connection status and submission feedback
- **File Upload**: Supports PDF and DOCX file formats
- **Form Validation**: Client-side validation before submission

## Setup

1. Install dependencies:

```bash
npm install
```

2. Create a `.env.local` file (optional, defaults to `http://localhost:7860`):

```
NEXT_PUBLIC_GRADIO_URL=http://localhost:7860
```

3. Run the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Usage

1. Make sure the Gradio backend is running (see `src/gradio/README.md`)
2. Open the Next.js app in your browser
3. Fill out the application form
4. Upload your CV (PDF or DOCX)
5. Submit the application

## Building for Production

```bash
npm run build
npm start
```

## Integration

This frontend integrates with:

- **Gradio Backend** (`src/gradio/app.py`) - Handles CV upload and candidate registration
- **CV Utilities** (`src/cv_ui/utils/`) - File saving and database operations

## Architecture

Based on the CV Upload Stage requirements from `info.md`:

- Entry point for candidates into the system
- Collects candidate information and CV files
- Registers candidates in the database with status "applied"
- Triggers automatic CV parsing after registration
