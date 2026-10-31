import ast
import base64
import csv
import difflib
import hashlib
import io
import json
import math
import operator
import random
import re
import secrets
import socket
import ssl
import statistics
import string
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import certifi
from fastmcp import FastMCP
from fastmcp.prompts import Message

mcp = FastMCP(
    "MCP Server - has few tools"
)

# ---------------- Date & time ----------------

@mcp.tool()
def current_time():
    """ Return current date and time """

    return datetime.now().strftime(
        "%d-%m-%y %H%M%S"
    )

@mcp.tool()
def time_in_timezone(timezone: str = "UTC"):
    """ Return the current time in a timezone, e.g. 'Asia/Dubai', 'Europe/London', 'America/New_York' """

    return datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d %H:%M:%S %Z")

@mcp.tool()
def convert_timezone(time: str, from_timezone: str, to_timezone: str):
    """ Convert a time 'YYYY-MM-DD HH:MM' from one timezone to another """

    dt = datetime.strptime(time, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(from_timezone))
    return dt.astimezone(ZoneInfo(to_timezone)).strftime("%Y-%m-%d %H:%M %Z")

@mcp.tool()
def days_between(start_date: str, end_date: str):
    """ Count the days between two dates in 'YYYY-MM-DD' format """

    delta = date.fromisoformat(end_date) - date.fromisoformat(start_date)
    return {"days": delta.days, "weeks": round(delta.days / 7, 2)}

@mcp.tool()
def add_days(start_date: str, days: int):
    """ Add (or subtract, with a negative number) days to a 'YYYY-MM-DD' date """

    result = date.fromisoformat(start_date) + timedelta(days=days)
    return {"date": result.isoformat(), "weekday": result.strftime("%A")}

@mcp.tool()
def calculate_age(birth_date: str):
    """ Calculate age in years from a birth date in 'YYYY-MM-DD' format """

    born = date.fromisoformat(birth_date)
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

# ---------------- Math & numbers ----------------

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}
_FUNCTIONS = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "log": math.log, "log10": math.log10, "abs": abs, "round": round,
    "pi": math.pi, "e": math.e,
}

def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.Name) and node.id in _FUNCTIONS:
        return _FUNCTIONS[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS:
        return _FUNCTIONS[node.func.id](*[_safe_eval(arg) for arg in node.args])
    raise ValueError("Unsupported expression")

@mcp.tool()
def calculate(expression: str):
    """ Safely evaluate a math expression, e.g. '(2 + 3) * 4', 'sqrt(16) + 2**3' """

    return _safe_eval(ast.parse(expression, mode="eval").body)

_UNITS = {
    # length (base: meter)
    "mm": ("length", 0.001), "cm": ("length", 0.01), "m": ("length", 1), "km": ("length", 1000),
    "in": ("length", 0.0254), "ft": ("length", 0.3048), "yd": ("length", 0.9144), "mi": ("length", 1609.344),
    # weight (base: kilogram)
    "mg": ("weight", 1e-6), "g": ("weight", 0.001), "kg": ("weight", 1),
    "oz": ("weight", 0.0283495), "lb": ("weight", 0.453592),
    # volume (base: liter)
    "ml": ("volume", 0.001), "l": ("volume", 1), "gal": ("volume", 3.78541),
}

@mcp.tool()
def convert_units(value: float, from_unit: str, to_unit: str):
    """ Convert length (mm, cm, m, km, in, ft, yd, mi), weight (mg, g, kg, oz, lb),
    volume (ml, l, gal) or temperature (c, f, k) """

    f, t = from_unit.lower(), to_unit.lower()
    temps = {"c", "f", "k"}
    if f in temps and t in temps:
        celsius = {"c": value, "f": (value - 32) * 5 / 9, "k": value - 273.15}[f]
        result = {"c": celsius, "f": celsius * 9 / 5 + 32, "k": celsius + 273.15}[t]
        return round(result, 4)
    if _UNITS[f][0] != _UNITS[t][0]:
        raise ValueError(f"Cannot convert {_UNITS[f][0]} to {_UNITS[t][0]}")
    return round(value * _UNITS[f][1] / _UNITS[t][1], 6)

@mcp.tool()
def percentage(value: float, total: float):
    """ Return what percentage 'value' is of 'total' """

    return round(value / total * 100, 2)

@mcp.tool()
def percentage_change(old_value: float, new_value: float):
    """ Return the percentage increase or decrease from old_value to new_value """

    return round((new_value - old_value) / old_value * 100, 2)

@mcp.tool()
def number_stats(numbers: list[float]):
    """ Return count, sum, min, max, mean, median and standard deviation of a list of numbers """

    return {
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mean": round(statistics.mean(numbers), 4),
        "median": statistics.median(numbers),
        "stdev": round(statistics.stdev(numbers), 4) if len(numbers) > 1 else 0,
    }

@mcp.tool()
def prime_factors(number: int):
    """ Check if a number is prime and return its prime factors """

    factors, n, d = [], number, 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return {"is_prime": factors == [number], "factors": factors}

@mcp.tool()
def loan_emi(principal: float, annual_interest_rate: float, months: int):
    """ Calculate monthly loan EMI, total payment and total interest """

    r = annual_interest_rate / 12 / 100
    emi = principal / months if r == 0 else principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    return {
        "monthly_emi": round(emi, 2),
        "total_payment": round(emi * months, 2),
        "total_interest": round(emi * months - principal, 2),
    }

@mcp.tool()
def bmi(weight_kg: float, height_cm: float):
    """ Calculate Body Mass Index and its category """

    value = weight_kg / (height_cm / 100) ** 2
    if value < 18.5:
        category = "Underweight"
    elif value < 25:
        category = "Normal"
    elif value < 30:
        category = "Overweight"
    else:
        category = "Obese"
    return {"bmi": round(value, 1), "category": category}

# ---------------- Text ----------------

@mcp.tool()
def text_stats(text: str):
    """ Count words, characters, sentences and estimated reading time of a text """

    words = len(text.split())
    return {
        "words": words,
        "characters": len(text),
        "characters_no_spaces": len(re.sub(r"\s", "", text)),
        "sentences": len(re.findall(r"[.!?]+", text)) or (1 if text.strip() else 0),
        "reading_time_minutes": round(words / 200, 1),
    }

@mcp.tool()
def change_case(text: str, mode: str = "upper"):
    """ Change text case. mode: upper, lower, title, sentence, snake, camel, kebab """

    words = re.findall(r"[A-Za-z0-9]+", text)
    cases = {
        "upper": lambda: text.upper(),
        "lower": lambda: text.lower(),
        "title": lambda: text.title(),
        "sentence": lambda: text[:1].upper() + text[1:].lower(),
        "snake": lambda: "_".join(w.lower() for w in words),
        "kebab": lambda: "-".join(w.lower() for w in words),
        "camel": lambda: words[0].lower() + "".join(w.capitalize() for w in words[1:]) if words else "",
    }
    return cases[mode]()

@mcp.tool()
def slugify(text: str):
    """ Convert text into a URL-friendly slug """

    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

@mcp.tool()
def compare_texts(text_a: str, text_b: str):
    """ Compare two texts, return a similarity score and a line-by-line diff """

    diff = difflib.unified_diff(text_a.splitlines(), text_b.splitlines(), "text_a", "text_b", lineterm="")
    return {
        "similarity_percent": round(difflib.SequenceMatcher(None, text_a, text_b).ratio() * 100, 2),
        "diff": "\n".join(diff),
    }

@mcp.tool()
def regex_search(pattern: str, text: str):
    """ Find all matches of a regular expression in a text """

    return [m.group(0) for m in re.finditer(pattern, text)]

@mcp.tool()
def extract_contacts(text: str):
    """ Extract email addresses, URLs and phone numbers from a text """

    return {
        "emails": re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text),
        "urls": re.findall(r"https?://[^\s,;)\"']+", text),
        "phones": re.findall(r"\+?\d[\d\s-]{7,}\d", text),
    }

# ---------------- Developer & encoding ----------------

@mcp.tool()
def hash_text(text: str, algorithm: str = "sha256"):
    """ Hash a text with md5, sha1, sha256 or sha512 """

    return hashlib.new(algorithm, text.encode()).hexdigest()

@mcp.tool()
def base64_convert(text: str, mode: str = "encode"):
    """ Base64 encode or decode a text. mode: encode or decode """

    if mode == "decode":
        return base64.b64decode(text).decode()
    return base64.b64encode(text.encode()).decode()

@mcp.tool()
def url_convert(text: str, mode: str = "encode"):
    """ URL encode or decode a text. mode: encode or decode """

    if mode == "decode":
        return urllib.parse.unquote_plus(text)
    return urllib.parse.quote_plus(text)

@mcp.tool()
def generate_uuid(count: int = 1):
    """ Generate one or more random UUIDs """

    return [str(uuid.uuid4()) for _ in range(count)]

@mcp.tool()
def decode_jwt(token: str):
    """ Decode a JWT token header and payload (without verifying the signature) """

    def _part(segment):
        return json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))

    header, payload, _ = token.split(".")
    return {"header": _part(header), "payload": _part(payload)}

@mcp.tool()
def format_json(json_text: str, indent: int = 2):
    """ Validate and pretty-print a JSON string """

    return json.dumps(json.loads(json_text), indent=indent, ensure_ascii=False)

@mcp.tool()
def csv_to_json(csv_text: str):
    """ Convert CSV text (with a header row) into a list of JSON objects """

    return list(csv.DictReader(io.StringIO(csv_text)))

@mcp.tool()
def generate_password(length: int = 12):
    """ Generate a random password """

    chars = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(chars) for _ in range(length))

@mcp.tool()
def password_strength(password: str):
    """ Check how strong a password is and give tips to improve it """

    checks = {
        "at least 12 characters": len(password) >= 12,
        "lowercase letter": bool(re.search(r"[a-z]", password)),
        "uppercase letter": bool(re.search(r"[A-Z]", password)),
        "digit": bool(re.search(r"\d", password)),
        "symbol": bool(re.search(r"[^A-Za-z0-9]", password)),
    }
    score = sum(checks.values())
    return {
        "score": f"{score}/5",
        "strength": ["Very weak", "Very weak", "Weak", "Medium", "Strong", "Very strong"][score],
        "missing": [name for name, ok in checks.items() if not ok],
    }

# ---------------- Random ----------------

@mcp.tool()
def roll_dice(sides: int = 6):
    """ Roll a dice and return the result """

    return random.randint(1, sides)

@mcp.tool()
def flip_coin():
    """ Flip a coin and return Heads or Tails """

    return random.choice(["Heads", "Tails"])

@mcp.tool()
def random_pick(options: list[str], count: int = 1):
    """ Randomly pick one or more items from a list of options """

    return random.sample(options, count)

# ---------------- Internet ----------------

# python.org builds on macOS ship without CA certificates, so use certifi's bundle
_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

def _open(url):
    request = urllib.request.Request(url, headers={"User-Agent": "mcp-server"})
    return urllib.request.urlopen(request, timeout=10, context=_SSL_CONTEXT)

def _get_json(url):
    with _open(url) as response:
        return json.loads(response.read())

@mcp.tool()
def get_weather(city: str):
    """ Get the current weather for a city """

    query = urllib.parse.urlencode({"name": city, "count": 1})
    places = _get_json(f"https://geocoding-api.open-meteo.com/v1/search?{query}").get("results")
    if not places:
        return f"City '{city}' not found"
    place = places[0]
    params = urllib.parse.urlencode({
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m",
    })
    current = _get_json(f"https://api.open-meteo.com/v1/forecast?{params}")["current"]
    return {
        "location": f"{place['name']}, {place.get('country', '')}",
        "temperature_c": current["temperature_2m"],
        "feels_like_c": current["apparent_temperature"],
        "humidity_percent": current["relative_humidity_2m"],
        "wind_kmh": current["wind_speed_10m"],
    }

@mcp.tool()
def check_website(url: str):
    """ Check if a website is up and return its status code and response time """

    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    start = datetime.now()
    try:
        with _open(url) as response:
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
    except Exception as error:
        return {"url": url, "up": False, "error": str(error)}
    return {
        "url": url,
        "up": status < 400,
        "status_code": status,
        "response_ms": int((datetime.now() - start).total_seconds() * 1000),
    }

@mcp.tool()
def dns_lookup(hostname: str):
    """ Look up the IP addresses of a domain name """

    infos = socket.getaddrinfo(hostname, None)
    return sorted({info[4][0] for info in infos})

# ---------------- Resources ----------------
# Read-only data the client app can load by URI (the model does not "call" these)

@mcp.resource("info://server")
def server_info():
    """ Basic information about this MCP server """

    return {
        "name": "MCP Server - has few tools",
        "version": "1.0",
        "author": "Khurshid Ansari",
        "features": ["tools", "resources", "prompts"],
    }

@mcp.resource("info://units")
def supported_units():
    """ Units supported by the convert_units tool, grouped by type """

    groups = {"temperature": ["c", "f", "k"]}
    for unit, (kind, _) in _UNITS.items():
        groups.setdefault(kind, []).append(unit)
    return groups

@mcp.resource("info://timezones")
def common_timezones():
    """ Common timezone names to use with the time tools """

    return [
        "UTC", "Asia/Dubai", "Asia/Kolkata", "Asia/Karachi", "Asia/Riyadh",
        "Asia/Tokyo", "Asia/Singapore", "Europe/London", "Europe/Paris",
        "America/New_York", "America/Los_Angeles", "Australia/Sydney",
    ]

# Resource template: {city} in the URI becomes the function argument
@mcp.resource("weather://{city}")
def weather_resource(city: str):
    """ Current weather for a city, e.g. weather://Dubai """

    return get_weather(city)

@mcp.resource("time://{timezone}")
def time_resource(timezone: str):
    """ Current time in a timezone, e.g. time://UTC """

    return time_in_timezone(timezone)

# ---------------- Prompts ----------------
# Reusable prompt templates the user can pick (e.g. as slash commands)

@mcp.prompt()
def code_review(code: str, language: str = "python"):
    """ Review code for bugs, security issues and readability """

    return (
        f"You are a senior {language} developer. Review the code below.\n"
        "List bugs first, then security issues, then readability improvements.\n"
        "For each point show the line and a fixed version.\n\n"
        f"```{language}\n{code}\n```"
    )

@mcp.prompt()
def explain_simple(topic: str):
    """ Explain a topic in simple words for a beginner """

    return f"Explain {topic} in simple words for a beginner, with one real-life example and a short summary."

@mcp.prompt()
def summarize(text: str, max_words: int = 100):
    """ Summarize a text into bullet points """

    return f"Summarize the text below in at most {max_words} words, as bullet points.\n\n{text}"

@mcp.prompt()
def translate(text: str, language: str = "Arabic"):
    """ Translate a text into another language """

    # A prompt can return several messages to set up a conversation
    return [
        Message(f"You are a professional translator. Translate everything I send into {language}. "
                "Reply with the translation only."),
        Message(f"Understood. Send the text and I will translate it into {language}.", role="assistant"),
        Message(text),
    ]

@mcp.prompt()
def trip_planner(city: str, days: int = 3):
    """ Plan a trip, telling the model which tools of this server to use """

    return (
        f"Plan a {days}-day trip to {city}.\n"
        f"1. Use the get_weather tool to check the weather in {city}.\n"
        f"2. Use the time_in_timezone tool to tell me the local time there.\n"
        "3. Suggest a day-by-day plan that suits the weather."
    )

if __name__ == "__main__":
    print("start the mcp time server")
    mcp.run()
