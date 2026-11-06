const { chromium } = require('/Users/colin/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch({headless:true, executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  const page = await browser.newPage();
  await page.addInitScript(() => {
    window.playLog = [];
    window.playAudios = [];
    const play = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function() { window.playLog.push(this.src); window.playAudios.push(this); return play.call(this); };
  });
  await page.goto('http://127.0.0.1:18765');
  await page.waitForSelector('#play');
  const decoded = await page.evaluate(async () => {
    const context = new AudioContext();
    const results = {};
    for (const lesson of [62,63]) {
      const data = await (await fetch(`data/book2/lesson-${lesson}.json`)).json();
      results[lesson] = 0;
      for (const word of data.words) {
        for (const path of Object.values(word.audio)) {
          const r = await fetch(path);
          if (!r.ok) throw new Error(`fetch ${path}: ${r.status}`);
          const audio = await context.decodeAudioData(await r.arrayBuffer());
          if (audio.numberOfChannels !== 1 || audio.duration < .1) throw new Error(`invalid ${path}`);
          results[lesson]++;
        }
      }
    }
    await context.close();
    return results;
  });
  await page.selectOption('#lesson-select','62');
  await page.waitForSelector('#play');
  await page.click('#play');
  await page.waitForFunction(() => window.playLog.length >= 3, null, {timeout:20000});
  const sequence = await page.evaluate(() => window.playLog.slice(0,3).map(s=>s.split('/').pop()));
  if (!sequence[0].includes('-slow.') || !sequence[1].includes('-meaning.') || !sequence[2].includes('-normal.')) throw new Error(`sequence ${sequence}`);
  await page.selectOption('#lesson-select','63');
  await page.waitForSelector('#play');
  const stopped = await page.evaluate(() => window.playAudios.every(a=>a.paused));
  if (!stopped) throw new Error('old audio still playing');
  await page.reload();
  await page.waitForSelector('#play');
  if (await page.locator('#lesson-select').inputValue() !== '63') throw new Error('lesson not remembered');
  fs.writeFileSync(process.argv[2],JSON.stringify({decoded,sequence,switching_stops_old_audio:stopped,lesson_selection_persisted:true},null,2)+'\n');
  await browser.close();
})().catch(e=>{console.error(e);process.exitCode=1;});
