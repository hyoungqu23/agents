const fs = require('node:fs')
const path = require('node:path')
const assert = require('node:assert/strict')
const { chromium } = require('@playwright/test')

const resultFile = path.join(__dirname, 'trial-result.json')
const imageFile = path.join(__dirname, 'trial.png')
const hostName = '시험 호스트'
const guestName = '초대 손님'
const result = { game: '불 꺼진 집', status: 'running', stage: 'setup', screenshot: null }

function checkpoint(stage) {
  result.stage = stage
  fs.writeFileSync(resultFile, JSON.stringify(result, null, 2) + '\n')
}

async function capture(locator, description) {
  const png = await locator.screenshot({ animations: 'disabled' })
  fs.writeFileSync(imageFile, png)
  result.screenshot = { subject: description, width: png.readUInt32BE(16), height: png.readUInt32BE(20) }
}

async function join(page, nickname) {
  await page.getByLabel('닉네임', { exact: true }).fill(nickname)
  await page.getByRole('button', { name: '이 이름으로 들어가기', exact: true }).click()
  await player(page, nickname).waitFor()
  const code = page.locator('.lobby-code-block strong')
  await code.waitFor()
  const value = (await code.innerText()).trim()
  assert.match(value, /^[A-Z0-9]{6}$/)
  return value
}

function player(page, nickname) {
  return page.locator('.players-list').getByText(nickname, { exact: true })
}

async function main() {
  let browser
  try {
    fs.rmSync(imageFile, { force: true })
    checkpoint('validate local target')
    const base = new URL(process.env.BASE_URL)
    assert.ok(['localhost', '127.0.0.1'].includes(base.hostname))
    assert.ok(base.protocol === 'http:' && !base.username && !base.password)
    assert.ok(!process.env.GAME_STORE || process.env.GAME_STORE === 'memory')
    browser = await chromium.launch()
    result.browser = browser.version()
    async function freshContext() {
      const ctx = await browser.newContext({ serviceWorkers: 'block', viewport: { width: 1280, height: 900 } })
      ctx.setDefaultTimeout(45000)
      await ctx.route('**/*', route => new URL(route.request().url()).origin === base.origin
        ? route.continue() : route.abort())
      await ctx.routeWebSocket('**/*', socket => {
        const url = new URL(socket.url())
        if (url.protocol === 'ws:' && url.host === base.host) socket.connectToServer()
        else socket.close()
      })
      return ctx
    }
    const hostContext = await freshContext()
    await hostContext.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: base.origin })
    const host = await hostContext.newPage()
    checkpoint('select game and create room')
    await host.goto(base.origin, { waitUntil: 'domcontentloaded' })
    const card = host.locator('article').filter({ has: host.getByRole('heading', { name: result.game, exact: true }) })
    const start = card.getByRole('button', { name: '불을 끄고 시작하기', exact: true })
    await capture(start, 'game creation button')
    await start.click()
    checkpoint('join as host')
    result.hostRoomCode = await join(host, hostName)
    const roster = host.locator('.players-list')
    await capture(roster, 'host roster before invitation')
    checkpoint('copy invite through host panel')
    const panel = host.locator('aside').filter({ has: host.getByRole('heading', { name: '친구 초대' }) })
    await panel.getByRole('button', { name: '초대 링크 복사' }).click()
    const manual = panel.getByLabel('직접 복사할 초대 링크')
    const copied = panel.getByRole('button', { name: '복사했습니다' })
    await copied.or(manual).waitFor()
    const fallback = await manual.isVisible()
    const invite = new URL(fallback ? await manual.inputValue() : await host.evaluate(() => navigator.clipboard.readText()))
    assert.ok(invite.origin === base.origin && !invite.username && !invite.password)
    result.inviteSource = fallback ? 'visible manual copy field' : 'clipboard'
    checkpoint('join through invite in fresh guest context')
    const guest = await (await freshContext()).newPage()
    await guest.goto(invite.href, { waitUntil: 'domcontentloaded' })
    result.guestRoomCode = await join(guest, guestName)
    checkpoint('verify shared room and host roster')
    assert.equal(result.hostRoomCode, result.guestRoomCode)
    await player(guest, hostName).waitFor()
    await host.bringToFront()
    await player(host, guestName).waitFor()
    await player(host, hostName).waitFor()
    await capture(roster, 'host roster after guest joined')
    result.hostVisiblePlayers = [hostName, guestName]
    result.status = 'passed'
    checkpoint('complete')
  } catch {
    // Browser errors can quote invite fragments, input values and DOM snapshots.
    result.status = 'failed'
    checkpoint(result.stage)
    process.exitCode = 1
  } finally {
    if (browser) await browser.close()
  }
}

main().catch(() => {
  result.status = 'failed'
  checkpoint(result.stage)
  process.exitCode = 1
})
