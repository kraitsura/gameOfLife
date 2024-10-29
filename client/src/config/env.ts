// src/config/env.ts
interface Config {
    apiUrl: string;
    wsUrl: string;
    environment: string;
}

const config: Config = {
    apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
    environment: import.meta.env.MODE || 'development'
};

export default config;