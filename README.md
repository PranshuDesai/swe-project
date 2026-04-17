# GameScript AI — Text to 2D Platformer (Python)

Generate a playable 2D platformer from any text description using Claude AI.

## Setup

### 1. Install dependencies
```bash
pip install pygame anthropic
```

### 2. Set your Anthropic API key
```bash
# macOS / Linux
export ANTHROPIC_API_KEY=sk-ant-...

# Windows (Command Prompt)
set ANTHROPIC_API_KEY=sk-ant-...

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Run the game
```bash
python gamescript_ai.py
```

> ⚠️ No API key? The app still works — it falls back to a local keyword parser
> (same as the original HTML). Set the key for true AI-powered generation.

---

## How it works

1. You type any game description in the left panel
2. The description is sent to **Claude (claude-opus-4-5)** via the Anthropic API
3. Claude extracts a structured game config (hero color, enemy types & speed,
   collectibles, win condition, background colors, platform count, etc.)
4. Pygame builds and renders the game live — every prompt gives a different result

### Example prompts to try
- `"A blue hero jumps on green platforms, collects golden coins, avoids red enemies. Collect all coins to win."`
- `"A cyan robot shoots pink laser beams at alien invaders. Defeat all aliens."`
- `"A purple wizard survives a haunted forest for 30 seconds while avoiding orange ghosts."`
- `"A yellow ninja collects magical crystals on floating islands. Reach the golden flag to win."`

---

## Controls

| Key | Action |
|-----|--------|
| ← → / A D | Move |
| ↑ / W / Space | Jump |
| Z | Shoot (if enabled) |
| R | Restart |

---

## Key differences from original HTML version

| Feature | Original HTML | This Python version |
|---------|--------------|---------------------|
| Parser | Hardcoded keyword matching | Claude LLM — unique per prompt |
| Colors | Limited color detection | Arbitrary color from description |
| Enemies | Fixed 4, fixed speed | Count + speed vary per prompt |
| Platforms | Always 7, same layout | Count varies, slight randomization |
| Win condition | Limited detection | Fully prompt-driven |
| Background | Always dark blue | Matches game mood |
| Game title | Generic | Claude names the game |
| Renderer | HTML Canvas | Pygame |
