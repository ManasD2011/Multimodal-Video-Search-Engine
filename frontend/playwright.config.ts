import { defineConfig, devices } from "@playwright/test";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const repositoryRoot = fileURLToPath(new URL("..", import.meta.url));

export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: "http://127.0.0.1:5173",
    ...devices["Desktop Chrome"],
  },
  webServer: [
    {
      command: `"${join(repositoryRoot, ".venv", "Scripts", "python.exe")}" -m uvicorn vidsearch.api.main:create_app --factory --app-dir "${join(repositoryRoot, "src")}" --host 127.0.0.1 --port 8001`,
      cwd: repositoryRoot,
      url: "http://127.0.0.1:8001/healthz",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        VIDSEARCH_DATA_DIR: join(repositoryRoot, "frontend", ".test-data"),
      },
    },
    {
      command: "npm run dev -- --host 127.0.0.1",
      cwd: fileURLToPath(new URL(".", import.meta.url)),
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        VIDSEARCH_API_PROXY: "http://127.0.0.1:8001",
      },
    },
  ],
});
