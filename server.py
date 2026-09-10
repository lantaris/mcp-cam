#!/usr/bin/env python3
"""Local MCP server for OpenCode — camera access via OpenCV."""
import cv2
import base64
from typing import Optional
from mcp.server.fastmcp import FastMCP

def _auto_brightness(cap: cv2.VideoCapture) -> bool:
    ret, frame = cap.read()
    if not ret or frame is None:
        return False
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = gray.mean() / 255.0
    if mean_brightness < 0.5:
        current = cap.get(cv2.CAP_PROP_BRIGHTNESS)
        new_val = min(1.0, current + 0.2) if current < 0.8 else 1.0
        cap.set(cv2.CAP_PROP_BRIGHTNESS, new_val)
        return True
    return False

def _device_index_from_id(connection_id: str) -> int:
    try:
        return int(connection_id.split("_")[-1])
    except (ValueError, IndexError):
        return 0

mcp = FastMCP("mcp-cam")

@mcp.tool(description="Capture a single frame from the camera by device index and return it as base64 image. Optionally save to file or flip horizontally.")
async def quick_capture(device_index: int = 0, flip: bool = False, save_path: Optional[str] = None) -> str:
    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        return f"ERROR: Cannot open camera device {device_index}"
    ret, frame = cap.read()
    if ret and frame is not None:
        _auto_brightness(cap)
        ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        return "ERROR: Failed to capture frame"
    if flip:
        frame = cv2.flip(frame, 1)
    if save_path:
        cv2.imwrite(save_path, frame)
    _, buffer = cv2.imencode(".jpg", frame)
    b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")
    return f"IMAGE_BASE64:{b64}"

@mcp.tool(description="Open the camera by device index, optionally with a custom name, and return a connection ID. The camera is released immediately (lazy open).")
async def open_camera(device_index: int = 0, name: Optional[str] = None) -> str:
    conn_id = name or f"cam_{device_index}"
    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        cap.release()
        return f"ERROR: Cannot open camera device {device_index}"
    cap.release()
    return conn_id

@mcp.tool(description="Capture a frame using an existing connection ID (derived from device index), optionally save to file or flip horizontally. Returns base64 image.")
async def capture_frame(connection_id: str, flip: bool = False, save_path: Optional[str] = None) -> str:
    device_index = _device_index_from_id(connection_id)
    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        return f"ERROR: Cannot open camera device {device_index}"
    ret, frame = cap.read()
    if ret and frame is not None:
        _auto_brightness(cap)
        ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        return "ERROR: Failed to capture frame from connection"
    if flip:
        frame = cv2.flip(frame, 1)
    if save_path:
        cv2.imwrite(save_path, frame)
    _, buffer = cv2.imencode(".jpg", frame)
    b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")
    return f"IMAGE_BASE64:{b64}"

@mcp.tool(description="Get video properties (width, height, fps, brightness, contrast, saturation) for a camera connection.")
async def get_video_properties(connection_id: str) -> str:
    device_index = _device_index_from_id(connection_id)
    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        return f"ERROR: Cannot open camera device {device_index}"
    props = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "brightness": cap.get(cv2.CAP_PROP_BRIGHTNESS),
        "contrast": cap.get(cv2.CAP_PROP_CONTRAST),
        "saturation": cap.get(cv2.CAP_PROP_SATURATION),
    }
    cap.release()
    return str(props)

@mcp.tool(description="Set a video property (width, height, brightness, contrast, saturation) for a camera connection by name and value.")
async def set_video_property(connection_id: str, property_name: str, value: float) -> str:
    device_index = _device_index_from_id(connection_id)
    cap = cv2.VideoCapture(device_index)
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
    result = cap.set(prop_map[property_name], value)
    cap.release()
    return f"OK: set {property_name} = {value} (success={bool(result)})"

@mcp.tool(description="Close the camera connection. Note: the server does not hold persistent connections; this returns a confirmation message.")
async def close_connection(connection_id: str) -> str:
    return "OK: no persistent connections (camera not held open)"

@mcp.tool(description="List active camera connections. The server uses lazy open per call, so there are no persistent connections.")
async def list_active_connections() -> str:
    return "No persistent connections (lazy open per call)"

def main():
    mcp.run()

if __name__ == "__main__":
    main()
