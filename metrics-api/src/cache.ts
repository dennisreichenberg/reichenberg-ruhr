import { RepoMetrics } from "./github";

const CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour

interface CacheEntry {
  data: RepoMetrics;
  expiresAt: number;
}

const store = new Map<string, CacheEntry>();

export function getCached(slug: string): RepoMetrics | null {
  const entry = store.get(slug);
  if (!entry) return null;
  if (Date.now() > entry.expiresAt) {
    store.delete(slug);
    return null;
  }
  return entry.data;
}

export function setCached(slug: string, data: RepoMetrics): void {
  store.set(slug, { data, expiresAt: Date.now() + CACHE_TTL_MS });
}

export function getAllCached(): RepoMetrics[] {
  const now = Date.now();
  const results: RepoMetrics[] = [];
  for (const [slug, entry] of store.entries()) {
    if (now <= entry.expiresAt) {
      results.push(entry.data);
    } else {
      store.delete(slug);
    }
  }
  return results;
}
