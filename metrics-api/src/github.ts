const GITHUB_API = "https://api.github.com";
const TOKEN = process.env.GITHUB_TOKEN;

function headers(): Record<string, string> {
  const h: Record<string, string> = {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "reichenberg-metrics-api/1.0",
  };
  if (TOKEN) h["Authorization"] = `Bearer ${TOKEN}`;
  return h;
}

async function ghFetch(path: string): Promise<unknown> {
  const res = await fetch(`${GITHUB_API}${path}`, { headers: headers() });
  if (!res.ok) throw new Error(`GitHub API ${path} -> ${res.status}`);
  return res.json();
}

export interface RepoMetrics {
  slug: string;
  description: string | null;
  stars: number;
  forks: number;
  openIssues: number;
  watchers: number;
  lastCommitAt: string | null;
  defaultBranch: string;
  readmeLength: number | null;
  traffic: {
    views: { count: number; uniques: number } | null;
    clones: { count: number; uniques: number } | null;
  };
  fetchedAt: string;
}

export async function fetchRepoMetrics(owner: string, repo: string, slug: string): Promise<RepoMetrics> {
  const repoData = await ghFetch(`/repos/${owner}/${repo}`) as {
    description: string | null;
    stargazers_count: number;
    forks_count: number;
    open_issues_count: number;
    watchers_count: number;
    pushed_at: string | null;
    default_branch: string;
  };

  let readmeLength: number | null = null;
  try {
    const readme = await ghFetch(`/repos/${owner}/${repo}/readme`) as { size: number };
    readmeLength = readme.size;
  } catch {
    // README not found or inaccessible
  }

  let views: { count: number; uniques: number } | null = null;
  let clones: { count: number; uniques: number } | null = null;

  // Traffic requires push access (token with repo scope)
  if (TOKEN) {
    try {
      const v = await ghFetch(`/repos/${owner}/${repo}/traffic/views`) as { count: number; uniques: number };
      views = { count: v.count, uniques: v.uniques };
    } catch {
      // Insufficient scope or no data
    }
    try {
      const c = await ghFetch(`/repos/${owner}/${repo}/traffic/clones`) as { count: number; uniques: number };
      clones = { count: c.count, uniques: c.uniques };
    } catch {
      // Insufficient scope or no data
    }
  }

  return {
    slug,
    description: repoData.description,
    stars: repoData.stargazers_count,
    forks: repoData.forks_count,
    openIssues: repoData.open_issues_count,
    watchers: repoData.watchers_count,
    lastCommitAt: repoData.pushed_at,
    defaultBranch: repoData.default_branch,
    readmeLength,
    traffic: { views, clones },
    fetchedAt: new Date().toISOString(),
  };
}
