"""
face_tracker.py  ─ Jarvis skill: слежение за лицом / головой
===========================================================

* Детектирует лицо через MediaPipe Face Detection (до ≈45 ° поворота).
* Если лицо не найдено, fallback → MediaPipe Pose для оценки положения головы.
* Вычисляет yaw/pitch-углы камеры и шлёт их по WebSocket через DisplayDriver.
* Опционально показывает окно OpenCV или стримит кадры base64.
* Подробное логирование на каждом шаге (DEBUG показывает ещё детальнее).

Зависимости
-----------
pip install mediapipe opencv-python numpy
"""

from __future__ import annotations

import base64
import threading
import time
from typing import Final

import cv2
import mediapipe as mp
import numpy as np

from logging_config import setup_logging

# ────────────────────────────────────────────────────────────────────────────
# Константы и настройки
# ────────────────────────────────────────────────────────────────────────────
DEBUG_GUI: Final[bool]      = True     # показывать окно OpenCV
SEND_FRAME_B64: Final[bool] = False    # отправлять кадр base64 по WS
CAM_INDEX: Final[int]       = 0        # индекс веб-камеры
FPS: Final[int]             = 5       # целевой FPS обработки
FOV_DEG_X: Final[float]     = 62.0     # горизонтальный угол обзора камеры
FOV_DEG_Y: Final[float]     = 38.0     # вертикальный
SMOOTH_ALPHA: Final[float]  = 0.25     # эксп. сглаживание yaw/pitch
POSE_MIN_VIS: Final[float]  = 0.80     # миним. надёжность keypoints

PATTERNS: Final[list[str]] = [
    "включи слежение",
    "включить слежение",
    "выключи слежение",
    "отключи слежение",
]

# ────────────────────────────────────────────────────────────────────────────
# Логирование
# ────────────────────────────────────────────────────────────────────────────
logger = setup_logging(__name__)

# ────────────────────────────────────────────────────────────────────────────
# Глобальное состояние
# ────────────────────────────────────────────────────────────────────────────
_is_running: bool | None = None     # None → неизвестно, False → выключен
_thread: threading.Thread | None = None

# Драйвер WebSocket (динамически импортируем — Jarvis кладёт модуль в PYTHONPATH)
try:
    from display import get_driver, DisplayItem
    _driver = get_driver()
except Exception as exc:             # pylint: disable=broad-except
    logger.warning("Display driver isn't available: %s", exc)
    _driver = None                   # unit-тесты / offline-режим


# ────────────────────────────────────────────────────────────────────────────
# Внешняя точка: обработчик голосовой команды
# ────────────────────────────────────────────────────────────────────────────
def handle(text: str) -> str:
    """
    Включает или выключает слежение по команде пользователя.
    Возвращает фразу-ответ для TTS, либо пустую строку.
    """
    global _is_running, _thread                         # pylint: disable=global-statement

    t = text.lower()
    if any(p in t for p in ("включи", "включить")) and "слеж" in t:
        if _is_running:
            return "Слежение уже запущено"
        logger.info("🚀 Запускаю слежение")
        _is_running = True
        _thread = threading.Thread(target=_loop, name="face_tracker", daemon=True)
        _thread.start()
        return "Включаю слежение"
    if any(p in t for p in ("выключи", "отключи")) and "слеж" in t:
        if not _is_running:
            return "Слежение уже выключено"
        logger.info("🛑 Останавливаю слежение")
        _is_running = False
        return "Отключаю слежение"
    return ""  # не наша команда


# ────────────────────────────────────────────────────────────────────────────
# Главный поток захвата и детекции
# ────────────────────────────────────────────────────────────────────────────
def _loop() -> None:  # pylint: disable=too-many-locals,too-many-statements
    """
    В фоновом режиме захватывает видео, ищет лицо/голову,
    отправляет yaw/pitch через WebSocket, рисует GUI (если включено).
    """
    global _is_running
    # Инициализация MediaPipe
    mp_face = mp.solutions.face_detection.FaceDetection(
        model_selection=1,                      # 0 — до 2 м, 1 — до 5 м
        min_detection_confidence=0.55,
    )
    mp_pose = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=0,
        enable_segmentation=False,
        min_detection_confidence=0.5,
    )

    cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)   # CAP_DSHOW — fast on Windows
    if not cap.isOpened():
        logger.error("📷 Не удалось открыть камеру #%d", CAM_INDEX)
        return

    logger.info("▶ Face-tracker поток запущен")
    dt_target = 1.0 / FPS

    yaw_prev = pitch_prev = 0.0
    frame_id = 0

    try:
        while _is_running:
            loop_t0 = time.time()
            ok, frame_bgr = cap.read()
            if not ok:
                logger.warning("♻️ Кадр не получен (%d)", frame_id)
                continue

            frame_id += 1
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            # 1) Face Detection
            face = None
            face_det = mp_face.process(frame_rgb).detections
            if face_det:
                face = max(face_det, key=lambda d: d.score[0])

            # 2) Fallback → Pose
            kind = "face"
            if face:
                rel_bb = face.location_data.relative_bounding_box
                x_rel, y_rel, w_rel, h_rel = (
                    rel_bb.xmin, rel_bb.ymin, rel_bb.width, rel_bb.height
                )
                logger.debug("🟢 Face @ %.2f %.2f %.2f×%.2f",
                             x_rel, y_rel, w_rel, h_rel)
            else:
                result = mp_pose.process(frame_rgb)
                pose   = result.pose_landmarks
                if pose:
                    vis = POSE_MIN_VIS
                    lms = pose.landmark
                    xs = [
                        lms[mp.solutions.pose.PoseLandmark.LEFT_EAR].x,
                        lms[mp.solutions.pose.PoseLandmark.RIGHT_EAR].x,
                        lms[mp.solutions.pose.PoseLandmark.NOSE].x,
                    ]
                    ys = [
                        lms[mp.solutions.pose.PoseLandmark.LEFT_EAR].y,
                        lms[mp.solutions.pose.PoseLandmark.RIGHT_EAR].y,
                        lms[mp.solutions.pose.PoseLandmark.NOSE].y,
                    ]
                    visibilities = [
                        lms[mp.solutions.pose.PoseLandmark.LEFT_EAR].visibility,
                        lms[mp.solutions.pose.PoseLandmark.RIGHT_EAR].visibility,
                        lms[mp.solutions.pose.PoseLandmark.NOSE].visibility,
                    ]
                    xs_vis = [x for x, v in zip(xs, visibilities) if v > vis]
                    ys_vis = [y for y, v in zip(ys, visibilities) if v > vis]
                    if len(xs_vis) >= 2:
                        x_rel, y_rel = min(xs_vis), min(ys_vis)
                        w_rel = max(xs_vis) - x_rel
                        h_rel = max(ys_vis) - y_rel
                        kind = "head"
                        logger.debug("🟠 Head @ %.2f %.2f %.2f×%.2f",
                                     x_rel, y_rel, w_rel, h_rel)
                    else:
                        kind = None
                else:
                    kind = None

            if kind:
                fh, fw = frame_bgr.shape[:2]
                cx = (x_rel + w_rel / 2) * fw
                cy = (y_rel + h_rel / 2) * fh

                # Переход в углы (0 в центре кадра)
                yaw =  (cx - fw / 2.0) / fw * FOV_DEG_X
                pitch = -(cy - fh / 2.0) / fh * FOV_DEG_Y

                # Экспоненциальное сглаживание
                yaw   = yaw_prev   + SMOOTH_ALPHA * (yaw   - yaw_prev)
                pitch = pitch_prev + SMOOTH_ALPHA * (pitch - pitch_prev)
                yaw_prev, pitch_prev = yaw, pitch

                _send_servo(yaw, pitch)

                # GUI — рисуем рамку
                if DEBUG_GUI:
                    color = (0, 255, 0) if kind == "face" else (0, 165, 255)
                    pt1 = (int(x_rel * fw), int(y_rel * fh))
                    pt2 = (int((x_rel + w_rel) * fw), int((y_rel + h_rel) * fh))
                    cv2.rectangle(frame_bgr, pt1, pt2, color, 2)
                    cv2.putText(frame_bgr, f"{kind}:{yaw:+.1f},{pitch:+.1f}",
                                (pt1[0], max(15, pt1[1] - 6)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1,
                                lineType=cv2.LINE_AA)

            else:
                logger.debug("🫥 %d: нет лица/головы", frame_id)

            # Отладочное окно / стриминг
            if DEBUG_GUI:
                cv2.imshow("Jarvis-View", frame_bgr)
                if cv2.waitKey(1) & 0xFF == 27:   # Esc → выключить
                    logger.info("Esc → прекращаем слежение")
                    break

            if SEND_FRAME_B64:
                _send_frame(frame_bgr, frame_id)

            # Держим целевой FPS
            dt = time.time() - loop_t0
            if dt < dt_target:
                time.sleep(dt_target - dt)
    finally:
        cap.release()
        cv2.destroyAllWindows()
        logger.info("⏹ Face-tracker поток завершён")
        _is_running = False


# ────────────────────────────────────────────────────────────────────────────
# Вспомогательные функции отправки
# ────────────────────────────────────────────────────────────────────────────
def _send_servo(yaw: float, pitch: float) -> None:
    """
    Отправка yaw/pitch через DisplayDriver → WebSocket.
    """
    if not _driver:
        logger.debug("🛈 Driver отсутствует, yaw=%.1f, pitch=%.1f", yaw, pitch)
        return
    try:
        pkt = DisplayItem(kind="servo",
                          payload={"yaw": round(yaw, 1),
                                   "pitch": round(pitch, 1)})
        _driver.draw(pkt)
        logger.info("WS → yaw=%+.1f pitch=%+.1f", yaw, pitch)
    except Exception as exc:                        # pylint: disable=broad-except
        logger.exception("Ошибка отправки WS: %s", exc)


def _send_frame(frame_bgr: np.ndarray, frame_id: int) -> None:
    """
    Отправка JPEG-кадра base64 (можно просматривать вторым WS-клиентом).
    """
    if not _driver:
        return
    try:
        _, buf = cv2.imencode(".jpg", frame_bgr,
                              [int(cv2.IMWRITE_JPEG_QUALITY), 60])
        b64 = base64.b64encode(buf).decode()
        _driver.draw(DisplayItem(kind="frame", payload=b64))
        logger.debug("🖼 WS-frame #%d, %d bytes", frame_id, len(buf))
    except Exception:                               # pylint: disable=broad-except
        logger.exception("Не удалось отправить кадр #%d", frame_id)
