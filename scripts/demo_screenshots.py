"""demo_screenshots.py

Opens the demo page in a Chromium-based browser at 1440 by 900, saves a screenshot of three
pages, and fails when a page's content is taller than the window.

    python scripts/demo_screenshots.py                       # demo.duckdb, screenshots/
    python scripts/demo_screenshots.py --file FILE --out DIR

The pages are the convention hotel on day 10, the airport hotel on day 20 and the full-service
hotel on day 30. The script starts the page's Streamlit server on a free port, drives the
browser headless over the DevTools pipe, and needs no package beyond the standard library and
Streamlit. The browser is the first found of: the path in HOTEL_MARKET_BROWSER, a Chromium under
/Applications or in Playwright's cache, Google Chrome, or a chromium or chrome on the PATH. The
content height is the bottom edge of the page's main block, the title to the scorecard, which
must fit in the window with nothing cut off.
"""

from __future__ import annotations

import argparse
import base64
import glob
import json
import os
import select
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "src" / "hotel_market" / "demo_page.py"
WIDTH, HEIGHT = 1440, 900
PAGES = (("convention", 10), ("airport", 20), ("full-service", 30))  # (hotel key, day)
BROWSER_VARIABLE = "HOTEL_MARKET_BROWSER"
BROWSERS = (
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    str(
        Path.home()
        / "Library/Caches/ms-playwright/chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium"
    ),
    str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux*/chrome"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "chromium",
    "chromium-browser",
    "google-chrome",
    "chrome",
)
RENDER_TIMEOUT = 90  # seconds for a page to render and settle

# What the browser measures once the page has rendered. The content height is the bottom edge of
# the main block, which holds everything from the title to the scorecard. Streamlit scrolls the
# main section, so its scroll height says whether anything is cut off.
MEASURE = """(() => {
  const main = document.querySelector('[data-testid="stMain"]');
  const block = document.querySelector('[data-testid="stMainBlockContainer"]');
  const chart = '[data-testid="stVegaLiteChart"]';
  const charts = document.querySelectorAll(chart + ' canvas, ' + chart + ' svg');
  const scrolled = main ? main.scrollTop : 0;
  return JSON.stringify({
    window: window.innerHeight,
    content: block ? Math.ceil(block.getBoundingClientRect().bottom + scrolled) : null,
    scroll: main ? main.scrollHeight : document.documentElement.scrollHeight,
    visible: main ? main.clientHeight : document.documentElement.clientHeight,
    running: document.querySelector('[data-testid="stStatusWidget"]') !== null,
    charts: charts.length,
    metrics: document.querySelectorAll('[data-testid="stMetric"]').length,
  });
})()"""


def find_browser(environ: dict | None = None) -> str | None:
    """The first Chromium-based browser found, or None."""
    environ = os.environ if environ is None else environ
    named = environ.get(BROWSER_VARIABLE)
    candidates = [named] if named else list(BROWSERS)
    for candidate in candidates:
        if os.sep in candidate:
            found = sorted(glob.glob(candidate))
            if found:
                return found[-1]
        elif shutil.which(candidate):
            return shutil.which(candidate)
    return None


def too_tall(measured: dict) -> bool:
    """Whether the content is taller than the window or the main section scrolls."""
    return measured["content"] > measured["window"] or measured["scroll"] > measured["visible"]


class Browser:
    """A headless Chromium-based browser driven over the DevTools pipe: commands go to its file
    descriptor 3 and answers come back on 4, each a JSON message ended by a NUL byte."""

    def __init__(self, path: str, width: int = WIDTH, height: int = HEIGHT):
        to_browser_read, to_browser_write = os.pipe()
        from_browser_read, from_browser_write = os.pipe()
        self.profile = tempfile.mkdtemp(prefix="hotel-market-browser-")

        def wire() -> None:  # in the child, before exec: the pipe ends become 3 and 4
            out = from_browser_write
            if out == 3:
                out = os.dup(out)
            os.dup2(to_browser_read, 3)
            os.dup2(out, 4)
            os.set_inheritable(3, True)  # dup2 onto itself keeps close-on-exec
            os.set_inheritable(4, True)

        self.process = subprocess.Popen(
            [
                path,
                "--headless=new",
                "--remote-debugging-pipe",
                f"--window-size={width},{height}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--user-data-dir={self.profile}",
                "about:blank",
            ],
            preexec_fn=wire,
            close_fds=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.close(to_browser_read)
        os.close(from_browser_write)
        self.writer, self.reader = to_browser_write, from_browser_read
        self.buffer = b""
        self.last_id = 0
        self.session = None
        target = self.send("Target.createTarget", {"url": "about:blank"})["targetId"]
        self.session = self.send("Target.attachToTarget", {"targetId": target, "flatten": True})[
            "sessionId"
        ]
        self.send(
            "Emulation.setDeviceMetricsOverride",
            {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False},
        )
        self.send("Page.enable")

    def send(self, method: str, params: dict | None = None, timeout: float = 30) -> dict:
        """One command, answered. Commands after the attach go to the page's session."""
        self.last_id += 1
        message = {"id": self.last_id, "method": method, "params": params or {}}
        if self.session is not None:
            message["sessionId"] = self.session
        os.write(self.writer, json.dumps(message).encode() + b"\0")
        deadline = time.monotonic() + timeout
        while True:
            while b"\0" in self.buffer:
                raw, self.buffer = self.buffer.split(b"\0", 1)
                answer = json.loads(raw)
                if answer.get("id") == self.last_id:
                    if "error" in answer:
                        raise RuntimeError(f"{method}: {answer['error']}")
                    return answer.get("result", {})
            ready, _, _ = select.select(
                [self.reader], [], [], max(0.0, deadline - time.monotonic())
            )
            if not ready:
                raise TimeoutError(f"the browser did not answer {method} in {timeout}s")
            chunk = os.read(self.reader, 1 << 16)
            if not chunk:
                raise RuntimeError("the browser closed the pipe")
            self.buffer += chunk

    def evaluate(self, expression: str):
        return self.send("Runtime.evaluate", {"expression": expression, "returnByValue": True})[
            "result"
        ]["value"]

    def open(self, url: str, timeout: float = RENDER_TIMEOUT) -> dict:
        """Navigate, then wait until the page has rendered its charts and metrics and the
        measurements stop changing. Returns the measurements."""
        self.send("Page.navigate", {"url": url})
        deadline = time.monotonic() + timeout
        last = None
        while time.monotonic() < deadline:
            time.sleep(0.5)
            measured = json.loads(self.evaluate(MEASURE))
            rendered = not measured["running"] and measured["charts"] and measured["metrics"]
            if rendered and measured == last:
                return measured
            last = measured
        raise TimeoutError(f"{url} did not finish rendering in {timeout}s")

    def screenshot(self, path: Path) -> None:
        shot = self.send("Page.captureScreenshot", {"format": "png"})
        path.write_bytes(base64.b64decode(shot["data"]))

    def close(self) -> None:
        try:
            self.session = None
            self.send("Browser.close", timeout=5)
        except Exception:
            self.process.kill()
        self.process.wait(timeout=10)
        os.close(self.writer)
        os.close(self.reader)
        shutil.rmtree(self.profile, ignore_errors=True)


def free_port() -> int:
    with socket.socket() as opened:
        opened.bind(("127.0.0.1", 0))
        return opened.getsockname()[1]


def start_server(file: Path, port: int) -> subprocess.Popen:
    """The page's Streamlit server, headless, on the port; returns once it answers."""
    environment = dict(os.environ, HOTEL_MARKET_DEMO_FILE=str(file))
    process = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", str(PAGE),
            "--server.headless", "true",
            "--server.port", str(port),
            "--server.fileWatcherType", "none",
            "--browser.gatherUsageStats", "false",
        ],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )  # fmt: skip
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("the Streamlit server stopped; is the demo extra installed?")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return process
        except OSError:
            time.sleep(0.25)
    process.kill()
    raise TimeoutError("the Streamlit server did not start in 60s")


def shoot(file: Path, out: Path, browser_path: str) -> list[tuple[str, int, dict, Path]]:
    """Each page's measurements and screenshot path."""
    out.mkdir(parents=True, exist_ok=True)
    port = free_port()
    server = start_server(file, port)
    browser = None
    results = []
    try:
        browser = Browser(browser_path)
        for hotel, day in PAGES:
            measured = browser.open(f"http://127.0.0.1:{port}/?hotel={hotel}&day={day}")
            path = out / f"{hotel}-day{day}.png"
            browser.screenshot(path)
            results.append((hotel, day, measured, path))
    finally:
        if browser is not None:
            browser.close()
        server.terminate()
        server.wait(timeout=10)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Screenshot the demo page at 1440 by 900 and fail when its content is "
        "taller than the window."
    )
    parser.add_argument("--file", type=Path, default=Path("demo.duckdb"), help="the demo file")
    parser.add_argument(
        "--out", type=Path, default=Path("screenshots"), help="where the screenshots go"
    )
    args = parser.parse_args(argv)
    if not args.file.exists():
        print(f"{args.file} is not there. Run: hotel-market demo-data --seed 7 --out {args.file}")
        return 2
    browser_path = find_browser()
    if browser_path is None:
        print(f"No Chromium-based browser found; set {BROWSER_VARIABLE} to one.")
        return 2
    print(f"Browser: {browser_path}")
    failed = False
    for hotel, day, measured, path in shoot(args.file, args.out, browser_path):
        verdict = "too tall" if too_tall(measured) else "fits"
        failed = failed or too_tall(measured)
        print(
            f"{hotel} day {day}: content {measured['content']} px of {measured['window']} "
            f"({verdict}), {path}"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
