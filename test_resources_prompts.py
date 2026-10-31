import asyncio
from mcp_client import *

async def main():
    client = await connect()

    # ---------------- Resources ----------------
    print()
    print("Available resources")
    print("------------")
    for resource in await client.list_resources():
        print(resource.uri, "-", resource.description)

    print()
    print("Resource templates")
    print("------------")
    for template in await client.list_resource_templates():
        print(template.uri_template, "-", template.description)

    print()
    result = await client.read_resource("info://server")
    print("info://server:", result[0].text)

    result = await client.read_resource("weather://Dubai")
    print("weather://Dubai:", result[0].text)

    # ---------------- Prompts ----------------
    print()
    print("Available prompts")
    print("------------")
    for prompt in await client.list_prompts():
        args = [arg.name for arg in prompt.arguments or []]
        print(prompt.name, args, "-", prompt.description)

    print()
    result = await client.get_prompt("explain_simple", {"topic": "MCP"})
    print("explain_simple:", result.messages[0].content.text)

    print()
    result = await client.get_prompt("translate", {"text": "Good morning", "language": "Arabic"})
    for message in result.messages:
        print(f"[{message.role}] {message.content.text}")

    await disconnect(client)

asyncio.run(main())
