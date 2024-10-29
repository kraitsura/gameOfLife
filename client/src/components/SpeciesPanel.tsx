import { Diet, ReproductionStyle, Species } from '../types/simulation';
import { AddSpeciesDialog } from './AddSpeciesDialog';

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

export default function SpeciesPanel({
  species,
  onAddSpecies,
  selectedSpecies,
  onSelectSpecies
}: SpeciesPanelProps) {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Species</h2>
      
      {/* Species List */}
      <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
        {species.map(s => (
          <div
            key={s.id}
            className={`p-3 rounded-lg cursor-pointer transition-colors ${
              selectedSpecies === s.id ? 'bg-blue-900' : 'bg-gray-800 hover:bg-gray-700'
            }`}
            onClick={() => onSelectSpecies(selectedSpecies === s.id ? null : s.id)}
          >
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: s.color }}
              />
              <span className="font-medium">{s.name}</span>
            </div>
            <div className="text-sm text-gray-400 mt-1">
              Population: {s.population} | Diet: {s.diet} | Reproduction: {s.reproductionStyle.replace('_', ' ')}
            </div>
          </div>
        ))}
      </div>

      <AddSpeciesDialog onAddSpecies={onAddSpecies} />
    </div>
  );
}