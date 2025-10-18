import { useCallback, useEffect, useRef } from 'react';
import { useUIStore } from '../store/uiStore';

export interface UseCameraResult {
  zoom: number;
  panX: number;
  panY: number;
  setZoom: (zoom: number) => void;
  setPan: (x: number, y: number) => void;
  zoomIn: () => void;
  zoomOut: () => void;
  reset: () => void;
  handleWheel: (e: WheelEvent) => void;
  handleMouseDown: (e: MouseEvent) => void;
}

export function useCamera(
  minZoom: number = 0.5,
  maxZoom: number = 3.0,
  zoomStep: number = 0.1
): UseCameraResult {
  const { camera, setCamera, resetCamera } = useUIStore();
  const isDraggingRef = useRef(false);
  const lastMousePosRef = useRef({ x: 0, y: 0 });

  const setZoom = useCallback(
    (zoom: number) => {
      const clampedZoom = Math.max(minZoom, Math.min(maxZoom, zoom));
      setCamera({ zoom: clampedZoom });
    },
    [minZoom, maxZoom, setCamera]
  );

  const setPan = useCallback(
    (x: number, y: number) => {
      setCamera({ panX: x, panY: y });
    },
    [setCamera]
  );

  const zoomIn = useCallback(() => {
    setZoom(camera.zoom + zoomStep);
  }, [camera.zoom, zoomStep, setZoom]);

  const zoomOut = useCallback(() => {
    setZoom(camera.zoom - zoomStep);
  }, [camera.zoom, zoomStep, setZoom]);

  const reset = useCallback(() => {
    resetCamera();
  }, [resetCamera]);

  const handleWheel = useCallback(
    (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -zoomStep : zoomStep;
      setZoom(camera.zoom + delta);
    },
    [camera.zoom, zoomStep, setZoom]
  );

  const handleMouseDown = useCallback(
    (e: MouseEvent) => {
      // Only pan on middle mouse button or with space key
      if (e.button === 1 || e.button === 0) {
        e.preventDefault();
        isDraggingRef.current = true;
        lastMousePosRef.current = { x: e.clientX, y: e.clientY };

        const handleMouseMove = (moveEvent: MouseEvent) => {
          if (!isDraggingRef.current) return;

          const deltaX = moveEvent.clientX - lastMousePosRef.current.x;
          const deltaY = moveEvent.clientY - lastMousePosRef.current.y;

          setPan(camera.panX + deltaX, camera.panY + deltaY);

          lastMousePosRef.current = { x: moveEvent.clientX, y: moveEvent.clientY };
        };

        const handleMouseUp = () => {
          isDraggingRef.current = false;
          document.removeEventListener('mousemove', handleMouseMove);
          document.removeEventListener('mouseup', handleMouseUp);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
      }
    },
    [camera.panX, camera.panY, setPan]
  );

  return {
    zoom: camera.zoom,
    panX: camera.panX,
    panY: camera.panY,
    setZoom,
    setPan,
    zoomIn,
    zoomOut,
    reset,
    handleWheel,
    handleMouseDown,
  };
}
