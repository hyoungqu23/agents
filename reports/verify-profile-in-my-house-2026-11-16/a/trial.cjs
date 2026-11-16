const { chromium, expect } = require('@playwright/test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const output = name => path.join(__dirname, name);
const report = { game: '불 꺼진 집', passed: false, completed: [] };
const hostName = '시험 호스트';
const guestName = '초대 손님';
let stage = 'environment';
let browser;
let host;
let safeCapture;

async function join(page, nickname) {
  await page.getByLabel('닉네임', { exact: true }).fill(nickname);
  await page.getByRole('button', { name: '이 이름으로 들어가기' }).click();
  await expect(page.locator('.players-list').getByText(nickname, { exact: true })).toBeVisible();
}

async function main() {
  fs.rmSync(output('trial.png'), { force: true });
  const base = new URL(process.env.BASE_URL);
  assert(['localhost', '127.0.0.1', '[::1]'].includes(base.hostname));
  assert(['http:', 'https:'].includes(base.protocol) && !base.username && !base.password);
  assert.equal(process.env.GAME_STORE || 'memory', 'memory');
  browser = await chromium.launch();
  report.chromium = browser.version();

  async function newPage() {
    const context = await browser.newContext({ serviceWorkers: 'block', viewport: { width: 1280, height: 900 } });
    await context.route('**/*', route => new URL(route.request().url()).origin === base.origin
      ? route.continue() : route.abort());
    await context.routeWebSocket('**/*', socket => {
      const url = new URL(socket.url());
      if (url.host === base.host) socket.connectToServer();
      else socket.close();
    });
    context.setDefaultTimeout(30000);
    return context.newPage();
  }

  stage = 'select and create';
  host = await newPage();
  await host.goto(base.origin);
  const heading = host.getByRole('heading', { name: report.game, exact: true });
  await expect(heading).toBeVisible();
  safeCapture = heading;
  const card = host.getByRole('article').filter({ has: heading });
  await card.getByRole('button', { name: '불을 끄고 시작하기' }).click();
  stage = 'host joins lobby';
  await join(host, hostName);
  const roster = host.locator('.players-list');
  safeCapture = roster;
  await expect(roster.locator('strong')).toHaveCount(1);
  const code = await host.locator('.lobby-code-block strong').innerText();
  const roomPath = new URL(host.url()).pathname;
  assert.equal(roomPath, '/room/' + code);
  report.completed.push('Host alone in created room');

  stage = 'copy visible invite';
  await host.context().grantPermissions(['clipboard-read', 'clipboard-write'], { origin: base.origin });
  await host.getByRole('button', { name: '초대 링크 복사' }).click();
  const manual = host.getByRole('textbox', { name: '직접 복사할 초대 링크' });
  await expect(host.getByRole('button', { name: '복사했습니다' }).or(manual)).toBeVisible();
  const invite = new URL(await (await manual.isVisible() ? manual.inputValue() :
    host.evaluate(() => navigator.clipboard.readText())));
  assert(invite.origin === base.origin && !invite.username && !invite.password &&
    invite.pathname === roomPath + '/join' && invite.hash.length > 1);
  report.completed.push('Visible invite for host room obtained');

  stage = 'guest joins through invite';
  const guest = await newPage();
  await guest.goto(invite.href);
  await join(guest, guestName);
  assert.equal(new URL(guest.url()).pathname, roomPath);
  await expect(guest.locator('.lobby-code-block strong')).toHaveText(code);
  await expect(guest.locator('.players-list strong')).toHaveText([hostName, guestName]);
  report.completed.push('Independent guest sees both names in same room');

  stage = 'host observes guest';
  await expect(roster.locator('strong')).toHaveText([hostName, guestName], { timeout: 30000 });
  await expect(roster.getByText(guestName, { exact: true })).toBeVisible();
  report.hostRoster = [hostName, guestName];
  stage = 'capture host roster';
  await roster.screenshot({ path: output('trial.png'), animations: 'disabled' });
  report.completed.push('Host sees guest in live roster');
  report.passed = true;
}

main().catch(async () => {
  process.exitCode = 1;
  report.failedStage = stage;
  if (safeCapture && await safeCapture.isVisible().catch(() => false)) {
    await safeCapture.screenshot({ path: output('trial.png'), timeout: 3000 }).catch(() => {});
  }
}).finally(async () => {
  report.screenshot = fs.existsSync(output('trial.png')) ? 'trial.png' : null;
  fs.writeFileSync(output('trial-result.json'), JSON.stringify(report, null, 2) + '\n');
  await browser?.close();
});
