// client/src/components/SimulationRenderer.tsx
import React, { useRef, useEffect } from 'react';
import { SimulationState, RenderOptions, Particle, ParticleGroup } from '../types/simulation';

interface SimulationRendererProps {
  state: SimulationState;
  options: RenderOptions;
  width: number;
  height: number;
}

const SimulationRenderer: React.FC<SimulationRendererProps> = ({
  state,
  options,
  width,
  height
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const requestIdRef = useRef<number>();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas resolution
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);

    const render = () => {
      // Clear canvas
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, width, height);

      // Draw grid if enabled
      if (options.showGrid) {
        drawGrid(ctx, width, height, options.gridSize);
      }

      // First draw plants (background layer)
      for (const particle of state.particles.values()) {
        if (particle.rules.particleType === 'plant') {
          drawPlant(ctx, particle, options);
        }
      }

      // Draw particle groups if enabled
      if (options.showGroups) {
        drawGroups(ctx, state, options);
      }

      // Then draw creatures (foreground layer)
      for (const particle of state.particles.values()) {
        if (particle.rules.particleType === 'creature') {
          drawParticle(ctx, particle, state, options);
        }
      }

      // Continue render loop
      requestIdRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (requestIdRef.current) {
        cancelAnimationFrame(requestIdRef.current);
      }
    };
  }, [state, options, width, height]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        border: '1px solid #333',
        backgroundColor: '#000'
      }}
    />
  );
};

const drawGrid = (
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  gridSize: number
) => {
  ctx.beginPath();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
  ctx.lineWidth = 1;

  for (let x = 0; x <= width; x += gridSize) {
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
  }

  for (let y = 0; y <= height; y += gridSize) {
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
  }

  ctx.stroke();
};

const drawGroups = (
  ctx: CanvasRenderingContext2D,
  state: SimulationState,
  options: RenderOptions
) => {
  for (const group of state.groups.values()) {
    const members = Array.from(group.memberIds)
      .map(id => state.particles.get(id))
      .filter((p): p is Particle => p !== undefined);

    if (members.length < 2) continue;

    // Draw connections between group members
    ctx.beginPath();
    ctx.strokeStyle = `${members[0].color}66`;
    ctx.setLineDash([5, 5]);

    // Draw lines between all members
    for (let i = 0; i < members.length; i++) {
      for (let j = i + 1; j < members.length; j++) {
        ctx.moveTo(members[i].position.x, members[i].position.y);
        ctx.lineTo(members[j].position.x, members[j].position.y);
      }
    }

    ctx.stroke();
    ctx.setLineDash([]);
  }
};

const drawParticle = (
  ctx: CanvasRenderingContext2D,
  particle: Particle,
  state: SimulationState,
  options: RenderOptions
) => {
  const { position, attributes, color } = particle;
  const radius = attributes.size * options.particleScale;

  // Draw vision range if enabled
  if (options.showVision && particle.rules.particleType === 'creature') {
    ctx.beginPath();
    ctx.strokeStyle = `${color}33`;
    ctx.arc(position.x, position.y, particle.rules.visionRange, 0, Math.PI * 2);
    ctx.stroke();
  }

  // Draw particle body
  ctx.beginPath();
  ctx.fillStyle = color;

  if (particle.rules.particleType === 'plant') {
    // Draw plants as squares
    const size = radius * 2;
    ctx.fillRect(position.x - radius, position.y - radius, size, size);
  } else {
    // Draw creatures as circles
    ctx.arc(position.x, position.y, radius, 0, Math.PI * 2);
    ctx.fill();

    // Draw direction indicator
    const angle = Math.atan2(particle.velocity.y, particle.velocity.x);
    ctx.beginPath();
    ctx.moveTo(
      position.x + Math.cos(angle) * radius,
      position.y + Math.sin(angle) * radius
    );
    ctx.lineTo(
      position.x + Math.cos(angle) * radius * 1.5,
      position.y + Math.sin(angle) * radius * 1.5
    );
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  // Draw energy and hunger indicators
  if (options.showEnergy && particle.rules.particleType === 'creature') {
    const energyPercentage = attributes.energy / 100;
    const hungerPercentage = attributes.hunger / 100;
    const energyRadius = radius * 1.5;

    // Energy indicator (blue)
    ctx.beginPath();
    ctx.strokeStyle = `hsl(210, 100%, ${50 + energyPercentage * 50}%)`;
    ctx.lineWidth = 2;
    ctx.arc(
      position.x,
      position.y,
      energyRadius,
      -Math.PI / 2,
      (energyPercentage * Math.PI * 2) - Math.PI / 2
    );
    ctx.stroke();

    // Hunger indicator (red)
    ctx.beginPath();
    ctx.strokeStyle = `hsl(0, 100%, ${50 + hungerPercentage * 50}%)`;
    ctx.lineWidth = 2;
    ctx.arc(
      position.x,
      position.y,
      energyRadius * 1.2,
      -Math.PI / 2,
      (hungerPercentage * Math.PI * 2) - Math.PI / 2
    );
    ctx.stroke();
  }

  // Draw child indicator
  if (attributes.isChild) {
    ctx.beginPath();
    ctx.strokeStyle = 'yellow';
    ctx.lineWidth = 1;
    ctx.arc(position.x, position.y, radius * 1.8, 0, Math.PI * 2);
    ctx.stroke();
  }

  // Draw diet indicator
  if (options.showDiet && particle.rules.particleType === 'creature') {
    ctx.fillStyle = attributes.diet === 'herbivore' ? '#90EE90' :
      attributes.diet === 'carnivore' ? '#FF6B6B' :
        '#DDA0DD';  // omnivore
    ctx.beginPath();
    ctx.arc(position.x, position.y - radius * 1.5, radius * 0.3, 0, Math.PI * 2);
    ctx.fill();
  }
};

const drawPlant = (
  ctx: CanvasRenderingContext2D,
  plant: Particle,
  options: RenderOptions
) => {
  const { position, attributes, color } = plant;
  const radius = attributes.size * options.particleScale;

  // Draw plant body
  ctx.beginPath();
  ctx.fillStyle = color;

  // Draw plants as squares with slightly rounded corners
  const size = radius * 2;
  const cornerRadius = radius * 0.2;

  ctx.beginPath();
  ctx.moveTo(position.x - radius + cornerRadius, position.y - radius);
  ctx.lineTo(position.x + radius - cornerRadius, position.y - radius);
  ctx.quadraticCurveTo(position.x + radius, position.y - radius, position.x + radius, position.y - radius + cornerRadius);
  ctx.lineTo(position.x + radius, position.y + radius - cornerRadius);
  ctx.quadraticCurveTo(position.x + radius, position.y + radius, position.x + radius - cornerRadius, position.y + radius);
  ctx.lineTo(position.x - radius + cornerRadius, position.y + radius);
  ctx.quadraticCurveTo(position.x - radius, position.y + radius, position.x - radius, position.y + radius - cornerRadius);
  ctx.lineTo(position.x - radius, position.y - radius + cornerRadius);
  ctx.quadraticCurveTo(position.x - radius, position.y - radius, position.x - radius + cornerRadius, position.y - radius);
  ctx.closePath();
  ctx.fill();

  // Draw energy indicator if enabled
  if (options.showEnergy) {
    const energyPercentage = attributes.energy / 100;
    ctx.fillStyle = `rgba(255, 255, 255, ${energyPercentage * 0.3})`;
    ctx.fill();
  }
};

export default SimulationRenderer;