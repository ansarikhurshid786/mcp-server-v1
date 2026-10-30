import asyncio
from mcp_client import *

async def main():
    client = await connect()
    tools = await discover_tools(client)
    print()
    print("Available tools")
    print("------------")

    for tool in tools:
        print(tool.name)
    print()
    result = await execute_tools(
        client,
        "roll_dice"
    )
    print("Dice Result:", result.content[0].text)

asyncio.run(main())
