# CLAUDE.md — servo-test branch

You are helping the user verify that the two MG996R servos on a Raspberry Pi 5 turret move smoothly and independently before any vision code is involved. Read this whole file before doing anything.

## What this branch does

ONLY servo control. No camera, no detection, no Hailo. The point is to confirm the hardware is wired correctly, the servos respond, and motion is smooth (MG996Rs jerk hard if you snap them — `move_to()` interpolates).

If the user wants face tracking, switch to the `face-tracking` branch — that branch's `CLAUDE.md` covers it.

## Hardware assumptions

- Raspberry Pi 5
- 2× MG996R servos: pan on GPIO 12, tilt on GPIO 13 (both hardware-PWM-capable on Pi 5)
- External 5–6 V / ≥3 A supply for servos. Servos NEVER powered from Pi 5V. Common ground required.
- See `hardware/wiring.md` for the diagram.

## What the code looks like

```
src/
  servo.py           # lgpio PWM wrapper with smooth move_to()
  calibrate.py       # interactive: sweep each servo, find safe limits, write config.json
  manual_control.py  # arrow-key control to verify smooth, independent motion
tests/
  test_servo_math.py # Mac-runnable unit tests (no hardware)
```

## What's already done

- `Servo` class with hardware PWM via `lgpio` and a smooth `move_to()` that interpolates at a configurable angular speed.
- Pure-python servo math (angle→pulse width, clamping, step planning) split out of the I/O layer so it's testable without hardware.
- `calibrate.py` to find each servo's mechanical limits and write `config.json`.
- `manual_control.py` for keyboard-driven motion verification.
- Unit tests pass: `pytest tests/`.

## What's NOT done — your job

Mostly bring-up help, not new code:

### 1. Confirm the hardware is wired right

Before running anything, double-check with the user:
- Is the external servo PSU connected? (V+ to servo red, GND tied to both servo black and Pi GND.)
- Is anything powering the servos from the Pi 5V rail? If yes, STOP — disconnect first.
- Are pan/tilt on GPIO 12 / 13?

### 2. Run calibration

```bash
sudo apt install -y python3-lgpio
git clone https://github.com/ChrisC920/turret.git
cd turret
git checkout servo-test
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/calibrate.py
```

`calibrate.py` will sweep each axis 0→180° and prompt the user for safe min/max/center. It writes `config.json`. The values matter: subsequent code clamps to them so the servos never drive against the mechanical stops.

### 3. Verify smooth motion

```bash
python src/manual_control.py
```

Arrow keys nudge each axis ±2°, space recenters, q quits. Both axes should move smoothly with no buzzing/stalling/jerk. If motion is jerky:
- Increase `SPEED_DEG_PER_S` cautiously (default 180).
- Check the servo PSU isn't sagging under load (cheap supplies brown out — try a higher-rated one).

### 4. When the user is happy with servo motion

Tell them: "Servo bring-up is done. Switch to the `face-tracking` branch and follow that branch's CLAUDE.md to add Hailo face detection."

```bash
git checkout face-tracking
```

`config.json` carries over, so the calibration values you just wrote will be used by the tracker.

## Run order on a freshly-cloned repo

```bash
sudo apt install -y python3-lgpio
git clone https://github.com/ChrisC920/turret.git
cd turret && git checkout servo-test
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/calibrate.py
python src/manual_control.py
```

## Debugging

- **`lgpio.error: 'GPIO busy'`**: another process is holding the pin. `sudo lsof | grep gpiochip` to find it, or reboot.
- **Pi reboots when a servo moves**: servos are pulling current from the Pi 5V rail. Disconnect immediately and rewire to the external PSU.
- **Servo buzzes at one end of travel**: it's hitting a mechanical stop. Re-run `calibrate.py` and tighten the limits.
- **`ImportError: lgpio`** on Mac: that's expected — `lgpio` only runs on Linux/Pi. Run `pytest tests/` instead; the math layer doesn't need it.
- **Both servos move when only one should**: wiring crossed. Check GPIO 12 vs 13.

## Constraints when modifying code

- Don't power servos from the Pi. Don't suggest configurations that do.
- `lgpio` is required (Pi 5 doesn't support `pigpio`). Don't replace it.
- The math layer in `servo.py` (`angle_to_pulse_us`, `clamp_angle`, `plan_steps`) must stay pure-python so the tests run on a dev machine. I/O stays in the `Servo` class.
- Run `pytest tests/` after any change to the math.
- This branch must NOT depend on `picamera2`, `hailo`, or anything vision-related. That belongs on `face-tracking`.
