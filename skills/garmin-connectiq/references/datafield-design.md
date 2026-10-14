# Designing a data field that reads at a glance

What tested well for a "segment timer" field on a 260×260 round MIP screen, and why.

## Principles (borrowed from Garmin's own screens)

1. One large number per phase, always in the same place. The eye learns the position once.
2. A caption in plain words under every number ("behind on goal 3:01", "needed", "to go"). No
   abbreviations; nobody wants to study a legend mid-interval.
3. Colour means one thing: green ahead, red behind. Nothing else is coloured.
4. Show actions, not just measurements. "Pace needed to still make the goal" beats "goal pace",
   because it already includes how far behind you are.
5. Leave out what the watch shows elsewhere (heart rate, total time, current pace unless it is the
   point). Space on a 260 px disc is the scarcest resource.
6. Maps and rings look great in screenshots and are unreadable at 4:00/km. Keep them for the calm
   phases (approach, finish), or behind a setting.

## Layout that worked (full-screen field)

```
        Segment name            tiny, y 11 %
          +0:04                 FONT_NUMBER_HOT, coloured, y 29 %
     behind on KOM 2:25         tiny, y 44 %
     3:26         3:08          FONT_NUMBER_MEDIUM, x 30 % / 70 %, y 58 %
      now         needed        tiny, y 69 %
   [=========--------]          6 px progress bar, y 78 %, width 56 %
    1:12       640 m to go      tiny, y 89 %
```

Approach phase: "SEGMENT", name, optional route box with position dot, distance to start in
`FONT_LARGE` (a text font, so "m" renders), "to start · goal 3:01 (3:28/km)". Finish: name,
"FINISH", time in `FONT_NUMBER_HOT`, delta coloured, caption, then "New PR!" or average pace.

## Phase model

IDLE (nearest target, distance) → ARMED (inside start radius, blink "READY") → ACTIVE → FINISHED
(hold result 30 s) → IDLE. Detect a start the way Strava does: come within the radius, then move
away along the route direction; take the timestamp of minimum distance as the start. Abort when
off-route for N seconds. All radii as settings; GPS on a wrist is 5–15 m.

## Smaller fields

Half-screen: big delta left, "now/needed" right, name + remaining below. Quarter: one line,
"+0:04 3:08 needed", coloured. Decide by `dc.getHeight()`.
