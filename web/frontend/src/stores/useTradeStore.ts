import { create } from 'zustand';

interface Trade {
  id: string;
  timestamp: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  price: number;
  quantity: number;
  account: string;
  status: string;
}

interface TradeState {
  trades: Trade[];
  stats: any;
  addTrade: (trade: Trade) => void;
  setTrades: (trades: Trade[]) => void;
  setStats: (stats: any) => void;
}

export const useTradeStore = create<TradeState>((set) => ({
  trades: [],
  stats: null,
  addTrade: (trade) =>
    set((state) => ({
      trades: [trade, ...state.trades].slice(0, 100), // 保留最近100条
    })),
  setTrades: (trades) => set({ trades }),
  setStats: (stats) => set({ stats }),
}));
