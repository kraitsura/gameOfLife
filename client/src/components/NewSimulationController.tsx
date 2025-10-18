import React, { useMemo } from 'react';
import { Play, Pause, Database, Activity, Settings, Clock } from 'lucide-react';
import NewSimulationRenderer from './NewSimulationRenderer';
import { BottomDrawer, DrawerTab } from './gotham/BottomDrawer';
import { StatusBar, StatusItem } from './gotham/StatusBar';
import { CommandPalette, CommandItem } from './gotham/CommandPalette';
import { GothamDataGrid, Column } from './gotham/GothamDataGrid';
import { MetricCard } from './gotham/MetricCard';
import { GothamButton } from './gotham/GothamButton';
import { GothamBadge } from './gotham/GothamBadge';
import { GothamChart } from './gotham/GothamChart';
import { useSimulationWebSocket } from '../hooks/useSimulationWebSocket';
import { useCamera } from '../hooks/useCamera';
import { useCommandPalette } from '../hooks/useCommandPalette';
import { useUIStore } from '../store/uiStore';
import { Species, SpeciesStats } from '../types/new_simulation';

interface NewSimulationControllerProps {
  websocketUrl: string;
}

export default function NewSimulationController({ websocketUrl }: NewSimulationControllerProps) {
  const { state, isConnected, isPaused, togglePause } = useSimulationWebSocket(websocketUrl);
  const camera = useCamera();
  const commandPalette = useCommandPalette();
  const {
    selectedSpeciesId,
    setSelectedSpeciesId,
    renderOptions,
    setRenderOption,
    activeTab,
    setActiveTab,
  } = useUIStore();

  // Calculate statistics
  const stats = useMemo(() => {
    const entities = Array.from(state.entities.values()).filter(e => e.type === 'creature');
    const selectedEntities = selectedSpeciesId
      ? entities.filter(e => e.speciesId === selectedSpeciesId)
      : entities;

    const avgEnergy = selectedEntities.length > 0
      ? selectedEntities.reduce((sum, e) => sum + e.energy, 0) / selectedEntities.length
      : 0;

    const avgHealth = selectedEntities.length > 0
      ? selectedEntities.reduce((sum, e) => sum + e.health, 0) / selectedEntities.length
      : 0;

    const childCount = selectedEntities.filter(e => e.isChild).length;
    const packCount = state.packs.size;

    return { avgEnergy, avgHealth, childCount, packCount };
  }, [state.entities, state.packs, selectedSpeciesId]);

  // Prepare species data for grid
  const speciesData = useMemo(() => {
    return Array.from(state.species.values()).map((species) => {
      const speciesEntities = Array.from(state.entities.values()).filter(
        (e) => e.speciesId === species.id && e.type === 'creature'
      );

      const avgEnergy = speciesEntities.length > 0
        ? speciesEntities.reduce((sum, e) => sum + e.energy, 0) / speciesEntities.length
        : 0;

      const avgHealth = speciesEntities.length > 0
        ? speciesEntities.reduce((sum, e) => sum + e.health, 0) / speciesEntities.length
        : 0;

      return {
        ...species,
        avgEnergy,
        avgHealth,
      };
    });
  }, [state.species, state.entities]);

  // Species grid columns
  const speciesColumns: Column<any>[] = [
    {
      key: 'color',
      header: '',
      width: '40px',
      render: (species) => (
        <div className="w-4 h-4 rounded-sm border border-gotham-gray-800" style={{ backgroundColor: species.color }} />
      ),
    },
    {
      key: 'name',
      header: 'Species',
      render: (species) => <span className="font-semibold">{species.name}</span>,
    },
    {
      key: 'population',
      header: 'Population',
      sortable: true,
      align: 'right',
      render: (species) => species.population,
    },
    {
      key: 'traits',
      header: 'Traits',
      render: (species) => (
        <div className="flex gap-1 flex-wrap">
          {Array.from(species.traits).map((trait: string) => (
            <GothamBadge key={trait} variant="default">
              {trait}
            </GothamBadge>
          ))}
        </div>
      ),
    },
    {
      key: 'avgEnergy',
      header: 'Avg Energy',
      sortable: true,
      align: 'right',
      render: (species) => species.avgEnergy.toFixed(1),
    },
    {
      key: 'avgHealth',
      header: 'Avg Health',
      sortable: true,
      align: 'right',
      render: (species) => species.avgHealth.toFixed(1),
    },
  ];

  // Command palette commands
  const commands: CommandItem[] = [
    {
      id: 'pause',
      label: isPaused ? 'Resume Simulation' : 'Pause Simulation',
      icon: isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />,
      shortcut: 'Space',
      category: 'Simulation',
      onSelect: togglePause,
    },
    {
      id: 'reset-camera',
      label: 'Reset Camera',
      description: 'Reset zoom and pan to defaults',
      category: 'View',
      onSelect: camera.reset,
    },
    {
      id: 'toggle-grid',
      label: renderOptions.showGrid ? 'Hide Grid' : 'Show Grid',
      category: 'Rendering',
      onSelect: () => setRenderOption('showGrid', !renderOptions.showGrid),
    },
    {
      id: 'toggle-packs',
      label: renderOptions.showPacks ? 'Hide Packs' : 'Show Packs',
      category: 'Rendering',
      onSelect: () => setRenderOption('showPacks', !renderOptions.showPacks),
    },
    {
      id: 'toggle-energy',
      label: renderOptions.showEnergy ? 'Hide Energy' : 'Show Energy',
      category: 'Rendering',
      onSelect: () => setRenderOption('showEnergy', !renderOptions.showEnergy),
    },
  ];

  // Status bar items
  const statusItems: StatusItem[] = [
    {
      key: 'connection',
      label: 'Status',
      value: isConnected ? 'Connected' : 'Disconnected',
      color: isConnected ? 'text-gotham-success' : 'text-gotham-error',
    },
    {
      key: 'fps',
      label: 'FPS',
      value: 60,
      icon: <Activity className="w-3 h-3" />,
    },
    {
      key: 'tick',
      label: 'Tick',
      value: state.tickRate,
      icon: <Clock className="w-3 h-3" />,
    },
    {
      key: 'entities',
      label: 'Entities',
      value: state.entities.size,
      icon: <Database className="w-3 h-3" />,
    },
    {
      key: 'species',
      label: 'Species',
      value: state.species.size,
    },
    {
      key: 'packs',
      label: 'Packs',
      value: state.packs.size,
    },
  ];

  // Drawer tabs
  const drawerTabs: DrawerTab[] = [
    {
      id: 'species',
      label: 'Species',
      badge: state.species.size,
      content: (
        <div>
          <GothamDataGrid
            data={speciesData}
            columns={speciesColumns}
            onRowClick={(species) => setSelectedSpeciesId(
              selectedSpeciesId === species.id ? null : species.id
            )}
            selectedId={selectedSpeciesId || undefined}
            getId={(species) => species.id}
            emptyMessage="No species in simulation"
          />
        </div>
      ),
    },
    {
      id: 'statistics',
      label: 'Statistics',
      content: (
        <div className="space-y-6">
          <div className="grid grid-cols-4 gap-4">
            <MetricCard
              label="Avg Energy"
              value={stats.avgEnergy}
              subtitle={selectedSpeciesId ? 'Selected species' : 'All creatures'}
              icon={<Activity className="w-4 h-4" />}
            />
            <MetricCard
              label="Avg Health"
              value={stats.avgHealth}
              subtitle={selectedSpeciesId ? 'Selected species' : 'All creatures'}
              icon={<Activity className="w-4 h-4" />}
            />
            <MetricCard
              label="Children"
              value={stats.childCount}
              subtitle="Young creatures"
            />
            <MetricCard
              label="Packs"
              value={stats.packCount}
              subtitle="Active groups"
            />
          </div>
          <div className="gotham-panel p-4">
            <h4 className="text-sm font-semibold text-gotham-gray-100 uppercase tracking-wider mb-4">
              Population Over Time
            </h4>
            <GothamChart
              data={[]}
              type="line"
              dataKeys={[{ key: 'population', name: 'Population' }]}
              xAxisKey="tick"
              height={200}
            />
          </div>
        </div>
      ),
    },
    {
      id: 'controls',
      label: 'Controls',
      icon: <Settings className="w-4 h-4" />,
      content: (
        <div className="space-y-6">
          {/* Simulation Controls */}
          <div className="gotham-panel p-4">
            <h4 className="text-sm font-semibold text-gotham-gray-100 uppercase tracking-wider mb-4">
              Simulation
            </h4>
            <div className="flex items-center gap-4">
              <GothamButton
                variant={isPaused ? 'primary' : 'danger'}
                onClick={togglePause}
                disabled={!isConnected}
                icon={isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
              >
                {isPaused ? 'Resume' : 'Pause'}
              </GothamButton>

              {/* WebSocket Status */}
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gotham-gray-500">WebSocket:</span>
                <span className={`font-medium ${isConnected ? 'text-gotham-success' : 'text-gotham-error'}`}>
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>

          {/* Rendering Options */}
          <div className="gotham-panel p-4">
            <h4 className="text-sm font-semibold text-gotham-gray-100 uppercase tracking-wider mb-4">
              Rendering
            </h4>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(renderOptions).map(([key, value]) => {
                if (key === 'entityScale' || key === 'gridSize') return null;
                return (
                  <label key={key} className="flex items-center gap-2 text-sm text-gotham-gray-100 cursor-pointer hover:text-gotham-blueprint-400 transition-colors">
                    <input
                      type="checkbox"
                      checked={value as boolean}
                      onChange={(e) => setRenderOption(key as any, e.target.checked)}
                      className="w-4 h-4 bg-gotham-dark-500 border-gotham-gray-800 text-gotham-blueprint-400 focus:ring-gotham-blueprint-400 focus:ring-offset-gotham-dark-400"
                    />
                    <span>{key.replace(/([A-Z])/g, ' $1').replace(/^show/, '').trim()}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Camera Controls */}
          <div className="gotham-panel p-4">
            <h4 className="text-sm font-semibold text-gotham-gray-100 uppercase tracking-wider mb-4">
              Camera
            </h4>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gotham-gray-500 mb-2 block">Zoom: {camera.zoom.toFixed(2)}x</label>
                <input
                  type="range"
                  min="0.5"
                  max="3"
                  step="0.1"
                  value={camera.zoom}
                  onChange={(e) => camera.setZoom(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
              <GothamButton variant="secondary" size="sm" onClick={camera.reset}>
                Reset Camera
              </GothamButton>
            </div>
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="fixed inset-0 bg-gotham-dark-500 flex flex-col overflow-hidden">
      {/* Main Simulation Canvas */}
      <div className="flex-1 relative">
        <NewSimulationRenderer
          state={state}
          options={renderOptions}
          width={state.worldWidth}
          height={state.worldHeight}
          camera={camera}
        />

        {/* Floating HUD - Top Left */}
        <div className="absolute top-4 left-4 flex items-center gap-2 gotham-panel px-3 py-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-gotham-success' : 'bg-gotham-error'} animate-pulse`} />
          <span className="text-xs font-medium text-gotham-gray-100">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        {/* Floating HUD - Top Right */}
        <div className="absolute top-4 right-4 gotham-panel px-3 py-2">
          <div className="flex flex-col gap-1 text-xs font-mono">
            <div className="flex items-center justify-between gap-4">
              <span className="text-gotham-gray-500">Tick:</span>
              <span className="text-gotham-gray-100 font-semibold">{state.tickRate}</span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-gotham-gray-500">Entities:</span>
              <span className="text-gotham-gray-100 font-semibold">{state.entities.size}</span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-gotham-gray-500">Zoom:</span>
              <span className="text-gotham-gray-100 font-semibold">{camera.zoom.toFixed(2)}x</span>
            </div>
          </div>
        </div>

        {/* Hint */}
        <div className="absolute bottom-4 left-4 gotham-panel px-3 py-2">
          <div className="flex items-center gap-2 text-xs text-gotham-gray-500">
            <kbd className="px-1.5 py-0.5 bg-gotham-dark-300 border border-gotham-gray-800 rounded font-mono">⌘K</kbd>
            <span>Command Palette</span>
          </div>
        </div>
      </div>

      {/* Bottom Drawer */}
      <BottomDrawer
        tabs={drawerTabs}
        defaultTab={activeTab}
        onHeightChange={(height) => {}}
      />

      {/* Status Bar */}
      <StatusBar items={statusItems} />

      {/* Command Palette */}
      <CommandPalette
        isOpen={commandPalette.isOpen}
        onClose={commandPalette.close}
        commands={commands}
      />
    </div>
  );
}
