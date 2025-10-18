import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface CameraState {
  zoom: number;
  panX: number;
  panY: number;
}

export interface UIState {
  // Drawer state
  drawerHeight: number;
  drawerCollapsed: boolean;
  activeTab: string;

  // Camera state
  camera: CameraState;

  // Command palette
  commandPaletteOpen: boolean;

  // Selected entities/species
  selectedEntityId: string | null;
  selectedSpeciesId: string | null;

  // Render options (persisted preferences)
  renderOptions: {
    showGrid: boolean;
    showVision: boolean;
    showEnergy: boolean;
    showPacks: boolean;
    showHealth: boolean;
    entityScale: number;
    gridSize: number;
  };

  // Actions
  setDrawerHeight: (height: number) => void;
  setDrawerCollapsed: (collapsed: boolean) => void;
  setActiveTab: (tab: string) => void;
  setCamera: (camera: Partial<CameraState>) => void;
  resetCamera: () => void;
  setCommandPaletteOpen: (open: boolean) => void;
  setSelectedEntityId: (id: string | null) => void;
  setSelectedSpeciesId: (id: string | null) => void;
  setRenderOption: <K extends keyof UIState['renderOptions']>(
    key: K,
    value: UIState['renderOptions'][K]
  ) => void;
  setRenderOptions: (options: Partial<UIState['renderOptions']>) => void;
}

const DEFAULT_CAMERA: CameraState = {
  zoom: 1,
  panX: 0,
  panY: 0,
};

const DEFAULT_RENDER_OPTIONS: UIState['renderOptions'] = {
  showGrid: true,
  showVision: false,
  showEnergy: true,
  showPacks: true,
  showHealth: true,
  entityScale: 1,
  gridSize: 20,
};

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // Initial state
      drawerHeight: 300,
      drawerCollapsed: false,
      activeTab: 'species',
      camera: DEFAULT_CAMERA,
      commandPaletteOpen: false,
      selectedEntityId: null,
      selectedSpeciesId: null,
      renderOptions: DEFAULT_RENDER_OPTIONS,

      // Actions
      setDrawerHeight: (height) => set({ drawerHeight: height }),
      setDrawerCollapsed: (collapsed) => set({ drawerCollapsed: collapsed }),
      setActiveTab: (tab) => set({ activeTab: tab }),
      setCamera: (camera) =>
        set((state) => ({
          camera: { ...state.camera, ...camera },
        })),
      resetCamera: () => set({ camera: DEFAULT_CAMERA }),
      setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
      setSelectedEntityId: (id) => set({ selectedEntityId: id }),
      setSelectedSpeciesId: (id) => set({ selectedSpeciesId: id }),
      setRenderOption: (key, value) =>
        set((state) => ({
          renderOptions: { ...state.renderOptions, [key]: value },
        })),
      setRenderOptions: (options) =>
        set((state) => ({
          renderOptions: { ...state.renderOptions, ...options },
        })),
    }),
    {
      name: 'gotham-ui-store',
      partialize: (state) => ({
        drawerHeight: state.drawerHeight,
        activeTab: state.activeTab,
        renderOptions: state.renderOptions,
      }),
    }
  )
);
