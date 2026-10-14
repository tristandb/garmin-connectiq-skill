---
name: garmin-connectiq
description: Build, test and ship Garmin Connect IQ apps in Monkey C (data fields, watch faces, widgets, device apps) for watches such as the Forerunner 255/955 or fenix 7. Use this whenever the user mentions Garmin, Connect IQ, Monkey C, monkeyc, a .prg or .iq file, the Connect IQ simulator, a data field or watch face, sideloading onto a watch, or wants something on their Garmin that Garmin itself does not offer. Covers SDK and device-profile setup on macOS, building and signing, the simulator and unit tests, Monkey C pitfalls, fetching data through the phone, and getting the app onto the watch (mass storage, MTP, Connect IQ Store).
---

# Garmin Connect IQ development

Connect IQ apps are written in Monkey C, compiled per device with `monkeyc`, signed with your own
key and either sideloaded (`.prg`) or uploaded to the Connect IQ Store (`.iq`). Most pain is not in
the language but around it: device profiles, the simulator, and getting bytes onto the watch.
This skill captures what cost real time so the next project does not pay for it again.

## 1. Before writing code: check the toolchain

Do these checks first; each one has silently blocked a build before.

```bash
cat ~/Library/Application\ Support/Garmin/ConnectIQ/current-sdk.cfg      # active SDK path
ls ~/Library/Application\ Support/Garmin/ConnectIQ/Devices                 # downloaded device profiles
```

- **Device profiles are not part of the SDK.** `monkeyc` can only target devices whose profile is in
  `Devices/`. The error `Invalid device id found in the application manifest: 'fr255'` or
  `Device 'fr255' requires API Level '5.2.0'. The current SDK supports up to '5.0.0'` means: open the
  **Connect IQ SDK Manager** (GUI, Garmin login required, you cannot script it), download the device
  under *Devices*, and if needed a newer SDK. The SDK Manager also switches `current-sdk.cfg`, so
  re-read it after it ran. A DMG-based SDK Manager that is unmounted is gone; the user re-downloads it
  from developer.garmin.com/connect-iq/sdk.
- **Memory limit per app type** is in `Devices/<id>/compiler.json` (`appTypes[].memoryLimit`). The
  simulator shows live usage in its status bar ("30.6/252.4kB"). Older devices give data fields
  as little as 32 KB; check before designing.
- **Developer key**: `make key` in the bundled Makefile, or
  `openssl genrsa -out developer_key.pem 4096 && openssl pkcs8 -topk8 -inform PEM -outform DER -in developer_key.pem -out developer_key.der -nocrypt`.
  Keep `keys/` out of git.
- While a device profile is missing, compile against an installed device with the same screen to
  validate the code (fenix 7 and Forerunner 255 are both 260×260 MIP). The bundled Makefile has a
  `check` target that filters the manifest for this.

## 2. Project layout

```
manifest.xml          app type, id (32 hex), minSdkVersion, products, permissions
monkey.jungle         "project.manifest = manifest.xml"
source/*.mc           Monkey C
resources/strings/strings.xml, drawables/drawables.xml (+ 40×40 launcher icon PNG, required)
resources/settings/properties.xml + settings.xml     app settings (editable from Garmin Connect)
resources/jsondata/*.xml                              <jsonData id="x" filename="x.json"/> -> Rez.JsonData.x
```

Start from `assets/Makefile` (targets: build, check, test, package, deploy, deploy-mtp, demo) and
`assets/manifest.xml`. Pick the app type deliberately: a **data field** runs inside a native activity
and gets `Activity.Info` (GPS, speed, timer) every second but has no input handling and the smallest
memory budget; a **device app** has its own screens and buttons but must record activities itself.
Permissions are named per API module: `Communications`, `FitContributor`, `Positioning`, `Background`;
`Fit` is not a permission and fails the manifest for data fields. **`Activity.Info.currentLocation` is
always null on a real watch without the `Positioning` permission**, while a demo mode or the
simulator's data simulation hides that; add the permission the moment you read any location.

## 3. Build, package, deploy

```bash
monkeyc -d fr255 -f monkey.jungle -o bin/app-fr255.prg -y keys/developer_key.der -w -l 1 -r   # one device
monkeyc -e -f monkey.jungle -o bin/app.iq -y keys/developer_key.der -w -l 1 -r                 # Store package, all devices in manifest
```

`-l 1` is gradual type checking: strict enough to catch real mistakes, loose enough not to fight the
API's union types. `-t` compiles `(:test)` functions in; `-r` strips debug info for release.

Getting the `.prg` onto the watch, in order of preference:

1. **Mass storage**: the watch mounts as `/Volumes/GARMIN`; copy to `GARMIN/APPS/`, eject, unplug.
   The watch installs on disconnect. If it does not mount, the watch is in MTP mode (see next).
2. **MTP** (Forerunner 255/955, fenix 7 and newer default to MTP; macOS cannot mount it): `brew install
   libmtp`, then `python3 scripts/mtp_send.py bin/app-fr255.prg`. The stock `mtp-sendfile` fails with
   "Error sending file" on these watches because they expose several storage ids; the script picks
   the storage of the `GARMIN/Apps` folder explicitly. Do not run OpenMTP or Garmin Express at the
   same time; they claim the device. The watch may also offer *Settings → System → USB mode → Mass
   storage*; try that first.
3. **Connect IQ Store** (apps.garmin.com/developer/upload): upload the `.iq`, a 40×40 icon, description
   and a screenshot. A beta listing stays "pending" and is installable only by the developer's own
   account through the Connect IQ phone app, over Bluetooth, no cable. Settings for a *sideloaded* app
   can only be edited with Garmin Express (USB); settings for a *Store* app also from the phone. For a
   personal sideload, bake the needed values into the `properties.xml` defaults before building.

## 4. Simulator, logging, tests

```bash
"$SDK/bin/connectiq" &                       # start the simulator app (once)
"$SDK/bin/monkeydo" bin/app-fr255.prg fr255  # load the app; System.println output appears here
"$SDK/bin/monkeydo" bin/app-fr255-test.prg fr255 -t   # run (:test) unit tests, prints PASS/FAIL table
```

- `System.println` is the only cheap debugging channel; it prints to `monkeydo`'s stdout. Log state
  transitions and anything the simulator feeds you (GPS present? timer running?).
- **Unit tests** live in `source/` as `module X { (:test) function f(logger as Logger) as Boolean }`,
  using `Toybox.Test`. Design the core logic so it can be driven without `Activity.Info`
  (e.g. `step(lat, lon, timerMs, running)`), then tests can simulate a whole run in milliseconds.
  `Test.assertEqual(x, null)` throws "Failed invoking <symbol>" because it calls `.equals` on null;
  use `Test.assert(x == null)`.
- **The simulator persists app settings** between runs in
  `$TMPDIR/com.garmin.connectiq/GARMIN/APPS/SETTINGS/<APPNAME>.SET`. A new default in
  `properties.xml` is ignored until you delete that file. Lost hours live here.
- **FIT playback is unreliable**: *Simulation → FIT Data* crashed simulator 9.2.0 on both a
  spec-valid generated file and a real Garmin file, and delivered no positions. Instead add a
  `demo` boolean property: when on, `compute()` synthesises positions along a known route and feeds
  them to the same state machine. That gives deterministic screenshots of every phase and doubles as
  Store-screenshot material. See `references/testing.md` for the demo-mode pattern and a FIT writer.
- Screenshots: the simulator window is a normal macOS window; `screencapture -x out.png` works, but
  the window may sit on another display or behind others (`open "$SDK/bin/ConnectIQ.app"` fronts it).
  Without Accessibility permission you cannot drive its menus, so plan verification around
  `println` and the demo mode rather than menu clicks.

## 5. Monkey C pitfalls that bit

Read `references/monkey-c-gotchas.md` when writing drawing code, web requests or settings; the short
version:

- **Number fonts (`FONT_NUMBER_*`) contain digits and `:` only**; text in them renders as boxes. Use
  `FONT_TINY..FONT_LARGE` for anything with letters ("350 m").
- **Round screens clip text**: a line at 85 % of the height has a chord of only ~170 px on a 260 px
  screen. Keep bottom lines short, split into two lines, or compute `2*sqrt(r²-dy²)` and `fit()` text
  by shrinking until `dc.getTextWidthInPixels` fits.
- `getBackgroundColor()` tells you day/night; choose foreground accordingly and pick colours that
  survive MIP displays (`COLOR_GREEN`/`COLOR_RED` on dark, `COLOR_DK_GREEN` on light).
- `Activity.Info.timerTime` and `currentLocation` are null before the timer starts and before GPS lock;
  design the idle state to work with location alone.
- `Communications.makeWebRequest` callback must be typed
  `(code as Number, data as Dictionary or String or PersistedContent.Iterator or Null)`; return a JSON
  **object** at the top level, not an array. The request goes through the phone's Garmin Connect app,
  so expect code -104 (no phone) and cache the last good answer in `Application.Storage`.
  Trigger the fetch from `onLayout()` or the first `compute()`, not from `initialize()`.
- `Application.Properties.getValue` throws for unknown keys; wrap in try/catch and type-check the
  result (`instanceof Number`), because settings arrive as whatever the user typed.
- JSON resources: decimals become `Float` (32-bit). Store coordinates as integer micro-degrees and
  convert with `.toDouble() / 1000000.0d`; `Position.Location.toDegrees()` gives `Double`s. Keep
  geometry in a local metre grid (`x = (lon-lon0)*111320*cos(lat0)`, `y = (lat-lat0)*110574`) so all
  distance maths is cheap `Float`.
- Monkey C arrays of numbers are not packed; a 400-point polyline is fine, a 4000-point one is not.
  Simplify tracks off-device (Douglas-Peucker, ~3 m) before shipping them.
- Each JSON resource load, Storage value and web response counts against the app memory limit;
  check the simulator status bar after loading real data.

## 6. Data from the outside world

A watch app cannot talk to arbitrary services on its own; it has three channels, and the right one
depends on who updates the data:

| Channel | Update needs | Good for |
|---|---|---|
| JSON resource compiled in | rebuild + cable | fixed data, demo content |
| App settings (`properties.xml`) | Garmin Connect app (Store apps) / Express (sideload) | short strings, numbers, a pairing code |
| `makeWebRequest` + `Storage` cache | phone with Garmin Connect nearby when the app starts | anything that changes: feeds, routes, goals |

Settings strings are a poor place for long payloads (nobody pastes a 2 KB polyline on a phone).
The pattern that worked: a short **pairing code** in settings, a base URL compiled in, and a static
JSON feed per code published by CI (GitHub Actions to Cloudflare Pages was free and took an hour).
Design the feed object to be exactly what the resource JSON looks like, so the same loader handles
compiled-in, cached and fetched data.

## 7. Designing a data field people can read while running

Garmin's own activity screens are the convention users already know: one large number, a small
caption under it, at most two secondary values, colour only for good/bad. Copy that rather than
building a dashboard. Everything that is on another screen already (pace, heart rate, total time)
does not belong on yours. Turn deficits into actions ("pace needed to still make the goal") rather
than into more numbers. Let the layout adapt to the field size: full screen (≥180 px) gets the
complete layout, half screen (≥70 px) two lines, anything smaller one line. See
`references/datafield-design.md` for the layout that tested well and the reasoning behind it.

## 8. When the data comes from a third-party platform

Platform APIs (Strava is the example that prompted this section) have developer terms that go beyond
rate limits: athlete caps that require review, bans on showing other users' data (a leaderboard time
is another user's data), cache time limits, mandatory deauthorisation handling and brand rules, and
sometimes a general "do not replicate our features" clause. Read the agreement before building
something other people will use on top of it, and keep a path that works from the user's own files
(GPX/FIT) so the app survives losing the API. Personal use with your own account is a very different
position from distributing the app, and Garmin's own store policies are a second thing to check
before promising anyone an install.
