import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "fs";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";


function readRepoVersion(): string {
  const versionFilePath = resolve(dirname(fileURLToPath(import.meta.url)), "..", "VERSION");
  try {
    const value = readFileSync(versionFilePath, "utf-8").trim();
    return value || "0.1.0";
  } catch {
    return "0.1.0";
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const backendOrigin = env.VITE_BACKEND_ORIGIN ?? "http://localhost:8000";
  const repoVersion = readRepoVersion();

  return {
    plugins: [react()],
    define: {
      __APP_VERSION__: JSON.stringify(repoVersion),
    },
    server: {
      proxy: {
        "/api": {
          target: backendOrigin,
          changeOrigin: true,
        },
      },
    },
  };
});
