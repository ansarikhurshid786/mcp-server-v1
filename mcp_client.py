from fastmcp import Client


async def connect():
    """
    connect to the MCP Server 
    """

    client = Client("server.py")
    await client.__aenter__()
    print("connnected to MCP Server")
    return client

async def disconnect(client):
    """
    Close the mcp connection
    """

    await client.__aexit__(
        None,
        None,
        None
    )

async def discover_tools(client):
    """
    Retrieve all the tools 
    """

    tools = await client.list_tools()
    return tools


async def execute_tools(
        client,
        tool_name,
        arguments=None
):
    """ Execute a tool"""
    if arguments is None:
        arguments = {}
    result = await client.call_tool(
        tool_name,
        arguments
    )
    return result

if __name__ == "__main__":
    main()