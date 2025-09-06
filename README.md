# Trim Back Matter

Podcast episode downloader and smart audio trimmer.

## Setup

```bash
npm install
pip3 install pydub numpy scipy
```

## Usage

1. **Enter your feed url:** edit `feedUrl` in `downloadEpisodes.mjs`

2. **Download episodes:**

   ```bash
   node downloadEpisodes.mjs
   ```

3. **Clip a short shared section of the outro** and place it in `jingle_sample.mp3`
   I haven't automated this yet.

4. **Smart trim** (requires `jingle_sample.mp3`):

   ```bash
   python3 smart_trim.py
   ```

## Output

- Episodes: `./episodes/`
- Smart trimmed: `./smart_trimmed/`
- Removed sections (for quality control): `./removed/`
