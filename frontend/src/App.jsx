import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Analysis from './pages/Analysis';
import Chat from './pages/Chat';
import DocsTab from './pages/DocsTab';
import InterviewTab from './pages/InterviewTab';
import AuthCallback from './pages/AuthCallback';
import DashboardLayout from './components/DashboardLayout';

// 인증 가드 컴포넌트
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        
        <Route path="/" element={
          <ProtectedRoute>
            <Analysis />
          </ProtectedRoute>
        } />
        
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }>
          <Route path="chat" element={<Chat />} />
          <Route path="docs" element={<DocsTab />} />
          <Route path="interview" element={<InterviewTab />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;