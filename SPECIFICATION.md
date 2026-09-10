# Specification — mcp-cam

## Protocol
- MCP (Model Context Protocol) via `mcp` Python SDK (`FastMCP`).
- Transport: stdio (local process spawned by OpenCode).

## Tools
- `quick_capture`: single-shot camera capture with optional flip and save path. Returns base64 JPEG.
- `open_camera`: persistent `VideoCapture` connection by `connection_id`.
- `capture_frame`: capture from open connection.
- `get_video_properties`: read width, height, fps, brightness, contrast, saturation.
- `set_video_property`: set width, height, brightness, contrast, saturation.
- `close_connection`: release `VideoCapture` resource.
- `list_active_connections`: active connection IDs.

## Dependencies
- Python 3.10+
- `opencv-python`
- `mcp` (Python SDK)
