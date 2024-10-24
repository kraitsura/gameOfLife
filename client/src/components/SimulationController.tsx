// client/src/components/SimulationController.tsx
import React, { useState, useEffect, useRef } from 'react';
import { SimulationState, RenderOptions, Species, Diet, ReproductionStyle, ParticleRules, ParticleType } from '../types/simulation';
import SimulationRenderer from './SimulationRenderer';
import SpeciesPanel from './SpeciesPanel';
import StatisticsPanel from './StatisticsPanel';

interface SimulationControllerProps {
    websocketUrl: string;
}

const SimulationController: React.FC<SimulationControllerProps> = ({ websocketUrl }) => {
    const [state, setState] = useState<SimulationState>({
        particles: new Map(),
        species: new Map(),
        groups: new Map(),
        worldWidth: 800,
        worldHeight: 600,
        tickCount: 0
    });

    const [options, setOptions] = useState<RenderOptions>({
        showGrid: true,
        showVision: false,
        showEnergy: true,
        showGroups: true,
        showDiet: true,
        particleScale: 1,
        gridSize: 20
    });

    const [isConnected, setIsConnected] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [selectedSpecies, setSelectedSpecies] = useState<string | null>(null);

    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        wsRef.current = new WebSocket(websocketUrl);

        wsRef.current.onopen = () => {
            setIsConnected(true);
            console.log('Connected to simulation server');
        };

        wsRef.current.onmessage = (event) => {
            const update = JSON.parse(event.data);
            setState(prevState => {
                const newParticles = new Map();
                const newSpecies = new Map();
                const newGroups = new Map();

                // Update particles
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

                // Update species
                if (update.species) {
                    Object.entries(update.species).forEach(([id, species]: [string, any]) => {
                        newSpecies.set(id, species);
                    });
                }

                // Update groups
                if (update.groups) {
                    Object.entries(update.groups).forEach(([id, group]: [string, any]) => {
                        newGroups.set(id, {
                            ...group,
                            memberIds: new Set(group.memberIds),
                            parentIds: group.parentIds ? new Set(group.parentIds) : undefined
                        });
                    });
                }

                return {
                    ...prevState,
                    particles: newParticles,
                    species: newSpecies,
                    groups: newGroups,
                    tickCount: update.tickCount,
                    worldWidth: update.worldWidth,
                    worldHeight: update.worldHeight
                };
            });
        };

        wsRef.current.onclose = () => {
            setIsConnected(false);
            console.log('Disconnected from simulation server');
        };

        wsRef.current.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [websocketUrl]);

    const handleTogglePause = () => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: isPaused ? 'start' : 'pause'
            }));
            setIsPaused(!isPaused);
        }
    };

    const handleAddSpecies = (
        name: string,
        color: string,
        diet: Diet,
        reproductionStyle: ReproductionStyle,
        initialCount: number
    ) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            const rules: ParticleRules = {
                reproductionRate: 0.001,
                energyConsumption: 0.1,
                maxSpeed: 2.0,
                visionRange: 50.0,
                socialDistance: 20.0,
                particleType: 'creature'
            };

            wsRef.current.send(JSON.stringify({
                type: 'add_species',
                name,
                color,
                diet,
                reproductionStyle,
                rules,
                initialCount
            }));
        }
    };

    const handleOptionChange = (option: keyof RenderOptions, value: boolean | number) => {
        setOptions(prev => ({
            ...prev,
            [option]: value
        }));
    };

    return (
        <div className="flex flex-col gap-4">
            <div className="flex gap-4">
                {/* Main Simulation View */}
                <div className="flex-1">
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
                            <div>Groups: {state.groups.size}</div>
                        </div>
                    </div>

                    {/* Controls */}
                    <div className="flex gap-4 p-4 bg-gray-800 rounded mt-4">
                        <button
                            onClick={handleTogglePause}
                            className={`px-4 py-2 rounded ${isPaused ? 'bg-green-500' : 'bg-red-500'
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
                                Show Energy/Hunger
                            </label>

                            <label className="flex items-center gap-2 text-white">
                                <input
                                    type="checkbox"
                                    checked={options.showGroups}
                                    onChange={e => handleOptionChange('showGroups', e.target.checked)}
                                />
                                Show Groups
                            </label>

                            <label className="flex items-center gap-2 text-white">
                                <input
                                    type="checkbox"
                                    checked={options.showDiet}
                                    onChange={e => handleOptionChange('showDiet', e.target.checked)}
                                />
                                Show Diet
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
                </div>

                {/* Side Panel */}
                <div className="w-80 bg-gray-800 p-4 rounded">
                    <SpeciesPanel
                        species={Array.from(state.species.values())}
                        onAddSpecies={handleAddSpecies}
                        selectedSpecies={selectedSpecies}
                        onSelectSpecies={setSelectedSpecies}
                    />
                    <StatisticsPanel state={state} selectedSpecies={selectedSpecies} />
                </div>
            </div>
        </div>
    );
};

export default SimulationController;