"""MG996R servo control via lgpio hardware PWM on Raspberry Pi 5.

The Servo class is split into a pure-python math layer (angle_to_duty,
clamp_angle, plan_steps) and a thin lgpio I/O layer so the math is
testable on a Mac without lgpio installed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterator, Optional


@dataclass(frozen=True)
class ServoSpec:
    gpio: int
    min_us: int = 500
    max_us: int = 2500
    freq_hz: int = 50
    min_angle: float = 0.0
    max_angle: float = 180.0


def clamp_angle(spec: ServoSpec, angle: float) -> float:
    if angle < spec.min_angle:
        return spec.min_angle
    if angle > spec.max_angle:
        return spec.max_angle
    return angle


def angle_to_pulse_us(spec: ServoSpec, angle: float) -> float:
    a = clamp_angle(spec, angle)
    span_angle = spec.max_angle - spec.min_angle
    span_us = spec.max_us - spec.min_us
    return spec.min_us + (a - spec.min_angle) / span_angle * span_us


def angle_to_duty_pct(spec: ServoSpec, angle: float) -> float:
    period_us = 1_000_000.0 / spec.freq_hz
    return angle_to_pulse_us(spec, angle) / period_us * 100.0


def plan_steps(
    start_angle: float,
    end_angle: float,
    speed_deg_per_s: float,
    tick_hz: float = 50.0,
) -> Iterator[float]:
    """Yield intermediate angles for a smooth move at constant angular velocity.

    The final yielded value is exactly end_angle so the caller doesn't have
    to do its own correction.
    """
    if speed_deg_per_s <= 0:
        raise ValueError("speed_deg_per_s must be positive")
    if tick_hz <= 0:
        raise ValueError("tick_hz must be positive")

    delta = end_angle - start_angle
    if delta == 0:
        yield end_angle
        return

    step = speed_deg_per_s / tick_hz
    direction = 1.0 if delta > 0 else -1.0
    n_steps = int(abs(delta) // step)
    current = start_angle
    for _ in range(n_steps):
        current += direction * step
        yield current
    if current != end_angle:
        yield end_angle


class Servo:
    """Hardware-PWM servo on a single GPIO via lgpio.

    Usage:
        with Servo(ServoSpec(gpio=12)) as s:
            s.move_to(90, speed_deg_per_s=60)
            s.stop()
    """

    def __init__(self, spec: ServoSpec, chip: int = 0):
        self.spec = spec
        self.chip = chip
        self._handle: Optional[int] = None
        self._current_angle: float = (spec.min_angle + spec.max_angle) / 2.0

    def __enter__(self) -> "Servo":
        import lgpio  # imported lazily so tests can run without lgpio

        self._lgpio = lgpio
        self._handle = lgpio.gpiochip_open(self.chip)
        self.set_angle(self._current_angle)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            self.stop()
        finally:
            if self._handle is not None:
                self._lgpio.gpiochip_close(self._handle)
                self._handle = None

    @property
    def current_angle(self) -> float:
        return self._current_angle

    def set_angle(self, angle: float) -> None:
        """Snap to angle (no smoothing). Most callers want move_to."""
        if self._handle is None:
            raise RuntimeError("Servo not opened (use 'with Servo(...)')")
        a = clamp_angle(self.spec, angle)
        duty = angle_to_duty_pct(self.spec, a)
        self._lgpio.tx_pwm(self._handle, self.spec.gpio, self.spec.freq_hz, duty)
        self._current_angle = a

    def move_to(self, angle: float, speed_deg_per_s: float = 90.0, tick_hz: float = 50.0) -> None:
        """Smooth move from current angle to target at constant angular speed.

        Blocks for the duration of the move. MG996Rs jerk hard if you snap
        them; this loop interpolates so the motion looks smooth.
        """
        if self._handle is None:
            raise RuntimeError("Servo not opened")
        target = clamp_angle(self.spec, angle)
        period = 1.0 / tick_hz
        for step in plan_steps(self._current_angle, target, speed_deg_per_s, tick_hz):
            self.set_angle(step)
            time.sleep(period)

    def stop(self) -> None:
        """Release the PWM line so the servo isn't held against load."""
        if self._handle is None:
            return
        self._lgpio.tx_pwm(self._handle, self.spec.gpio, self.spec.freq_hz, 0)
