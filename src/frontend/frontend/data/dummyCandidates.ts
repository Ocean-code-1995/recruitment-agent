export interface Candidate {
  id: string
  name: string
  email: string
  phone: string
  status: 'applied' | 'screened' | 'voice_screening' | 'scheduled' | 'rejected' | 'hired'
  cvPath: string
  appliedAt: string
  position: string
  skills: string[]
  experience: string
  education: string
  plan?: PlanStep[]
  reasoningLog?: ReasoningLog[]
}

export interface PlanStep {
  id: string
  step: string
  status: 'completed' | 'in_progress' | 'pending'
  timestamp?: string
}

export interface ReasoningLog {
  timestamp: string
  message: string
  type?: 'info' | 'success' | 'warning' | 'error'
}

export const dummyCandidates: Candidate[] = [
  {
    id: '1',
    name: 'Sarah Chen',
    email: 'sarah.chen@example.com',
    phone: '+1 555-0123',
    status: 'voice_screening',
    cvPath: '/cvs/sarah_chen.pdf',
    appliedAt: '2025-01-15T10:30:00',
    position: 'AI Engineer',
    skills: ['Python', 'PyTorch', 'LangChain', 'NLP', 'MLOps'],
    experience: '5 years in ML engineering, worked on LLM deployment at scale',
    education: 'M.S. Computer Science, Stanford University',
    plan: [
      { id: '1', step: 'Screen CVs', status: 'completed', timestamp: '10:35' },
      { id: '2', step: 'Invite for voice screening', status: 'completed', timestamp: '11:00' },
      { id: '3', step: 'Conduct voice screening', status: 'in_progress', timestamp: '11:15' },
      { id: '4', step: 'Schedule HR interview', status: 'pending' },
      { id: '5', step: 'Await HR decision', status: 'pending' },
    ],
    reasoningLog: [
      { timestamp: '10:35', message: 'Detected strong match for AI Engineer role. Excellent Python and PyTorch experience.', type: 'success' },
      { timestamp: '10:40', message: 'CV score: 9.2/10. Strong background in LLM deployment and MLOps.', type: 'info' },
      { timestamp: '11:00', message: 'Invitation email sent to candidate for voice screening.', type: 'info' },
      { timestamp: '11:15', message: 'Voice screening in progress. Candidate demonstrating strong technical knowledge.', type: 'info' },
    ],
  },
  {
    id: '2',
    name: 'Michael Rodriguez',
    email: 'michael.r@example.com',
    phone: '+1 555-0124',
    status: 'scheduled',
    cvPath: '/cvs/michael_rodriguez.pdf',
    appliedAt: '2025-01-14T14:20:00',
    position: 'AI Engineer',
    skills: ['Python', 'TensorFlow', 'Deep Learning', 'Computer Vision', 'Docker'],
    experience: '3 years in deep learning research, published papers on CV',
    education: 'Ph.D. Computer Vision, MIT',
    plan: [
      { id: '1', step: 'Screen CVs', status: 'completed', timestamp: '14:25' },
      { id: '2', step: 'Invite for voice screening', status: 'completed', timestamp: '15:00' },
      { id: '3', step: 'Conduct voice screening', status: 'completed', timestamp: '15:30' },
      { id: '4', step: 'Schedule HR interview', status: 'completed', timestamp: '16:00' },
      { id: '5', step: 'Await HR decision', status: 'in_progress', timestamp: '16:15' },
    ],
    reasoningLog: [
      { timestamp: '14:25', message: 'Strong academic background with Ph.D. from MIT. Excellent research credentials.', type: 'success' },
      { timestamp: '14:30', message: 'CV score: 8.8/10. Strong in computer vision and deep learning.', type: 'info' },
      { timestamp: '15:30', message: 'Voice screening completed. Confidence score: 8.5/10. Candidate shows good communication skills.', type: 'success' },
      { timestamp: '16:00', message: 'HR interview scheduled for January 20, 2025 at 2:00 PM.', type: 'info' },
    ],
  },
  {
    id: '3',
    name: 'Emily Watson',
    email: 'emily.watson@example.com',
    phone: '+1 555-0125',
    status: 'screened',
    cvPath: '/cvs/emily_watson.pdf',
    appliedAt: '2025-01-16T09:15:00',
    position: 'AI Engineer',
    skills: ['Python', 'LangChain', 'RAG', 'Vector Databases', 'FastAPI'],
    experience: '4 years building AI applications, expertise in RAG systems',
    education: 'B.S. Computer Science, UC Berkeley',
    plan: [
      { id: '1', step: 'Screen CVs', status: 'completed', timestamp: '09:20' },
      { id: '2', step: 'Invite for voice screening', status: 'in_progress', timestamp: '09:45' },
      { id: '3', step: 'Conduct voice screening', status: 'pending' },
      { id: '4', step: 'Schedule HR interview', status: 'pending' },
      { id: '5', step: 'Await HR decision', status: 'pending' },
    ],
    reasoningLog: [
      { timestamp: '09:20', message: 'Good match for AI Engineer role. Strong experience with LangChain and RAG systems.', type: 'info' },
      { timestamp: '09:25', message: 'CV score: 8.0/10. Solid practical experience building production AI systems.', type: 'info' },
      { timestamp: '09:45', message: 'Preparing voice screening invitation...', type: 'info' },
    ],
  },
  {
    id: '4',
    name: 'David Kim',
    email: 'david.kim@example.com',
    phone: '+1 555-0126',
    status: 'applied',
    cvPath: '/cvs/david_kim.pdf',
    appliedAt: '2025-01-17T11:00:00',
    position: 'AI Engineer',
    skills: ['Python', 'Scikit-learn', 'Pandas', 'SQL', 'AWS'],
    experience: '2 years in data science, transitioning to ML engineering',
    education: 'M.S. Data Science, NYU',
    plan: [
      { id: '1', step: 'Screen CVs', status: 'in_progress', timestamp: '11:05' },
      { id: '2', step: 'Invite for voice screening', status: 'pending' },
      { id: '3', step: 'Conduct voice screening', status: 'pending' },
      { id: '4', step: 'Schedule HR interview', status: 'pending' },
      { id: '5', step: 'Await HR decision', status: 'pending' },
    ],
    reasoningLog: [
      { timestamp: '11:05', message: 'CV received. Analyzing candidate profile...', type: 'info' },
    ],
  },
  {
    id: '5',
    name: 'Jessica Martinez',
    email: 'jessica.m@example.com',
    phone: '+1 555-0127',
    status: 'rejected',
    cvPath: '/cvs/jessica_martinez.pdf',
    appliedAt: '2025-01-13T08:30:00',
    position: 'AI Engineer',
    skills: ['Java', 'Spring Boot', 'SQL', 'REST APIs'],
    experience: '3 years in backend development, limited ML experience',
    education: 'B.S. Software Engineering, University of Texas',
    plan: [
      { id: '1', step: 'Screen CVs', status: 'completed', timestamp: '08:35' },
      { id: '2', step: 'Invite for voice screening', status: 'pending' },
      { id: '3', step: 'Conduct voice screening', status: 'pending' },
      { id: '4', step: 'Schedule HR interview', status: 'pending' },
      { id: '5', step: 'Await HR decision', status: 'pending' },
    ],
    reasoningLog: [
      { timestamp: '08:35', message: 'CV reviewed. Limited ML/AI experience detected.', type: 'warning' },
      { timestamp: '08:40', message: 'CV score: 5.2/10. Strong backend skills but lacks required AI/ML expertise.', type: 'info' },
      { timestamp: '08:45', message: 'Candidate does not meet minimum requirements for AI Engineer position.', type: 'error' },
    ],
  },
]

export function getCandidateById(id: string): Candidate | undefined {
  return dummyCandidates.find(c => c.id === id)
}

