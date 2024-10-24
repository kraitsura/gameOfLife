// client/src/components/ParticleContextMenu.tsx
import React from 'react';
import { Particle } from '../types/simulation';

interface ParticleContextMenuProps {
  particle: Particle;
  x: number;
  y: number;
  onClose: () => void;
}

const ParticleContextMenu: React.FC<ParticleContextMenuProps> = ({
  particle,
  x,
  y,
  onClose
}) => {
  const formatStat = (value: number) => value.toFixed(1);

  return (
    <div
      className="fixed bg-gray-800 text-white p-4 rounded shadow-lg z-50"
      style={{
        left: x + 'px',
        top: y + 'px',
        maxWidth: '300px'
      }}
    >
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-2">
          <div
            className="w-4 h-4 rounded"
            style={{ backgroundColor: particle.color }}
          />
          <span className="font-bold">
            {particle.rules.particleType === 'plant' ? 'Plant' : 'Creature'}
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white"
        >
          ×
        </button>
      </div>

      <div className="space-y-2 text-sm">
        <div className="grid grid-cols-2 gap-1">
          <span className="text-gray-400">Energy:</span>
          <span>{formatStat(particle.attributes.energy)}</span>
          
          <span className="text-gray-400">Hunger:</span>
          <span>{formatStat(particle.attributes.hunger)}</span>
          
          <span className="text-gray-400">Age:</span>
          <span>{particle.attributes.age}</span>
          
          {particle.rules.particleType === 'creature' && (
            <>
              <span className="text-gray-400">Diet:</span>
              <span className="capitalize">{particle.attributes.diet}</span>
              
              <span className="text-gray-400">Reproduction:</span>
              <span className="capitalize">
                {particle.attributes.reproductionStyle.replace('_', ' ')}
              </span>
              
              <span className="text-gray-400">Pack Mentality:</span>
              <span>{formatStat(particle.attributes.packMentality)}</span>
              
              <span className="text-gray-400">Speed:</span>
              <span>
                {formatStat(Math.sqrt(
                  particle.velocity.x ** 2 + particle.velocity.y ** 2
                ))}
              </span>
              
              {particle.attributes.isChild && (
                <>
                  <span className="text-gray-400">Status:</span>
                  <span className="text-yellow-400">Child</span>
                </>
              )}
              
              {particle.attributes.groupId && (
                <>
                  <span className="text-gray-400">Group Time:</span>
                  <span>{particle.attributes.timeInGroup}</span>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ParticleContextMenu;