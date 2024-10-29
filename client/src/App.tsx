// client/src/App.tsx
import React from 'react';
import SimulationController from './components/SimulationController';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import IntroPage from './pages/IntroPage';

function App() {
  return (
    <Router>
      <div className="h-screen bg-black text-white font-sans overflow-hidden">
        <main className="h-full">
        <Routes>
          <Route path="/" element={<IntroPage />} />
          <Route path="/simulation" element={<SimulationController websocketUrl="ws://localhost:8000/ws/simulation" />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;