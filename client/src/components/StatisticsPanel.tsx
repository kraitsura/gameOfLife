// client/src/components/StatisticsPanel.tsx
import { SimulationState } from '../types/simulation';

interface StatisticsPanelProps {
  state: SimulationState;
  selectedSpecies: string | null;
}

export default function StatisticsPanel({ state, selectedSpecies }: StatisticsPanelProps) {
  const calculateStats = () => {
    let totalEnergy = 0;
    let totalHunger = 0;
    let childCount = 0;
    let groupCount = 0;
    let particles = Array.from(state.particles.values());
    
    if (selectedSpecies) {
      particles = particles.filter(p => p.speciesId === selectedSpecies);
    }

    particles.forEach(p => {
      totalEnergy += p.attributes.energy;
      totalHunger += p.attributes.hunger;
      if (p.attributes.isChild) childCount++;
      if (p.attributes.groupId) groupCount++;
    });

    const count = particles.length;
    
    return {
      avgEnergy: count ? (totalEnergy / count).toFixed(1) : '0',
      avgHunger: count ? (totalHunger / 

 count).toFixed(1) : '0',
      childCount,
      groupCount,
      groupPercentage: count ? ((groupCount / count) * 100).toFixed(1) : '0'
    };
  };

  const stats = calculateStats();

  return (
    <div className="mt-8">
      <h2 className="text-xl font-bold mb-4">Statistics</h2>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="text-sm text-gray-400">Average Energy</div>
          <div className="text-2xl font-bold">{stats.avgEnergy}</div>
        </div>
        
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="text-sm text-gray-400">Average Hunger</div>
          <div className="text-2xl font-bold">{stats.avgHunger}</div>
        </div>
        
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="text-sm text-gray-400">Children</div>
          <div className="text-2xl font-bold">{stats.childCount}</div>
        </div>
        
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="text-sm text-gray-400">Groups</div>
          <div className="text-2xl font-bold">
            {stats.groupCount} <span className="text-sm font-normal">({stats.groupPercentage}%)</span>
          </div>
        </div>
      </div>
    </div>
  );
}