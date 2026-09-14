"""Submit timed reading samples to the WeRead web API."""

import hashlib
import json
import logging
import random
import sys
import time
import urllib.parse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import (
    PUSH_METHOD,
    READ_INTERVAL_SECONDS,
    READ_NUM,
    book,
    chapter,
    data,
    load_credentials,
)
from log_utils import setup_logging
from push import push


KEY = "3c5c8717f3daf09iop3423zafeqoi"
READ_URL = "https://weread.qq.com/web/book/read"
RENEW_URL = "https://weread.qq.com/web/login/renewal"
FIX_SYNCKEY_URL = "https://weread.qq.com/web/book/chapterInfos"
COOKIE_DATA_VARIANTS = (
    {"rq": "%2Fweb%2Fbook%2Fread", "ql": False},
    {"rq": "%2Fweb%2Fbook%2Fread", "ql": True},
    {"rq": "%2Fweb%2Fbook%2Fread"},
)
REQUEST_TIMEOUT = (5, 20)
MAX_CONSECUTIVE_FAILURES = 5


def encode_data(payload):
    """Encode request data in the ordering expected by WeRead."""
    return "&".join(
        f"{key}={urllib.parse.quote(str(payload[key]), safe='')}"
        for key in sorted(payload)
    )


def cal_hash(input_string):
    """Calculate the checksum used by the WeRead web client."""
    left = 0x15051505
    right = left
    length = len(input_string)
    index = length - 1

    while index > 0:
        left = 0x7FFFFFFF & (
            left ^ ord(input_string[index]) << (length - index) % 30
        )
        right = 0x7FFFFFFF & (
            right ^ ord(input_string[index - 1]) << index % 30
        )
        index -= 2

    return hex(left + right)[2:].lower()


def build_session(headers, cookies):
    """Create a bounded-retry HTTP session."""
    retries = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"POST"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session = requests.Session()
    session.mount("https://", adapter)
    session.headers.update(headers)
    for name, value in cookies.items():
        session.cookies.set(name, value, domain=".weread.qq.com", path="/")
    return session


def refresh_cookie(session):
    """Refresh the session key without logging any credential value."""
    logging.info("正在刷新登录凭据。")
    for cookie_data in COOKIE_DATA_VARIANTS:
        try:
            response = session.post(
                RENEW_URL,
                data=json.dumps(cookie_data, separators=(",", ":")),
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException:
            logging.warning("刷新登录凭据的请求失败，正在尝试下一种方式。")
            continue

        if any(cookie.name == "wr_skey" and cookie.value for cookie in response.cookies):
            # requests has already merged the Set-Cookie response into the session.
            logging.info("登录凭据刷新成功。")
            return

    raise RuntimeError("无法刷新登录凭据，请重新获取 WXREAD_CURL_BASH。")


def fix_no_synckey(session):
    """Ask WeRead for chapter metadata when a read response lacks synckey."""
    response = session.post(
        FIX_SYNCKEY_URL,
        data=json.dumps({"bookIds": ["3300060341"]}, separators=(",", ":")),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def post_read_sample(session, payload):
    response = session.post(
        READ_URL,
        data=json.dumps(payload, separators=(",", ":")),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    try:
        result = response.json()
    except requests.JSONDecodeError as exc:
        raise RuntimeError("阅读接口返回了无效响应。") from exc
    if not isinstance(result, dict):
        raise RuntimeError("阅读接口返回了无效响应。")
    return result


def make_payload(template, last_time):
    payload = template.copy()
    this_time = int(time.time())
    payload["b"] = random.choice(book)
    payload["c"] = random.choice(chapter)
    payload["ct"] = this_time
    payload["rt"] = max(1, this_time - last_time)
    payload["ts"] = int(this_time * 1000) + random.randint(0, 1000)
    payload["rn"] = random.randint(0, 1000)
    payload["sg"] = hashlib.sha256(
        f"{payload['ts']}{payload['rn']}{KEY}".encode()
    ).hexdigest()
    payload.pop("s", None)
    payload["s"] = cal_hash(encode_data(payload))
    return payload, this_time


def run():
    refresh_print = setup_logging()
    headers, cookies = load_credentials()
    session = build_session(headers, cookies)

    try:
        refresh_cookie(session)
        logging.info(
            "计划提交 %d 次阅读记录，目标时长 %.1f 分钟。",
            READ_NUM,
            READ_NUM * READ_INTERVAL_SECONDS / 60,
        )

        completed = 0
        consecutive_failures = 0
        last_time = int(time.time()) - READ_INTERVAL_SECONDS

        while completed < READ_NUM:
            payload, this_time = make_payload(data, last_time)
            try:
                result = post_read_sample(session, payload)
                if result.get("succ") and "synckey" in result:
                    completed += 1
                    consecutive_failures = 0
                    last_time = this_time
                    refresh_print(
                        f"阅读进度: {completed}/{READ_NUM}，"
                        f"已完成 {completed * READ_INTERVAL_SECONDS / 60:.1f} 分钟"
                    )
                    if completed < READ_NUM:
                        time.sleep(READ_INTERVAL_SECONDS)
                    continue

                consecutive_failures += 1
                if result.get("succ"):
                    logging.warning("响应缺少同步标记，正在尝试修复。")
                    fix_no_synckey(session)
                else:
                    logging.warning("阅读请求未被接受，正在刷新登录凭据。")
                    refresh_cookie(session)
            except (requests.RequestException, RuntimeError):
                consecutive_failures += 1
                logging.warning("阅读请求失败，将进行有限次数重试。")

            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                raise RuntimeError(
                    f"连续 {MAX_CONSECUTIVE_FAILURES} 次请求失败，已安全终止。"
                )
            time.sleep(2)

        logging.info("阅读脚本已完成。")
        if PUSH_METHOD:
            push(
                "微信读书自动阅读完成。\n"
                f"阅读时长：{completed * READ_INTERVAL_SECONDS / 60:.1f} 分钟。",
                PUSH_METHOD,
                is_success=True,
            )
    finally:
        session.close()


def main():
    try:
        run()
    except (ValueError, RuntimeError) as exc:
        logging.error("运行失败：%s", exc)
        if PUSH_METHOD:
            push("微信读书自动阅读失败，请检查 Actions 日志。", PUSH_METHOD, is_success=False)
        return 1
    except requests.RequestException:
        # Request exceptions can include headers or URLs; omit their details.
        logging.error("运行失败：网络请求异常，详细信息已隐藏。")
        if PUSH_METHOD:
            push("微信读书自动阅读失败，请检查 Actions 日志。", PUSH_METHOD, is_success=False)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
