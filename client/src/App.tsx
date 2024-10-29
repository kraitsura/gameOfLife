// client/src/App.tsx
import SimulationController from './components/SimulationController';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import IntroPage from './pages/IntroPage';

function App() {
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/simulation';

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