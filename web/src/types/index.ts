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

export interface Template {
  id: string;
  name: string;
  description: string;
  metrics: {
    expected_return: number;
    volatility: number;
    max_drawdown: number;
    sharpe_ratio: number;
  };
  allocation: {
    [key: string]: number;
  };
  personality_tags: string[];
}
