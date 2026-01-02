# MCP Time Server - Installation Instructions

## Installation Steps

1. **Download the package** (mcp-time-server-1.0.0.tgz)

2. **Install globally on Windows:**
   ```powershell
   npm install -g C:\Users\saurav\Downloads\mcp-time-server-1.0.0.tgz
   ```
   (Adjust path to where you downloaded the file)

3. **Update Claude Desktop config:**
   Edit: `%APPDATA%\Claude\claude_desktop_config.json`
   
   Replace your current config with:
   ```json
{
    "mcpServers": {
        "kite": {
            "command": "npx",
            "args": ["mcp-remote", "https://mcp.kite.trade/mcp"]
        },
        "time": {
            "command": "mcp-time-server"
        }
    }
}
   ```

4. **Restart Claude Desktop**

5. **Test it** by asking: "What's the current time?"

## Available Tools

- `get_current_time` - Current time in IST
- `get_current_date` - Current date in IST  
- `get_datetime` - Full date and time in IST

## Troubleshooting

If it doesn't work:
1. Check if installed: `npm list -g mcp-time-server`
2. Find install path: `npm root -g`
3. Check Claude logs: Click "Open Logs Folder" in MCP settings
