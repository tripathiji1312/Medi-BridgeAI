/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
    // e2e/ holds Playwright specs (run via `npm run e2e`, a separate test
    // runner with its own `test`/`describe` globals) -- without this
    // exclude, vitest's default include glob also picks them up and they
    // fail immediately since Playwright's test() isn't vitest's. Repeats
    // vitest's own default excludes since setting this option replaces
    // (not merges with) them.
    exclude: [
      "**/node_modules/**",
      "**/dist/**",
      "**/cypress/**",
      "**/.{idea,git,cache,output,temp}/**",
      "**/{karma,rollup,webpack,vite,vitest,jest,ava,babel,nyc,cypress,tsup,build}.config.*",
      "**/e2e/**",
    ],
  },
});
