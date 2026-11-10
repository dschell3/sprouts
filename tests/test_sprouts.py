import math, os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
URL = (ROOT / "index.html").as_uri()
CHROME = os.environ.get("CHROME")  # optional path to a Chrome binary; default uses Playwright's Chromium

def interp(pts, step=4):
    out = [pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for k in range(1, n + 1):
            out.append((x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n))
    return out

def arc(cx, cy, r, a0, a1, n=40):
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]

class G:
    def __init__(self, page):
        self.p = page
    def box(self):
        return self.p.locator("#svg").bounding_box()
    def to_client(self, x, y):
        b = self.box()
        return b["x"] + (x + 10) / 520 * b["width"], b["y"] + (y + 10) / 520 * b["height"]
    def stroke(self, pts):
        pts = interp(pts)
        self.p.mouse.move(*self.to_client(*pts[0]))
        self.p.mouse.down()
        for x, y in pts[1:]:
            self.p.mouse.move(*self.to_client(x, y))
        for _ in range(6):
            self.p.mouse.move(*self.to_client(*pts[-1]))
        self.p.mouse.up()
    def st(self):
        return self.p.evaluate("""() => { const s = window.__sprouts.state();
          return {moves: s.moveCount, player: s.player, over: s.over, winner: s.winner,
                  movable: s.analysis.movable, hint: s.analysis.hint, regions: s.analysis.regions,
                  spots: s.spots.map(p => [Math.round(p.x), Math.round(p.y), p.deg])}; }""")
    def msg(self):
        return self.p.inner_text("#msg")
    def load(self, spots, edges):
        self.p.evaluate("st => window.__sprouts.load(st)", {"spots": spots, "edges": edges})

def seed(x, y, deg=0):
    return {"x": x, "y": y, "deg": deg}
def edge(a, b, pts):
    return {"a": a, "b": b, "pts": [{"x": x, "y": y} for x, y in pts]}

fails = []
def check(cond, label):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        fails.append(label)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"]) if CHROME else pw.chromium.launch()
    page = br.new_page(viewport={"width": 1200, "height": 1000})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(URL)
    g = G(page)

    # --- Scripted 2-seed game: A=(350,250), B=(150,250) ---
    page.click("[data-seeds='2']")
    s = g.st()
    check(sorted(s["spots"]) == [[150, 250, 0], [350, 250, 0]], "2-seed layout " + str(s["spots"]))
    A, B = (350, 250), (150, 250)

    # Move 1: A -> B over the top
    g.stroke([A] + arc(250, 250, 100, 0, -math.pi)[1:])
    s = g.st()
    check(s["moves"] == 1 and len(s["spots"]) == 3 and s["player"] == 2, f"move 1 committed {s['moves']} {s['spots']}")

    # Illegal: straight across the middle from A toward B should be fine (no line there) -- instead test crossing:
    # A -> up through the top vine
    g.stroke([A, (330, 230), (330, 160), (330, 100)])
    s = g.st()
    check(s["moves"] == 1, "crossing stroke rejected; msg=" + g.msg())

    # Move 2: A -> B under the bottom
    g.stroke([A] + arc(250, 250, 100, 0, math.pi)[1:])
    s = g.st()
    check(s["moves"] == 2 and s["player"] == 1, f"move 2 committed {s['spots']}")

    # Find the two new seeds (top C and bottom D)
    C = [p for p in s["spots"] if p[1] < 200][0]
    D = [p for p in s["spots"] if p[1] > 300][0]
    # Move 3: C -> D straight down the middle (inside the closed curve)
    g.stroke([(C[0], C[1]), (250, 250), (D[0], D[1])])
    s = g.st()
    check(s["moves"] == 3 and s["movable"], f"move 3 committed, still movable {s['spots']} hint={s['hint']}")

    # Full seed: C now has 3 vines; try to start on it
    g.stroke([(C[0], C[1]), (C[0], C[1] - 60)])
    check(g.st()["moves"] == 3 and "full" in g.msg(), "full seed rejected; msg=" + g.msg())

    # Brushing past full seed C (within CAPTURE_R) is a different message from starting on it
    g.stroke([A, (300, 180), (262, 165), (200, 170)])
    check(g.st()["moves"] == 3 and "touched a full seed" in g.msg(), "brushing a full seed explained; msg=" + g.msg())

    # Move 4: A -> B around the outside top (big arc, radius 190)
    pts = [A, (440, 250)] + arc(250, 250, 190, 0, -math.pi)[1:] + [(60, 250), B]
    g.stroke(pts)
    s = g.st()
    check(s["moves"] == 4, f"move 4 committed {s['moves']} msg={g.msg()}")
    check(s["over"] and s["winner"] == 2, f"auto-detected game over, P2 wins: over={s['over']} winner={s['winner']} hint={s['hint']}")
    page.screenshot(path=str(OUT / "desktop_over.png"), full_page=True)

    # --- Loop test & challenge mode ---
    page.click("[data-mode='challenge']")
    page.click("#btnNew")
    s = g.st()
    # loop from A to the right and back
    loop = [A] + [(350 + 60 * math.cos(t) + 60, 250 + 60 * math.sin(t)) for t in [math.pi * (1 - k / 30 * 2) for k in range(0, 31)]][1:]
    # Circle centered (410,250) r=60 starting at (350,250) and returning to it
    g.stroke(loop)
    s = g.st()
    check(s["moves"] == 1 and len(s["spots"]) == 3, f"loop committed {s['spots']} msg={g.msg()}")
    Adeg = [p for p in s["spots"] if p[0] == 350 and p[1] == 250][0][2]
    check(Adeg == 2, f"loop counts as 2 on seed (deg={Adeg})")

    # A second loop on A should fail (only 1 shoot left)
    g.stroke([A] + [(350 - 60 * math.cos(t) - 60 + 0, 250 + 60 * math.sin(t)) for t in [math.pi * (k / 30 * 2) for k in range(0, 31)]][1:])
    check(g.st()["moves"] == 1 and "loop" in g.msg().lower(), "second loop rejected; msg=" + g.msg())

    # Challenge: claim stuck while moves exist
    check(page.is_visible("#btnStuck"), "I'm stuck visible in challenge mode")
    page.click("#btnStuck")
    check(not g.st()["over"] and page.is_visible("#btnHint"), "wrong stuck claim rejected, hint offered")
    page.click("#btnHint")
    check(page.locator(".hintring").count() >= 1, f"hint rings shown: {page.locator('.hintring').count()}")

    # Log numbering: the unnumbered "I'm stuck" line must not shift the next move's number
    g.stroke([B] + arc(90, 250, 60, 0, 2 * math.pi)[1:])
    nums = page.evaluate("[...document.querySelectorAll('#log li[value]')].map(li => li.value)")
    check(g.st()["moves"] == 2 and nums == [1, 2], f"log numbers after a stuck claim: {nums}")

    # --- Out of bounds ---
    page.click("[data-mode='auto']")
    page.click("#btnNew")
    g.stroke([A, (480, 250), (520, 250)])
    check(g.st()["moves"] == 0 and "garden" in g.msg().lower(), "out-of-bounds rejected; msg=" + g.msg())

    # --- A stroke that starts beside an existing vine can still peel away from it ---
    page.click("[data-seeds='2']")
    g.stroke([A] + arc(250, 250, 100, 0, -math.pi)[1:])          # leaves A straight up
    g.stroke([(352, 225), (400, 190), (440, 250), (400, 340), (250, 370), (100, 300), B])
    check(g.st()["moves"] == 2, "stroke starting 2 units beside a vine accepted; msg=" + g.msg())

    # --- A tap on a seed is a gentle prompt, not an error ---
    page.click("[data-seeds='2']")
    page.mouse.move(*g.to_client(*A)); page.mouse.down(); page.mouse.up()
    check("tap" in g.msg() and not page.evaluate("document.getElementById('msg').classList.contains('bad')"),
          "tap gives a neutral prompt; msg=" + g.msg())

    # --- Lost pointer capture mid-stroke must not lock the board ---
    page.click("[data-seeds='2']")
    page.mouse.move(*g.to_client(*A)); page.mouse.down()
    page.mouse.move(*g.to_client(330, 200))
    page.evaluate("document.getElementById('svg').dispatchEvent(new PointerEvent('lostpointercapture', {pointerId: 1}))")
    # no pointerup ever arrives; the next stroke starts with the button still "down"
    g.stroke([A] + arc(250, 250, 100, 0, -math.pi)[1:])
    check(g.st()["moves"] == 1, "stroke accepted after a lost pointer capture; msg=" + g.msg())

    # --- load() hook: a hand-built position round-trips ---
    g.load([seed(100, 250), seed(400, 250, 2), seed(250, 100, 3)],
           [edge(1, 2, [(400, 250), (350, 150), (250, 100)])])
    s = g.st()
    check(s["spots"] == [[100, 250, 0], [400, 250, 2], [250, 100, 3]] and s["moves"] == 0 and s["movable"],
          f"loaded position: {s['spots']} movable={s['movable']}")

    # --- New seed needs room: a vine squeezed down a lane 16 wide is drawable but can't sprout ---
    def lane_position(half):
        # two full-seed "fences" above and below y=250, each `half` units from the centre line
        return ([seed(100, 250), seed(400, 250), seed(130, 200, 3), seed(370, 200, 3), seed(130, 300, 3), seed(370, 300, 3)],
                [edge(2, 3, [(130, 200), (160, 250 - half), (340, 250 - half), (370, 200)]),
                 edge(4, 5, [(130, 300), (160, 250 + half), (340, 250 + half), (370, 300)])])
    g.load(*lane_position(8))
    g.stroke([(100, 250), (400, 250)])
    check(g.st()["moves"] == 0 and "No room" in g.msg(), "vine with no room for a seed rejected; msg=" + g.msg())
    g.load(*lane_position(20))
    g.stroke([(100, 250), (400, 250)])
    check(g.st()["moves"] == 1, "same vine with room accepted; msg=" + g.msg())

    # --- Analysis matches the drawing rules: a doorway too narrow to draw through is closed ---
    def two_rooms(door):
        # P in the left room and Q in the right, split by a wall of full seeds with a gap of `door`
        sp = [seed(100, 250, 2), seed(400, 250, 2), seed(250, 24, 3), seed(250, 250 - door / 2, 3),
              seed(250, 250 + door / 2, 3), seed(250, 476, 3)]
        return sp, [edge(2, 3, [(250, 24), (250, 250 - door / 2)]), edge(4, 5, [(250, 250 + door / 2), (250, 476)])]
    g.load(*two_rooms(36))      # the two door posts' capture discs overlap: nothing fits
    s = g.st()
    check(not s["movable"], f"36-unit doorway between full seeds counts as closed: movable={s['movable']} regions={s['regions']}")
    g.load(*two_rooms(80))
    s = g.st()
    check(s["movable"] and sorted(s["hint"]) == [0, 1], f"80-unit doorway is open: movable={s['movable']} hint={s['hint']}")
    g.stroke([(100, 250), (400, 250)])
    check(g.st()["moves"] == 1, "and a vine really can be drawn through it; msg=" + g.msg())

    # --- 8 seeds renders ---
    page.click("[data-seeds='8']")
    check(len(g.st()["spots"]) == 8, "8 seeds")

    check(not errs, "no page errors " + str(errs))

    # Mobile screenshot
    m = br.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    m.goto(URL)
    m.click("[data-seeds='5']")
    m.screenshot(path=str(OUT / "mobile.png"))
    br.close()

print("\nFAILURES:", fails if fails else "none")
sys.exit(1 if fails else 0)
