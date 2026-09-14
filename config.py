"""Runtime configuration for the WeRead automation.

Authentication is accepted only through ``WXREAD_CURL_BASH``. The value is
parsed as data and is never executed as a shell command.
"""

import math
import os
import shlex


READ_INTERVAL_SECONDS = 30
DEFAULT_READ_MINUTES = 68
MAX_READ_MINUTES = 80


def _positive_int(value, name):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} 必须是正整数。") from exc
    if parsed <= 0:
        raise ValueError(f"{name} 必须是正整数。")
    return parsed


def read_count_from_env(environ=None):
    """Return the number of 30-second samples requested by the environment."""
    environ = os.environ if environ is None else environ

    # Keep READ_NUM support for existing local/Docker installations.
    if environ.get("READ_NUM"):
        count = _positive_int(environ["READ_NUM"], "READ_NUM")
        max_count = math.ceil(MAX_READ_MINUTES * 60 / READ_INTERVAL_SECONDS)
        if count > max_count:
            raise ValueError(f"READ_NUM 不能超过 {max_count}。")
        return count

    raw_minutes = environ.get("READ_MINUTES", str(DEFAULT_READ_MINUTES))
    try:
        minutes = float(raw_minutes)
    except (TypeError, ValueError) as exc:
        raise ValueError("READ_MINUTES 必须是数字。") from exc
    if not 0 < minutes <= MAX_READ_MINUTES:
        raise ValueError(f"READ_MINUTES 必须大于 0 且不超过 {MAX_READ_MINUTES}。")
    return math.ceil(minutes * 60 / READ_INTERVAL_SECONDS)


READ_NUM = read_count_from_env()
PUSH_METHOD = os.getenv("PUSH_METHOD", "").strip()
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
WXPUSHER_SPT = os.getenv("WXPUSHER_SPT", "").strip()
SERVERCHAN_SPT = os.getenv("SERVERCHAN_SPT", "").strip()


def _option_value(arguments, index, prefixes):
    argument = arguments[index]
    if argument in prefixes:
        if index + 1 >= len(arguments):
            raise ValueError(f"{argument} 缺少参数。")
        return arguments[index + 1], 2
    for prefix in prefixes:
        marker = prefix + "="
        if argument.startswith(marker):
            return argument[len(marker):], 1
    return None, 1


def convert(curl_command):
    """Extract request headers and cookies from a Bash-format cURL command.

    The command is tokenized with ``shlex`` and is never executed.
    """
    if not curl_command or not curl_command.strip():
        return {}, {}

    try:
        arguments = shlex.split(curl_command, posix=True)
    except ValueError as exc:
        raise ValueError("WXREAD_CURL_BASH 格式无效。") from exc

    extracted_headers = {}
    cookie_strings = []
    index = 0
    while index < len(arguments):
        value, consumed = _option_value(arguments, index, ("-H", "--header"))
        if value is not None:
            if ":" in value:
                name, header_value = value.split(":", 1)
                name = name.strip()
                if name:
                    extracted_headers[name] = header_value.strip()
            index += consumed
            continue

        value, consumed = _option_value(arguments, index, ("-b", "--cookie"))
        if value is not None:
            cookie_strings.append(value)
            index += consumed
            continue
        index += 1

    for name in list(extracted_headers):
        if name.lower() == "cookie":
            cookie_strings.append(extracted_headers.pop(name))

    extracted_cookies = {}
    for cookie_string in cookie_strings:
        for item in cookie_string.split(";"):
            if "=" not in item:
                continue
            name, value = item.split("=", 1)
            if name.strip():
                extracted_cookies[name.strip()] = value.strip()

    return extracted_headers, extracted_cookies


def load_credentials(curl_command=None):
    """Load and minimally validate credentials without exposing their values."""
    curl_command = os.getenv("WXREAD_CURL_BASH") if curl_command is None else curl_command
    parsed_headers, parsed_cookies = convert(curl_command)
    if not parsed_cookies:
        raise ValueError("未配置有效的 WXREAD_CURL_BASH Cookie。")
    if "wr_skey" not in parsed_cookies:
        raise ValueError("WXREAD_CURL_BASH 中缺少 wr_skey Cookie。")
    return parsed_headers, parsed_cookies


# Book/chapter identifiers used by the original project.
book = [
    "36d322f07186022636daa5e", "6f932ec05dd9eb6f96f14b9", "43f3229071984b9343f04a4", "d7732ea0813ab7d58g0184b8",
    "3d03298058a9443d052d409", "4fc328a0729350754fc56d4", "a743220058a92aa746632c0", "140329d0716ce81f140468e",
    "1d9321c0718ff5e11d9afe8", "ff132750727dc0f6ff1f7b5", "e8532a40719c4eb7e851cbe", "9b13257072562b5c9b1c8d6",
]

chapter = [
    "ecc32f3013eccbc87e4b62e", "a87322c014a87ff679a21ea", "e4d32d5015e4da3b7fbb1fa", "16732dc0161679091c5aeb1",
    "8f132430178f14e45fce0f7", "c9f326d018c9f0f895fb5e4", "45c322601945c48cce2e120", "d3d322001ad3d9446802347",
    "65132ca01b6512bd43d90e3", "c20321001cc20ad4d76f5ae", "c51323901dc51ce410c121b", "aab325601eaab3238922e53",
    "9bf32f301f9bf31c7ff0a60", "c7432af0210c74d97b01b1c", "70e32fb021170efdf2eca12", "6f4322302126f4922f45dec",
]

# Request template retained from the upstream project.
data = {
    "appId": "wb182564874603h266381671",
    "b": "ce032b305a9bc1ce0b0dd2a",
    "c": "7f632b502707f6ffaa6bf2e",
    "ci": 27,
    "co": 389,
    "sm": "19聚会《三体》网友的聚会地点是一处僻静",
    "pr": 74,
    "rt": 15,
    "ts": 1744264311434,
    "rn": 466,
    "sg": "2b2ec618394b99deea35104168b86381da9f8946d4bc234e062fa320155409fb",
    "ct": 1744264311,
    "ps": "4ee326507a65a465g015fae",
    "pc": "aab32e207a65a466g010615",
    "s": "36cc0815",
}
