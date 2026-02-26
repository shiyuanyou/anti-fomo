import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Asset, PortfolioConfig } from '@/types';

// Storage strategy pattern
interface StorageStrategy {
  load(): Promise<PortfolioConfig | null>;
  save(config: PortfolioConfig): Promise<boolean>;
}

// Local mode strategy (reads/writes backend config.asset.yaml via API)
class LocalStorageStrategy implements StorageStrategy {
  async load(): Promise<PortfolioConfig | null> {
    try {
      const res = await fetch('/api/assets');
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.error('Failed to load local config via API', e);
    }
    return null;
  }

  async save(config: PortfolioConfig): Promise<boolean> {
    try {
      const res = await fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      return res.ok;
    } catch (e) {
      console.error('Failed to save local config via API', e);
      return false;
    }
  }
}

// Cloud mode strategy (reads/writes browser localStorage)
class CloudStorageStrategy implements StorageStrategy {
  private STORAGE_KEY = 'anti_fomo_portfolio';

  async load(): Promise<PortfolioConfig | null> {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      if (data) {
        return JSON.parse(data);
      }
    } catch (e) {
      console.error('Failed to load from localStorage', e);
    }
    return null;
  }

  async save(config: PortfolioConfig): Promise<boolean> {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(config));
      return true;
    } catch (e) {
      console.error('Failed to save to localStorage', e);
      return false;
    }
  }
}

// Default empty config
const DEFAULT_CONFIG: PortfolioConfig = {
  portfolio: {
    total_amount: 0,
    holdings: []
  }
};

export const useConfigStore = defineStore('config', () => {
  const assets = ref<Asset[]>([]);
  const totalAmount = computed(() => assets.value.reduce((sum, a) => sum + a.amount, 0));
  
  // Determine strategy based on Vite env variable
  const mode = import.meta.env.VITE_APP_MODE || 'local';
  const strategy: StorageStrategy = mode === 'cloud' 
    ? new CloudStorageStrategy() 
    : new LocalStorageStrategy();

  const isSaving = ref(false);
  const saveStatus = ref<'idle' | 'success' | 'error'>('idle');

  async function loadConfig() {
    const config = await strategy.load();
    if (config && config.portfolio && Array.isArray(config.portfolio.holdings)) {
      // Add local IDs to assets for v-for tracking
      assets.value = config.portfolio.holdings.map(a => ({
        ...a,
        id: a.id || crypto.randomUUID()
      }));
    } else {
      assets.value = [];
    }
  }

  async function saveConfig() {
    isSaving.value = true;
    saveStatus.value = 'idle';
    
    // Clean up IDs before saving
    const configToSave: PortfolioConfig = {
      portfolio: {
        total_amount: totalAmount.value,
        holdings: assets.value.map(({ id, ...rest }) => rest)
      }
    };

    const success = await strategy.save(configToSave);
    isSaving.value = false;
    saveStatus.value = success ? 'success' : 'error';
    
    // Reset status after a delay
    if (success) {
      setTimeout(() => {
        if (saveStatus.value === 'success') saveStatus.value = 'idle';
      }, 3000);
    }
    
    return success;
  }

  function addAsset(asset: Omit<Asset, 'id'>) {
    assets.value.push({
      ...asset,
      id: crypto.randomUUID()
    });
  }

  function removeAsset(id: string) {
    assets.value = assets.value.filter(a => a.id !== id);
  }

  function updateAsset(id: string, updatedAsset: Partial<Asset>) {
    const index = assets.value.findIndex(a => a.id === id);
    if (index !== -1) {
      assets.value[index] = { ...assets.value[index], ...updatedAsset };
    }
  }

  // Clear all assets (useful for "Copy this template" feature later)
  function setAssets(newAssets: Omit<Asset, 'id'>[]) {
    assets.value = newAssets.map(a => ({
      ...a,
      id: crypto.randomUUID()
    }));
  }

  return {
    mode,
    assets,
    totalAmount,
    isSaving,
    saveStatus,
    loadConfig,
    saveConfig,
    addAsset,
    removeAsset,
    updateAsset,
    setAssets
  };
});
