# CLAUDE.md — main branch

You are looking at the `main` branch of a Raspberry Pi 5 face-tracking turret repo. **`main` is scaffolding only — there is no code here.** The actual implementation lives on two feature branches.

## What the user wants

A Pi 5 + AI HAT (Hailo) + Pi camera + 2× MG996R servos that pans and tilts to track a detected face. The camera is mounted on the pan plane but is fixed in vertical orientation (it pans with the turret but does NOT tilt with it).

## Step 1 — figure out where the user is

Ask (or infer from their question):
- Has the turret been physically wired and powered yet?
- Have they confirmed the servos move smoothly?
- Are they ready to bring up vision?

## Step 2 — switch to the right branch

| User's situation | Branch | Why |
|---|---|---|
| Just cloned, hasn't tested servos | `servo-test` | Verify servos move smoothly and independently. No vision. |
| Servos work, ready for face tracking | `face-tracking` | Full Hailo detection + pan/tilt control loop. |

Each branch has its own `CLAUDE.md` with a complete bring-up walkthrough specific to that stage. Switch and read it:

```bash
git checkout servo-test     # or: git checkout face-tracking
cat CLAUDE.md
```

**Do not implement anything on `main`.** Direct the user to the appropriate branch and follow its CLAUDE.md from there.

## Hardware quick-reference (applies to both branches)

- Raspberry Pi 5 with AI HAT (Hailo-8 / 8L) and Pi camera (CSI)
- 2× MG996R servos: pan on GPIO 12, tilt on GPIO 13 (hardware-PWM-capable on Pi 5)
- External 5–6 V / ≥3 A supply for servos. **Servos NEVER powered from Pi 5V rail.** Common ground required.
- Software: `lgpio` for PWM (NOT `pigpio` — unsupported on Pi 5), Hailo runtime via `hailo-all`, plus `hailo-rpi5-examples` for the detection pipeline.

See `hardware/wiring.md` for the wiring diagram.

## Repo layout overview

- `main` — README, .gitignore, requirements.txt, hardware/wiring.md, this file.
- `servo-test` — adds `src/servo.py`, `src/calibrate.py`, `src/manual_control.py`, `tests/test_servo_math.py`.
- `face-tracking` — adds `src/geometry.py`, `src/face_source.py`, `src/tracker.py`, `tests/test_geometry.py`, `config.json`.

## What to do RIGHT NOW

1. Recommend `git checkout servo-test` if the user hasn't validated servo motion yet.
2. Recommend `git checkout face-tracking` if servos are confirmed working.
3. After switching, read that branch's `CLAUDE.md` and follow it.
