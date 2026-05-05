# Wiring

## Pinout

| Signal | Pi 5 GPIO (BCM) | Pin # |
|---|---|---|
| Pan servo PWM (horizontal) | GPIO 12 | 32 |
| Tilt servo PWM (vertical) | GPIO 13 | 33 |
| Servo GND (common) | GND | any GND pin |

GPIO 12 and 13 are hardware-PWM-capable on the Pi 5. If those pins conflict with the AI HAT's pin usage on your stack, fall back to GPIO 18 / 19 and update `config.json`.

## Power — read this before plugging in

**Do not power the MG996R servos from the Raspberry Pi.** Each one draws ~600 mA at stall and the inrush will brown out the Pi.

```
                 ┌──────────────┐
   5–6V PSU  ────┤ V+   Servo 1 ├── PWM ←─── Pi GPIO 12
   (≥3A)        │              │
                 └──────┬───────┘
                        │ GND
                        ├───────────── Pi GND  (common ground required)
                 ┌──────┴───────┐
                 │ V+   Servo 2 ├── PWM ←─── Pi GPIO 13
                 │              │
                 └──────────────┘
```

- Servo V+ → external 5–6 V supply
- Servo GND → external supply GND **and** Pi GND (tied together)
- Servo PWM → Pi GPIO 12 / 13
- Add a 470–1000 µF electrolytic across the servo V+/GND rail close to the servos to absorb stall surges

## Camera

CSI ribbon to either CAM port. The camera is mounted on the pan plane and **does not tilt** with the barrel — keep that in mind when assembling, the camera should always look horizontally forward regardless of where the barrel is aimed.
