# Sprouts (garden theme)

A mobile-friendly, browser-based version of the pencil-and-paper graph theory game **Sprouts** (Conway & Paterson, 1967). It's being built for a math professor's classes. Brussels Sprouts and other play surfaces come later.

Owner: Darren (GitHub: dschell3). Hosted as a **GitHub Page**.

## Repo layout

```
index.html              # the whole game: HTML + CSS + JS in one file, no dependencies
tests/test_sprouts.py   # Playwright gameplay tests (simulated mouse strokes)
CLAUDE.md
```

Keep the game as **one self-contained `index.html`**: no build step, no frameworks, no external requests. GitHub Pages serves it as is.

## Rules implemented (Sprouts, normal play)

- Start with *n* seeds (spots), with *n* from 2 to 8.
- A move draws a vine (curve) from one seed to another, or a loop from a seed back to itself. A new seed is placed on the vine.
- Vines may not cross themselves or other vines, and may not pass through a seed.
- A seed holds at most 3 vine ends. A loop uses 2 of them.
- Normal play: the player who cannot move loses, so the last player to move wins. **No misère mode.**
- Facts shown in the UI: a game lasts at most 3n − 1 moves and at least 2n moves.

## Product decisions (agreed with the owner)

- **Pass-and-play** for now. A computer opponent comes later.
- **Freehand drawing** with a finger on phones and a mouse on desktop. Only fall back to tap-two-seeds if freehand UX proves bad.
- **Mobile first.** The board is a square "garden bed". Single column at ≤840px.
- **End-of-game setting:**
  - *Auto*: the game detects that no moves are left and announces the winner.
  - *Challenge*: the game stays quiet; the player taps "I'm stuck" and the game checks the claim. A wrong claim offers "Show a hint", which pulses seeds that can be joined.
- **Helpers on by default**: green pips inside seeds show remaining shoots (lives), and full seeds turn grey. They can be toggled off, since the professor may want it less guided.
- **No undo in Sprouts.** Invalid strokes are simply discarded on release.
- Player names stay "Player 1" / "Player 2". Colors: P1 green, P2 terracotta.
- **Theme:** garden/greenhouse (seeds, vines, soil bed, wooden frame), styled like the owner's earlier "Coffee Shop Expedition" game: cards, pills, a move log, a scoreboard, and "How to play" details. Light and dark mode via CSS variables. The backup theme idea is retro arcade / Pac-Man (wraparound fits the torus).
- Owner's writing style for UI text: simple, short sentences.

## How the code works (index.html)

All coordinates are in **board units**: the bed is `B = 500` square (SVG viewBox `-10 -10 520 520`, frame outside 0..500).

**State:** `spots[] {x, y, deg}`, `edges[] {a, b, pts[], player}`, `segs[]` (flattened segments `[x1,y1,x2,y2,edgeIndex]`), `log[]`, `scores{}`.
- Each move is stored as **two edges** split at the new seed, so there are never self-loop edges.
- Seed centres are shared by exact coordinate equality. `segX()` relies on this: segments that only share an endpoint don't count as crossing, unless they overlap at a near-zero angle.

**Drawing pipeline:** `pointerdown`, then `pointermove` (coalesced events with light exponential smoothing), then `addPoint` (subdivided into steps of `STEP` = 2.5), then `pushPoint`, then `checkPoint`.
- A stroke must start within `START_R` of a seed that has lives.
- A stroke **auto-completes** when it comes within `CAPTURE_R` of a seed. The start seed only counts after the stroke has "armed", i.e. moved `ARM_R` away from it.
- Rejections:
  - out of bounds (`MARGIN`);
  - crossing an existing vine or itself;
  - clearance: vines must stay `CLEAR` (7) apart. The gap needed is 0 within `NO_CLEAR_R` (14) of a seed and ramps up linearly to `CLEAR` at `FULL_CLEAR_R` (60), so vines can converge on a seed and a stroke can start beside an existing vine;
  - a full target seed;
  - a loop on a seed with fewer than 2 lives.
- `pickSplit()` places the new seed in the middle 30–70% of the vine, at the point with the most room. A spot needs `SEED_GAP_V` (16) from other vines and `SEED_GAP_S` (28) from other seeds; if no spot in the band qualifies, the move is rejected with "No room for a new seed on that vine.".

**Region analysis (`analyze()`)** runs after every move. It is used for Auto end detection, Challenge checks and hints, and will be needed by the future computer opponent.
1. Rasterize all vines onto a hidden canvas at 2× scale (`R = 1000`, line width 0.75 units).
2. Flood-fill the empty pixels (4-connected) into region labels.
3. For each edge, sample a point 4 units off **each side**, at a spot where no other vine is within 5 units. These give the regions on its left and right. In a planar drawing, each side of an edge belongs to exactly one face.
4. A seed's regions are the union of the side regions of its incident edges. A seed with no vines uses the label at its centre.
5. A move exists if some region's bordering seeds have **total lives ≥ 2**: either two seeds with a life each, or one seed with 2 lives for a loop.

Why raster: the same flood fill works on a torus or Klein bottle by wrapping neighbours across edges.
Known weak spot: in very cramped drawings, a face could be missed, which would cause a false "game over". The clearance rules exist to prevent this. If tuning clearance, keep the raster gap ≥ ~2px.

**Test hook:** `window.__sprouts.state()` exposes state for tests, and `window.__sprouts.load({spots, edges})` replaces the board with a hand-built position (seeds `{x, y, deg}`, edges `{a, b, pts}`; vine ends are snapped to their seeds). Keep both.

## Testing

```
pip install playwright && python -m playwright install chromium
python tests/test_sprouts.py
```

The tests drive real mouse strokes through the SVG:
- a full scripted 2-seed game, where Auto must end it after move 4 with Player 2 winning;
- rejected crossing, full-seed and second-loop moves;
- a loop counting as 2;
- Challenge "I'm stuck" with a hint;
- out of bounds;
- 8-seed layout;
- no page errors.

They also save `tests/mobile.png` (390×844) and `tests/desktop_over.png` screenshots, so look at them after UI changes.

**Run the tests after every change to drawing or analysis code. Add a test for every bug fixed.**

## Roadmap (in rough order)

1. **Polish Sprouts from real phone testing.** Watch for: clearance strictness, seed size (currently `SPOT_R` 14), whether the "Too close" message hides real crossings, and accidental auto-complete near seeds.
2. **Surfaces** (professor's request): Square (done), **Torus**, **Klein bottle**. All are defined from the square by gluing edges.
   - Torus: opposite edges glued straight across.
   - Klein bottle: one pair glued straight, the other pair glued with a flip.
   - Cylinder, Möbius strip and projective plane are cheap extras.
   - Preferred UX: a **tiled view** (the square surrounded by copies of itself, mirrored for Klein) so strokes cross seams naturally, then get mapped back into the fundamental square. The simpler alternative is wrapping the stroke at the edge.
   - Region analysis: make the flood-fill neighbours wrap. Crossing and clearance checks need wrapped coordinates.
   - The Surface pills are already in the UI, disabled and marked "(soon)".
3. **Computer opponent.** Only practical for small *n* (about 2–5). It will reuse `analyze()` to find legal moves.
4. **Brussels Sprouts.** Not yet decided whether it is a separate page or a toggle/tab here.
   - Seeds are crosses with 4 arms. A move joins two free arms, and a new cross is placed on the vine, which uses 2 of its arms (one free arm on each side).
   - Every game lasts exactly 5n − 2 moves, so the winner is fixed by *n*. Present it as a "why is the winner fixed?" puzzle.
   - Owner wants **undo** in Brussels Sprouts when playing the computer.
   - Same surfaces and opponent options as Sprouts.

## Conventions

- Vanilla JS inside the one IIFE, CSS variables for all colors, and SVG for the board.
- Touch: the board uses `touch-action: none` and pointer capture. Keep buttons and pills ≥ 38–46px tall.
- Respect `prefers-reduced-motion` and dark mode.
- Don't add network calls, analytics or storage without asking.
