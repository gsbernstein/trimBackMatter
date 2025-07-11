import Parser from 'rss-parser';
import fetch from 'node-fetch';
import fs from 'fs';
import path from 'path';

const feedUrl = 'https://rss.art19.com/super-simple-podcast';
const outputDir = './episodes';

const parser = new Parser();

const downloadFile = async (url, filePath) => {
  const res = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0', // tricks Podtrac/Art19
    },
  });
  if (!res.ok) throw new Error(`Fetch failed: ${res.status} ${res.statusText}`);

  const fileStream = fs.createWriteStream(filePath);
  await new Promise((resolve, reject) => {
    res.body.pipe(fileStream);
    res.body.on('error', reject);
    fileStream.on('finish', resolve);
  });
};

(async () => {
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir);

  const feed = await parser.parseURL(feedUrl);
  const items = feed.items.reverse(); // oldest first

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const url = item.enclosure.url;
    const title = item.title.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_');
    const number = String(i + 1).padStart(3, '0');
    const filePath = path.join(outputDir, `${number}_${title}.mp3`);

    if (fs.existsSync(filePath)) {
      console.log(`Skipped: ${number}_${title}`);
      continue;
    }

    console.log(`Downloading: ${number}_${title}`);
    try {
      await downloadFile(url, filePath);
    } catch (err) {
      console.error(`Error downloading ${title}: ${err.message}`);
    }
  }
})();