from mcp.server.fastmcp import FastMCP

# 1. Initialize the server
mcp = FastMCP("gis-real")

# 2. Define a tool (This is what your Agent calls)
@mcp.tool()
def get_coordinates(location: str) -> str:
    """Get coordinates for a location (Mock GIS function)"""
    # In the real hackathon, you'd use GeoPandas here
    return f"Coordinates for {location}: 12.9716 N, 77.5946 E (Mock Data)"

# 3. Define another tool (e.g. NDVI)
@mcp.tool()
def calculate_ndvi(lat: float, long: float) -> float:
    """Calculate vegetation health"""
    return 0.75  # Mock healthy value

if __name__ == "__main__":
    # CRITICAL: This starts the loop and keeps the script running!
    mcp.run()