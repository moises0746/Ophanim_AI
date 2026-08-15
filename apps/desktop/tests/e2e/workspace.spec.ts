import path from 'node:path';
import { expect, test } from '@playwright/test';

const screenshotRoot = path.resolve(process.cwd(), '../../docs/screenshots/UI-R1-T01');

test('renders the responsive Assistant shell and core route flow', async ({ page }, testInfo) => {
  const browserErrors: string[] = [];
  page.on('pageerror', (error) => browserErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') browserErrors.push(message.text());
  });

  await page.goto('/');
  await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible();
  await expect(page.getByRole('status')).toContainText(/ready/i);
  await expect(page.getByText(/no activity yet/i)).toBeVisible();

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflow).toBe(false);

  await page.screenshot({
    path: path.join(screenshotRoot, `${testInfo.project.name}.png`),
    fullPage: false,
    animations: 'disabled',
  });

  if (await page.getByRole('button', { name: /open navigation/i }).isVisible()) {
    await page.getByRole('button', { name: /open navigation/i }).click();
  }
  await page.getByRole('link', { name: /models & runtimes/i }).click();
  await expect(page.getByRole('heading', { name: /model routing/i })).toBeVisible();
  await expect(page.getByRole('heading', { name: /no models available/i })).toBeVisible();
  expect(browserErrors).toEqual([]);
});

test('preserves semantic state when reduced motion is requested', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  await expect(page.getByRole('status')).toHaveAttribute('data-assistant-state', 'idle');
  await expect(page.getByRole('status')).toHaveAccessibleName(/ophanim state: ready/i);
});
