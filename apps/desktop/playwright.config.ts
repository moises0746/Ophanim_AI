import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  outputDir: './test-results',
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:4173',
    channel: 'msedge',
    colorScheme: 'dark',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run dev -- --host 0.0.0.0 --port 4173 --strictPort',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: true,
    timeout: 30_000,
  },
  projects: [
    { name: 'desktop-1920x1080', use: { ...devices['Desktop Edge'], viewport: { width: 1920, height: 1080 } } },
    { name: 'desktop-1440x900', use: { ...devices['Desktop Edge'], viewport: { width: 1440, height: 900 } } },
    { name: 'desktop-1280x720', use: { ...devices['Desktop Edge'], viewport: { width: 1280, height: 720 } } },
    { name: 'narrow-tablet-820x1180', use: { ...devices['Desktop Edge'], viewport: { width: 820, height: 1180 } } },
  ],
});
