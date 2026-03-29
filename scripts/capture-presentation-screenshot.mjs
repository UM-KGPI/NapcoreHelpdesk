import { chromium } from 'playwright';

const [, , token, outputPath] = process.argv;

if (!token || !outputPath) {
  console.error('Usage: node scripts/capture-presentation-screenshot.mjs <jwt-token> <output-path>');
  process.exit(1);
}

const pageUrl = 'http://127.0.0.1:5173';

const browser = await chromium.launch({ headless: true });

try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1400 }, deviceScaleFactor: 1.5 });
  await page.goto(pageUrl, { waitUntil: 'networkidle' });

  await page.getByLabel('JWT Bearer Token').fill(token);

  const messageField = page.getByLabel('Message');
  await messageField.fill('How should a NeTEx timetable exchange be validated before publication?');
  await page.getByRole('button', { name: 'Send' }).click();

  await page.locator('.chat-assistant').waitFor({ state: 'visible', timeout: 30000 });
  await page.locator('.chat-assistant .muted.tiny').waitFor({ state: 'visible', timeout: 30000 });

  const chatPanel = page.locator('.chat-panel');
  await chatPanel.scrollIntoViewIfNeeded();
  await chatPanel.screenshot({ path: outputPath });
} finally {
  await browser.close();
}