// src/config/env.ts
interface Config {
    wsUrl: string;
    environment: string;
}

const config: Config = {
    wsUrl: process.env.NODE_ENV === 'production' 
        ? 'wss://simulation.aaryareddy.com/ws/simulation'
        : (import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/simulation'),
    environment: import.meta.env.MODE || 'development'
};

export default config;