import React from 'react';
import SimulationController from './components/SimulationController';

function App() {
  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <SimulationController websocketUrl="ws://localhost:8000/ws/simulation" />
    </div>
  );
}

export default App;