import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from history import History

class RequestScheduler:
    """
    Controls the global request rate.

    All threads share the same scheduler, so only one request is
    allowed during each jitter interval.
    """

    def __init__(self, jitter_min, jitter_max):
        self.jitter_min = jitter_min
        self.jitter_max = jitter_max
        self.next_request = 0
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            now = time.monotonic()

            wait = max(0, self.next_request - now)
            base = max(now, self.next_request)

            self.next_request = (
                base + random.uniform(
                    self.jitter_min,
                    self.jitter_max
                )
            )

        if wait > 0:
            time.sleep(wait)


def read_wordlist(data):
    return data.decode("utf-8").splitlines()


def worker(url, scheduler, timeout, retry, method, cookies, data):
    start = time.monotonic()
    for attempt in range(retry + 1):
        scheduler.wait()

        try:
            if method == "GET":
                response = requests.get(
                    url=url,
                    cookies=cookies,
                    timeout=timeout
                )
            else:
                response = requests.post(
                    url=url,
                    data=data,
                    cookies=cookies,
                    timeout=timeout
                )

            return {
                "url": url,
                "attempts": attempt + 1,
                "status": response.status_code,
                "length": len(response.text),
                "text": "",
                # "text": response.text,
                "cookies": response.cookies.get_dict(),
                "elapsed": response.elapsed.total_seconds(),
                "error": False
            }

        except requests.RequestException as e:
            if attempt == retry:
                return {
                    "url": url,
                    "attempts": attempt + 1,
                    "status": None,
                    "length": 0,
                    "text": "",
                    "cookies": {},
                    "elapsed": time.monotonic() - start,
                    "error": str(e)
                }


def run(config):
    target = config.get("target")
    if target:
        target.strip('/')

    wordlist = set(
        read_wordlist(config.get("wordlist", b""))
    )
    wordlist.add("")

    extensions = set(
        config.get("extensions", [""]).replace(' ', '').split(',')
    )
    extensions.add("")

    cookies = dict(
        config.get("cookies", {})
    )

    data = dict(
        config.get("data", {})
    )

    method = config.get("method", "GET").upper()

    if data:
        method = "POST"

    jitter_min = float(config.get("jitter_min", 0))
    jitter_max = float(config.get("jitter_max", 0))
    timeout = float(config.get("timeout", 1))
    retry = int(config.get("retry", 0))
    threads = int(config.get("threads", 1))

    urls = set()

    for word in wordlist:
        for ext in extensions:
            if not word:
                urls.add(target)
            elif ext:
                urls.add(f"{target}{'/' if not target.endswith('/') else ''}{word}{'.' if not ext.startswith('.') else ''}{ext}")
            else:
                urls.add(f"{target}{'/' if not target.endswith('/') else ''}{word}")

    History.write(root_id=config["root_id"], source_id=config["source_id"], message=f"[web_enum] Starting enum of {len(urls)} endpoints against {target}")

    scheduler = RequestScheduler(jitter_min, jitter_max)

    results = []

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(worker, url, scheduler, timeout, retry, method, cookies, data)
            for url in urls
        ]

        for future in as_completed(futures):
            result = future.result()
            if result['error']:
                History.write(root_id=config["root_id"], source_id=config["source_id"], message=f"[web_enum] {result['error']} {result['url']}")
            else:
                History.write(root_id=config["root_id"], source_id=config["source_id"], message=f"[web_enum] {result['status']:<4} {result['length']:<8} {result['url']}")
            results.append(result)

    return {
        "target": target,
        "results": results
    }