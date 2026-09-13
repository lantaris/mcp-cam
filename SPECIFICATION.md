# Specification — mcp-cam

## Protocol
- MCP (Model Context Protocol) via `mcp` Python SDK (`FastMCP`).
- Transport: stdio (local process spawned by OpenCode).
- Backend: DirectShow (`cv2.CAP_DSHOW`) for Windows camera access.

## Capture Pattern
- Lazy open: each tool opens and releases the camera independently.
- No persistent `VideoCapture` connections are maintained.
- Auto-brightness correction is applied automatically when the mean gray level is < 0.5.
- All capture functions support `flip` and `quality` parameters.

## Tools
- `capture_base64`: single-shot camera capture by device index. Returns base64 JPEG string (`IMAGE_BASE64:...`).
- `capture_image`: single-shot camera capture by device index. Returns native FastMCP `Image`.
- `capture_jpg`: single-shot camera capture by device index. Saves JPEG file (`quality` controls compression, default 95).
- `capture_frame_base64`: capture using existing connection ID. Returns base64 JPEG string.
- `capture_frame_image`: capture using existing connection ID. Returns native FastMCP `Image`.
- `capture_frame_jpg`: capture using existing connection ID. Saves JPEG file.
- `get_video_properties`: read width, height, fps, brightness, contrast, saturation by connection ID.
- `set_video_property`: set width, height, brightness, contrast, or saturation by connection ID.

## Parameters
- `device_index`: camera index (default 0).
- `connection_id`: string like `cam_2` (device index embedded).
- `flip`: horizontal flip (default False).
- `quality`: JPEG quality 1-100 (default 95).
- `save_path`: optional file path; defaults to system temp directory with random UUID filename.

## Dependencies
- Python 3.10+
- `opencv-python`
- `mcp` (Python SDK)
- `fastmcp` (FastMCP framework)
