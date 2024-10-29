import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Species, Diet, ReproductionStyle } from '../types/simulation';

interface AddSpeciesDialogProps {
  onAddSpecies: (
    name: string,
    color: string,
    diet: Diet,
    reproductionStyle: ReproductionStyle,
    initialCount: number
  ) => void;
}

export function AddSpeciesDialog({ onAddSpecies }: AddSpeciesDialogProps) {
  const [open, setOpen] = useState(false);
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
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded-full transition-colors">
          Add New Species
        </button>
      </DialogTrigger>
      <DialogContent className="bg-gray-900 text-white">
        <DialogHeader>
          <DialogTitle>Add New Species</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            value={newSpecies.name}
            onChange={e => setNewSpecies(prev => ({ ...prev, name: e.target.value }))}
            placeholder="Species Name"
            className="w-full px-3 py-2 rounded bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />

          <div className="flex gap-2">
            <input
              type="color"
              value={newSpecies.color}
              onChange={e => setNewSpecies(prev => ({ ...prev, color: e.target.value }))}
              className="h-10 w-10 rounded bg-gray-800"
            />
            <select
              value={newSpecies.diet}
              onChange={e => setNewSpecies(prev => ({ ...prev, diet: e.target.value as Diet }))}
              className="flex-1 px-3 py-2 rounded bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="herbivore">Herbivore</option>
              <option value="carnivore">Carnivore</option>
              <option value="omnivore">Omnivore</option>
            </select>
          </div>

          <select
            value={newSpecies.reproductionStyle}
            onChange={e => setNewSpecies(prev => ({ 
              ...prev, 
              reproductionStyle: e.target.value as ReproductionStyle 
            }))}
            className="w-full px-3 py-2 rounded bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="self_replicating">Self Replicating</option>
            <option value="two_parents">Two Parents</option>
          </select>

          <input
            type="number"
            value={newSpecies.initialCount}
            onChange={e => setNewSpecies(prev => ({ 
              ...prev, 
              initialCount: Math.max(1, parseInt(e.target.value) || 1)
            }))}
            className="w-full px-3 py-2 rounded bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="1"
            max="50"
            placeholder="Initial Population"
          />

          <button
            type="submit"
            className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded-full transition-colors"
          >
            Add Species
          </button>
        </form>
      </DialogContent>
    </Dialog>
  );
}