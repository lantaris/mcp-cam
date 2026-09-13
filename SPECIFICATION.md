# Specification — mcp-cam

## Protocol
- MCP (Model Context Protocol) via `mcp` Python SDK (`MCPServer`).
- Transport: stdio (local process spawned by OpenCode).
- Backend: DirectShow (`cv2.CAP_DSHOW`) for Windows camera access.

## Capture Pattern
- Lazy open: each tool opens and releases the camera independently.
- No persistent `VideoCapture` connections are maintained.
- Auto-brightness correction is applied automatically when the mean gray level is < 0.5.
- All capture functions support `flip` and `quality` parameters.

## Tools
- `list_devices`: list all available cameras with their `index` and `name`.
- `capture_base64`: single-shot camera capture by device index. Returns base64 JPEG string (`IMAGE_BASE64:...`). If `device_index` is not specified, the first camera from `list_devices` is used.
- `capture_image`: single-shot camera capture by device index. Returns native `Image`. If `device_index` is not specified, the first camera from `list_devices` is used.
- `capture_jpg`: single-shot camera capture by device index. Saves JPEG file (`quality` controls compression, default 95). If `device_index` is not specified, the first camera from `list_devices` is used.
- `get_video_properties`: read width, height, fps, brightness, contrast, saturation by index. If `index` is not specified, the first camera from `list_devices` is used.
- `set_video_property`: set width, height, brightness, contrast, or saturation by index. If `index` is not specified, the first camera from `list_devices` is used.

## Parameters
- `device_index` / `index`: camera index (default: first camera from `list_devices`).
- `flip`: horizontal flip (default False).
- `quality`: JPEG quality 1-100 (default 95).
- `save_path`: optional file path; defaults to system temp directory with random UUID filename.
- `property_name`: exact property name (`width`, `height`, `brightness`, `contrast`, `saturation`).

## Dependencies
- Python 3.10+
- `opencv-python`
- `numpy`
- `mcp` (Python SDK)
- `cv2-enumerate-cameras`
