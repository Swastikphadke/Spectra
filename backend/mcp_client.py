import asyncio
import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --- CONFIGURATION ---
# Adjust paths as necessary for your environment
NASA_MCP_PATH = r"D:\Spectra\NASA-MCP-server\dist\index.js"
GIS_MCP_PATH = r"D:\Spectra\GIS-Real\main.py"
NODE_PATH = r"C:\Program Files\nodejs\node.exe"
PYTHON_PATH = r"D:\Spectra\GIS-Real\.venv\Scripts\python.exe" # Or just "python" if in venv

# --- MCP CLIENT MANAGER ---
class MCPClientManager:
    def __init__(self):
        self.nasa_session = None
        self.gis_session = None
        self.exit_stack = AsyncExitStack()

    async def initialize(self):
        """Starts MCP servers and initializes sessions."""
        print("🔌 Connecting to MCP Servers...")
        
        # 1. NASA MCP
        nasa_params = StdioServerParameters(
            command=NODE_PATH,
            args=[NASA_MCP_PATH],
            env={"NASA_API_KEY": "kWiy0mz0ocWHh1zUIrqfTX6tzfYQRmOfob1ysWw2"} 
        )
        
        # 2. GIS MCP
        gis_params = StdioServerParameters(
            command=PYTHON_PATH,
            args=[GIS_MCP_PATH],
            env={"PYTHONUNBUFFERED": "1"}
        )

        try:
            # Use AsyncExitStack to manage context managers properly
            print("   [1/4] Launching NASA Process...")
            nasa_transport = await self.exit_stack.enter_async_context(stdio_client(nasa_params))
            self.nasa_session = await self.exit_stack.enter_async_context(ClientSession(nasa_transport[0], nasa_transport[1]))
            print("   [1/4] NASA Process Launched.")

            print("   [2/4] Launching GIS Process...")
            gis_transport = await self.exit_stack.enter_async_context(stdio_client(gis_params))
            self.gis_session = await self.exit_stack.enter_async_context(ClientSession(gis_transport[0], gis_transport[1]))
            print("   [2/4] GIS Process Launched.")

            # Initialize
            print("   [3/4] Initializing NASA Session...")
            await asyncio.wait_for(self.nasa_session.initialize(), timeout=5.0)
            print("   [3/4] NASA Session Initialized.")

            print("   [4/4] Initializing GIS Session...")
            await asyncio.wait_for(self.gis_session.initialize(), timeout=5.0)
            print("   [4/4] GIS Session Initialized.")
            
            print("✅ MCP Servers Connected!")
        except Exception as e:
            print(f"❌ MCP Connection Failed: {e}")
            await self.cleanup()

    async def call_nasa_tool(self, tool_name: str, arguments: dict):
        if not self.nasa_session:
            await self.initialize()
        if self.nasa_session:
            return await self.nasa_session.call_tool(tool_name, arguments)
        raise Exception("NASA MCP Session not available")

    async def call_gis_tool(self, tool_name: str, arguments: dict):
        if not self.gis_session:
            await self.initialize()
        if self.gis_session:
            return await self.gis_session.call_tool(tool_name, arguments)
        raise Exception("GIS MCP Session not available")

    async def cleanup(self):
        """Closes connections."""
        print("🔌 Closing MCP Connections...")
        await self.exit_stack.aclose()
        self.nasa_session = None
        self.gis_session = None
        print("🔌 MCP Connections Closed.")

# Global Instance
mcp_manager = MCPClientManager()

async def get_nasa_weather_mcp(lat: float, lon: float):
    """
    Fetches weather data using the NASA MCP Server.
    """
    try:
        import datetime
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(days=7)).strftime("%Y%m%d")
        end_date = today.strftime("%Y%m%d")

        # Using the 'nasa_power' tool from the NASA MCP
        result = await mcp_manager.call_nasa_tool("nasa_power", {
            "latitude": lat,
            "longitude": lon,
            "parameters": "PRECTOTCORR,GWETTOP",
            "community": "AG",
            "start": start_date,
            "end": end_date,
            "format": "json"
        })
        
        # Parse result (MCP returns a specific structure)
        # result usually has 'content' list
        return result.content[0].text

    except Exception as e:
        print(f"MCP Call Failed: {e}")
        return {"error": str(e)}

async def get_gis_data_mcp(location: str):
    try:
        result = await mcp_manager.call_gis_tool("get_coordinates", {"location": location})
        return result.content[0].text
    except Exception as e:
        return {"error": str(e)}

async def get_nasa_apod_mcp():
    """
    Fetches the Astronomy Picture of the Day.
    """
    try:
        result = await mcp_manager.call_nasa_tool("nasa_apod", {})
        return result.content[0].text
    except Exception as e:
        print(f"MCP APOD Call Failed: {e}")
        return {"error": str(e)}
