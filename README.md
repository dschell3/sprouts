# Sprouts

A browser version of the pencil-and-paper graph theory game **Sprouts**
(Conway and Paterson, 1967), built for math classes. Two players share one
screen and draw vines between seeds with a finger or a mouse. The last
player who can move wins.

Play it at https://dschell3.github.io/sprouts/. Brussels Sprouts is at
https://dschell3.github.io/sprouts/#brussels.

The whole game is one file, `index.html`. No build step, no dependencies,
no network calls. It works on phones and desktops, in light and dark mode.

## The games

### Sprouts

- The garden starts with 2 to 8 seeds. Player 1 goes first.
- A move draws a vine from one seed to another, or loops a vine from a seed
  back to itself. A new seed sprouts in the middle of the vine.
- Vines can't cross each other or themselves, and can't pass through a seed.
- A seed can hold at most 3 vines. A loop counts as 2.
- If you can't grow a vine on your turn, you lose.

A game with *n* seeds lasts at most 3*n* − 1 moves. On the flat square it
also lasts at least 2*n* moves, and with perfect play Player 1 appears to
win exactly when *n* leaves a remainder of 3, 4 or 5 when divided by 6. The
game shows these facts under "For the curious".

### Brussels Sprouts

- The garden starts with 1 to 6 crosses. Each cross has 4 free arms.
- A move draws a vine from a free arm to another free arm, which can be an
  arm of the same cross. A new cross grows across the middle of the vine,
  with one free arm on each side.
- Vines can't cross each other, themselves, or the arms of a cross. Each
  arm takes one vine.
- If you can't join two arms on your turn, you lose.

On the flat square every Brussels Sprouts game lasts exactly 5*n* − 2 moves,
so the winner is decided before anyone draws. The game doesn't say so. It
asks the players to find out.

### Surfaces

Both games can be played on three surfaces:

- **Square.** The plain garden bed.
- **Torus.** Opposite edges are glued to each other. A vine that goes off
  the right edge comes back in on the left, at the same height.
- **Klein bottle.** Left and right are glued straight across. Top and
  bottom are glued with a flip, so a vine leaving the top at *x* comes back
  in at the bottom at 500 − *x*.

Arrows on the frame show which edges are glued and which way. When a vine
reaches a glued edge it stops and waits. A pulsing ring marks where it comes
back in. Touch the ring to keep drawing. On the torus and Klein bottle a
loop around the surface fences nothing off, which changes the strategy.

### Playing

- **Auto** ends the game and names the winner when no moves are left.
  **Challenge** stays quiet. When you think there is no move, tap
  "I'm stuck" and the game checks. A wrong claim offers a hint.
- **Helpers** show how many vines a seed can still take (green dots) or
  which arms are free (green tips). Full seeds turn grey. They can be
  turned off.
- A small **Give up** link hands the win to the other player. It needs two
  taps.
- A move log and a scoreboard per game and seed count live in the side
  cards. Nothing is saved between visits.

## How it works

All coordinates are board units: the bed is a 500-unit square drawn in an
SVG. Vines are polylines of recorded stroke points. Each move is stored as
two edges split at the new seed.

**Drawing.** A stroke must start on a seed (or a free arm tip). It finishes
itself when it comes within 20 units of a seed it may end on. A stroke is
rejected if it leaves the bed, crosses a vine or itself, comes closer than
7 units to another vine (the gap relaxes near seeds, where vines converge
anyway), ends on a full seed, or leaves no room for the new seed.

**Surfaces.** Vines always live in square coordinates and are cut at the
seams into pieces. Every distance check takes the minimum over a point's
images in the neighbouring copies of the square, flipped where the surface
says so. On the square these reduce to plain checks.

**End detection.** After every move the game draws all vines onto a hidden
grid as walls as wide as the clearance rule demands, so two vines too close
for a third to pass between them merge into one wall. Seeds become discs
of the capture radius. A flood fill labels the free space into regions,
wrapping across the seams on glued surfaces. A move exists if some region
has two free shoots on its border. A face that is topologically open but
too cramped to draw in counts as closed.

## Tests

Playwright drives real mouse strokes through the board.

```
pip install playwright
python -m playwright install chromium
python tests/test_sprouts.py
```

The suite plays scripted games on every surface and in both variants,
checks the rejections, the seam pick-up, end detection in hand-built
positions, and the UI switches. It saves `tests/mobile.png` and
`tests/desktop_over.png` for a visual check.

## Roadmap

- A computer opponent for small games, with undo when playing it.
- Cylinder, Möbius strip and projective plane, which are one row each in
  the surface table.

## Credits

Sprouts was invented by John Conway and Michael Paterson in 1967. Brussels
Sprouts is Conway's variant.
