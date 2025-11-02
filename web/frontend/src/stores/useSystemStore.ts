import { create } from 'zustand';

interface SystemState {
  status: 'running' | 'stopped' | 'error' | 'unknown';
  uptime: number;
  lastUpdate: string;
  config: any;
  setStatus: (status: SystemState['status']) => void;
  setUptime: (uptime: number) => void;
  setLastUpdate: (lastUpdate: string) => void;
  setConfig: (config: any) => void;
}

export const useSystemStore = create<SystemState>((set) => ({
  status: 'unknown',
  uptime: 0,
  lastUpdate: '',
  config: null,
  setStatus: (status) => set({ status }),
  setUptime: (uptime) => set({ uptime }),
  setLastUpdate: (lastUpdate) => set({ lastUpdate }),
  setConfig: (config) => set({ config }),
}));
