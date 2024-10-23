// client/src/components/SimulationController.tsx
import React, { useState, useEffect } from 'react';
import { SimulationState, RenderOptions, Particle } from '../types/simulation';
import SimulationRenderer from './SimulationRenderer';

interface SimulationControllerProps {
  websocketUrl: string;
}

const SimulationController: React.FC<SimulationControllerProps> = ({ websocketUrl }) => {
  const [state, setState] = useState<SimulationState>({
    particles: new Map(),
    species: new Map(),
    worldWidth: 800,
    worldHeight: 600,
    tickCount: 0
  });

  const [options, setOptions] = useState<RenderOptions>({
    showGrid: true,
    showVision: false,
    showEnergy: true,
    particleScale: 2,
    gridSize: 20
  });

  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(websocketUrl);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('Connected to simulation server');
    };

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setState(prevState => {
        const newParticles = new Map(prevState.particles);
        const newSpecies = new Map(prevState.species);

        // Convert particles object to array and update
        if (update.particles) {
          Object.entries(update.particles).forEach(([id, particle]: [string, any]) => {
            newParticles.set(id, {
              ...particle,
              position: {
                x: particle.position.x,
                y: particle.position.y
              },
              velocity: {
                x: particle.velocity.x,
                y: particle.velocity.y
              }
            });
          });
        }

        // Convert species object to array and update
        if (update.species) {
          Object.entries(update.species).forEach(([id, species]: [string, any]) => {
            newSpecies.set(id, species);
          });
        }

        return {
          ...prevState,
          particles: newParticles,
          species: newSpecies,
          tickCount: update.tickCount,
          worldWidth: update.worldWidth,
          worldHeight: update.worldHeight
        };
      });
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('Disconnected from simulation server');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, [websocketUrl]);

  const handleTogglePause = () => {
    const ws = new WebSocket(websocketUrl);
    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: isPaused ? 'start' : 'pause'
      }));
      setIsPaused(!isPaused);
    };
  };

  const handleOptionChange = (option: keyof RenderOptions, value: boolean | number) => {
    setOptions(prev => ({
      ...prev,
      [option]: value
    }));
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Simulation Canvas */}
      <div className="relative">
        <SimulationRenderer
          state={state}
          options={options}
          width={state.worldWidth}
          height={state.worldHeight}
        />
        
        {/* Status Indicator */}
        <div className="absolute top-2 left-2 flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-white text-sm">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        {/* Stats Overlay */}
        <div className="absolute top-2 right-2 bg-black/50 text-white p-2 rounded">
          <div>Tick: {state.tickCount}</div>
          <div>Particles: {state.particles.size}</div>
          <div>Species: {state.species.size}</div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex gap-4 p-4 bg-gray-800 rounded">
        <button
          onClick={handleTogglePause}
          className={`px-4 py-2 rounded ${
            isPaused ? 'bg-green-500' : 'bg-red-500'
          } text-white`}
          disabled={!isConnected}
        >
          {isPaused ? 'Resume' : 'Pause'}
        </button>

        <div className="flex gap-4">
          <label className="flex items-center gap-2 text-white">
            <input
              type="checkbox"
              checked={options.showGrid}
              onChange={e => handleOptionChange('showGrid', e.target.checked)}
            />
            Show Grid
          </label>

          <label className="flex items-center gap-2 text-white">
            <input
              type="checkbox"
              checked={options.showVision}
              onChange={e => handleOptionChange('showVision', e.target.checked)}
            />
            Show Vision Range
          </label>

          <label className="flex items-center gap-2 text-white">
            <input
              type="checkbox"
              checked={options.showEnergy}
              onChange={e => handleOptionChange('showEnergy', e.target.checked)}
            />
            Show Energy
          </label>
        </div>

        <div className="flex items-center gap-2 text-white">
          <label>Particle Scale:</label>
          <input
            type="range"
            min="0.5"
            max="2"
            step="0.1"
            value={options.particleScale}
            onChange={e => handleOptionChange('particleScale', parseFloat(e.target.value))}
            className="w-32"
          />
        </div>
      </div>

      {/* Debug Info */}
      {process.env.NODE_ENV === 'development' && (
        <pre className="text-xs text-white bg-black/50 p-2 rounded mt-4">
          {JSON.stringify({
            connected: isConnected,
            particles: state.particles.size,
            species: state.species.size,
            tick: state.tickCount
          }, null, 2)}
        </pre>
      )}
    </div>
  );
};

export default SimulationController;