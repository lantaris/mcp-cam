# mcp-cam — Local MCP Server for OpenCode

Provides camera access via Python OpenCV through the Model Context Protocol.

## Установка

### pip
```
pip install mcp-cam
```

### uv
```
uv pip install mcp-cam
```

### uvx
```
uvx mcp-cam
```

## Run
```
python mcp-cam/server.py
```

or

```
uvx mcp-cam
```

## OpenCode Config (`opencode.jsonc`)
```jsonc
{
  "mcp": {
    "mcp-cam": {
      "type": "local",
      "command": ["uvx", "mcp-cam"],
      "cwd": ".",
      "enabled": true
    }
  }
}
```
