// client/src/App.tsx
import React from 'react';
import SimulationController from './components/SimulationController';

function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 p-4 shadow-lg">
        <h1 className="text-2xl font-bold">Particle Life Simulation</h1>
      </header>
      
      <main className="p-8">
        <SimulationController websocketUrl="ws://localhost:8000/ws/simulation" />
      </main>

      <footer className="bg-gray-800 p-4 text-center text-gray-400">
        <div className="text-sm">
          Controls:
          <span className="mx-2">Click on particles for details</span>
          <span className="mx-2">|</span>
          <span className="mx-2">Use controls to adjust visualization</span>
          <span className="mx-2">|</span>
          <span className="mx-2">Add new species in the side panel</span>
        </div>
      </footer>
    </div>
  );
}

export default App;