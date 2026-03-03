# py_getTracker — 高性能 HTTP/HTTPS Tracker 自动获取与优选工具

**py_getTracker** 是一个轻量级、高性能的 BitTorrent Tracker 优选工具。它能够从互联网自动抓取最新的 HTTP/HTTPS Tracker 列表，利用多线程并发技术对每个 Tracker 进行连接性探测，并根据响应延迟（RTT）进行智能排序，最终生成一份高质量的可用 Tracker 清单。

总所周知，BT 下载速度受限于 Tracker 服务器的响应延迟。而一个 Torrent 文件中通常会包含多个 Tracker 地址，手动选择最优 Tracker 是一项耗时且繁琐的任务。

**py_getTracker** 正是为了解决这一问题而诞生的。它能够自动从互联网抓取最新的 Tracker 列表，利用多线程并发技术对每个 Tracker 进行连接性探测，并根据响应延迟（RTT）进行智能排序，最终生成一份高质量根据你的网络生成的可用 Tracker 清单。


## ✨ 核心优势

为什么选择 py_getTracker？

1.  **极速并发探测**：
    *   内置高并发多线程引擎（默认 64 线程），能在数秒内完成数百个 Tracker 的可用性检测。
    *   告别手动筛选的繁琐，大幅节省时间。

2.  **真实延迟优选**：
    *   不仅仅是检测“是否存活”，更会根据网络往返时延（RTT）进行升序排列。
    *   将响应最快的 Tracker 排在最前，显著提升下载连接速度。

3.  **智能混合模式**：
    *   支持 `TCP` 建连探测（最可靠，推荐）、`ICMP Ping` 探测以及 `Mixed` 混合模式。
    *   混合模式下优先尝试 Ping，失败后自动回退到 TCP，兼顾速度与准确性。

4.  **完全自动化管理**：
    *   首次运行自动生成配置文件 `sources.ini`，内置全网热门 Tracker 源。
    *   支持自定义添加 URL 或本地文件路径，轻松管理您的 Tracker 来源。

5.  **零依赖单文件运行**：
    *   提供编译好的 `.exe` 可执行文件，无需安装 Python 环境，下载即用。

---

## 🚀 快速开始（EXE 使用说明）

### 1. 下载与运行
下载最新发布的 `py_getTracker.exe` 文件，直接双击运行即可。

### 2. 自动执行流程
程序启动后将自动执行以下步骤：
1.  **加载源**：读取 `sources.ini` 中的配置（首次运行会自动创建，并内置 4 个最佳公共源）。
2.  **抓取与去重**：从所有源中下载 Tracker 列表，自动去除重复项，并过滤非 HTTP/HTTPS 协议。
3.  **并发探测**：使用默认的 TCP 模式对成百上千个 Tracker 进行连接测试。
4.  **排序输出**：将可用的 Tracker 按延迟从低到高排序，保存到当前目录下的 `Tracker.txt` 文件中。

### 3. 获取结果
运行结束后，打开同目录下的 `Tracker.txt`，全选内容复制到您的下载软件（如 qBittorrent, BitComet, Aria2 等）中即可享受加速。

---

## ⚙️ 进阶配置与使用

### 配置文件 (sources.ini)
程序会在同目录下生成 `sources.ini`，您可以直接用记事本编辑它来管理 Tracker 源：

```ini
[sources]
# 格式：自定义名称 = URL 或 本地文件路径
# 支持在线 URL
url1 = https://example.com/trackers.txt
# 支持本地文件
file1 = C:\MyFiles\local_trackers.txt
```

### 命令行参数 (高级用户)
如果您习惯使用命令行（CMD / PowerShell），可以通过参数覆盖默认行为：

```bash
# 查看所有可用参数
py_getTracker.exe --help

# 示例 1：临时指定源，不使用配置文件
py_getTracker.exe --sources https://example.com/list.txt

# 示例 2：使用混合探测模式 (Mixed)，并设置超时时间为 2 秒
py_getTracker.exe --probe mixed --timeout 2000

# 示例 3：增加并发数到 128 (适合网络带宽充足的情况)
py_getTracker.exe --concurrency 128 --output MyBestTrackers.txt
```

#### 参数详解

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `--sources` | 逗号分隔的 URL 或文件路径，用于临时覆盖源配置 | (无) |
| `--config` | 配置文件路径 | `sources.ini` |
| `--probe` | 探测模式：`tcp` (推荐), `ping`, `mixed` | `tcp` |
| `--timeout` | 单次探测超时时间 (毫秒) | 1000 |
| `--retries` | 每个 Tracker 的重试次数 | 1 |
| `--concurrency` | 并发线程数，建议 32-256 之间 | 64 |
| `--output` | 结果输出文件路径 | `Tracker.txt` |

---

## ⚠️ 注意事项与常见问题

1.  **关于 Ping 模式的权限**：
    *   在部分 Windows 系统上，使用 `--probe ping` 可能需要管理员权限才能发送 ICMP 包。如果遇到报错或全部失败，请尝试使用默认的 `tcp` 模式，或以管理员身份运行 CMD。

2.  **网络代理**：
    *   程序会自动遵循系统的环境变量（如 `HTTP_PROXY`, `HTTPS_PROXY`）。如果您需要通过代理抓取源，请确保系统环境已配置正确。

3.  **杀毒软件误报**：
    *   由于程序涉及大量并发网络连接，某些敏感的杀毒软件可能会误报。请放心，本程序完全开源安全，您可以自行查阅源码或自行编译。

---

## 🛠️ 源码运行与编译（开发者）

如果您希望从源码运行或自行编译 EXE：

1.  **环境要求**：Python 3.8+
2.  **安装依赖**：
    ```bash
    pip install -r requirements.txt
    ```
3.  **运行脚本**：
    ```bash
    python main.py
    ```
4.  **打包编译**：
    ```bash
    pyinstaller py_getTracker.spec
    ```

## 📄 许可证
本项目采用 [MIT 许可证](LICENSE) 开源。
