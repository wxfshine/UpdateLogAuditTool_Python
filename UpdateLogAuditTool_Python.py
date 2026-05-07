import json
import logging
import os
import re
import time
from datetime import datetime
from urllib.parse import quote

import requests

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None
    ImageOps = None

# ======================
# 你的 Cookie（完全不变）
# ======================
FedAuth = "77u/PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48U1A+VjE1LDBoLmZ8bWVtYmVyc2hpcHwyMDAzYmZmZDgxNDgwZjVkQGxpdmUuY29tLDAjLmZ8bWVtYmVyc2hpcHx3YW5neGZAY21nb3MuY29tLDEzNDIyNTk0NDQzMDAwMDAwMCwxMzQyMDUyNDU4NDAwMDAwMDAsMTM0MjMwMjY0NDc3MTA4NjEyLDEyNC4xMjYuMjI0LjgzLDMsNzBkNTQ3NTAtYzYwZC00NGUxLThiM2MtZjQ2ZWE3ODc0MzU3LCwwMDRkNjQ5YS1hZDZkLTAxODctZDkyNi03NDhiZjAyZjkzZmYsZmMyNjExYTItZjA5NC0wMDAwLTJmNmQtZWIzNWZhMzM2OGJjLGZjMjYxMWEyLWYwOTQtMDAwMC0yZjZkLWViMzVmYTMzNjhiYywsMCwxMzQyMjU5ODA0NzY3OTYxOTksMTM0MjI4NTM2NDc2Nzk2MTk5LCwsZXlKNGJYTmZZMk1pT2lKYlhDSkRVREZjSWwwaUxDSndjbVZtWlhKeVpXUmZkWE5sY201aGJXVWlPaUozWVc1bmVHWkFZMjFuYjNNdVkyOXRJaXdpZFhScElqb2lUSGwxUjNnNVFsZzJSVFpsYUhaVldVRlhNVWRCUVNJc0ltRjFkR2hmZEdsdFpTSTZJakV6TkRJeU5UazBORFF6TURBd01EQXdNQ0o5LDI2NTA0Njc3NDM5OTk5OTk5OTksMTM0MjI1OTQ0NDcwMDAwMDAwLDYwY2JjOGY0LTRmNTYtNDhmMy05MTMzLWUzZjZkMzkyY2NlZCwsLCwsLDExNTI5MjE1MDQ2MDY4NDY5NzYsLDc3NixDMGh3eHg1c3Z6MWVQNjBfcE83RERVMThzdUEsLDAsLG15T3RJSVN5L0x0SGJwclBCWDkxRkMwTkNqOEliMjJTV1lnZFA3ODVTcUEyNVhIdUtwd3BhSkQ0SGVYeng2M1NYL2tPZUN1TEFoVkJYbVhQNSsvdjAvNDMwcnpLTk9VTDRobGsyaTE2aGkxMVZPT0dtbjZUeTBlblhpNVB5d3BFamlnQnpmOEhwOUxhU29DeEFZL1NnRGg3NDBhalRzNzNraXpNOXZBTmhxTU9XNTQ1b3QwYmpPcEdLMjdNM2ZIMTEzK0xKN2xSZ2ZHdG51Q2I2L000cCtpdTA3VGQreXhBRm51TEREOGwvQ3Z4OUpGU0NOenNEV1did1FONW4zbGtDUS9GMk95UzZHa3F6OWg2Z1ZVWW1DVnJLbXk5N1BCT0NKZVphYmpBdlJsSFFQTTBRZU9MYm5OcXpIVTFDN1VrRDVxRVluMXVVVEVJazZHb1ZDWkRVdz09PC9TUD4="
rtFa = "zDEfW2/gcjouTbqqW0R1rqQMKIRbKt1OfR/R5prv1x8mNzBkNTQ3NTAtYzYwZC00NGUxLThiM2MtZjQ2ZWE3ODc0MzU3IzEzNDIyNTk0NDQ3NzQyMTE2MiNmYzI2MTFhMi0xMDkwLTAwMDAtMmY2ZC1lMjE4Zjk3MjdjNWQjd2FuZ3hmJTQwY21nb3MuY29tIzc3NiNZMXQyM1pscEpmS2Exc3lUb3k3NUVlUXVoQUEjWTF0MjNabHBKZkthMXN5VG95NzVFZVF1aEFBYBRlW5p0vSrHaBR1AktzYXC9U6J09uj7MGN5qQwlUfe25tIwAaMFizAC7q1mIRkZF1SfQlIyGXVMPjzD+St3Kg0a/I9S2pTs2eXCpYmzojYV23QLzC2+6j5IKfAIw7a+C8b4NWs9b9qWJ1sI2NCycYanObUSebANoMs6+rb47oAfa6idm+sTuHh3rHZel95nekzdjO2HJoLcAu09UoJhCKlOpRFd9IvPwEl8fILV80gjna5VOwNzJmdbnRKUEcY3KpjM3hjRKtC6nrN9YaJRZJNGx54oeVCkAABzvhkFz2F/3Nra0nTyetAocNKQBjyBr/k3uyut+wFIg/MgocTfDMwAAAA="

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "monitor_config.json")
DEFAULT_CONFIG = {
    "poll_interval_minutes": 5,
    "site_url": "https://cmgos.sharepoint.cn/sites/RD",
    "folder_path": "/sites/RD/Shared Documents",
    "root_sub_folder": "/sites/RD/Shared Documents/17.B包环境和操作历史状态",
    "excluded_folder_names": ["王晓峰"],
    "wang_xiaofeng_folder": "/sites/RD/Shared Documents/17.B包环境和操作历史状态/王晓峰",
    "upload_file_content": "王晓峰验证文件",
    "base_local": r"D:\UpdateLogAuditTool_Log",
    "log_dir": r"D:\UpdateLogAuditTool_Log\log",
    "state_file": r"D:\UpdateLogAuditTool_Log\log\monitor_state.json",
    "enable_upload_validation_file": False,
}

site_url = DEFAULT_CONFIG["site_url"]
folder_path = DEFAULT_CONFIG["folder_path"]
root_sub_folder = DEFAULT_CONFIG["root_sub_folder"]
excluded_folder_names = set(DEFAULT_CONFIG["excluded_folder_names"])
wang_xiaofeng_folder = DEFAULT_CONFIG["wang_xiaofeng_folder"]
upload_file_content = DEFAULT_CONFIG["upload_file_content"]
base_local = DEFAULT_CONFIG["base_local"]
log_dir = DEFAULT_CONFIG["log_dir"]
state_file = DEFAULT_CONFIG["state_file"]
poll_interval_minutes = DEFAULT_CONFIG["poll_interval_minutes"]
enable_upload_validation_file = DEFAULT_CONFIG["enable_upload_validation_file"]

logger = logging.getLogger("UpdateLogAuditTool")
logger.setLevel(logging.INFO)
logger.propagate = False

session = requests.Session()
session.cookies.set("FedAuth", FedAuth)
session.cookies.set("rtFa", rtFa)

headers = {
    "Accept": "application/json;odata=nometadata",
    "User-Agent": "Mozilla/5.0",
}


def ensure_config_file():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(DEFAULT_CONFIG, file, ensure_ascii=False, indent=2)


def load_config():
    ensure_config_file()

    encodings = ["utf-8", "utf-8-sig", "gbk", "mbcs"]
    last_error = None

    for encoding in encodings:
        try:
            with open(CONFIG_FILE, "r", encoding=encoding) as file:
                return json.load(file)
        except UnicodeDecodeError as ex:
            last_error = ex
            continue

    raise UnicodeDecodeError(
        last_error.encoding if last_error else "unknown",
        last_error.object if last_error else b"",
        last_error.start if last_error else 0,
        last_error.end if last_error else 0,
        "Unable to decode monitor_config.json with supported encodings: utf-8, utf-8-sig, gbk, mbcs",
    )


def apply_config(config):
    global site_url
    global folder_path
    global root_sub_folder
    global excluded_folder_names
    global wang_xiaofeng_folder
    global upload_file_content
    global base_local
    global log_dir
    global state_file
    global poll_interval_minutes
    global enable_upload_validation_file

    site_url = config.get("site_url", DEFAULT_CONFIG["site_url"])
    folder_path = config.get("folder_path", DEFAULT_CONFIG["folder_path"])
    root_sub_folder = config.get("root_sub_folder", DEFAULT_CONFIG["root_sub_folder"])
    excluded_folder_names = set(
        config.get("excluded_folder_names", DEFAULT_CONFIG["excluded_folder_names"])
    )
    wang_xiaofeng_folder = config.get(
        "wang_xiaofeng_folder", DEFAULT_CONFIG["wang_xiaofeng_folder"]
    )
    upload_file_content = config.get(
        "upload_file_content", DEFAULT_CONFIG["upload_file_content"]
    )
    base_local = config.get("base_local", DEFAULT_CONFIG["base_local"])
    log_dir = config.get("log_dir", DEFAULT_CONFIG["log_dir"])
    state_file = config.get("state_file", DEFAULT_CONFIG["state_file"])
    poll_interval_minutes = int(
        config.get("poll_interval_minutes", DEFAULT_CONFIG["poll_interval_minutes"])
    )
    enable_upload_validation_file = bool(
        config.get(
            "enable_upload_validation_file",
            DEFAULT_CONFIG["enable_upload_validation_file"],
        )
    )


def setup_logging():
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "monitor.log")

    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


def log_info(message):
    print(message)
    logger.info(message)


def log_error(message):
    print(message)
    logger.error(message)


def get_request_digest():
    resp = session.post(
        f"{site_url}/_api/contextinfo",
        headers={
            "Accept": "application/json;odata=verbose",
            "User-Agent": headers["User-Agent"],
        },
    )
    resp.raise_for_status()
    return resp.json()["d"]["GetContextWebInformation"]["FormDigestValue"]


def get_folder_items(target_folder_path: str, item_type: str):
    api_url = f"{site_url}/_api/web/getfolderbyserverrelativeurl('{target_folder_path}')/{item_type}"
    resp = session.get(api_url, headers=headers)
    resp.raise_for_status()
    return resp.json().get("value", [])


def upload_text_file_to_sharepoint(folder_relative_url: str, file_name: str, content: str) -> None:
    digest = get_request_digest()
    encoded_folder = quote(folder_relative_url, safe="/()' ")
    encoded_file_name = quote(file_name, safe="")
    upload_url = (
        f"{site_url}/_api/web/GetFolderByServerRelativeUrl('{encoded_folder}')/"
        f"Files/add(url='{encoded_file_name}',overwrite=true)"
    )
    upload_headers = {
        "Accept": "application/json;odata=nometadata",
        "User-Agent": headers["User-Agent"],
        "X-RequestDigest": digest,
        "Content-Type": "text/plain; charset=utf-8",
    }
    resp = session.post(upload_url, headers=upload_headers, data=content.encode("utf-8"))
    resp.raise_for_status()


def print_main_directory():
    all_items = []

    folders = get_folder_items(folder_path, "folders")
    for folder in folders:
        name = folder.get("Name", "")
        if name and name not in ["Forms", ""]:
            all_items.append(f"📂 {name}")

    files = get_folder_items(folder_path, "files")
    for file in files:
        name = file.get("Name", "")
        if name:
            all_items.append(f"📄 {name}")

    log_info("=" * 70)
    log_info("📂 主目录：Shared Documents")
    log_info("=" * 70)

    for index, item in enumerate(sorted(all_items), 1):
        log_info(f"{index:2d}. {item}")

    log_info(f"\n✅ 主目录共找到：{len(all_items)} 个项目！")


def download_file(server_url: str, local_path: str) -> bool:
    resp = session.get(f"https://cmgos.sharepoint.cn{server_url}", stream=True)
    resp.raise_for_status()
    with open(local_path, "wb") as local_file:
        for chunk in resp.iter_content(1024):
            local_file.write(chunk)
    return True


def download_sharepoint_content():
    print_main_directory()

    log_info("\n" + "=" * 70)
    log_info("📂 进入子文件夹：17.B包环境和操作历史状态")
    log_info("=" * 70)

    sub_folders = []
    time_folder = datetime.now().strftime("%Y%m%d%H%M")
    root_local = os.path.join(base_local, time_folder)
    os.makedirs(root_local, exist_ok=True)

    folders = get_folder_items(root_sub_folder, "folders")
    for folder in folders:
        name = folder.get("Name", "")
        path = folder.get("ServerRelativeUrl", "")
        if not name or name == "Forms":
            continue
        if name in excluded_folder_names:
            log_info(f"⏭️ 已跳过文件夹：{name}")
            continue
        sub_folders.append({"name": name, "path": path})
        log_info(f"📂 {name}")

    log_info(f"\n✅ 子文件夹共找到：{len(sub_folders)} 个！")
    log_info("\n" + "=" * 70)
    log_info("📂 开始递归下载所有子文件夹内的文件到 D 盘")
    log_info("=" * 70)
    log_info(f"📁 本地根目录：{root_local}\n")

    total_success = 0

    for user_folder in sub_folders:
        folder_name = user_folder["name"]
        folder_sp_path = user_folder["path"]
        log_info(f"正在处理：{folder_name}")

        local_user_folder = os.path.join(root_local, folder_name)
        os.makedirs(local_user_folder, exist_ok=True)

        try:
            files = get_folder_items(folder_sp_path, "files")
            for file in files:
                name = file.get("Name", "")
                server_url = file.get("ServerRelativeUrl", "")
                if not name or not server_url:
                    continue
                local_path = os.path.join(local_user_folder, name)
                try:
                    download_file(server_url, local_path)
                    log_info(f"  ✅ 已下载：{name}")
                    total_success += 1
                except Exception as ex:
                    log_error(f"  ❌ 下载失败：{name}，原因：{ex}")
        except Exception as ex:
            log_error(f"  ⚠️  读取失败：{folder_name}，原因：{ex}")

    return total_success, root_local


def upload_validation_file():
    log_info("\n" + "=" * 70)
    log_info("📤 开始上传王晓峰验证文件到 SharePoint")
    log_info("=" * 70)

    upload_file_name = datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"
    upload_text_file_to_sharepoint(wang_xiaofeng_folder, upload_file_name, upload_file_content)
    log_info(f"✅ 已上传验证文件：{upload_file_name}")
    log_info(f"📂 上传目标目录：{wang_xiaofeng_folder}")


def collect_remote_state(folder_relative_url: str):
    state = {"folders": [], "files": []}

    def walk(current_folder: str):
        folders = get_folder_items(current_folder, "folders")
        for folder in folders:
            name = folder.get("Name", "")
            path = folder.get("ServerRelativeUrl", "")
            if not name or name == "Forms":
                continue
            if name in excluded_folder_names:
                continue
            state["folders"].append({
                "name": name,
                "path": path,
            })
            walk(path)

        files = get_folder_items(current_folder, "files")
        for file in files:
            name = file.get("Name", "")
            path = file.get("ServerRelativeUrl", "")
            if not name or not path:
                continue
            state["files"].append({
                "name": name,
                "path": path,
                "size": str(file.get("Length", "")),
                "modified": str(file.get("TimeLastModified", "")),
            })

    walk(folder_relative_url)
    state["folders"] = sorted(state["folders"], key=lambda item: item["path"])
    state["files"] = sorted(state["files"], key=lambda item: item["path"])
    return state


def load_last_state():
    if not os.path.exists(state_file):
        return None
    with open(state_file, "r", encoding="utf-8") as file:
        return json.load(file)


def save_last_state(state):
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)


def find_tesseract_executable():
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]

    for executable_path in possible_paths:
        if os.path.exists(executable_path):
            return executable_path

    return None


def get_ocr_engine():
    if Image is None or ImageOps is None:
        log_error("OCR 跳过：未安装 Pillow，无法识别 PNG 图片中的时间信息。")
        return None

    try:
        import pytesseract
    except ImportError:
        log_error("OCR 跳过：未安装 pytesseract，无法识别 PNG 图片中的时间信息。")
        return None

    try:
        tesseract_cmd = os.environ.get("TESSERACT_CMD") or find_tesseract_executable()
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        return pytesseract
    except Exception as ex:
        log_error(f"OCR 初始化失败：{ex}")
        return None


def preprocess_image_for_ocr(image_path: str):
    image = Image.open(image_path)
    image = image.convert("L")
    image = ImageOps.autocontrast(image)
    image = image.point(lambda pixel: 255 if pixel > 180 else 0)
    return image


def extract_time_matches(ocr_text: str):
    compact_text = re.sub(r"\s+", "", ocr_text)
    pattern = re.compile(r"(\d{4})[/-](\d{2})[/-](\d{2})(\d{2}):(\d{2}):(\d{2})")
    matches = []

    for match in pattern.finditer(compact_text):
        matches.append(
            f"{match.group(1)}/{match.group(2)}/{match.group(3)} {match.group(4)}:{match.group(5)}:{match.group(6)}"
        )

    return matches


def extract_time_ranges_from_png(image_path: str, ocr_engine):
    try:
        image = preprocess_image_for_ocr(image_path)
        full_text = ocr_engine.image_to_string(image, lang="chi_sim+eng", config="--psm 6")
    except Exception as ex:
        log_error(f"OCR 识别失败：{image_path}，原因：{ex}")
        return None
    time_matches = extract_time_matches(full_text)
    if len(time_matches) < 2:
        return {
            "start_time": None,
            "end_time": None,
            "ocr_text": full_text,
            "time_matches": time_matches,
        }

    return {
        "start_time": time_matches[0],
        "end_time": time_matches[1],
        "ocr_text": full_text,
        "time_matches": time_matches,
    }


def analyze_zhou_liming_png(download_root: str, analysis_lines):
    zhou_lim_ing_folder = os.path.join(download_root, "周利明")
    if not os.path.isdir(zhou_lim_ing_folder):
        log_info("OCR 分析跳过：未找到 周利明 目录。")
        return

    ocr_engine = get_ocr_engine()
    if ocr_engine is None:
        return

    analysis_lines.append("")
    analysis_lines.append("周利明目录 PNG OCR 分析结果：")
    analysis_lines.append("-" * 70)

    matched_count = 0

    for file_name in sorted(os.listdir(zhou_lim_ing_folder)):
        if not file_name.lower().endswith(".png"):
            continue

        image_path = os.path.join(zhou_lim_ing_folder, file_name)
        log_info(f"开始 OCR 识别：{image_path}")
        ocr_result = extract_time_ranges_from_png(image_path, ocr_engine)
        log_info(f"OCR 原文：\n{ocr_result['ocr_text'] if ocr_result else '(无识别结果)'}")

        if ocr_result is None:
            log_info(f"OCR 识别失败或无结果：{file_name}")
            continue

        if len(ocr_result["time_matches"]) < 2:
            log_info(
                f"OCR 未提取到 2 个时间：{file_name}，当前仅识别到 {len(ocr_result['time_matches'])} 个时间"
            )
            continue

        matched_count += 1
        analysis_lines.append(
            f"  文件名：{file_name} | 开始时间：{ocr_result['start_time']} | 结束时间：{ocr_result['end_time']}"
        )
        log_info(
            f"OCR 提取成功：{file_name}，开始时间={ocr_result['start_time']}，结束时间={ocr_result['end_time']}"
        )

    if matched_count == 0:
        analysis_lines.append("  (未识别到符合要求的 PNG 图片)")


def analyze_download_content(download_root: str):
    analysis_lines = []
    analysis_name = f"analysis_{os.path.basename(download_root)}.txt"
    analysis_path = os.path.join(log_dir, analysis_name)

    analysis_lines.append(f"分析目录：{download_root}")
    analysis_lines.append("=" * 70)

    for current_root, _, files in os.walk(download_root):
        relative_folder = os.path.relpath(current_root, download_root)
        folder_display = "根目录" if relative_folder == "." else relative_folder
        analysis_lines.append(f"文件夹：{folder_display}")

        if not files:
            analysis_lines.append("  (无文件)")
            continue

        for file_name in sorted(files):
            file_path = os.path.join(current_root, file_name)
            stat = os.stat(file_path)
            created_time = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            file_size = stat.st_size
            analysis_lines.append(
                f"  文件名：{file_name} | 创建时间：{created_time} | 大小：{file_size} 字节"
            )

    analyze_zhou_liming_png(download_root, analysis_lines)

    with open(analysis_path, "w", encoding="utf-8") as file:
        file.write("\n".join(analysis_lines))

    log_info("\n" + "=" * 70)
    log_info("📊 最新下载内容分析结果")
    log_info("=" * 70)
    for line in analysis_lines:
        log_info(line)
    log_info(f"📄 分析结果已保存：{analysis_path}")


def perform_check_cycle(last_state):
    log_info("\n" + "=" * 70)
    log_info(f"🕒 开始检测：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_info("=" * 70)

    current_state = collect_remote_state(root_sub_folder)

    if last_state is None:
        log_info("首次检测，开始执行全量下载。")
        total_success, root_local = download_sharepoint_content()
        analyze_download_content(root_local)
        if enable_upload_validation_file:
            try:
                upload_validation_file()
            except Exception as ex:
                log_error(f"上传验证文件失败：{ex}")
        log_info(f"🎉 本次下载完成，共下载文件：{total_success} 个")
        return current_state

    if current_state != last_state:
        log_info("检测到内容有变化，开始重新下载全部内容。")
        total_success, root_local = download_sharepoint_content()
        analyze_download_content(root_local)
        if enable_upload_validation_file:
            try:
                upload_validation_file()
            except Exception as ex:
                log_error(f"上传验证文件失败：{ex}")
        log_info(f"🎉 本次下载完成，共下载文件：{total_success} 个")
        return current_state

    log_info("内容没有变化，本次不执行下载。")
    return last_state


def monitor_sharepoint():
    last_state = load_last_state()

    while True:
        try:
            last_state = perform_check_cycle(last_state)
            save_last_state(last_state)
        except KeyboardInterrupt:
            log_info("监控已手动停止。")
            raise
        except Exception as ex:
            log_error(f"检测过程中发生错误：{ex}")

        log_info(f"等待 {poll_interval_minutes} 分钟后进行下一次检测。")
        time.sleep(poll_interval_minutes * 60)


def main():
    config = load_config()
    apply_config(config)
    setup_logging()
    log_info("配置加载完成，开始监控 SharePoint。")
    log_info(f"配置文件：{CONFIG_FILE}")
    log_info(f"轮询间隔：{poll_interval_minutes} 分钟")
    log_info(f"日志目录：{log_dir}")
    log_info(f"监控目录：{root_sub_folder}")
    log_info(
        "说明：为避免程序自己上传验证文件后再次触发变更，默认不自动上传验证文件；"
        "如需启用，请在 monitor_config.json 中把 enable_upload_validation_file 改为 true。"
    )
    monitor_sharepoint()


if __name__ == "__main__":
    main()