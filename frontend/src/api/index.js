const BASE_URL = 'http://localhost:8000';

const getHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };
};

const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error occurred' }));
    throw new Error(error.detail || response.statusText);
  }
  return response.json();
};

export const api = {
  get: async (endpoint) => {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      headers: getHeaders(),
    });
    return handleResponse(response);
  },

  post: async (endpoint, body) => {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse(response);
  },

  patch: async (endpoint, body) => {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'PATCH',
      headers: getHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse(response);
  },

  delete: async (endpoint) => {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: getHeaders(),
    });
    return handleResponse(response);
  },
};

export const authService = {
  me: () => api.get('/auth/me'),
  login: (code) => api.get(`/auth/callback?code=${code}`),
  updateProfile: (data) => api.patch('/user/profile', data),
  getProfile: (username) => api.get(`/auth/profile/${username}`),
  getGithubRepos: () => api.get('/auth/github/repos'),
  upgradeTier: () => api.post('/auth/upgrade'),
};

export const projectService = {
  analyze: (data) => api.post('/analyze', data),
  getStatus: (taskId) => api.get(`/status/${taskId}`),
  getOverview: (username) => api.get(`/overview/${username}`),
  getNetwork: (sessionId) => api.post('/generate/network', { session_id: sessionId }),
  getArchitectureAnalysis: (sessionId) => api.post('/generate/architecture-analysis', { session_id: sessionId }),
  checkUpdate: (projectId) => api.post(`/projects/${projectId}/check-update`),
};

export const chatService = {
  ask: (data) => api.post('/chat', data),
  getHistory: (sessionId) => api.get(`/chat/history/${sessionId}`),
  getSessionInfo: (sessionId) => api.get(`/chat/session/${sessionId}/info`),
  getProjectSessions: (projectId) => api.get(`/chat/sessions/${projectId}`),
};

export const docsService = {
  generateReadme: (data) => api.post('/generate/readme', data),
  getProjectReadmes: (projectId) => api.get(`/readmes/${projectId}`),
};

export const dashboardService = {
  getGlobalStats: () => api.get('/stats/global'),
};
