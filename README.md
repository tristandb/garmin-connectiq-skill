# garmin-connectiq

An agent skill for building, testing and shipping **Garmin Connect IQ** apps (Monkey C): data fields,
watch faces, widgets and device apps. It captures what cost real time while building a GPS data
field for a Forerunner 255, so your agent does not repeat it:

- device profiles and SDK versions that silently block a build, and the memory limit per app type
- the `Positioning` permission that makes `currentLocation` null on a real watch but not in the simulator
- Monkey C pitfalls: number fonts that only contain digits, round-screen clipping, settings, storage, web requests
- testing without running outside: a testable state machine, unit tests, a demo mode instead of the simulator's FIT playback
- getting a `.prg` onto a watch that macOS cannot mount (MTP), and the Connect IQ Store beta route
- designing a data field that reads at running pace, and what to check before building on a third-party API

## Install

```bash
npx skills add tristandb/garmin-connectiq-skill
```

Works with Claude Code, Cursor, Codex and the other agents the [`skills`](https://github.com/vercel-labs/skills)
CLI supports. Add `-g` for a user-wide install.

## What is in it

```
skills/garmin-connectiq/
  SKILL.md                      workflow: toolchain, project layout, build, simulator, pitfalls, data, design
  references/                   monkey-c-gotchas.md, testing.md, datafield-design.md
  assets/                       Makefile and manifest.xml templates
  scripts/mtp_send.py           copy a .prg to a watch over MTP (needs libmtp)
```

Written against Connect IQ SDK 7.2–9.2 and a Forerunner 255, on macOS. Corrections welcome.

## License

MIT, see [LICENSE](LICENSE).
