export interface Asset {
  id?: string;
  name: string;
  code: string;
  amount: number;
  type: string;
  region: string;
  style: string;
}

export interface PortfolioConfig {
  portfolio: {
    total_amount: number;
    holdings: Asset[];
  }
}

export interface AllocationItem {
  category: string;
  region: string;
  weight: number;  // decimal, e.g. 0.2 for 20%
}

export interface TemplateMetrics {
  expected_return: number;
  volatility: number;
  max_drawdown: number;
  sharpe_ratio: number;
  data_period: string;
}

export interface Template {
  id: string;
  name: string;
  tagline: string;
  description: string;
  target_audience: string;
  risk_level: string;  // "低" | "中" | "中高" | "高"
  allocations: AllocationItem[];
  allocation: Record<string, number> | null;  // simple dict e.g. {"A股大盘": 20}
  metrics: TemplateMetrics;
  personality_tags: string[];
  original_data?: {
    personality_description?: string;
    [key: string]: unknown;
  } | null;
}
