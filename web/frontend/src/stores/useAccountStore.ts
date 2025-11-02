import { create } from 'zustand';

interface Account {
  name: string;
  type: 'master' | 'follower';
  enabled: boolean;
  balance: number;
  positions: any[];
  leverage: number;
}

interface AccountState {
  accounts: Account[];
  setAccounts: (accounts: Account[]) => void;
  updateAccount: (name: string, updates: Partial<Account>) => void;
}

export const useAccountStore = create<AccountState>((set) => ({
  accounts: [],
  setAccounts: (accounts) => set({ accounts }),
  updateAccount: (name, updates) =>
    set((state) => ({
      accounts: state.accounts.map((acc) =>
        acc.name === name ? { ...acc, ...updates } : acc
      ),
    })),
}));
