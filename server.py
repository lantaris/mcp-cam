#!/usr/bin/env python3
"""Local MCP server for OpenCode — camera access via OpenCV."""
import base64
import os
import tempfile
from typing import Optional
from uuid import uuid4

import cv2
import numpy as np
from cv2_enumerate_cameras import enumerate_cameras
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.utilities.types import Image


def _capture_frame(cap: cv2.VideoCapture, flip: bool = False) -> Optional[np.ndarray]:
    ret, frame = cap.read()
    if not ret or frame is None:
        return None
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if gray.mean() / 255.0 < 0.5:
        current = cap.get(cv2.CAP_PROP_BRIGHTNESS)
        new_val = min(1.0, current + 0.2) if current < 0.8 else 1.0
        cap.set(cv2.CAP_PROP_BRIGHTNESS, new_val)
        ret, frame = cap.read()
        if not ret or frame is None:
            return None
    if flip:
        frame = cv2.flip(frame, 1)
    return frame


def _capture_by_device_index(device_index: int, flip: bool = False) -> Optional[np.ndarray]:
    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        return None
    try:
        return _capture_frame(cap, flip)
    finally:
        cap.release()


def _frame_to_base64(frame: np.ndarray, quality: int = 95) -> str:
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    _, buffer = cv2.imencode(".jpg", frame, encode_params)
    b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")
    return f"IMAGE_BASE64:{b64}"


def _frame_to_image(frame: np.ndarray, quality: int = 95) -> Image:
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    _, buffer = cv2.imencode(".jpg", frame, encode_params)
    return Image(data=buffer.tobytes(), format="jpeg")


def _resolve_save_path(save_path: Optional[str]) -> str:
    if save_path:
        return save_path
    return os.path.join(tempfile.gettempdir(), f"capture_{uuid4().hex}.jpg")


mcp = MCPServer("mcp-cam")


@mcp.tool(
    description=(
        "Capture one frame from a camera and return base64 string. Params: device_index (int, optional, defaults to first device from list_devices), flip (bool, default False — flip horizontally), quality (int, default 95 — JPEG image quality). Auto-adjusts brightness if dark. Returns: IMAGE_BASE64:... JPEG string or error message."
    )
)
async def capture_base64(device_index: int = None, flip: bool = False, quality: int = 95) -> str:
    if device_index is None:
        devices = await list_devices()
        device_index = devices[0]["index"] if devices and "index" in devices[0] else 0
    frame = _capture_by_device_index(device_index, flip)
    if frame is None:
        return f"ERROR: Cannot open camera device {device_index}"
    return _frame_to_base64(frame, quality)


@mcp.tool(
    description=(
        "Capture one frame from a camera and save as JPEG file. Params: device_index (int, optional, defaults to first device from list_devices), flip (bool, default False — flip horizontally), quality (int, default 95 — JPEG image quality), save_path (str, optional — temporary path if omitted). Auto-adjusts brightness if dark. Returns: saved file path or error message."
    )
)
async def capture_jpg(device_index: int = None, flip: bool = False, quality: int = 95, save_path: Optional[str] = None) -> str:
    if device_index is None:
        devices = await list_devices()
        device_index = devices[0]["index"] if devices and "index" in devices[0] else 0
    frame = _capture_by_device_index(device_index, flip)
    if frame is None:
        return f"ERROR: Cannot open camera device {device_index}"
    path = _resolve_save_path(save_path)
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    cv2.imwrite(path, frame, encode_params)
    return f"OK: saved to {path}"


@mcp.tool(
    description=(
        "Capture one frame from a camera and return native Image — native screenshot for agent directly visible in chat. Params: device_index (int, optional, defaults to first device from list_devices), flip (bool, default False — flip horizontally), quality (int, default 95 — JPEG image quality). Auto-adjusts brightness if dark. Returns: Image or raises error."
    )
)
async def capture_image(device_index: int = None, flip: bool = False, quality: int = 95) -> Image:
    if device_index is None:
        devices = await list_devices()
        device_index = devices[0]["index"] if devices and "index" in devices[0] else 0
    frame = _capture_by_device_index(device_index, flip)
    if frame is None:
        raise RuntimeError(f"Cannot open camera device {device_index}")
    return _frame_to_image(frame, quality)


@mcp.tool(
    description=(
        "Get camera properties (width, height, fps, brightness, contrast, saturation). Params: index (int, optional, defaults to first device from list_devices). Returns: properties dict string or error message."
    )
)
async def get_camera_properties(index: int = None) -> str:
    if index is None:
        devices = await list_devices()
        index = devices[0]["index"] if devices and "index" in devices[0] else 0
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        return f"ERROR: Cannot open camera device {index}"
    try:
        props = {
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "brightness": cap.get(cv2.CAP_PROP_BRIGHTNESS),
            "contrast": cap.get(cv2.CAP_PROP_CONTRAST),
            "saturation": cap.get(cv2.CAP_PROP_SATURATION),
        }
        return str(props)
    finally:
        cap.release()


@mcp.tool(
    description=(
        "Set camera property (width/height/brightness/contrast/saturation). Params: index (int, optional, defaults to first device from list_devices), property_name (str, default 'brightness'), value (float, default 0). Returns: confirmation with new value and success flag, or error message."
    )
)
async def set_camera_property(index: int = None, property_name: str = "brightness", value: float = 0) -> str:
    if index is None:
        devices = await list_devices()
        index = devices[0]["index"] if devices and "index" in devices[0] else 0
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        return f"ERROR: Cannot open camera device {index}"
    prop_map = {
        "width": cv2.CAP_PROP_FRAME_WIDTH,
        "height": cv2.CAP_PROP_FRAME_HEIGHT,
        "brightness": cv2.CAP_PROP_BRIGHTNESS,
        "contrast": cv2.CAP_PROP_CONTRAST,
        "saturation": cv2.CAP_PROP_SATURATION,
    }
    if property_name not in prop_map:
        cap.release()
        return f"ERROR: Unknown property {property_name}"
    try:
        result = cap.set(prop_map[property_name], value)
        return f"OK: set {property_name} = {value} (success={bool(result)})"
    finally:
        cap.release()


@mcp.tool(
    description=(
        "List available cameras: returns list of dicts with index and name."
    )
)
async def list_devices() -> list:
    result = []
    try:
        for cam in enumerate_cameras():
            result.append({"index": cam.index, "name": cam.name})
    except Exception as e:
        return [{"error": str(e)}]
    return result


def main():
    mcp.run()


if __name__ == "__main__":
    main()