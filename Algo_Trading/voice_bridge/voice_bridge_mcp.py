import asyncio
import json
import os
from datetime import datetime
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

INSTRUCTION_FILE = os.path.join(os.path.dirname(__file__), "instructions.txt")

async def main():
    server = Server("voice-bridge")

    @server.call_tool()
    async def handle_write_instruction(name: str, arguments: dict):
        if name == "write_instruction":
            instruction = arguments.get("instruction", "")
            try:
                with open(INSTRUCTION_FILE, 'w') as f:
                    f.write(instruction)
                return [TextContent(
                    type="text",
                    text=f"✅ Instruction written\nTime: {datetime.now().isoformat()}"
                )]
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
        return [TextContent(type="text", text="Unknown tool")]

    @server.list_tools()
    async def list_tools():
        return [Tool(
            name="write_instruction",
            description="Write instruction to instructions.txt",
            inputSchema={
                "type": "object",
                "properties": {
                    "instruction": {
                        "type": "string",
                        "description": "Instruction to write"
                    }
                },
                "required": ["instruction"]
            }
        )]

    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
