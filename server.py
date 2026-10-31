import random
import secrets
import string
from datetime import datetime
from fastmcp import FastMCP

mcp = FastMCP(
    "MCP Server - has few tools"
)

@mcp.tool()
def current_time():
    """ Return current date and time """

    return datetime.now().strftime(
        "%d-%m-%y %H%M%S"
    )

@mcp.tool()
def roll_dice(sides: int = 6):
    """ Roll a dice and return the result """

    return random.randint(1, sides)

@mcp.tool()
def generate_password(length: int = 12):
    """ Generate a random password """

    chars = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(chars) for _ in range(length))

if __name__ == "__main__":
    print("start the mcp time server")
    mcp.run()
