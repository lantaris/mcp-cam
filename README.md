# mcp-cam — Local MCP Server for OpenCode

Provides camera access via Python OpenCV through the Model Context Protocol.

## Setup
```
pip install opencv-python mcp
```

## Run
```
python mcp-cam/server.py
```

## OpenCode Config (`opencode.jsonc`)
```jsonc
{
  "mcp": {
    "mcp-cam": {
      "type": "local",
      "command": ["python", "mcp-cam/server.py"],
      "cwd": ".",
      "enabled": true
    }
  }
}
```
