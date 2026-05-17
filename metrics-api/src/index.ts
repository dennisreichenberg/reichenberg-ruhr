import express from "express";
import { fetchRepoMetrics, RepoMetrics } from "./github";
import { getCached, setCached, getAllCached } from "./cache";
import { TOOLS, GITHUB_OWNER } from "./tools";

const app = express();
const PORT = parseInt(process.env.PORT ?? "3001", 10);

async function getMetricsForTool(slug: string, repo: string): Promise<RepoMetrics> {
  const cached = getCached(slug);
  if (cached) return cached;

  const metrics = await fetchRepoMetrics(GITHUB_OWNER, repo, slug);
  setCached(slug, metrics);
  return metrics;
}

// GET /api/tools/metrics - all 14 tools aggregated
app.get("/api/tools/metrics", async (_req, res) => {
  try {
    const cachedAll = getAllCached();
    const cachedSlugs = new Set(cachedAll.map((m) => m.slug));

    const missing = TOOLS.filter((t) => !cachedSlugs.has(t.slug));

    // Fetch missing in parallel
    const fetched = await Promise.allSettled(
      missing.map((t) => getMetricsForTool(t.slug, t.repo))
    );

    const results: RepoMetrics[] = [...cachedAll];
    for (const r of fetched) {
      if (r.status === "fulfilled") results.push(r.value);
    }

    // Sort to original TOOLS order
    const order = TOOLS.map((t) => t.slug);
    results.sort((a, b) => order.indexOf(a.slug) - order.indexOf(b.slug));

    res.json({ owner: GITHUB_OWNER, count: results.length, tools: results });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to fetch metrics" });
  }
});

// GET /api/tools/:slug/metrics - single tool detail
app.get("/api/tools/:slug/metrics", async (req, res) => {
  const tool = TOOLS.find((t) => t.slug === req.params.slug);
  if (!tool) {
    res.status(404).json({ error: "Tool not found", availableSlugs: TOOLS.map((t) => t.slug) });
    return;
  }
  try {
    const metrics = await getMetricsForTool(tool.slug, tool.repo);
    res.json(metrics);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to fetch metrics for tool" });
  }
});

// Health check
app.get("/health", (_req, res) => {
  res.json({ status: "ok", tools: TOOLS.length });
});

app.listen(PORT, () => {
  console.log(`Metrics API running on http://localhost:${PORT}`);
  console.log(`GET http://localhost:${PORT}/api/tools/metrics`);
  if (!process.env.GITHUB_TOKEN) {
    console.warn("Warning: GITHUB_TOKEN not set -- traffic data will be unavailable and rate limits are lower");
  }
});
