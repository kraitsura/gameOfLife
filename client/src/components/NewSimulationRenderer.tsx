// client/src/components/NewSimulationRenderer.tsx
import React, { useRef, useEffect } from 'react';
import { SimulationState, RenderOptions, Entity } from '../types/new_simulation';
import { UseCameraResult } from '../hooks/useCamera';
import { gothamColors } from '../lib/gotham-theme';

interface NewSimulationRendererProps {
    state: SimulationState;
    options: RenderOptions;
    width: number;
    height: number;
    camera: UseCameraResult;
    onEntityClick?: (entityId: string) => void;
}

const NewSimulationRenderer: React.FC<NewSimulationRendererProps> = ({
    state,
    options,
    width,
    height,
    camera,
    onEntityClick,
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const requestIdRef = useRef<number>();
    const stateRef = useRef(state);
    const optionsRef = useRef(options);
    const cameraRef = useRef(camera);

    // Update refs when props change
    useEffect(() => {
        stateRef.current = state;
    }, [state]);

    useEffect(() => {
        optionsRef.current = options;
    }, [options]);

    useEffect(() => {
        cameraRef.current = camera;
    }, [camera]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d', { alpha: false });
        if (!ctx) return;

        let frameCount = 0;
        let lastTime = performance.now();
        const targetFPS = 60;
        const frameInterval = 1000 / targetFPS;

        const updateCanvasSize = () => {
            const container = canvas.parentElement;
            if (!container) return;

            const containerWidth = container.clientWidth;
            const containerHeight = container.clientHeight;
            const dpr = window.devicePixelRatio || 1;

            // Only update canvas size if it actually changed
            if (canvas.width !== containerWidth * dpr || canvas.height !== containerHeight * dpr) {
                canvas.width = containerWidth * dpr;
                canvas.height = containerHeight * dpr;
                canvas.style.width = `${containerWidth}px`;
                canvas.style.height = `${containerHeight}px`;

                // Calculate and store transform matrix with camera
                const currentCamera = cameraRef.current;
                const scaleX = containerWidth / width;
                const scaleY = containerHeight / height;
                const baseScale = Math.min(scaleX, scaleY);
                const scale = baseScale * currentCamera.zoom;
                const offsetX = (containerWidth - width * baseScale) / 2 + currentCamera.panX;
                const offsetY = (containerHeight - height * baseScale) / 2 + currentCamera.panY;

                ctx.setTransform(
                    scale * dpr,
                    0,
                    0,
                    scale * dpr,
                    offsetX * dpr,
                    offsetY * dpr
                );
            }
        };

        // Throttled resize observer
        let resizeTimeout: number;
        const resizeObserver = new ResizeObserver(() => {
            if (resizeTimeout) {
                window.cancelAnimationFrame(resizeTimeout);
            }
            resizeTimeout = window.requestAnimationFrame(updateCanvasSize);
        });

        if (canvas.parentElement) {
            resizeObserver.observe(canvas.parentElement);
        }

        updateCanvasSize();

        // Camera event handlers
        const handleWheel = (e: WheelEvent) => {
            camera.handleWheel(e);
            updateCanvasSize(); // Reapply transform after zoom
        };

        const handleMouseDown = (e: MouseEvent) => {
            camera.handleMouseDown(e);
        };

        canvas.addEventListener('wheel', handleWheel, { passive: false });
        canvas.addEventListener('mousedown', handleMouseDown);

        const render = (currentTime: number) => {
            if (!ctx || !canvas) return;

            // Implement frame rate control
            const elapsed = currentTime - lastTime;
            if (elapsed < frameInterval) {
                requestIdRef.current = requestAnimationFrame(render);
                return;
            }

            // Update time tracking
            lastTime = currentTime - (elapsed % frameInterval);
            frameCount++;

            // Clear canvas with solid black background
            ctx.fillStyle = '#000000';
            ctx.fillRect(0, 0, width, height);

            const currentState = stateRef.current;
            const currentOptions = optionsRef.current;

            // Draw grid if enabled (removed frame skipping to prevent flashing)
            if (currentOptions.showGrid) {
                drawGrid(ctx, width, height, currentOptions.gridSize);
            }

            // Batch similar drawing operations
            // First draw all plants
            for (const entity of currentState.entities.values()) {
                if (entity.speciesId === 'plant') {
                    drawPlant(ctx, entity, currentOptions);
                }
            }

            // Then draw all groups
            if (currentOptions.showPacks) {
                drawPacks(ctx, currentState);
            }

            // Finally draw all creatures
            for (const entity of currentState.entities.values()) {
                if (entity.speciesId !== 'plant') {
                    drawEntity(ctx, entity, currentOptions, currentState.worldWidth, currentState.worldHeight);
                }
            }

            // Continue render loop
            requestIdRef.current = requestAnimationFrame(render);
        };

        requestIdRef.current = requestAnimationFrame(render);

        return () => {
            resizeObserver.disconnect();
            canvas.removeEventListener('wheel', handleWheel);
            canvas.removeEventListener('mousedown', handleMouseDown);
            if (requestIdRef.current) {
                cancelAnimationFrame(requestIdRef.current);
            }
            if (resizeTimeout) {
                cancelAnimationFrame(resizeTimeout);
            }
        };
    }, []); // Empty dependency array since we're using refs

    return (
        <canvas
            ref={canvasRef}
            style={{
                width: '100%',
                height: '100%',
                display: 'block'
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
    // Blueprint-style grid with subtle glow
    ctx.beginPath();
    ctx.strokeStyle = gothamColors.gray[900];
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

    // Draw thicker lines every 5 grid units for major grid
    ctx.beginPath();
    ctx.strokeStyle = gothamColors.gray[800];
    ctx.lineWidth = 1.5;

    for (let x = 0; x <= width; x += gridSize * 5) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
    }

    for (let y = 0; y <= height; y += gridSize * 5) {
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
    }

    ctx.stroke();
};

const drawPacks = (
    ctx: CanvasRenderingContext2D,
    state: SimulationState
) => {
    for (const pack of state.packs.values()) {
        const members = Array.from(pack.memberIds)
            .map(id => state.entities.get(id))
            .filter((e): e is Entity => e !== undefined);

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

const drawEntity = (
    ctx: CanvasRenderingContext2D,
    entity: Entity,
    options: RenderOptions,
    worldWidth?: number,
    worldHeight?: number
) => {
    const { position, color, velocity } = entity;
    const radius = entity.size * options.entityScale;

    // Draw vision range if enabled
    if (options.showVision && entity.type === 'creature') {
        ctx.save();

        // Clip vision circle to world boundaries if near edges
        if (worldWidth !== undefined && worldHeight !== undefined) {
            ctx.beginPath();
            ctx.rect(0, 0, worldWidth, worldHeight);
            ctx.clip();
        }

        ctx.beginPath();
        ctx.strokeStyle = `${color}33`;
        ctx.arc(position.x, position.y, entity.visionRange, 0, Math.PI * 2);
        ctx.stroke();

        ctx.restore();
    }

    // Draw particle body
    ctx.beginPath();
    ctx.fillStyle = color;


    // Draw creatures as circles
    ctx.arc(position.x, position.y, radius, 0, Math.PI * 2);
    ctx.fill();

    // Draw direction indicator
    const angle = Math.atan2(velocity.y, velocity.x);
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


    // Draw energy and health indicators
    if (options.showEnergy && entity.type === 'creature') {
        const energyPercentage = entity.energy / 100;
        const healthPercentage = entity.health / 100;
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

        // Health indicator (red)
        ctx.beginPath();
        ctx.strokeStyle = `hsl(0, 100%, ${50 + healthPercentage * 50}%)`;
        ctx.lineWidth = 2;
        ctx.arc(
            position.x,
            position.y,
            energyRadius * 1.2,
            -Math.PI / 2,
            (healthPercentage * Math.PI * 2) - Math.PI / 2
        );
        ctx.stroke();
    }

    // Draw child indicator
    if (entity.isChild) {
        ctx.beginPath();
        ctx.strokeStyle = 'yellow';
        ctx.lineWidth = 1;
        ctx.arc(position.x, position.y, radius * 1.8, 0, Math.PI * 2);
        ctx.stroke();
    }

};

const drawPlant = (
    ctx: CanvasRenderingContext2D,
    plant: Entity,
    options: RenderOptions
) => {
    const { position, color } = plant;
    const radius = plant.size * options.entityScale;

    // Draw plant body
    ctx.beginPath();
    ctx.fillStyle = color;

    // Draw plants as squares with slightly rounded corners
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
        const energyPercentage = plant.energy / 100;
        ctx.fillStyle = `rgba(255, 255, 255, ${energyPercentage * 0.3})`;
        ctx.fill();
    }
};

export default NewSimulationRenderer;