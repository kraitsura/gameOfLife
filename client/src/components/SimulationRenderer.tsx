// client/src/components/SimulationRenderer.tsx
import React, { useRef, useEffect } from 'react';
import { SimulationState, RenderOptions, Particle } from '../types/simulation';

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

  // Setup canvas and start render loop
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

      // Draw particles
      for (const particle of state.particles.values()) {
        drawParticle(ctx, particle, options);
      }

      // Continue render loop
      requestIdRef.current = requestAnimationFrame(render);
    };

    render();

    // Cleanup
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

// Helper functions for drawing
const drawGrid = (
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  gridSize: number
) => {
  ctx.beginPath();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
  ctx.lineWidth = 1;

  // Vertical lines
  for (let x = 0; x <= width; x += gridSize) {
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
  }

  // Horizontal lines
  for (let y = 0; y <= height; y += gridSize) {
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
  }

  ctx.stroke();
};

const drawParticle = (
  ctx: CanvasRenderingContext2D,
  particle: Particle,
  options: RenderOptions
) => {
  const { position, attributes, color } = particle;
  const radius = attributes.size * options.particleScale;

  // Draw vision range if enabled
  if (options.showVision) {
    ctx.beginPath();
    ctx.strokeStyle = `${color}33`; // 20% opacity
    ctx.arc(position.x, position.y, particle.rules.visionRange, 0, Math.PI * 2);
    ctx.stroke();
  }

  // Draw particle body
  ctx.beginPath();
  ctx.fillStyle = color;
  ctx.arc(position.x, position.y, radius, 0, Math.PI * 2);
  ctx.fill();

  // Draw energy indicator if enabled
  if (options.showEnergy) {
    const energyPercentage = attributes.energy / 100;
    const energyRadius = radius * 1.5;
    
    ctx.beginPath();
    ctx.strokeStyle = `hsl(${energyPercentage * 120}, 100%, 50%)`;
    ctx.lineWidth = 2;
    ctx.arc(
      position.x,
      position.y,
      energyRadius,
      -Math.PI / 2,
      (energyPercentage * Math.PI * 2) - Math.PI / 2
    );
    ctx.stroke();
  }

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
};

export default SimulationRenderer;