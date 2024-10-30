// client/src/App.tsx
import SimulationController from './components/SimulationController';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import IntroPage from './pages/IntroPage';

function App() {
  const wsUrl = import.meta.env.DEV 
    ? 'ws://localhost:8000/ws/simulation'  // Development
    : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/simulation`; // Production

  return (
    <Router>
      <div className="h-screen bg-black text-white font-sans overflow-hidden">
        <main className="h-full">
          <Routes>
            <Route path="/" element={<IntroPage />} />
            <Route path="/sim" element={<SimulationController websocketUrl={wsUrl} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;