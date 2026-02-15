/**
 * PWA Screenshot Comment Generator
 *
 * Reads before/after screenshots, uploads them to the ci-screenshots branch
 * via the GitHub API, and generates a markdown PR comment comparing them.
 *
 * Environment variables:
 *   BEFORE_DIR       - Directory with base branch screenshots (default: screenshots-before)
 *   AFTER_DIR        - Directory with PR branch screenshots (default: screenshots-after)
 *   PR_NUMBER        - Pull request number (required)
 *   GITHUB_TOKEN     - GitHub token for API access (required)
 *   GITHUB_REPOSITORY - owner/repo (required)
 *   OUTPUT_FILE      - Output markdown file (default: pwa_screenshots_message.md)
 */

import { readFileSync, readdirSync, existsSync, writeFileSync } from "fs";
import { join } from "path";

const BEFORE_DIR = process.env.BEFORE_DIR || "screenshots-before";
const AFTER_DIR = process.env.AFTER_DIR || "screenshots-after";
const PR_NUMBER = process.env.PR_NUMBER;
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GITHUB_REPOSITORY = process.env.GITHUB_REPOSITORY;
const OUTPUT_FILE = process.env.OUTPUT_FILE || "pwa_screenshots_message.md";

const BRANCH_NAME = "ci-screenshots";
const API_BASE = "https://api.github.com";
const BOT_AUTHOR = {
  name: "github-actions[bot]",
  email: "github-actions[bot]@users.noreply.github.com",
};

function apiHeaders() {
  return {
    Accept: "application/vnd.github.v3+json",
    Authorization: `Bearer ${GITHUB_TOKEN}`,
  };
}

/** Ensure the ci-screenshots branch exists. */
async function ensureBranch() {
  const refUrl = `${API_BASE}/repos/${GITHUB_REPOSITORY}/git/ref/heads/${BRANCH_NAME}`;
  const res = await fetch(refUrl, { headers: apiHeaders() });
  if (res.ok) return;

  console.log(`Creating orphan branch "${BRANCH_NAME}"...`);
  // Get the default branch SHA to base the new branch on
  const repoRes = await fetch(`${API_BASE}/repos/${GITHUB_REPOSITORY}`, {
    headers: apiHeaders(),
  });
  const repoData = await repoRes.json();
  const defaultBranch = repoData.default_branch;

  const defaultRef = await fetch(
    `${API_BASE}/repos/${GITHUB_REPOSITORY}/git/ref/heads/${defaultBranch}`,
    { headers: apiHeaders() }
  );
  const defaultRefData = await defaultRef.json();

  await fetch(`${API_BASE}/repos/${GITHUB_REPOSITORY}/git/refs`, {
    method: "POST",
    headers: apiHeaders(),
    body: JSON.stringify({
      ref: `refs/heads/${BRANCH_NAME}`,
      sha: defaultRefData.object.sha,
    }),
  });
}

/** Upload a single image file to the ci-screenshots branch. Returns the raw URL or null. */
async function uploadImage(branchPath, localPath) {
  const content = readFileSync(localPath).toString("base64");
  const url = `${API_BASE}/repos/${GITHUB_REPOSITORY}/contents/${branchPath}`;

  // Try to create the file
  const res = await fetch(url, {
    method: "PUT",
    headers: apiHeaders(),
    body: JSON.stringify({
      message: `[CI] PWA screenshot for PR #${PR_NUMBER}`,
      content,
      branch: BRANCH_NAME,
      author: BOT_AUTHOR,
      committer: BOT_AUTHOR,
    }),
  });

  if (res.ok) {
    const rawUrl = `https://github.com/${GITHUB_REPOSITORY}/raw/${BRANCH_NAME}/${branchPath}`;
    console.log(`  Uploaded ${branchPath}`);
    return rawUrl;
  }

  // File might already exist — get its SHA and update
  if (res.status === 422) {
    const getRes = await fetch(`${url}?ref=${BRANCH_NAME}`, {
      headers: apiHeaders(),
    });
    if (getRes.ok) {
      const existing = await getRes.json();
      const updateRes = await fetch(url, {
        method: "PUT",
        headers: apiHeaders(),
        body: JSON.stringify({
          message: `[CI] PWA screenshot for PR #${PR_NUMBER}`,
          content,
          branch: BRANCH_NAME,
          sha: existing.sha,
          author: BOT_AUTHOR,
          committer: BOT_AUTHOR,
        }),
      });
      if (updateRes.ok) {
        const rawUrl = `https://github.com/${GITHUB_REPOSITORY}/raw/${BRANCH_NAME}/${branchPath}`;
        console.log(`  Updated ${branchPath}`);
        return rawUrl;
      }
    }
  }

  const body = await res.text();
  console.error(`  Failed to upload ${branchPath}: ${res.status} ${body}`);
  return null;
}

/** Human-readable name from a screenshot filename like "homepage.png" → "Homepage" */
function filenameToName(filename) {
  return filename
    .replace(/\.png$/, "")
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

async function main() {
  if (!PR_NUMBER || !GITHUB_TOKEN || !GITHUB_REPOSITORY) {
    console.error(
      "Required env vars: PR_NUMBER, GITHUB_TOKEN, GITHUB_REPOSITORY"
    );
    process.exit(1);
  }

  await ensureBranch();

  const hasBeforeDir = existsSync(BEFORE_DIR);
  const hasAfterDir = existsSync(AFTER_DIR);

  if (!hasAfterDir) {
    console.error(`After directory "${AFTER_DIR}" not found`);
    process.exit(1);
  }

  const afterFiles = readdirSync(AFTER_DIR).filter((f) => f.endsWith(".png"));
  const beforeFiles = hasBeforeDir
    ? readdirSync(BEFORE_DIR).filter((f) => f.endsWith(".png"))
    : [];

  const timestamp = Date.now();
  const rows = [];

  for (const filename of afterFiles) {
    const name = filenameToName(filename);
    const afterPath = join(AFTER_DIR, filename);
    const branchAfterPath = `pwa/pr-${PR_NUMBER}/${timestamp}/after/${filename}`;

    console.log(`Processing ${name}...`);
    const afterUrl = await uploadImage(branchAfterPath, afterPath);

    let beforeUrl = null;
    if (beforeFiles.includes(filename)) {
      const beforePath = join(BEFORE_DIR, filename);
      const branchBeforePath = `pwa/pr-${PR_NUMBER}/${timestamp}/before/${filename}`;
      beforeUrl = await uploadImage(branchBeforePath, beforePath);
    }

    rows.push({ name, beforeUrl, afterUrl });
  }

  // Generate markdown
  let message = "## PWA Screenshots\n\n";
  message +=
    "Visual comparison of PWA pages between the base branch and this PR.\n\n";

  for (const { name, beforeUrl, afterUrl } of rows) {
    if (!afterUrl) continue;

    message += `### ${name}\n\n`;

    if (beforeUrl) {
      message += "| Before | After |\n";
      message += "|--------|-------|\n";
      message += `| ![Before](${beforeUrl}) | ![After](${afterUrl}) |\n\n`;
    } else {
      message += `*New page (no base branch screenshot)*\n\n`;
      message += `![After](${afterUrl})\n\n`;
    }
  }

  writeFileSync(OUTPUT_FILE, message);
  console.log(`\nComment markdown written to ${OUTPUT_FILE}`);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
