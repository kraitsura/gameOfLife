// client/src/components/StatisticsPanel.tsx
import React from 'react';
import { SimulationState } from '../types/simulation';

interface StatisticsPanelProps {
  state: SimulationState;
  selectedSpecies: string | null;
}

const StatisticsPanel: React.FC<StatisticsPanelProps> = ({ state, selectedSpecies }) => {
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
      avgHunger: count ? (totalHunger / count).toFixed(1) : '0',
      childCount,
      groupCount,
      groupPercentage: count ? ((groupCount / count) * 100).toFixed(1) : '0'
    };
  };

  const stats = calculateStats();

  return (
    <div className="text-white mt-6">
      <h2 className="text-xl font-bold mb-4">Statistics</h2>
      
      <div className="space-y-2">
        <div className="bg-gray-700 p-2 rounded">
          <div className="text-sm text-gray-300">Average Energy</div>
          <div className="text-lg">{stats.avgEnergy}</div>
        </div>
        
        <div className="bg-gray-700 p-2 rounded">
          <div className="text-sm text-gray-300">Average Hunger</div>
          <div className="text-lg">{stats.avgHunger}</div>
        </div>
        
        <div className="bg-gray-700 p-2 rounded">
          <div className="text-sm text-gray-300">Children</div>
          <div className="text-lg">{stats.childCount}</div>
        </div>
        
        <div className="bg-gray-700 p-2 rounded">
          <div className="text-sm text-gray-300">Groups</div>
          <div className="text-lg">
            {stats.groupCount} ({stats.groupPercentage}% in groups)
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatisticsPanel;