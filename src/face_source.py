"""Face detection source (Pi-only).

Wraps the Hailo detection pipeline from hailo-ai/hailo-rpi5-examples and
exposes a simple `latest()` method that returns a list of Detections.

This file deliberately keeps the integration surface tiny: tracker.py
doesn't need to know anything about GStreamer, Hailo, or picamera2 — it
just calls `faces.latest()` each control tick.

To wire this up on the Pi:

  1. Install hailo-all per the official Raspberry Pi docs.
  2. git clone https://github.com/hailo-ai/hailo-rpi5-examples ~/hailo-rpi5-examples
  3. Activate their venv / install their deps.
  4. Edit `_run_pipeline` below to match the example's API surface for
     whichever face/person detector you choose (e.g. detection.py with a
     YOLOv8-face HEF). The example's `app_callback_class` exposes per-frame
     detection lists; push them into self._latest under self._lock.

The skeleton below uses a thread + lock so the control loop can read the
freshest detections without blocking on the camera/inference pipeline.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tracker import Detection


class FaceSource:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self._latest: list = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "FaceSource":
        self._thread = threading.Thread(target=self._run_pipeline, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def latest(self) -> list:
        with self._lock:
            return list(self._latest)

    def _publish(self, detections: list) -> None:
        with self._lock:
            self._latest = detections

    def _run_pipeline(self) -> None:
        """Hailo detection pipeline.

        REPLACE THIS with a call into hailo-rpi5-examples. The example
        framework calls a user callback for every frame with a list of
        Hailo detection objects; convert those to tracker.Detection and
        call self._publish(...).

        Pseudocode:

            from hailo_apps_infra.hailo_rpi_common import (
                get_caps_from_pad, get_numpy_from_buffer, app_callback_class,
            )
            from detection_pipeline import GStreamerDetectionApp

            class CB(app_callback_class):
                def __init__(self, source): super().__init__(); self.source = source

            def callback(pad, info, user_data):
                buf = info.get_buffer()
                roi = hailo.get_roi_from_buffer(buf)
                dets = roi.get_objects_typed(hailo.HAILO_DETECTION)
                from tracker import Detection
                out = []
                for d in dets:
                    if d.get_label() != "face":  # or "person"
                        continue
                    bbox = d.get_bbox()  # normalized 0..1
                    w_px = bbox.width()  * cam_w
                    h_px = bbox.height() * cam_h
                    cx   = (bbox.xmin() + bbox.width()/2)  * cam_w
                    cy   = (bbox.ymin() + bbox.height()/2) * cam_h
                    out.append(Detection(cx, cy, w_px, h_px))
                user_data.source._publish(out)
                return Gst.PadProbeReturn.OK

            cb = CB(self)
            app = GStreamerDetectionApp(callback, cb)
            app.run()

        Until this is wired up, the loop just publishes empty results.
        """
        while not self._stop.is_set():
            self._stop.wait(0.1)
