// client/src/App.tsx
import React from 'react';
import SimulationController from './components/SimulationController';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import IntroPage from './pages/IntroPage';

function App() {
  return (
    <Router basename="/simulation">
      <div className="h-screen bg-black text-white font-sans overflow-hidden">
        <main className="h-full">
          <Routes>
            <Route path="/" element={<IntroPage />} />
            <Route path="/simulation" element={<SimulationController websocketUrl={import.meta.env.VITE_WS_URL} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;