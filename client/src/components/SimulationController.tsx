// client/src/components/SimulationController.tsx
import { useState, useEffect, useRef } from 'react';
import { SimulationState, RenderOptions, Diet, ReproductionStyle, ParticleRules } from '../types/simulation';
import SimulationRenderer from './SimulationRenderer';
import SpeciesPanel from './SpeciesPanel';
import StatisticsPanel from './StatisticsPanel';

type SimulationControllerProps = {
    websocketUrl: string;
};

export default function SimulationController({ websocketUrl }: SimulationControllerProps) {
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
        <div className="flex items-center justify-center min-h-screen p-8">
            <div className="flex flex-col gap-8 w-full max-w-7xl">
                <div className="flex gap-8 h-[600px]">
                    {/* Main Simulation View */}
                    <div className="flex-1 bg-gray-900 rounded-lg shadow-xl overflow-hidden w-full h-full">
                        <div className="relative w-full h-full">
                            <SimulationRenderer
                                state={state}
                                options={options}
                                width={state.worldWidth}
                                height={state.worldHeight}
                            />

                            {/* New overlay layer */}
                            <div className="absolute inset-0 z-20 pointer-events-none">
                                {/* Status Indicator - updated classes */}
                                <div className="absolute top-4 left-4 flex items-center gap-2 bg-black/50 backdrop-blur-sm p-2 rounded pointer-events-auto">
                                    <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                                    <span className="text-sm">
                                        {isConnected ? 'Connected' : 'Disconnected'}
                                    </span>
                                </div>

                                {/* Stats Overlay - updated classes */}
                                <div className="absolute top-4 right-4 bg-black/50 backdrop-blur-sm p-2 rounded text-sm pointer-events-auto">
                                    <div>Tick: {state.tickCount}</div>
                                    <div>Particles: {state.particles.size}</div>
                                    <div>Species: {state.species.size}</div>
                                    <div>Groups: {state.groups.size}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Side Panel */}
                    <div className="w-96 bg-gray-900 p-6 rounded-lg shadow-xl">
                        <SpeciesPanel
                            species={Array.from(state.species.values())}
                            onAddSpecies={handleAddSpecies}
                            selectedSpecies={selectedSpecies}
                            onSelectSpecies={setSelectedSpecies}
                        />
                        <StatisticsPanel state={state} selectedSpecies={selectedSpecies} />
                    </div>
                </div>

                {/* Controls */}
                <div className="bg-gray-900 p-6 rounded-lg shadow-xl">
                    <div className="flex flex-wrap gap-6 items-center">
                        <button
                            onClick={handleTogglePause}
                            className={`px-4 py-2 rounded-full ${isPaused ? 'bg-green-600' : 'bg-red-600'} text-white transition-colors`}
                            disabled={!isConnected}
                        >
                            {isPaused ? 'Resume' : 'Pause'}
                        </button>

                        <div className="flex flex-wrap gap-4">
                            {Object.entries(options).map(([key, value]) => (
                                key !== 'particleScale' && key !== 'gridSize' && (
                                    <label key={key} className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={value as boolean}
                                            onChange={e => handleOptionChange(key as keyof RenderOptions, e.target.checked)}
                                            className="form-checkbox text-blue-600"
                                        />
                                        <span className="text-sm">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
                                    </label>
                                )
                            ))}
                        </div>

                        <div className="flex items-center gap-2">
                            <span className="text-sm">Particle Scale:</span>
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
            </div>
        </div>
    );
}
