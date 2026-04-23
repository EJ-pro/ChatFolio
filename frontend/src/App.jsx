import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Analysis from './pages/Analysis';
import Chat from './pages/Chat';
import DocsTab from './pages/DocsTab';
import InterviewTab from './pages/InterviewTab';
import ArchitectureTab from './pages/ArchitectureTab';
import AuthCallback from './pages/AuthCallback';
import { Search, Github, Loader2, GitBranch, FileCode2, Share2, Sparkles, MessageSquare, BookOpen, Layers } from 'lucide-react';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import MyPage from './pages/MyPage';
import DashboardLayout from './components/DashboardLayout';
import Privacy from './pages/Privacy';
import Terms from './pages/Terms';
import FAQ from './pages/FAQ';
import DocDeepPipeline from './pages/DocDeepPipeline';

// Authentication guard component
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

// Home redirect component (handles root / access)
function Home() {
  const token = localStorage.getItem('token');
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) {
      navigate('/login', { replace: true });
      return;
    }

    // If token exists, fetch user info and navigate to their page
    fetch('http://localhost:8000/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => {
      if (!res.ok) throw new Error();
      return res.json();
    })
    .then(user => {
      const username = user.github_username || user.name;
      navigate(`/${username}/analysis`, { replace: true });
    })
    .catch(() => {
      localStorage.removeItem('token');
      navigate('/login', { replace: true });
    });
  }, [token, navigate]);

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        
{/* All major routes include :username */}
        <Route path="/:username" element={
          <ProtectedRoute>
            <MyPage />
          </ProtectedRoute>
        } />
        
        <Route path="/:username/analysis" element={
          <ProtectedRoute>
            <Analysis />
          </ProtectedRoute>
        } />
        
        <Route path="/:username/dashboard" element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }>
          <Route path="chat" element={<Chat />} />
          <Route path="architecture" element={<ArchitectureTab />} />
          <Route path="docs" element={<DocsTab />} />
          <Route path="interview" element={<InterviewTab />} />
        </Route>

{/* Default route redirects based on login state */}
        <Route path="/" element={<Home />} />
        
{/* Legal notice pages */}
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/terms" element={<Terms />} />
        <Route path="/faq" element={<FAQ />} />
        
{/* Documentation page */}
        <Route path="/doc" element={<DocDeepPipeline />} />
      </Routes>
    </Router>
  );
}

export default App;