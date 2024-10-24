// client/src/components/SpeciesPanel.tsx
import React, { useState } from 'react';
import { Species, Diet, ReproductionStyle } from '../types/simulation';

interface SpeciesPanelProps {
  species: Species[];
  onAddSpecies: (
    name: string,
    color: string,
    diet: Diet,
    reproductionStyle: ReproductionStyle,
    initialCount: number
  ) => void;
  selectedSpecies: string | null;
  onSelectSpecies: (id: string | null) => void;
}

const SpeciesPanel: React.FC<SpeciesPanelProps> = ({
  species,
  onAddSpecies,
  selectedSpecies,
  onSelectSpecies
}) => {
  const [newSpecies, setNewSpecies] = useState({
    name: '',
    color: '#' + Math.floor(Math.random()*16777215).toString(16),
    diet: 'omnivore' as Diet,
    reproductionStyle: 'two_parents' as ReproductionStyle,
    initialCount: 10
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAddSpecies(
      newSpecies.name,
      newSpecies.color,
      newSpecies.diet,
      newSpecies.reproductionStyle,
      newSpecies.initialCount
    );
    setNewSpecies({
      ...newSpecies,
      name: '',
      color: '#' + Math.floor(Math.random()*16777215).toString(16)
    });
  };

  return (
    <div className="text-white">
      <h2 className="text-xl font-bold mb-4">Species</h2>
      
      {/* Species List */}
      <div className="mb-4 space-y-2 max-h-48 overflow-y-auto">
        {species.map(s => (
          <div
            key={s.id}
            className={`p-2 rounded cursor-pointer hover:bg-gray-600 ${
              selectedSpecies === s.id ? 'bg-gray-600' : 'bg-gray-700'
            }`}
            onClick={() => onSelectSpecies(selectedSpecies === s.id ? null : s.id)}
          >
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded"
                style={{ backgroundColor: s.color }}
              />
              <span>{s.name}</span>
            </div>
            <div className="text-sm text-gray-300">
              Population: {s.population}
            </div>
            <div className="text-sm text-gray-300">
              Diet: {s.diet}
            </div>
            <div className="text-sm text-gray-300">
              Reproduction: {s.reproductionStyle.replace('_', ' ')}
            </div>
          </div>
        ))}
      </div>

      {/* Add New Species Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <h3 className="font-bold">Add New Species</h3>
        
        <div>
          <label className="block text-sm mb-1">Name:</label>
          <input
            type="text"
            value={newSpecies.name}
            onChange={e => setNewSpecies(prev => ({ ...prev, name: e.target.value }))}
            className="w-full px-2 py-1 rounded bg-gray-700"
            required
          />
        </div>

        <div>
          <label className="block text-sm mb-1">Color:</label>
          <input
            type="color"
            value={newSpecies.color}
            onChange={e => setNewSpecies(prev => ({ ...prev, color: e.target.value }))}
            className="w-full h-8 rounded bg-gray-700"
          />
        </div>

        <div>
          <label className="block text-sm mb-1">Diet:</label>
          <select
            value={newSpecies.diet}
            onChange={e => setNewSpecies(prev => ({ ...prev, diet: e.target.value as Diet }))}
            className="w-full px-2 py-1 rounded bg-gray-700"
          >
            <option value="herbivore">Herbivore</option>
            <option value="carnivore">Carnivore</option>
            <option value="omnivore">Omnivore</option>
          </select>
        </div>

        <div>
          <label className="block text-sm mb-1">Reproduction Style:</label>
          <select
            value={newSpecies.reproductionStyle}
            onChange={e => setNewSpecies(prev => ({ 
              ...prev, 
              reproductionStyle: e.target.value as ReproductionStyle 
            }))}
            className="w-full px-2 py-1 rounded bg-gray-700"
          >
            <option value="self_replicating">Self Replicating</option>
            <option value="two_parents">Two Parents</option>
          </select>
        </div>

        <div>
          <label className="block text-sm mb-1">Initial Count:</label>
          <input
            type="number"
            value={newSpecies.initialCount}
            onChange={e => setNewSpecies(prev => ({ 
              ...prev, 
              initialCount: Math.max(1, parseInt(e.target.value) || 1)
            }))}
            className="w-full px-2 py-1 rounded bg-gray-700"
            min="1"
            max="50"
          />
        </div>

        <button
          type="submit"
          className="w-full py-2 bg-blue-500 hover:bg-blue-600 rounded"
        >
          Add Species
        </button>
      </form>
    </div>
  );
};

export default SpeciesPanel;