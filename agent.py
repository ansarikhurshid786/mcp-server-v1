from openai import OpenAI
import io
from mcp_client import (
    connect,
    disconnect,
    discover_tools,
    execute_tools
)
import asyncio

# Ollama exposes an OpenAI-compatible API at /v1; the api_key is required by the SDK but ignored by Ollama
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

MODEL = "qwen3.5:0.8b"

async def planner(user_request, tools):
    tool_description = build_tool_description(tools)

    prompt = f""" 
    You are an AI Planner.
    Available tools: 
    {tool_description}
    Instructions:
    1. Select the best tool
    2. Reply only with the tool name
    3. Do not explain 
    User Request: 
    {user_request}
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    tool_name = response.choices[0].message.content
    return tool_name.strip()

async def main():
    #connect mcp server
    client = await connect()
    tools = await discover_tools(client)
    print()
    print("Available tools")
    print("------------")
    for tool in tools:
        print(tool.name)
    
    await disconnect(client)
    user_request = input("User: ")
    tool_name = await planner(
        user_request,
        tools
    )
    print()
    print("Planner selected: ", tool_name)

    tool_result = await execute_tools(client)

def build_tool_description(tools):
    descriptions = ""
    for tool in tools:
        descriptions += f""" 
        Tool: 
        {tool.name}
        Description: 
        {tool.description}
        ---------------------
        """
    return descriptions


if __name__ == "__main__":
    asyncio.run(main())