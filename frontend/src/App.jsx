import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Analysis from './pages/Analysis';
import Chat from './pages/Chat';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Analysis />} />
        <Route path="/chat" element={<Chat />} />
      </Routes>
    </Router>
  );
}

export default App;