#!/usr/bin/env python3
"""Local MCP server for OpenCode — camera access via OpenCV."""
import base64
import os
import tempfile
from typing import Optional
from uuid import uuid4

import cv2
import numpy as np
from fastmcp import FastMCP
from fastmcp.utilities.types import Image


def _device_index_from_id(connection_id: str) -> int:
    try:
        return int(connection_id.split("_")[-1])
    except (ValueError, IndexError):
        return 0


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
    cap = cv2.VideoCapture(device_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        return None
    try:
        return _capture_frame(cap, flip)
    finally:
        cap.release()


def _capture_by_connection_id(connection_id: str, flip: bool = False) -> Optional[np.ndarray]:
    device_index = _device_index_from_id(connection_id)
    return _capture_by_device_index(device_index, flip)


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


mcp = FastMCP("mcp-cam")


@mcp.tool(
    description=(
        "Capture a single frame from the camera by device index and return it as "
        "a base64-encoded JPEG image prefixed with 'IMAGE_BASE64:'. "
        "Uses DirectShow backend (cv2.CAP_DSHOW). "
        "Automatically adjusts brightness if the frame is too dark. "
        "Optionally applies horizontal flip (flip=True). "
        "JPEG quality can be set via quality parameter (1-100, default 95). "
        "Returns a string starting with 'IMAGE_BASE64:' followed by base64 data, "
        "or an error message if the camera cannot be opened or the frame cannot be read."
    )
)
async def capture_base64(device_index: int = 0, flip: bool = False, quality: int = 95) -> str:
    frame = _capture_by_device_index(device_index, flip)
    if frame is None:
        return f"ERROR: Cannot open camera device {device_index}"
    return _frame_to_base64(frame, quality)


@mcp.tool(
    description=(
        "Capture a single frame from the camera by device index and save it as a JPEG file. "
        "Uses DirectShow backend (cv2.CAP_DSHOW). "
        "Automatically adjusts brightness if the frame is too dark. "
        "Optionally applies horizontal flip (flip=True). "
        "JPEG quality can be set via quality parameter (1-100, default 95). "
        "If save_path is omitted, the file is saved to the system temporary directory "
        "with a random filename. "
        "Returns the path of the saved file on success, or an error message on failure."
    )
)
async def capture_jpg(device_index: int = 0, flip: bool = False, quality: int = 95, save_path: Optional[str] = None) -> str:
    frame = _capture_by_device_index(device_index, flip)
    if frame is None:
        return f"ERROR: Cannot open camera device {device_index}"
    path = _resolve_save_path(save_path)
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    cv2.imwrite(path, frame, encode_params)
    return f"OK: saved to {path}"


@mcp.tool(
    description=(
        "Capture a single frame from the camera by device index and return it as "
        "a native FastMCP Image object. "
        "Uses DirectShow backend (cv2.CAP_DSHOW). "
        "Automatically adjusts brightness if the frame is too dark. "
        "Optionally applies horizontal flip (flip=True). "
        "JPEG quality can be set via quality parameter (1-100, default 95). "
        "Returns an Image that MCP clients render natively, "
        "or raises an error if the camera cannot be opened or the frame cannot be read."
    )
)
async def capture_image(device_index: int = 0, flip: bool = False, quality: int = 95) -> Image:
    frame = _capture_by_device_index(device_index, flip)
    if frame is None:
        raise RuntimeError(f"Cannot open camera device {device_index}")
    return _frame_to_image(frame, quality)


@mcp.tool(
    description=(
        "Capture a single frame using an existing connection ID "
        "(device index embedded in the ID, e.g., 'cam_2'). "
        "Uses DirectShow backend (cv2.CAP_DSHOW). "
        "Automatically adjusts brightness if the frame is too dark. "
        "Optionally applies horizontal flip (flip=True). "
        "JPEG quality can be set via quality parameter (1-100, default 95). "
        "Returns a base64-encoded JPEG image prefixed with 'IMAGE_BASE64:', "
        "or an error message if the camera is unavailable or the frame cannot be read."
    )
)
async def capture_frame_base64(connection_id: str, flip: bool = False, quality: int = 95) -> str:
    frame = _capture_by_connection_id(connection_id, flip)
    if frame is None:
        device_index = _device_index_from_id(connection_id)
        return f"ERROR: Cannot open camera device {device_index}"
    return _frame_to_base64(frame, quality)


@mcp.tool(
    description=(
        "Capture a single frame using an existing connection ID "
        "(device index embedded in the ID, e.g., 'cam_2'). "
        "Uses DirectShow backend (cv2.CAP_DSHOW). "
        "Automatically adjusts brightness if the frame is too dark. "
        "Optionally applies horizontal flip (flip=True). "
        "JPEG quality can be set via quality parameter (1-100, default 95). "
        "Saves the frame as a JPEG file. "
        "If save_path is omitted, the file is saved to the system temporary directory "
        "with a random filename. "
        "Returns the path of the saved file on success, or an error message on failure."
    )
)
async def capture_frame_jpg(connection_id: str, flip: bool = False, quality: int = 95, save_path: Optional[str] = None) -> str:
    frame = _capture_by_connection_id(connection_id, flip)
    if frame is None:
        device_index = _device_index_from_id(connection_id)
        return f"ERROR: Cannot open camera device {device_index}"
    path = _resolve_save_path(save_path)
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    cv2.imwrite(path, frame, encode_params)
    return f"OK: saved to {path}"


@mcp.tool(
    description=(
        "Capture a single frame using an existing connection ID "
        "(device index embedded in the ID, e.g., 'cam_2'). "
        "Uses DirectShow backend (cv2.CAP_DSHOW). "
        "Automatically adjusts brightness if the frame is too dark. "
        "Optionally applies horizontal flip (flip=True). "
        "JPEG quality can be set via quality parameter (1-100, default 95). "
        "Returns a native FastMCP Image that MCP clients render natively, "
        "or raises an error if the camera is unavailable or the frame cannot be read."
    )
)
async def capture_frame_image(connection_id: str, flip: bool = False, quality: int = 95) -> Image:
    frame = _capture_by_connection_id(connection_id, flip)
    if frame is None:
        device_index = _device_index_from_id(connection_id)
        raise RuntimeError(f"Cannot open camera device {device_index}")
    return _frame_to_image(frame, quality)


@mcp.tool(
    description=(
        "Get video properties (width, height, fps, brightness, contrast, saturation) "
        "for a camera identified by connection ID. "
        "Connects to the device using DirectShow, reads the properties, "
        "then releases the camera. "
        "Returns a dictionary string (e.g., {'width': 640, ...}) "
        "or an error message if the device cannot be opened."
    )
)
async def get_video_properties(connection_id: str) -> str:
    device_index = _device_index_from_id(connection_id)
    cap = cv2.VideoCapture(device_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        return f"ERROR: Cannot open camera device {device_index}"
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
        "Set a video property (width, height, brightness, contrast, or saturation) "
        "for a camera identified by connection ID. "
        "The property name must match exactly (e.g., 'brightness'). "
        "Applies the value via VideoCapture.set(), releases the device, "
        "and returns a confirmation string with the new value and the backend success flag (True/False), "
        "or an error if the property is unknown or the camera is unavailable."
    )
)
async def set_video_property(connection_id: str, property_name: str, value: float) -> str:
    device_index = _device_index_from_id(connection_id)
    cap = cv2.VideoCapture(device_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        return f"ERROR: Cannot open camera device {device_index}"
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


def main():
    mcp.run()


if __name__ == "__main__":
    main()