const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export interface ApiError extends Error {
  status?: number;
}

export async function getRankings(year: number, limit = 20) {
  const url = `${API_BASE}/rankings/${year}?limit=${limit}`;
  const res = await fetch(url);

  if (!res.ok) {
    const err: ApiError = new Error(`Failed to fetch rankings (${res.status})`);
    err.status = res.status;
    throw err;
  }

  return res.json();
}

export async function getCompanyDetail(ticker: string) {
  const res = await fetch(`${API_BASE}/companies/${ticker}`);
  if (!res.ok) {
    const err: ApiError = new Error(`Failed to fetch company (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function fetchAndSaveCompany(ticker: string) {
  const res = await fetch(`${API_BASE}/companies/${ticker}/fetch`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err: ApiError = new Error(`Failed to fetch/save company (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function getPriceHistory(ticker: string, limit?: number) {
  const url = `${API_BASE}/companies/${ticker}/prices${limit ? `?limit=${limit}` : ''}`;
  const res = await fetch(url);
  if (!res.ok) {
    const err: ApiError = new Error(`Failed to fetch price history (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function analyzeMatchup(tickers: string[], query?: string) {
  const res = await fetch(`${API_BASE}/analyze/matchup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tickers, query }),
  });
  if (!res.ok) {
    const err: ApiError = new Error(`Failed to analyze matchup (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function getMarketTrends() {
  const res = await fetch(`${API_BASE}/analyze/market/trends`);
  if (!res.ok) {
    const err: ApiError = new Error(`Failed to fetch market trends (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function getRankingMovers() {
  const res = await fetch(`${API_BASE}/rankings/movers/latest`);
  if (!res.ok) {
    const err: ApiError = new Error(`Failed to fetch ranking movers (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

