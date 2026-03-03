#!/usr/bin/env python3
import argparse
import concurrent.futures
import os
import platform
import re
import socket
import subprocess
import sys
import time
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, urlunparse
from tqdm import tqdm
from configparser import ConfigParser

try:
    import requests
except Exception:
    requests = None

DEFAULT_SOURCES = [
    "https://gcore.jsdelivr.net/gh/XIU2/TrackersListCollection@master/best.txt",
    "https://cf.trackerslist.com/all.txt",
    "https://down.adysec.com/trackers_all.txt",
    "https://cdn.jsdelivr.net/gh/ngosang/trackerslist@master/trackers_all.txt",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch HTTP/HTTPS trackers, probe hosts/ports (TCP or ping), sort by RTT, and output Tracker.txt",
    )
    parser.add_argument(
        "--sources",
        type=str,
        default="",
        help=(
            "Comma-separated list of HTTP(S) URLs or local file paths containing trackers. "
            "If omitted, will read from --config (sources.ini) when available, otherwise use built-in defaults."
        ),
    )
    parser.add_argument("--config", type=str, default="sources.ini", help="Config file path for sources (plain lines or INI [sources] section)")
    parser.add_argument("--timeout", type=int, default=1000, help="Probe timeout per attempt (ms)")
    parser.add_argument("--retries", type=int, default=1, help="Retry attempts per host/port")
    parser.add_argument(
        "--concurrency", type=int, default=64, help="Number of concurrent workers"
    )
    parser.add_argument(
        "--icmp-count", type=int, default=3, help="ICMP echo count per ping command"
    )
    parser.add_argument(
        "--probe",
        type=str,
        choices=["tcp", "ping", "mixed"],
        default="tcp",
        help="Probe method: tcp (TCP connect RTT), ping (ICMP), mixed (ping then fallback to tcp)",
    )
    parser.add_argument(
        "--output", type=str, default="Tracker.txt", help="Output file path"
    )
    return parser.parse_args()


def read_local_file(path: str) -> List[str]:
    if not os.path.isfile(path):
        print(f"[WARN] Local source not found: {path}")
        return []
    for enc in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
        try:
            with open(path, "r", encoding=enc, errors="ignore") as f:
                return f.read().splitlines()
        except Exception:
            continue
    print(f"[WARN] Failed to read local source: {path}")
    return []


def fetch_url(url: str) -> List[str]:
    if requests is None:
        print("[ERROR] 'requests' not installed. Please run: pip install -r requirements.txt")
        return []
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text.splitlines()
    except Exception as e:
        print(f"[WARN] Failed to fetch {url}: {e}")
        return []


def load_sources_from_file(path: str) -> List[str]:
    items: List[str] = []
    if not os.path.isfile(path):
        return items
    # Try INI format: [sources] section
    try:
        cp = ConfigParser()
        cp.read(path, encoding="utf-8")
        if cp.has_section("sources"):
            for _, v in cp.items("sources"):
                v = v.strip()
                if v:
                    items.append(v)
    except Exception:
        pass
    # Fallback: plain text lines, ignore comments
    try:
        for enc in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
            try:
                with open(path, "r", encoding=enc, errors="ignore") as f:
                    for line in f:
                        s = line.strip()
                        if not s or s.startswith("#") or s.startswith(";"):
                            continue
                        items.append(s)
                break
            except Exception:
                continue
    except Exception:
        pass
    return sorted(set(items))


def gather_sources(sources_arg: str) -> List[str]:
    items = [s.strip() for s in sources_arg.split(",") if s.strip()]
    lines: List[str] = []
    for src in tqdm(items, desc="[STAGE] Fetching sources", unit="src"):
        if src.lower().startswith("http://") or src.lower().startswith("https://"):
            lines.extend(fetch_url(src))
        else:
            lines.extend(read_local_file(src))
    return lines


def is_http_tracker(line: str) -> bool:
    s = line.strip()
    return s.lower().startswith("http://") or s.lower().startswith("https://")


def canonicalize_url(url: str) -> str:
    try:
        p = urlparse(url.strip())
        scheme = p.scheme.lower()
        netloc = p.netloc
        path = p.path or "/"
        return urlunparse((scheme, netloc, path, "", p.query, p.fragment))
    except Exception:
        return url.strip()


def extract_host_port(url: str) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    try:
        p = urlparse(url)
        host = p.hostname
        port = p.port
        scheme = p.scheme.lower() if p.scheme else None
        if port is None and scheme:
            if scheme == "http":
                port = 80
            elif scheme == "https":
                port = 443
        return host, port, scheme
    except Exception:
        return None, None, None


def is_ipv6_literal(host: str) -> bool:
    return host is not None and ":" in host


def run_ping_command(host: str, count: int, timeout_ms: int) -> Tuple[int, str]:
    sysname = platform.system().lower()
    ipv6 = is_ipv6_literal(host)
    cmd: List[str] = []
    if sysname.startswith("win"):
        cmd = ["ping"]
        if ipv6:
            cmd.append("-6")
        cmd += ["-n", str(count), "-w", str(timeout_ms), host]
    else:
        timeout_s = max(1, int(round(timeout_ms / 1000)))
        cmd = ["ping"]
        if ipv6:
            cmd.append("-6")
        cmd += ["-c", str(count), "-W", str(timeout_s), host]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            shell=False,
        )
        output = proc.stdout
        decoded = None
        for enc in ("utf-8", "gbk", "latin-1"):
            try:
                decoded = output.decode(enc, errors="ignore")
                break
            except Exception:
                continue
        if decoded is None:
            decoded = output.decode("utf-8", errors="ignore")
        return proc.returncode, decoded
    except Exception as e:
        return 1, str(e)


def parse_avg_rtt_ms(output: str) -> Optional[int]:
    # Windows EN: Average = Xms
    m = re.search(r"Average\s*=\s*(\d+)\s*ms", output, flags=re.IGNORECASE)
    if m:
        return int(m.group(1))
    # Windows ZH: 平均 = Xms
    m = re.search(r"平均\s*=\s*(\d+)\s*ms", output)
    if m:
        return int(m.group(1))
    # Other variants: avg = Xms
    m = re.search(r"avg\s*=\s*(\d+)\s*ms", output, flags=re.IGNORECASE)
    if m:
        return int(m.group(1))
    # Fallback: parse individual time=XXms and average
    times = [int(x) for x in re.findall(r"time[=<]\s*(\d+)\s*ms", output, flags=re.IGNORECASE)]
    if times:
        return int(sum(times) / len(times))
    return None


def ping_host_avg_ms(host: str, count: int, timeout_ms: int, retries: int) -> Optional[int]:
    best: Optional[int] = None
    attempts = max(1, retries)
    for _ in range(attempts):
        code, out = run_ping_command(host, count, timeout_ms)
        rtt = parse_avg_rtt_ms(out)
        if rtt is not None:
            if best is None or rtt < best:
                best = rtt
            break
    return best


def tcp_connect_once_ms(host: str, port: int, timeout_ms: int) -> Optional[int]:
    timeout_s = max(0.5, timeout_ms / 1000.0)
    start = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout_s) as sock:
            pass
        end = time.monotonic()
        return int((end - start) * 1000)
    except Exception:
        return None


def tcp_connect_rtt_ms(host: str, port: int, timeout_ms: int, retries: int) -> Optional[int]:
    best: Optional[int] = None
    attempts = max(1, retries)
    for _ in range(attempts):
        rtt = tcp_connect_once_ms(host, port, timeout_ms)
        if rtt is not None:
            if best is None or rtt < best:
                best = rtt
            break
    return best


def get_app_dir() -> str:
    # When frozen by PyInstaller, sys.executable points to the .exe; otherwise use script file dir
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def ensure_sources_ini(path: str):
    # Create sources.ini with DEFAULT_SOURCES if it doesn't exist
    if os.path.isfile(path):
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        pass
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("[sources]\n")
            f.write("# 你可以在此添加或移除源，支持 HTTP(S) URL 或本地文件路径\n")
            f.write("# 注释行以 # 或 ; 开头\n\n")
            for idx, url in enumerate(DEFAULT_SOURCES, start=1):
                f.write(f"url{idx} = {url}\n")
        print(f"[INFO] Created default sources file: {path}")
    except Exception as e:
        print(f"[WARN] Failed to create default sources.ini: {e}")


def main():
    args = parse_args()

    # Resolve config path default to the executable/script directory
    app_dir = get_app_dir()
    default_config_path = os.path.join(app_dir, "sources.ini")
    config_path = args.config
    if not args.sources and (not config_path or config_path == "sources.ini"):
        config_path = default_config_path

    # If using default config path and file does not exist, create it on first run
    if not args.sources:
        ensure_sources_ini(config_path)

    # Determine sources: CLI > config file > built-in defaults
    if args.sources:
        sources_arg = args.sources
    else:
        file_items = load_sources_from_file(config_path)
        if file_items:
            print(f"[INFO] Using sources from {config_path}: {len(file_items)} entries")
            sources_arg = ",".join(file_items)
        else:
            print("[INFO] Using built-in default sources")
            sources_arg = ",".join(DEFAULT_SOURCES)

    print("[INFO] Gathering sources...")
    raw_lines = gather_sources(sources_arg)
    print(f"[INFO] Loaded {len(raw_lines)} lines from sources")

    print("[INFO] Normalizing and filtering HTTP/HTTPS trackers...")
    trackers: List[str] = []
    for l in tqdm(raw_lines, desc="[STAGE] Normalizing/filtering", unit="line"):
        if is_http_tracker(l):
            trackers.append(canonicalize_url(l))
    unique_trackers: List[str] = sorted(set(trackers))
    print(f"[INFO] HTTP/HTTPS trackers after dedupe: {len(unique_trackers)}")

    # Map (host, port) to trackers
    hp_to_trackers: Dict[Tuple[str, int], List[str]] = {}
    for t in tqdm(unique_trackers, desc="[STAGE] Extracting hosts", unit="url"):
        host, port, scheme = extract_host_port(t)
        if not host or port is None or not scheme:
            continue
        hp_to_trackers.setdefault((host, port), []).append(t)

    hp_list = list(hp_to_trackers.keys())
    print(f"[INFO] Unique host:port pairs to probe: {len(hp_list)}")

    # Concurrency probe
    hp_rtt: Dict[Tuple[str, int], Optional[int]] = {}

    def probe_one(hp: Tuple[str, int]) -> Tuple[Tuple[str, int], Optional[int]]:
        host, port = hp
        rtt: Optional[int] = None
        if args.probe == "ping":
            rtt = ping_host_avg_ms(host, args.icmp_count, args.timeout, args.retries)
        elif args.probe == "tcp":
            rtt = tcp_connect_rtt_ms(host, port, args.timeout, args.retries)
        else:  # mixed
            rtt = ping_host_avg_ms(host, args.icmp_count, args.timeout, args.retries)
            if rtt is None:
                rtt = tcp_connect_rtt_ms(host, port, args.timeout, args.retries)
        return hp, rtt

    print(f"[INFO] Probing concurrently (workers={args.concurrency}, method={args.probe})...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = [ex.submit(probe_one, hp) for hp in hp_list]
        with tqdm(total=len(futures), desc="[STAGE] Probing", unit="host") as pbar:
            for fut in concurrent.futures.as_completed(futures):
                hp, rtt = fut.result()
                hp_rtt[hp] = rtt
                pbar.update(1)

    # Build reachable tracker list with RTT
    reachable: List[Tuple[str, int]] = []
    for hp, trackers_on_hp in hp_to_trackers.items():
        rtt = hp_rtt.get(hp)
        if rtt is None:
            continue
        for t in trackers_on_hp:
            reachable.append((t, rtt))

    reachable_sorted = [t for t, _ in sorted(reachable, key=lambda x: x[1])]  # sort by RTT

    # Write output
    out_path = args.output
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            for t in tqdm(reachable_sorted, desc="[STAGE] Writing output", unit="tracker"):
                f.write(t + "\n")
        print(f"[INFO] Wrote {len(reachable_sorted)} trackers to {out_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write output: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()