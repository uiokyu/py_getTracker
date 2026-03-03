# py_getTracker — HTTP/HTTPS Tracker Fetcher & Tester

Fetch HTTP/HTTPS Tracker lists from the internet, probe their availability concurrently, and generate a high-quality list sorted by response latency (RTT). The output `Tracker.txt` contains one address per line.

## Features
- **Automatic Source Fetching**: Supports multiple HTTP/HTTPS sources and local files.
- **Configurable Sources**: Automatically generates `sources.ini` for easy management of tracker lists.
- **Concurrent Probing**: High-performance concurrency (default 64 threads).
- **Multiple Probe Modes**:
  - `tcp`: TCP connection RTT (default, most reliable for HTTP trackers).
  - `ping`: ICMP Echo (requires privileges on some systems).
  - `mixed`: Ping first, fallback to TCP if ping fails.
- **Smart Sorting**: Sorts trackers by latency (RTT) in ascending order.
- **Standard Output**: Generates `Tracker.txt` compatible with most BitTorrent clients.

## Requirements
- Python 3.8+ (Tested on 3.14.3)
- OS: Windows (Recommended), Linux, macOS
- Network: Internet access (some probe modes like `ping` may require administrative privileges or firewall rules)

## Installation

1. Install Python 3.8 or higher.
2. (Optional) Create a virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .\.venv\Scripts\activate
   # Linux/macOS
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Quick Start (Zero Config)
Simply run the script. On the first run, it will generate a `sources.ini` file with default public tracker lists.

```bash
python main.py
```

**Default Behavior:**
- **Sources**: Reads from `sources.ini`. If missing, creates it with 4 default public lists:
  - https://gcore.jsdelivr.net/gh/XIU2/TrackersListCollection@master/best.txt
  - https://cf.trackerslist.com/all.txt
  - https://down.adysec.com/trackers_all.txt
  - https://cdn.jsdelivr.net/gh/ngosang/trackerslist@master/trackers_all.txt
- **Probe Method**: `tcp` (TCP Connect RTT)
- **Timeout**: 1000 ms
- **Concurrency**: 64 threads
- **Output**: `Tracker.txt`

### Advanced Usage

You can override defaults using command-line arguments:

```bash
python main.py --help
```

**Examples:**

1. **Override sources temporarily**:
   ```bash
   python main.py --sources https://example.com/list.txt,local_list.txt
   ```

2. **Use Mixed Probe Mode (Ping + TCP)**:
   ```bash
   python main.py --probe mixed --timeout 1500
   ```

3. **High Concurrency & Custom Output**:
   ```bash
   python main.py --concurrency 128 --output MyTrackers.txt
   ```

## Configuration (sources.ini)

The `sources.ini` file is generated automatically in the same directory as the script. You can edit it to add or remove tracker sources.

```ini
[sources]
# Add your sources here (URL or local file path)
url1 = https://example.com/trackers.txt
file1 = C:\path\to\local_trackers.txt
```

## CLI Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--sources` | Comma-separated URLs or file paths. Overrides `sources.ini`. | (None) |
| `--config` | Path to the configuration file. | `sources.ini` |
| `--probe` | Probe method: `tcp`, `ping`, `mixed`. | `tcp` |
| `--timeout` | Timeout per probe attempt (ms). | 1000 |
| `--retries` | Retry attempts per host. | 1 |
| `--concurrency` | Number of concurrent worker threads. | 64 |
| `--icmp-count` | Number of ICMP echoes (for `ping` mode). | 3 |
| `--output` | Output file path. | `Tracker.txt` |

## Notes & Limitations
- **ICMP Restrictions**: The `ping` mode may fail if the OS or firewall blocks ICMP packets (common on non-Admin Windows terminals). Use `tcp` mode if unsure.
- **Proxy Support**: The script uses the system's `requests` environment (e.g., `HTTP_PROXY` / `HTTPS_PROXY` env vars) but does not have a specific CLI argument for proxies.
- **Performance**: Setting concurrency too high (>500) may cause network congestion or file descriptor limits on some systems.

## License
[MIT](LICENSE)
