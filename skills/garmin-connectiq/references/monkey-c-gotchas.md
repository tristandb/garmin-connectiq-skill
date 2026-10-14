# Monkey C gotchas, with the fix for each

Collected while building a GPS data field for the Forerunner 255 (Connect IQ API 5.x, SDK 7.2–9.2).

## Drawing

- **Fonts.** `Graphics.FONT_NUMBER_MILD/MEDIUM/HOT/THAI_HOT` only contain `0-9`, `:`, `.`, `-`.
  Any letter renders as an empty box. Use `FONT_XTINY/TINY/SMALL/MEDIUM/LARGE` for text and units.
- **Round screens.** Usable width at vertical offset `dy` from the centre is `2*sqrt(r² - dy²)`.
  On 260 px: 254 px at the centre, 172 px at 85 % height, 114 px at 92 %. Put short strings at the
  bottom. A `fit(dc, text, font, maxWidth)` helper that trims the string until
  `dc.getTextWidthInPixels(text, font) <= maxWidth` saves every layout.
- **Centred text.** `dc.drawText(x, y, font, s, Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER)`.
- **Arcs.** `dc.drawArc(cx, cy, r, Graphics.ARC_CLOCKWISE, startDeg, endDeg)`: 0° is 3 o'clock,
  degrees increase counter-clockwise; use 0..360 (not negative). `dc.setPenWidth(10)` before, reset
  to 1 after. A 270° gauge from 225° clockwise to 315° puts "100 %" at 12 o'clock.
- **Colours on MIP.** 64 colours, no anti-aliasing. `COLOR_LT_GRAY` on white is invisible; use
  `COLOR_DK_GRAY` for "inactive" on both backgrounds. For good/bad use `COLOR_GREEN`/`COLOR_RED` on
  black and `COLOR_DK_GREEN`/`COLOR_RED` on white. `getBackgroundColor()` (DataField) tells which.
- **Field sizes.** A data field is drawn into whatever rectangle the user's layout gives it. Branch on
  `dc.getWidth()`/`dc.getHeight()`: full (≥180×180), medium (height ≥70), small. Users expect the
  one-field layout to be the rich one.
- **Blinking.** Toggle a boolean in `compute()` (1 Hz) and skip drawing on alternate ticks; there is
  no timer API in a data field.

## Activity data

- `compute(info)` runs once per second while the activity app is open, also before the timer starts.
  `info.timerTime` (ms) and `info.timerState` are null until the user presses start;
  `info.currentLocation` is null until GPS lock. Treat each independently.
- `info.currentLocation` requires `<iq:uses-permission id="Positioning"/>` in the manifest; without it
  the field is null on the device forever (compiles fine, and the simulator's demo data hides it).
  Also null until GPS lock. Show the user a distinct "no GPS" state so this is diagnosable in the field.
- `info.currentLocation.toDegrees()` returns `[lat, lon]` as `Double`. Keep lat/lon maths in Double,
  convert to a local Float metre grid for everything else.
- `info.currentSpeed` is m/s (Float or null). Pace: `1000 / speed` seconds per km.
- `onTimerReset()` is the hook to clear per-activity state; `onTimerStart/Stop/Pause/Resume` exist too.
- Alerts: `Attention.vibrate([new Attention.VibeProfile(100, 400)])` and
  `Attention.playTone(Attention.TONE_LAP)` work from data fields; guard with `Attention has :vibrate`.
- FIT output: `createField("name", id, FitContributor.DATA_TYPE_SINT16, {:mesgType =>
  FitContributor.MESG_TYPE_RECORD, :units => "s"})` from the DataField; needs permission
  `FitContributor`. Record fields become graphs in Garmin Connect; session fields a single value.

## Settings, storage, resources

- `Application.Properties.getValue("key")` throws on unknown keys and returns whatever type the
  user entered. Wrap: `try { v = Properties.getValue(k); } catch (e) { v = null; }` then
  `if (v instanceof Number)`. Booleans arrive as Boolean, strings as String.
- `onSettingsChanged()` on the App is called when settings arrive from the phone; forward it to the
  view to re-read them.
- `Application.Storage.setValue(key, value)` persists Dictionaries/Arrays across runs; large values
  throw, so wrap in try/catch and tell the user ("feed too large").
- JSON resources: `<jsonData id="segments" filename="segments.json"/>` in `resources/jsondata/*.xml`,
  loaded with `WatchUi.loadResource(Rez.JsonData.segments)`. Integers become Number, decimals Float,
  objects Dictionary with String keys. Cast at the boundary: `d["n"] as String`.
- Types in JSON vs code: declare arrays as `Array<Float>` and make the generator always emit decimals
  (`1000.0`, not `1000`) so no element is a Number.

## Web requests

- Permission `Communications`. Call
  `Communications.makeWebRequest(url, null, {:method => Communications.HTTP_REQUEST_METHOD_GET,
  :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON}, method(:onFeed))`.
- Callback signature the type checker accepts:
  `function onFeed(code as Number, data as Dictionary or String or PersistedContent.Iterator or Null) as Void`
  (import `Toybox.PersistedContent`). A top-level JSON array is not in that union: wrap feeds in an
  object `{"segments": [...]}`.
- Response codes: 200 ok; -104 no phone connection; -300 network; -402 response too large for the
  app's memory. Always keep the previous data on failure.
- The request runs through the Garmin Connect app on the phone. In the simulator it uses the Mac's
  network directly, which is why it works there without a phone.
- Call it from `onLayout()` (first show) or the first `compute()`, not from `initialize()`; and never
  swap the active data set in the middle of an operation the user is in.

## Type checking (`-l 1`)

- `getInitialView() as [Views] or [Views, InputDelegates]` on SDK 7+.
- Nullable members: declare `as Number?`, then `(x as Number)` after a null check.
- Enums in a class (`enum { IDLE, ACTIVE }`) are referenced as `ClassName.IDLE`.
- `Math.sqrt()` returns Float for Float input; append `.toFloat()` when assigning to a Float var
  from mixed expressions to keep the checker quiet.
- String building with `+` works on Numbers; `n.format("%02d")`, `f.format("%.1f")`.
- Unit tests: `Test.assertEqual(a, b)` calls `a.equals(b)`; a null `a` throws
  "Unexpected Type Error: Failed invoking <symbol>". Use `Test.assert(a == null)`.
- Permissions are checked at compile time per used module; the error names the permission.

## Simulator

- Settings persist in `$TMPDIR/com.garmin.connectiq/GARMIN/APPS/SETTINGS/<APPNAME>.SET` and
  override new defaults from `properties.xml`; delete the file after changing defaults.
- The app name in that path comes from the `.prg` filename (`segments-fr255.prg` →
  `SEGMENTS-FR255.SET`); different output names get separate settings.
- `monkeydo` output buffers; give it ~10 s before reading the log.
- Only one `monkeydo` at a time; a new one replaces the running app.
- Compile-time device profiles update with the SDK Manager; an older SDK may stop compiling for a
  device after an update ("requires API Level 5.2.0").
