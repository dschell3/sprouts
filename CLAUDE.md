# Sprouts (garden theme)

A mobile-friendly, browser-based version of the pencil-and-paper graph theory game **Sprouts** (Conway & Paterson, 1967). It's being built for a math professor's classes. It plays on the square, the torus and the Klein bottle, and has a Brussels Sprouts variant.

Owner: Darren (GitHub: dschell3). Hosted as a **GitHub Page** at https://dschell3.github.io/sprouts/, deployed by `.github/workflows/static.yml` on every push to `main` (Pages source: GitHub Actions).

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
- Facts shown in the UI: a game lasts at most 3n − 1 moves (true on every surface) and, on the flat square, at least 2n moves. The "n mod 6" winner conjecture is marked as a flat-square result.

## Brussels Sprouts (variant)

- Chosen with the **Game** pills, the "Switch to …" link under the subtitle, or `#brussels` in the address (`setVariant`; the hash is kept in sync with `history.replaceState`, which is not storage). 1 to 6 crosses. Its own scoreboard table.
- Seeds are **crosses** (`spot.arms`: four `{dx, dy, used, seg}`), drawn as an upright plus with `ARM_LEN` (16) arms. A vine starts and ends at a **free arm tip** (`ports()`); joining two arms of the same cross is allowed. Arms with `seg` are obstacles like vines (they are in `segs` and in the raster).
- The new cross sits at the split point with two arms along the vine (used, not drawn or in `segs`, since the vine covers them) and a free bar across it. `barFits` requires both bar tips to have `CLEAR` from everything and to be inside the bed.
- Analysis: each free tip is credited with the face found just past its capture disc, looking along the arm in a small fan (`firstFree`). A move exists if some face holds two free tips. Capture discs are drawn at free tips (`blockDiscs`), while the clearance relaxation stays around centres (`seedDiscs`).
- No facts or stats are shown for Brussels. The win box just asks whether the length and winner change. (On the flat square every game lasts exactly 5n − 2 moves; on the torus and Klein bottle it runs between 5n − 2 and 5n, since a loop around the surface does not split a face. Not shown in the UI by the owner's choice.)
- Undo is deferred until the computer opponent exists.

## Surfaces

- **Square**, **Torus** (opposite edges glued straight across) and **Klein bottle** (left/right glued straight, top/bottom glued with a flip, so a vine leaving the top at x comes back in at the bottom at 500 − x). Chosen with the Surface pills; changing it starts a new game.
- **Crossing a seam:** the stroke stops at the edge and waits. A pulsing ring (`.pickup`) marks where it comes back in and the waiting vine is drawn dashed (`.stroke.waiting`). Touching within `START_R` of the ring resumes the same vine. Starting a stroke on a seed instead drops the waiting vine. A vine can also finish across a seam without a lift when the target seed is within `CAPTURE_R` of it on the other side.
- The frame shows gluing arrows (`renderSeams`): single arrows for the left/right pair, double for top/bottom, pointing opposite ways on a flipped pair.
- No bed margin on glued surfaces; the seam is the edge.

## Product decisions (agreed with the owner)

- **Pass-and-play** for now. A computer opponent comes later.
- **Freehand drawing** with a finger on phones and a mouse on desktop. Only fall back to tap-two-seeds if freehand UX proves bad.
- **Mobile first.** The board is a square "garden bed". Single column at ≤840px.
- **End-of-game setting:**
  - *Auto*: the game detects that no moves are left and announces the winner.
  - *Challenge*: the game stays quiet; the player taps "I'm stuck" and the game checks the claim. A wrong claim offers "Show a hint", which pulses seeds that can be joined.
- **Helpers on by default**: green pips inside seeds show remaining shoots (lives), and full seeds turn grey. They can be toggled off, since the professor may want it less guided.
- **No undo in Sprouts.** Invalid strokes are simply discarded on release.
- A small **"Give up"** link under the controls (two taps to confirm) hands the win to the other player. It can be removed if it proves unwanted.
- **No persistence.** Scores and settings live only for the page session.
- Player names stay "Player 1" / "Player 2". Colors: P1 green, P2 terracotta.
- The side cards fold: Move log and Scoreboard start collapsed everywhere, Settings starts collapsed on phones (≤840px) and open on desktop.
- **Theme:** garden/greenhouse (seeds, vines, soil bed, wooden frame), styled like the owner's earlier "Coffee Shop Expedition" game: cards, pills, a move log, a scoreboard, and "How to play" details. Light and dark mode via CSS variables. The backup theme idea is retro arcade / Pac-Man (wraparound fits the torus).
- Owner's writing style for UI text: simple, short sentences.

## How the code works (index.html)

All coordinates are in **board units**: the bed is `B = 500` square (SVG viewBox `-10 -10 520 520`, frame outside 0..500).

**State:** `variant`, `spots[] {x, y, deg, arms?}`, `edges[] {a, b, pts[], breaks[], player}`, `segs[]` (flattened segments `[x1,y1,x2,y2,edgeIndex]`), `log[]`, `scores{}`, `surface`, `pending` (a stroke waiting at a seam).
- Each move is stored as **two edges** split at the new seed, so there are never self-loop edges.
- Vines always live in square coordinates. On a glued surface a vine is cut at the seams into pieces: `breaks` lists the indices in `pts` where a new piece starts, and `pts[k-1] -> pts[k]` is not a segment when `k` is a break. `segs`, the raster and the SVG paths all work on pieces.
- **Surface helpers** (`SURFACES`, `images`, `unmap`, `wrapPt`, `seamExit`, `distToSegs`, `nearestSeed`, `eachCopy`): every distance check takes the minimum over a point's images in the neighbouring copies of the square, flipped where the surface says so. On the square they reduce to the plain checks.
- Seed centres are shared by exact coordinate equality. `segX()` relies on this: segments that only share an endpoint don't count as crossing, unless they overlap at a near-zero angle.

**Drawing pipeline:** `pointerdown`, then `pointermove` (coalesced events with light exponential smoothing), then `addPoint` (subdivided into steps of `STEP` = 2.5), then `pushPoint`, then `checkPoint`.
- A stroke must start within `START_R` of a seed that has lives. Nothing is recorded until the finger leaves the seed body (`SPOT_R`); the first segment then runs from the centre in the exit direction, so two vines started by touching the same spot on a seed don't share an overlapping stub.
- A stroke **auto-completes** when it comes within `CAPTURE_R` of a seed (or one of its images). The start seed only counts after the stroke has "armed", i.e. moved `ARM_R` away from it.
- On a glued surface, a stroke point outside the square triggers `leaveAtSeam`: the stroke is cut at the seam, becomes `pending` with a `resume` point, and the drag ends. `pointerdown` near `resume` picks it up again as a new piece.
- Rejections:
  - out of bounds (`MARGIN`);
  - crossing an existing vine or itself;
  - clearance: vines must stay `CLEAR` (7) apart. The gap needed is 0 within `NO_CLEAR_R` (14) of a seed and ramps up linearly to `CLEAR` at `FULL_CLEAR_R` (60), so vines can converge on a seed and a stroke can start beside an existing vine;
  - a full target seed;
  - a loop on a seed with fewer than 2 lives.
- `pickSplit()` places the new seed in the middle 30–70% of the vine, at the point with the most room. A spot needs `SEED_GAP_V` (22, just past `CAPTURE_R`) from other vines and `SEED_GAP_S` (28) from other seeds; if no spot in the band qualifies, the move is rejected with "No room for a new seed on that vine.".

**Region analysis (`analyze()`)** runs after every move. It is used for Auto end detection, Challenge checks and hints, and will be needed by the future computer opponent. It answers "where could a vine still be drawn?" using the same rules the drawing code enforces, so a face that is topologically open but too cramped to draw in counts as closed.
1. Rasterize all vines onto a hidden canvas at 2× scale (`R = 1000`) as walls `2 * CLEAR` wide, once per neighbouring copy on glued surfaces (`eachCopy`) so walls spill across the seams. Inside `FULL_CLEAR_R` of a seed redraw them `2 * clearanceAt(MID_R)` wide, and inside `MID_R` 0.75 wide, so the raster is a step-under-approximation of the clearance ramp: it never demands more room than the drawing rules do.
2. Fill a disc of `DISC_R` (`CAPTURE_R − 2`) around every seed (a vine that gets within `CAPTURE_R` finishes there) and the `MARGIN` strip around the bed.
3. Flood-fill the free pixels (4-connected) into region labels. On glued surfaces the neighbours wrap across the seams, mirrored on a flipped axis.
4. The regions a seed touches: walk outward from its centre at 72 angles, from just inside the disc to `RING_R` (`CAPTURE_R + 2`), and take the first free pixel on each ray. That pixel lies between the disc and any passing vine, so a vine skimming the seed never credits it with the face beyond. This relies on no vine running inside the disc: new vines keep `CAPTURE_R` away (they would finish there) and new seeds keep `SEED_GAP_V` from vines.
5. A move exists if some region's bordering seeds have **total lives ≥ 2**: either two seeds with a life each, or one seed with 2 lives for a loop.

Why raster: the same flood fill works on the torus and the Klein bottle by wrapping neighbours across edges, and `labelAt` wraps its point so the ray sampling follows.
Known slack: the raster under-approximates the clearance ramp near seeds and does not check that a loop has room to reach `ARM_R`, so it can still say "a move exists" for a face a careful player cannot use. It should never end a game early.

**Test hook:** `window.__sprouts.state()` exposes state for tests (including `surface` and `pending`), and `window.__sprouts.load({surface?, spots, edges})` replaces the board with a hand-built position (seeds `{x, y, deg}`, edges `{a, b, pts, breaks?}`; vine ends are snapped to their seeds). Keep both.

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
- torus: seam exit and pick-up, a loop around the torus that fences nothing off and a vine reaching it the long way round, clearance across a seam, end detection across a seam;
- Klein bottle: a vine leaving the top comes back mirrored at the bottom; left/right glued straight; dropping a waiting vine;
- Brussels Sprouts: switching by pill, header link and address; a full one-cross game that ends after exactly 3 moves; a vine can't cross an arm; a loop between two arms of one cross; a seam crossing on the torus;
- no page errors.

They also save `tests/mobile.png` (390×844) and `tests/desktop_over.png` screenshots, so look at them after UI changes.

**Run the tests after every change to drawing or analysis code. Add a test for every bug fixed.**

## Roadmap (in rough order)

1. **Polish Sprouts from real phone testing.** Watch for: clearance strictness, seed size (currently `SPOT_R` 14), whether the "Too close" message hides real crossings, and accidental auto-complete near seeds.
2. **Surfaces**: Square, Torus and Klein bottle are done (see Surfaces above). Cylinder, Möbius strip and projective plane are one row each in `SURFACES` (`gx`/`gy` of `none`, `glue` or `flip`) plus a pill, if the professor wants them. Test the seam pick-up on real phones.
3. **Computer opponent.** Only practical for small *n* (about 2–5). It will reuse `analyze()` to find legal moves.
4. **Brussels Sprouts** is done (see above). Still to come with the computer opponent: **undo** when playing the computer.

## Conventions

- Vanilla JS inside the one IIFE, CSS variables for all colors, and SVG for the board.
- Touch: the board uses `touch-action: none` and pointer capture. Keep buttons and pills ≥ 38–46px tall.
- Respect `prefers-reduced-motion` and dark mode.
- Don't add network calls, analytics or storage without asking.
