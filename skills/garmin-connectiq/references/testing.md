# Testing a GPS data field without running outside

## Make the core testable

Keep the state machine free of `Activity.Info`:

```monkeyc
function update(info as Activity.Info) as Void {      // adapter
    var loc = info.currentLocation; var t = info.timerTime;
    if (loc == null) { return; }
    var deg = loc.toDegrees();
    if (t == null) { scanNearest(deg[0], deg[1]); return; }   // before start: display only
    step(deg[0], deg[1], t, info.timerState == Activity.TIMER_STATE_ON);
}
function step(lat as Double, lon as Double, t as Number, running as Boolean) as Void { ... }
```

Unit tests then drive `step()` with a synthetic runner (constant speed along a known line) and
assert on state, timing (±2 s at 1 Hz) and events. A full 5-minute run is a 300-iteration loop.

```monkeyc
import Toybox.Test;
module TrackerTest {
    (:test)
    function runsAndTimes(logger as Logger) as Boolean {
        var tr = new Tracker(); tr.segments = [demoSegment()] as Array<Segment>;
        for (var t = 0; t <= 330; t++) { tr.step(lat(t), lon(t), t * 1000, true); ... }
        Test.assertMessage(tr.resultMs >= 268000 && tr.resultMs <= 272000, "time " + tr.resultMs);
        return true;
    }
}
```

Build with `-t`, run with `monkeydo app-test.prg fr255 -t`; the console prints a PASS/FAIL table.

## Demo mode instead of FIT playback

Add a boolean property `demo` (default false). When true, `compute()` ignores the real `info` and
generates a position along the first loaded route: 150 m run-in, the route at a plausible speed,
150 m run-out, then restart. Feed that into `step()`; everything downstream (alerts, drawing,
FIT fields) runs for real. For simulator screenshots build a variant with the default flipped to
true (`make demo` in the bundled Makefile) and delete the simulator's `.SET` file first.

Why not *Simulation → FIT Data*: simulator 9.2.0 crashed (SIGSEGV in its "parse main" thread) on a
spec-valid FIT file written from scratch and on a real Garmin activity with transplanted
coordinates, and delivered no positions when it did play. Your results may differ on other simulator
versions; try it once with a real activity exported as "original" from Garmin Connect, but do not
make your verification depend on it. If you generate FIT files yourself, validate them with the
`fitdecode` Python package (CRC check on) before blaming the simulator.

## Verifying visually

- `screencapture -x out.png` captures the whole display (per display: pass several filenames).
  Downscale with `sips -Z 1400` before looking.
- The simulator may be on another display or behind windows; `open "$SDK/bin/ConnectIQ.app"` fronts
  it. The Mac's screen lock turns captures black; `caffeinate -u -t 300 &` during a capture series.
- Without Accessibility permission for the terminal you cannot drive the simulator's menus
  (`osascript ... System Events` fails with -1719); do not plan on it.
- Timeline captures: run the demo build, then `screencapture` at fixed offsets (approach, mid,
  finish) from a background shell loop; that also gives Store screenshots.
