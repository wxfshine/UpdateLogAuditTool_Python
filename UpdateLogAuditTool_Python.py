import json
import logging
import hashlib
import ast
import shutil
import os
import re
import socket
import time
import tempfile
import ctypes
from ctypes import wintypes
from ftplib import FTP, error_perm
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
FedAuth_old = "77u/PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48U1A+VjE1LDBoLmZ8bWVtYmVyc2hpcHwyMDAzYmZmZDgxNDgwZjVkQGxpdmUuY29tLDAjLmZ8bWVtYmVyc2hpcHx3YW5neGZAY21nb3MuY29tLDEzNDIyNTk0NDQzMDAwMDAwMCwxMzQyMDUyNDU4NDAwMDAwMDAsMTM0MjMwMjY0NDc3MTA4NjEyLDEyNC4xMjYuMjI0LjgzLDMsNzBkNTQ3NTAtYzYwZC00NGUxLThiM2MtZjQ2ZWE3ODc0MzU3LCwwMDRkNjQ5YS1hZDZkLTAxODctZDkyNi03NDhiZjAyZjkzZmYsZmMyNjExYTItZjA5NC0wMDAwLTJmNmQtZWIzNWZhMzM2OGJjLGZjMjYxMWEyLWYwOTQtMDAwMC0yZjZkLWViMzVmYTMzNjhiYywsMCwxMzQyMjU5ODA0NzY3OTYxOTksMTM0MjI4NTM2NDc2Nzk2MTk5LCwsZXlKNGJYTmZZMk1pT2lKYlhDSkRVREZjSWwwaUxDSndjbVZtWlhKeVpXUmZkWE5sY201aGJXVWlPaUozWVc1bmVHWkFZMjFuYjNNdVkyOXRJaXdpZFhScElqb2lUSGwxUjNnNVFsZzJSVFpsYUhaVldVRlhNVWRCUVNJc0ltRjFkR2hmZEdsdFpTSTZJakV6TkRJeU5UazBORFF6TURBd01EQXdNQ0o5LDI2NTA0Njc3NDM5OTk5OTk5OTksMTM0MjI1OTQ0NDcwMDAwMDAwLDYwY2JjOGY0LTRmNTYtNDhmMy05MTMzLWUzZjZkMzkyY2NlZCwsLCwsLDExNTI5MjE1MDQ2MDY4NDY5NzYsLDc3NixDMGh3eHg1c3Z6MWVQNjBfcE83RERVMThzdUEsLDAsLG15T3RJSVN5L0x0SGJwclBCWDkxRkMwTkNqOEliMjJTV1lnZFA3ODVTcUEyNVhIdUtwd3BhSkQ0SGVYeng2M1NYL2tPZUN1TEFoVkJYbVhQNSsvdjAvNDMwcnpLTk9VTDRobGsyaTE2aGkxMVZPT0dtbjZUeTBlblhpNVB5d3BFamlnQnpmOEhwOUxhU29DeEFZL1NnRGg3NDBhalRzNzNraXpNOXZBTmhxTU9XNTQ1b3QwYmpPcEdLMjdNM2ZIMTEzK0xKN2xSZ2ZHdG51Q2I2L000cCtpdTA3VGQreXhBRm51TEREOGwvQ3Z4OUpGU0NOenNEV1did1FONW4zbGtDUS9GMk95UzZHa3F6OWg2Z1ZVWW1DVnJLbXk5N1BCT0NKZVphYmpBdlJsSFFQTTBRZU9MYm5OcXpIVTFDN1VrRDVxRVluMXVVVEVJazZHb1ZDWkRVdz09PC9TUD4="
FedAuth = "77u/PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48U1A+VjE1LDBoLmZ8bWVtYmVyc2hpcHwyMDAzYmZmZDgxNDgwZjVkQGxpdmUuY29tLDAjLmZ8bWVtYmVyc2hpcHx3YW5neGZAY21nb3MuY29tLDEzNDIyOTQ2OTUwMDAwMDAwMCwxMzQyMDUyNDU4NDAwMDAwMDAsMTM0MjMzNzg5NTQ2OTA0OTY0LDEyNC4xMjYuMjI0LjgzLDMsNzBkNTQ3NTAtYzYwZC00NGUxLThiM2MtZjQ2ZWE3ODc0MzU3LCwwMDRlMDBkYS01OGRjLTkxZTYtNjdlZC0zNDhiYzhlZTMzY2UsMjk3NzEyYTItMTBkYi0wMDAwLTJmNmQtZTU0ZWU4MGNiN2NkLDI5NzcxMmEyLTEwZGItMDAwMC0yZjZkLWU1NGVlODBjYjdjZCwsMCwxMzQyMjk1MDU1NDY1ODY2MDQsMTM0MjMyMDYxNTQ2NTg2NjA0LCwsZXlKNGJYTmZZMk1pT2lKYlhDSkRVREZjSWwwaUxDSndjbVZtWlhKeVpXUmZkWE5sY201aGJXVWlPaUozWVc1bmVHWkFZMjFuYjNNdVkyOXRJaXdpZFhScElqb2lUMVJ0UlZSQlh6TlFSWFUxVGtsYVlsOWZZMDVCUVNJc0ltRjFkR2hmZEdsdFpTSTZJakV6TkRJeU9UUTJPVFV3TURBd01EQXdNQ0o5LDI2NTA0Njc3NDM5OTk5OTk5OTksMTM0MjI5NDY5NTQwMDAwMDAwLDYwY2JjOGY0LTRmNTYtNDhmMy05MTMzLWUzZjZkMzkyY2NlZCwsLCwsLDExNTI5MjE1MDQ2MDY4NDY5NzYsLDc3NixDMGh3eHg1c3Z6MWVQNjBfcE83RERVMThzdUEsLDAsLGppdHFuenB6NkpOcTB5WlJkUlZRNWhvU3hidmh6dmRQZzVMV25LVDkrUVlZMnBaTXQ2YTQzWEMwTVJrbGJTRVV6ai82ZzIxT0NBNVJTYzYzMDBjbWs0TkZFOEpnU3FDZ3YxcWo1TnBRRzFjVWFpSnJNRzg5SmZZZnk5UkZWRHJVckk0YWlLeUIyYlp1ZlFPbDhQTVJFTWp4TmM1THZmVXNET214bWxiZkxYMk45Q0dhRHFLcHlIbkxzc0N6c1RERGpoT1psdG5LelpyUTNlWU5KbWhwQk5vSGxDLzJ3cWpFQVBndVM0YnBvME5aVS9EY3dVcVUwaTNFK0l1S0o1OEZSTmRjL1M1OGVCZCt6QTJhZGQzd1FsQUhHNk9sMjE4b3JQTXprR3BVZHlYMTdubjdFb0ZTVEpCVTJFV1pLdTRIeFU3SGZrSldualNPTDd0ODcrME03dz09PC9TUD4="
rtFa_old = "zDEfW2/gcjouTbqqW0R1rqQMKIRbKt1OfR/R5prv1x8mNzBkNTQ3NTAtYzYwZC00NGUxLThiM2MtZjQ2ZWE3ODc0MzU3IzEzNDIyNTk0NDQ3NzQyMTE2MiNmYzI2MTFhMi0xMDkwLTAwMDAtMmY2ZC1lMjE4Zjk3MjdjNWQjd2FuZ3hmJTQwY21nb3MuY29tIzc3NiNZMXQyM1pscEpmS2Exc3lUb3k3NUVlUXVoQUEjWTF0MjNabHBKZkthMXN5VG95NzVFZVF1aEFBYBRlW5p0vSrHaBR1AktzYXC9U6J09uj7MGN5qQwlUfe25tIwAaMFizAC7q1mIRkZF1SfQlIyGXVMPjzD+St3Kg0a/I9S2pTs2eXCpYmzojYV23QLzC2+6j5IKfAIw7a+C8b4NWs9b9qWJ1sI2NCycYanObUSebANoMs6+rb47oAfa6idm+sTuHh3rHZel95nekzdjO2HJoLcAu09UoJhCKlOpRFd9IvPwEl8fILV80gjna5VOwNzJmdbnRKUEcY3KpjM3hjRKtC6nrN9YaJRZJNGx54oeVCkAABzvhkFz2F/3Nra0nTyetAocNKQBjyBr/k3uyut+wFIg/MgocTfDMwAAAA="
rtFa = "XkqYzjKF9wrP5AyLJqr4Bi4jDtlzJarBV0Hrssh8fPcmNzBkNTQ3NTAtYzYwZC00NGUxLThiM2MtZjQ2ZWE3ODc0MzU3IzEzNDIyOTQ2OTU0NzE1NzI1OSMyOTc3MTJhMi05MGQ1LTAwMDAtMmY2ZC1lMWRlNDkyMzBiZDMjd2FuZ3hmJTQwY21nb3MuY29tIzc3NiNZMXQyM1pscEpmS2Exc3lUb3k3NUVlUXVoQUEjWTF0MjNabHBKZkthMXN5VG95NzVFZVF1aEFBErjqNnF3VBBmRzzHq2eb+0H93/V1zrCozZZnR7GlnK0RI2e1UAHI2z0l6y3Nc6b5knlpPUcO5yyd2L/qCfITRlC9I4cREEaT2irxgYJv+cBguSPwvqbakzqqESYmttQqulZiFO0NZuQRy6BNPIhx4egAMdSG9iBwB9Nqy3sciczQ88Xh/CWjPb/m5tsWe1qq3jNDvqf3PO8Vwsp9K9+wHp/sl8RDhP0UO0KQJpxmrpbgGazIJbwHerNMZCsKQI0Sl5W4eDFK/FNcl1JT8DplSvZrAQx8VU4gig0+sAEd7naT7U2L20ACedQf9uKE8F//0z6i8jo/xYR/vaGDZcIe18wAAAA="
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
    "Service_Data_Store_Type": "",
    "Service_Data_Ftp_Auth": [],
    "Service_Data_Path": "",
    "Service_Data_Ftp_Port": 21,
    "Service_Data_Ftp_Port_List": [],
    "Service_Data_Ftp_Timeout_Seconds": 30,
    "Service_Data_Ftp_Passive_Mode": True,
    "Service_Data_Ftp_Retry_Count": 3,
    "Service_Data_Ftp_Retry_Interval_Seconds": 5,
    "Service_Data_Smb_Host": "",
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
service_data_store_type = DEFAULT_CONFIG["Service_Data_Store_Type"]
service_data_ftp_auth = DEFAULT_CONFIG["Service_Data_Ftp_Auth"]
service_data_path = DEFAULT_CONFIG["Service_Data_Path"]
service_data_ftp_port = DEFAULT_CONFIG["Service_Data_Ftp_Port"]
service_data_ftp_port_list = DEFAULT_CONFIG["Service_Data_Ftp_Port_List"]
service_data_ftp_timeout_seconds = DEFAULT_CONFIG["Service_Data_Ftp_Timeout_Seconds"]
service_data_ftp_passive_mode = DEFAULT_CONFIG["Service_Data_Ftp_Passive_Mode"]
service_data_ftp_retry_count = DEFAULT_CONFIG["Service_Data_Ftp_Retry_Count"]
service_data_ftp_retry_interval_seconds = DEFAULT_CONFIG["Service_Data_Ftp_Retry_Interval_Seconds"]
service_data_smb_host = DEFAULT_CONFIG["Service_Data_Smb_Host"]
DEV_TARGET_FOLDERS = ["刘晴", "茹小龙", "周利明"]
DEV_FOLDER_PATTERN = re.compile(r"^(20\d{2})_(\d{1,2})B$", re.IGNORECASE)
LIU_QING_SEGMENT_SEPARATOR_PATTERN = re.compile(r"(?:\r?\n)={10,}(?:\r?\n)")
RU_XIAO_LONG_SEGMENT_SEPARATOR_PATTERN = re.compile(r"(?:\r?\n)-{10,}(?:\r?\n)")
LIU_QING_FIELD_ALIASES = {
    "Action": "action",
    "操作动作": "action",
    "Start Time": "start_time",
    "开始时间": "start_time",
    "操作开始时间": "start_time",
    "End Time": "end_time",
    "结束时间": "end_time",
    "操作结束时间": "end_time",
    "Computer Name": "computer_name",
    "机器名": "computer_name",
    "Login User": "login_user",
    "操作人员": "login_user",
    "Execution User": "execution_user",
    "执行用户": "execution_user",
    "Result": "result",
    "操作结果": "result",
    "Details": "operation_details",
    "审计详情": "operation_details",
    "审计说明": "operation_details",
    "上传时间": "upload_time",
}
RU_XIAO_LONG_FIELD_ALIASES = {
    "操作动作": "action",
    "操作开始时间": "start_time",
    "操作结束时间": "end_time",
    "UC导包成功时间": "uc_import_success_times",
    "机器名": "computer_name",
    "操作人员": "login_user",
    "操作结果": "result",
    "审计说明": "operation_details",
    "下载时间": "download_time",
}
LIU_QING_ACTION_CATALOG = [
    ("get_update_by_catalog", "任务流程类 Action", "GetUpdateByCatalog", ["getupdatebycatalog"]),
    ("export_metadata_from_wsus", "任务流程类 Action", "Export Metadata from WSUS", ["export metadata from wsus"]),
    ("extract_scissor_refine_metadata", "任务流程类 Action", "Extract, Scissor & Refine Metadata", ["extract, scissor & refine metadata", "extract scissor refine metadata"]),
    ("export_svg_files", "任务流程类 Action", "Export SVG Files", ["export svg files"]),
    ("download_content_from_xml", "任务流程类 Action", "Download Content from XML", ["download content from xml"]),
    ("ftp_connect", "FTP/FTPS 上传连接类 Action", "FTP 连接", ["ftp 连接", "ftp connect", "connect ftp"]),
    ("ftp_upload_update_file", "FTP/FTPS 上传连接类 Action", "FTP 上传更新文件", ["ftp 上传更新文件", "ftp upload update file"]),
    ("ftp_upload_completed", "FTP/FTPS 上传连接类 Action", "FTP 上传完成", ["ftp 上传完成", "ftp upload completed", "ftp upload complete"]),
    ("upload_file_to_ftps", "FTP/FTPS 上传连接类 Action", "上传文件到 FTPS", ["上传文件到ftps", "上传文件到 ftps", "upload file to ftps"]),
]

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
    global service_data_store_type
    global service_data_ftp_auth
    global service_data_path
    global service_data_ftp_port
    global service_data_ftp_port_list
    global service_data_ftp_timeout_seconds
    global service_data_ftp_passive_mode
    global service_data_ftp_retry_count
    global service_data_ftp_retry_interval_seconds
    global service_data_smb_host

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
    service_data_store_type = str(
        config.get("Service_Data_Store_Type", DEFAULT_CONFIG["Service_Data_Store_Type"])
    ).strip()
    service_data_ftp_auth = config.get(
        "Service_Data_Ftp_Auth", DEFAULT_CONFIG["Service_Data_Ftp_Auth"]
    )
    service_data_path = str(
        config.get("Service_Data_Path", DEFAULT_CONFIG["Service_Data_Path"])
    ).strip()
    service_data_ftp_port = int(
        config.get("Service_Data_Ftp_Port", DEFAULT_CONFIG["Service_Data_Ftp_Port"])
    )
    raw_port_list = config.get(
        "Service_Data_Ftp_Port_List", DEFAULT_CONFIG["Service_Data_Ftp_Port_List"]
    )
    if isinstance(raw_port_list, list):
        service_data_ftp_port_list = [
            int(port) for port in raw_port_list if str(port).strip()
        ]
    else:
        service_data_ftp_port_list = []
    service_data_ftp_timeout_seconds = int(
        config.get(
            "Service_Data_Ftp_Timeout_Seconds",
            DEFAULT_CONFIG["Service_Data_Ftp_Timeout_Seconds"],
        )
    )
    service_data_ftp_passive_mode = bool(
        config.get(
            "Service_Data_Ftp_Passive_Mode",
            DEFAULT_CONFIG["Service_Data_Ftp_Passive_Mode"],
        )
    )
    service_data_ftp_retry_count = max(
        1,
        int(
            config.get(
                "Service_Data_Ftp_Retry_Count",
                DEFAULT_CONFIG["Service_Data_Ftp_Retry_Count"],
            )
        ),
    )
    service_data_ftp_retry_interval_seconds = max(
        0,
        int(
            config.get(
                "Service_Data_Ftp_Retry_Interval_Seconds",
                DEFAULT_CONFIG["Service_Data_Ftp_Retry_Interval_Seconds"],
            )
        ),
    )
    service_data_smb_host = str(
        config.get("Service_Data_Smb_Host", DEFAULT_CONFIG["Service_Data_Smb_Host"])
    ).strip()


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
    logger.info(message)


def log_error(message):
    logger.error(message)


def get_service_data_ftp_host_and_path():
    if service_data_store_type.lower() != "ftp":
        return None, None

    if not isinstance(service_data_ftp_auth, list) or len(service_data_ftp_auth) < 2:
        raise ValueError("Service_Data_Ftp_Auth 配置无效，必须至少包含认证方式和主机地址。")

    auth_type = str(service_data_ftp_auth[0]).strip()
    ftp_host = str(service_data_ftp_auth[1]).strip()

    if auth_type != "Windows 凭据":
        raise ValueError(f"暂不支持的 Service_Data_Ftp_Auth 认证方式：{auth_type}")

    if not ftp_host:
        raise ValueError("Service_Data_Ftp_Auth 中未提供 FTP 主机地址。")

    if not service_data_path:
        raise ValueError("Service_Data_Path 未配置。")

    normalized_path = service_data_path.replace("\\", "/").strip()
    if not normalized_path.startswith("/"):
        normalized_path = "/" + normalized_path

    return ftp_host, normalized_path


def get_service_data_smb_path():
    if service_data_store_type.lower() not in ("smb", "windows_share", "windows share"):
        return None

    if not service_data_path:
        raise ValueError("Service_Data_Path 未配置。")

    normalized_path = service_data_path.strip()
    if normalized_path.startswith("\\\\"):
        return normalized_path

    smb_host = service_data_smb_host.strip()
    if not smb_host and isinstance(service_data_ftp_auth, list) and len(service_data_ftp_auth) >= 2:
        smb_host = str(service_data_ftp_auth[1]).strip()

    if not smb_host:
        raise ValueError("SMB 模式下未提供主机地址，请配置 Service_Data_Smb_Host。")

    normalized_path = normalized_path.lstrip("\\/")
    normalized_path = normalized_path.replace("/", "\\")
    return "\\\\" + smb_host + "\\" + normalized_path


class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


class CREDENTIAL_ATTRIBUTEW(ctypes.Structure):
    _fields_ = [
        ("Keyword", wintypes.LPWSTR),
        ("Flags", wintypes.DWORD),
        ("ValueSize", wintypes.DWORD),
        ("Value", ctypes.POINTER(ctypes.c_ubyte)),
    ]


class CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.POINTER(CREDENTIAL_ATTRIBUTEW)),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


def read_windows_credential(target_name: str):
    advapi32 = ctypes.WinDLL("Advapi32.dll")
    cred_ptr = ctypes.POINTER(CREDENTIALW)()
    cred_type_generic = 1
    cred_type_domain_password = 2

    advapi32.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIALW))]
    advapi32.CredReadW.restype = wintypes.BOOL
    advapi32.CredFree.argtypes = [ctypes.c_void_p]
    advapi32.CredFree.restype = None

    for cred_type in (cred_type_generic, cred_type_domain_password):
        cred_ptr = ctypes.POINTER(CREDENTIALW)()
        if advapi32.CredReadW(target_name, cred_type, 0, ctypes.byref(cred_ptr)):
            try:
                credential = cred_ptr.contents
                username = credential.UserName or ""
                password = ""
                if credential.CredentialBlob and credential.CredentialBlobSize:
                    password = ctypes.string_at(
                        credential.CredentialBlob,
                        credential.CredentialBlobSize,
                    ).decode("utf-16-le").rstrip("\x00")
                return username, password
            finally:
                advapi32.CredFree(cred_ptr)

    raise FileNotFoundError(f"未在 Windows 凭据中找到目标：{target_name}")


def read_ftp_windows_credential(ftp_host: str):
    candidate_target_names = [
        ftp_host,
        f"TERMSRV/{ftp_host}",
        f"Microsoft_FTP_{ftp_host}",
        f"ftp://{ftp_host}",
        f"LegacyGeneric:target=ftp://{ftp_host}",
        f"LegacyGeneric:target={ftp_host}",
    ]

    last_error = None
    for target_name in candidate_target_names:
        try:
            return read_windows_credential(target_name)
        except FileNotFoundError as ex:
            last_error = ex

    raise FileNotFoundError(
        f"未在 Windows 凭据中找到 FTP 主机 {ftp_host} 对应的凭据，请确认该主机的 Windows 凭据已保存。"
    ) from last_error


def create_ftp_connection():
    ftp_host, remote_path = get_service_data_ftp_host_and_path()
    username, password = read_ftp_windows_credential(ftp_host)

    candidate_ports = []
    for port in [service_data_ftp_port, *service_data_ftp_port_list]:
        if port not in candidate_ports:
            candidate_ports.append(port)

    last_error = None
    for ftp_port in candidate_ports:
        try:
            probe_ftp_tcp_connectivity(ftp_host, ftp_port, service_data_ftp_timeout_seconds)

            ftp = FTP()
            ftp.connect(ftp_host, ftp_port, timeout=service_data_ftp_timeout_seconds)
            ftp.login(username, password)
            ftp.encoding = "utf-8"
            ftp.set_pasv(service_data_ftp_passive_mode)
            return ftp, ftp_host, remote_path, ftp_port
        except Exception as ex:
            last_error = ex
            log_error(f"FTP 连接失败：host={ftp_host}, port={ftp_port}，原因：{ex}")

    raise ConnectionError(
        f"无法连接 FTP 主机 {ftp_host}，已尝试端口：{candidate_ports}"
    ) from last_error


def probe_ftp_tcp_connectivity(host: str, port: int, timeout_seconds: int):
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return
    except OSError as ex:
        raise ConnectionError(
            f"TCP 预连接失败：{host}:{port}，timeout={timeout_seconds}s，原因：{ex}"
        ) from ex


def ensure_local_directory(path: str):
    os.makedirs(path, exist_ok=True)


def is_ftp_directory(ftp: FTP, remote_path: str):
    current_dir = ftp.pwd()
    try:
        ftp.cwd(remote_path)
        ftp.cwd(current_dir)
        return True
    except error_perm:
        return False


def list_ftp_entries(ftp: FTP, remote_path: str):
    entries = []

    def parse_line(line: str):
        parts = line.split(maxsplit=8)
        if len(parts) < 9:
            return
        name = parts[8]
        if name in (".", ".."): 
            return
        entry_type = "dir" if parts[0].startswith("d") else "file"
        entries.append({"name": name, "type": entry_type})

    try:
        ftp.retrlines(f"LIST {remote_path}", parse_line)
        return entries
    except error_perm as ex:
        raise FileNotFoundError(f"无法列出 FTP 路径：{remote_path}，原因：{ex}") from ex


def download_ftp_tree_to_local(ftp: FTP, remote_root: str, local_root: str):
    ensure_local_directory(local_root)

    for entry in list_ftp_entries(ftp, remote_root):
        remote_item_path = f"{remote_root.rstrip('/')}/{entry['name']}"
        local_item_path = os.path.join(local_root, entry["name"])

        if entry["type"] == "dir" and is_ftp_directory(ftp, remote_item_path):
            download_ftp_tree_to_local(ftp, remote_item_path, local_item_path)
            continue

        ensure_local_directory(os.path.dirname(local_item_path))
        with open(local_item_path, "wb") as local_file:
            ftp.retrbinary(f"RETR {remote_item_path}", local_file.write)


def get_service_data_remote_display_path(ftp_host: str, remote_path: str):
    return f"ftp://{ftp_host}{remote_path}"


def build_service_data_display_path():
    store_type = service_data_store_type.lower()
    if store_type == "ftp":
        ftp_host, remote_path = get_service_data_ftp_host_and_path()
        return get_service_data_remote_display_path(ftp_host, remote_path)
    if store_type in ("smb", "windows_share", "windows share"):
        return get_service_data_smb_path()
    return service_data_path


def get_service_data_base_local():
    return os.path.join(base_local, "Service_data")


def get_dev_data_base_local():
    return os.path.join(base_local, "Dev_data")


def get_dev_analysis_latest_json_path():
    return os.path.join(log_dir, "dev_analysis_latest.json")


def get_dev_analysis_latest_text_path():
    return os.path.join(log_dir, "dev_analysis_latest.txt")


def compute_file_hash(file_path: str):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def build_directory_snapshot(root_path: str):
    snapshot = {"folders": [], "files": []}

    for current_root, dirs, files in os.walk(root_path):
        relative_root = os.path.relpath(current_root, root_path)
        if relative_root != ".":
            snapshot["folders"].append(relative_root.replace("/", "\\"))

        for dir_name in sorted(dirs):
            dir_path = os.path.join(current_root, dir_name)
            relative_dir_path = os.path.relpath(dir_path, root_path)
            snapshot["folders"].append(relative_dir_path.replace("/", "\\"))

        for file_name in sorted(files):
            full_path = os.path.join(current_root, file_name)
            relative_path = os.path.relpath(full_path, root_path)
            snapshot["files"].append({
                "path": relative_path.replace("/", "\\"),
                "size": os.path.getsize(full_path),
                "hash": compute_file_hash(full_path),
            })

    snapshot["folders"] = sorted(set(snapshot["folders"]))
    snapshot["files"] = sorted(snapshot["files"], key=lambda item: item["path"])
    return snapshot


def count_files_in_directory(root_path: str):
    return sum(len(files) for _, _, files in os.walk(root_path))


def get_latest_snapshot_root(base_local_path: str, temp_prefix: str):
    if not os.path.isdir(base_local_path):
        return None

    candidate_dirs = []
    for entry in os.listdir(base_local_path):
        entry_path = os.path.join(base_local_path, entry)
        if os.path.isdir(entry_path) and not entry.startswith(temp_prefix):
            candidate_dirs.append(entry_path)

    if not candidate_dirs:
        return None

    candidate_dirs.sort(key=os.path.getmtime, reverse=True)
    return candidate_dirs[0]


def remove_empty_parent_directories(path: str, stop_path: str):
    current_path = path
    stop_path = os.path.abspath(stop_path)
    while current_path and os.path.abspath(current_path).startswith(stop_path):
        if os.path.abspath(current_path) == stop_path:
            break
        try:
            os.rmdir(current_path)
        except OSError:
            break
        current_path = os.path.dirname(current_path)


def parse_dev_period_folder_name(folder_name: str):
    match = DEV_FOLDER_PATTERN.fullmatch(folder_name.strip())
    if not match:
        return None

    year = int(match.group(1))
    month = int(match.group(2))
    return {
        "folder_name": folder_name,
        "year": year,
        "month": month,
        "label": f"{year}-{month:02d}",
    }


def get_latest_service_data_snapshot_root(service_data_base_local: str):
    return get_latest_snapshot_root(service_data_base_local, "service_data_")


def copy_local_tree_to_temp(source_root: str, temp_root: str):
    ensure_local_directory(temp_root)

    for current_root, dirs, files in os.walk(source_root):
        relative_root = os.path.relpath(current_root, source_root)
        target_root = temp_root if relative_root == "." else os.path.join(temp_root, relative_root)
        ensure_local_directory(target_root)

        for dir_name in dirs:
            ensure_local_directory(os.path.join(target_root, dir_name))

        for file_name in files:
            source_file_path = os.path.join(current_root, file_name)
            target_file_path = os.path.join(target_root, file_name)
            shutil.copy2(source_file_path, target_file_path)


def finalize_service_data_snapshot(temp_root: str, remote_display_path: str):
    current_snapshot = build_directory_snapshot(temp_root)
    service_data_base_local = get_service_data_base_local()
    latest_local_snapshot_root = get_latest_service_data_snapshot_root(service_data_base_local)

    if latest_local_snapshot_root and current_snapshot == build_directory_snapshot(latest_local_snapshot_root):
        shutil.rmtree(temp_root, ignore_errors=True)
        log_info(f"目前 {remote_display_path} 地址中数据不变，不再本地存储。")
        return

    time_folder = datetime.now().strftime("%Y%m%d%H%M%S")
    target_local_root = os.path.join(service_data_base_local, time_folder)
    os.rename(temp_root, target_local_root)

    file_count = sum(len(files) for _, _, files in os.walk(target_local_root))
    log_info(f"✅ Service_Data 数据已保存到本地：{target_local_root}")
    log_info(f"📄 本次共保存文件：{file_count} 个")


def download_service_data_from_smb():
    remote_path = get_service_data_smb_path()

    if not os.path.exists(remote_path):
        raise FileNotFoundError(f"无法访问 Windows 共享路径：{remote_path}")

    log_info("\n" + "=" * 70)
    log_info("📥 开始获取服务部门 Service_Data 数据")
    log_info("=" * 70)
    log_info(f"远程路径：{remote_path}")

    service_data_base_local = get_service_data_base_local()
    os.makedirs(service_data_base_local, exist_ok=True)

    temp_root = tempfile.mkdtemp(prefix="service_data_", dir=service_data_base_local)
    try:
        copy_local_tree_to_temp(remote_path, temp_root)
        finalize_service_data_snapshot(temp_root, remote_path)
        temp_root = None
    finally:
        if temp_root and os.path.isdir(temp_root):
            shutil.rmtree(temp_root, ignore_errors=True)


def download_service_data_from_ftp():
    if service_data_store_type.lower() != "ftp":
        return

    ftp = None
    temp_root = None
    last_error = None

    for attempt in range(1, service_data_ftp_retry_count + 1):
        ftp = None
        temp_root = None
        try:
            ftp, ftp_host, remote_path, connected_port = create_ftp_connection()
            remote_display_path = get_service_data_remote_display_path(ftp_host, remote_path)

            log_info("\n" + "=" * 70)
            log_info("📥 开始获取服务部门 Service_Data 数据")
            log_info("=" * 70)
            log_info(f"远程路径：{remote_display_path}")
            log_info(
                f"FTP 连接参数：host={ftp_host}, port={connected_port}, timeout={service_data_ftp_timeout_seconds}s, passive={service_data_ftp_passive_mode}, attempt={attempt}/{service_data_ftp_retry_count}"
            )

            service_data_base_local = get_service_data_base_local()
            os.makedirs(service_data_base_local, exist_ok=True)

            temp_root = tempfile.mkdtemp(prefix="service_data_", dir=service_data_base_local)
            download_ftp_tree_to_local(ftp, remote_path, temp_root)

            finalize_service_data_snapshot(temp_root, remote_display_path)
            temp_root = None
            return
        except Exception as ex:
            last_error = ex
            if attempt < service_data_ftp_retry_count:
                log_error(
                    f"获取 Service_Data 数据失败，第 {attempt} 次重试前等待 {service_data_ftp_retry_interval_seconds} 秒：{ex}"
                )
                time.sleep(service_data_ftp_retry_interval_seconds)
            else:
                raise
        finally:
            if ftp is not None:
                try:
                    ftp.quit()
                except Exception:
                    ftp.close()
            if temp_root and os.path.isdir(temp_root):
                shutil.rmtree(temp_root, ignore_errors=True)


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


def download_sharepoint_folder_tree(folder_relative_url: str, local_root: str):
    ensure_local_directory(local_root)

    for folder in get_folder_items(folder_relative_url, "folders"):
        folder_name = folder.get("Name", "")
        folder_path = folder.get("ServerRelativeUrl", "")
        if not folder_name or folder_name == "Forms" or not folder_path:
            continue
        download_sharepoint_folder_tree(
            folder_path,
            os.path.join(local_root, folder_name),
        )

    for file in get_folder_items(folder_relative_url, "files"):
        file_name = file.get("Name", "")
        file_path = file.get("ServerRelativeUrl", "")
        if not file_name or not file_path:
            continue
        download_file(file_path, os.path.join(local_root, file_name))


def get_monitored_dev_remote_folders():
    remote_folders = {}
    for folder in get_folder_items(root_sub_folder, "folders"):
        folder_name = folder.get("Name", "")
        folder_path = folder.get("ServerRelativeUrl", "")
        if folder_name in DEV_TARGET_FOLDERS and folder_path:
            remote_folders[folder_name] = folder_path
    return remote_folders


def build_dev_period_download_plan():
    download_plan = []
    remote_people = get_monitored_dev_remote_folders()

    for person_name in DEV_TARGET_FOLDERS:
        person_remote_path = remote_people.get(person_name)
        if not person_remote_path:
            log_info(f"研发目录缺失：{person_name}")
            continue

        for folder in get_folder_items(person_remote_path, "folders"):
            folder_name = folder.get("Name", "")
            folder_path = folder.get("ServerRelativeUrl", "")
            period_info = parse_dev_period_folder_name(folder_name)
            if not period_info or not folder_path:
                continue
            download_plan.append(
                {
                    "person_name": person_name,
                    "remote_path": folder_path,
                    **period_info,
                }
            )

    download_plan.sort(
        key=lambda item: (item["year"], item["month"], item["person_name"]),
        reverse=True,
    )
    return download_plan


def collect_dev_remote_state():
    state = {"folders": [], "files": []}

    def walk(current_folder: str):
        folders = get_folder_items(current_folder, "folders")
        for folder in folders:
            name = folder.get("Name", "")
            path = folder.get("ServerRelativeUrl", "")
            if not name or name == "Forms" or not path:
                continue
            state["folders"].append({"name": name, "path": path})
            walk(path)

        files = get_folder_items(current_folder, "files")
        for file in files:
            name = file.get("Name", "")
            path = file.get("ServerRelativeUrl", "")
            if not name or not path:
                continue
            state["files"].append(
                {
                    "name": name,
                    "path": path,
                    "size": str(file.get("Length", "")),
                    "modified": str(file.get("TimeLastModified", "")),
                }
            )

    remote_people = get_monitored_dev_remote_folders()
    for person_name in DEV_TARGET_FOLDERS:
        person_path = remote_people.get(person_name)
        if not person_path:
            continue
        state["folders"].append({"name": person_name, "path": person_path})
        walk(person_path)

    state["folders"] = sorted(state["folders"], key=lambda item: item["path"])
    state["files"] = sorted(state["files"], key=lambda item: item["path"])
    return state


def save_changed_dev_folders_to_local():
    log_info("\n" + "=" * 70)
    log_info("📥 开始同步研发部门 Dev_data 数据")
    log_info("=" * 70)

    dev_data_base_local = get_dev_data_base_local()
    os.makedirs(dev_data_base_local, exist_ok=True)

    latest_snapshot_root = get_latest_snapshot_root(dev_data_base_local, "dev_data_")
    temp_root = tempfile.mkdtemp(prefix="dev_data_", dir=dev_data_base_local)
    changed_folders = []

    try:
        for period_plan in build_dev_period_download_plan():
            person_name = period_plan["person_name"]
            folder_name = period_plan["folder_name"]
            remote_path = period_plan["remote_path"]
            temp_period_root = os.path.join(temp_root, person_name, folder_name)

            log_info(f"正在检查研发目录：{person_name}/{folder_name}")
            download_sharepoint_folder_tree(remote_path, temp_period_root)

            current_snapshot = build_directory_snapshot(temp_period_root)
            latest_period_root = None
            if latest_snapshot_root:
                latest_period_root = os.path.join(latest_snapshot_root, person_name, folder_name)

            if latest_period_root and os.path.isdir(latest_period_root):
                latest_snapshot = build_directory_snapshot(latest_period_root)
                if current_snapshot == latest_snapshot:
                    shutil.rmtree(temp_period_root, ignore_errors=True)
                    remove_empty_parent_directories(os.path.dirname(temp_period_root), temp_root)
                    log_info(f"⏭️ 研发目录无变化：{person_name}/{folder_name}")
                    continue

            file_count = count_files_in_directory(temp_period_root)
            changed_folders.append(
                {
                    "person_name": person_name,
                    "folder_name": folder_name,
                    "year": period_plan["year"],
                    "month": period_plan["month"],
                    "remote_path": remote_path,
                    "file_count": file_count,
                }
            )
            log_info(f"✅ 研发目录发现变化：{person_name}/{folder_name}，文件数：{file_count}")

        if not changed_folders:
            shutil.rmtree(temp_root, ignore_errors=True)
            log_info("研发目录本次无新增或变化文件，不生成新的 Dev_data 快照。")
            return None, []

        time_folder = datetime.now().strftime("%Y%m%d%H%M%S")
        target_root = os.path.join(dev_data_base_local, time_folder)
        os.rename(temp_root, target_root)
        log_info(f"✅ 研发部门 Dev_data 已保存到本地：{target_root}")
        log_info(f"📁 本次共保存变化目录：{len(changed_folders)} 个")
        log_info(f"📄 本次共保存文件：{count_files_in_directory(target_root)} 个")
        return target_root, changed_folders
    finally:
        if os.path.isdir(temp_root):
            shutil.rmtree(temp_root, ignore_errors=True)


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


def build_local_file_records(folder_path: str):
    records = []
    for current_root, _, files in os.walk(folder_path):
        for file_name in sorted(files):
            file_path = os.path.join(current_root, file_name)
            relative_path = os.path.relpath(file_path, folder_path).replace("/", "\\")
            stat = os.stat(file_path)
            records.append(
                {
                    "file_name": file_name,
                    "relative_path": relative_path,
                    "size": stat.st_size,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
    return records


def read_text_file_content(file_path: str):
    encodings = ["utf-8", "utf-8-sig", "gbk", "mbcs"]

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue

    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        return file.read()


def parse_operation_datetime(value: str):
    if not value:
        return None

    normalized_value = str(value).strip()
    for date_format in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
        try:
            return datetime.strptime(normalized_value, date_format)
        except ValueError:
            continue
    return None


def normalize_operation_datetime_text(value: str):
    if not value:
        return ""

    normalized_value = str(value).strip()
    for date_format in [
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%m/%d/%Y, %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
    ]:
        try:
            return datetime.strptime(normalized_value, date_format).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    return normalized_value


def normalize_liu_qing_action(action_text: str):
    raw_action = str(action_text or "").strip()
    normalized_action = re.sub(r"^step\s*\d+\s*[:：-]?\s*", "", raw_action, flags=re.IGNORECASE)
    normalized_action = re.sub(r"\bstep\s*\d+\b[:：-]?\s*", "", normalized_action, flags=re.IGNORECASE).strip()
    lowered_action = normalized_action.lower()
    compact_action = re.sub(r"\s+", "", lowered_action)

    for action_code, category_name, action_name, keywords in LIU_QING_ACTION_CATALOG:
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in lowered_action or re.sub(r"\s+", "", keyword_lower) in compact_action:
                return {
                    "action_code": action_code,
                    "category_name": category_name,
                    "action_name": action_name,
                    "action_raw": raw_action,
                }

    return {
        "action_code": "other",
        "category_name": "其他 Action",
        "action_name": normalized_action or raw_action or "未知 Action",
        "action_raw": raw_action,
    }


def summarize_liu_qing_actions(operation_records):
    summary_map = {}

    for operation_record in operation_records:
        summary_key = (operation_record["category_name"], operation_record["action_name"])
        if summary_key not in summary_map:
            summary_map[summary_key] = {
                "category_name": operation_record["category_name"],
                "action_name": operation_record["action_name"],
                "count": 0,
            }
        summary_map[summary_key]["count"] += 1

    return sorted(summary_map.values(), key=lambda item: (item["category_name"], item["action_name"]))


def parse_liu_qing_segment(segment_text: str, source_file_path: str):
    lines = [line.rstrip() for line in segment_text.splitlines() if line.strip()]
    if not lines:
        return None

    parsed_fields = {
        "action": "",
        "start_time": "",
        "end_time": "",
        "computer_name": "",
        "login_user": "",
        "execution_user": "",
        "result": "",
        "operation_details": "",
        "upload_time": "",
    }
    current_field = None
    field_pattern = re.compile(r"^\s*([^:：]+?)\s*[:：]\s*(.*)$")

    for line in lines:
        matched_line = field_pattern.match(line)
        if matched_line:
            alias_name = matched_line.group(1).strip()
            field_value = matched_line.group(2).strip()
            target_field = LIU_QING_FIELD_ALIASES.get(alias_name)
            if target_field:
                parsed_fields[target_field] = field_value
                current_field = target_field
                continue

        if current_field == "operation_details":
            parsed_fields[current_field] = f"{parsed_fields[current_field]}\n{line.strip()}".strip()
            continue

    if not parsed_fields["action"]:
        return None

    if parsed_fields["upload_time"]:
        if parsed_fields["operation_details"]:
            parsed_fields["operation_details"] = f"{parsed_fields['operation_details']} -- 上传时间={parsed_fields['upload_time']}"
        else:
            parsed_fields["operation_details"] = f"上传时间={parsed_fields['upload_time']}"

    action_info = normalize_liu_qing_action(parsed_fields["action"])
    start_time_value = parsed_fields["start_time"]
    end_time_value = parsed_fields["end_time"]
    sort_datetime = parse_operation_datetime(start_time_value) or parse_operation_datetime(end_time_value)

    return {
        "action_code": action_info["action_code"],
        "category_name": action_info["category_name"],
        "action_name": action_info["action_name"],
        "action_raw": action_info["action_raw"],
        "start_time": start_time_value,
        "end_time": end_time_value,
        "computer_name": parsed_fields["computer_name"],
        "login_user": parsed_fields["login_user"],
        "execution_user": parsed_fields["execution_user"],
        "result": parsed_fields["result"],
        "operation_details": parsed_fields["operation_details"],
        "details": parsed_fields["operation_details"],
        "source_file": os.path.basename(source_file_path),
        "source_relative_path": os.path.basename(source_file_path),
        "sort_time": sort_datetime.strftime("%Y-%m-%d %H:%M:%S") if sort_datetime else (start_time_value or end_time_value or ""),
    }


def parse_liu_qing_operation_records(period_folder_path: str):
    operation_records = []
    file_stats = []
    unclassified_actions = []
    skipped_segments = []
    total_segment_count = 0

    for current_root, _, files in os.walk(period_folder_path):
        for file_name in sorted(files):
            if not file_name.lower().endswith((".log", ".txt")):
                continue

            file_path = os.path.join(current_root, file_name)
            relative_path = os.path.relpath(file_path, period_folder_path).replace("/", "\\")
            log_info(f"开始分析刘晴日志文件：{relative_path}")
            try:
                file_content = read_text_file_content(file_path)
            except Exception as ex:
                log_error(f"读取刘晴日志文件失败：{file_path}，原因：{ex}")
                continue

            normalized_content = file_content.replace("\r\n", "\n")
            segments = [segment.strip() for segment in LIU_QING_SEGMENT_SEPARATOR_PATTERN.split(normalized_content) if segment.strip()]
            if not segments and normalized_content.strip():
                segments = [normalized_content.strip()]

            log_info(f"刘晴日志文件切分完成：{relative_path}，识别到片段数={len(segments)}")
            parsed_count = 0
            skipped_count = 0
            unclassified_count = 0
            total_segment_count += len(segments)

            for segment_index, segment in enumerate(segments, 1):
                operation_record = parse_liu_qing_segment(segment, file_path)
                if operation_record is None:
                    skipped_count += 1
                    skipped_segments.append(
                        {
                            "source_relative_path": relative_path,
                            "segment_index": segment_index,
                            "segment_preview": segment[:200],
                            "reason": "未识别到操作动作字段",
                        }
                    )
                    log_info(
                        f"刘晴日志片段跳过：文件={relative_path}，片段序号={segment_index}，原因=未识别到操作动作字段"
                    )
                    continue
                parsed_count += 1
                operation_record["source_relative_path"] = relative_path
                operation_record["segment_index"] = segment_index
                operation_records.append(operation_record)

                if operation_record["action_code"] == "other":
                    unclassified_count += 1
                    unclassified_actions.append(
                        {
                            "source_relative_path": relative_path,
                            "segment_index": segment_index,
                            "action_raw": operation_record["action_raw"],
                            "start_time": operation_record["start_time"],
                            "end_time": operation_record["end_time"],
                        }
                    )
                    log_info(
                        f"刘晴日志发现未归类操作：文件={relative_path}，片段序号={segment_index}，原始动作={operation_record['action_raw']}"
                    )

            file_stat = {
                "source_relative_path": relative_path,
                "segment_count": len(segments),
                "parsed_segment_count": parsed_count,
                "skipped_segment_count": skipped_count,
                "unclassified_action_count": unclassified_count,
            }
            file_stats.append(file_stat)
            log_info(
                f"刘晴日志解析统计：文件={relative_path}，片段总数={file_stat['segment_count']}，已解析={parsed_count}，跳过={skipped_count}，未归类动作={unclassified_count}"
            )

    operation_records.sort(key=lambda item: (item["sort_time"], item["action_name"], item["source_relative_path"]))
    parse_diagnostics = {
        "summary": {
            "file_count": len(file_stats),
            "segment_count": total_segment_count,
            "parsed_segment_count": len(operation_records),
            "skipped_segment_count": len(skipped_segments),
            "unclassified_action_count": len(unclassified_actions),
        },
        "file_stats": file_stats,
        "unclassified_actions": unclassified_actions,
        "skipped_segments": skipped_segments,
    }
    return operation_records, parse_diagnostics


def analyze_liu_qing_folder(period_folder_path: str, period_info):
    if not os.path.isdir(period_folder_path):
        return {
            "status": "missing",
            "title": "刘晴操作日志分析",
            "details": [f"目录不存在：{period_folder_path}"],
            "action_summary": [],
            "operation_records": [],
            "parse_diagnostics": None,
        }

    operation_records, parse_diagnostics = parse_liu_qing_operation_records(period_folder_path)
    action_summary = summarize_liu_qing_actions(operation_records)
    details = [
        f"目录：{period_info['folder_name']}",
        f"年月标记：{period_info['label']}",
        f"日志文件数：{len([item for item in build_local_file_records(period_folder_path) if item['file_name'].lower().endswith(('.log', '.txt'))])}",
        f"实质性操作片段数：{len(operation_records)}",
        f"Action 分类数：{len(action_summary)}",
    ]

    if parse_diagnostics["summary"]["skipped_segment_count"]:
        details.append(f"未识别片段数：{parse_diagnostics['summary']['skipped_segment_count']}")
    if parse_diagnostics["summary"]["unclassified_action_count"]:
        details.append(f"未归类动作数：{parse_diagnostics['summary']['unclassified_action_count']}")

    if not operation_records:
        details.append("当前目录未解析到符合格式的操作片段。")

    return {
        "status": "completed" if operation_records else "warning",
        "title": "刘晴操作日志分析",
        "details": details,
        "action_summary": action_summary,
        "operation_records": operation_records,
        "parse_diagnostics": parse_diagnostics,
    }


def summarize_ru_xiao_long_actions(operation_records):
    summary_map = {}

    for operation_record in operation_records:
        summary_key = (operation_record["category_name"], operation_record["action_name"])
        if summary_key not in summary_map:
            summary_map[summary_key] = {
                "category_name": operation_record["category_name"],
                "action_name": operation_record["action_name"],
                "count": 0,
            }
        summary_map[summary_key]["count"] += 1

    return sorted(summary_map.values(), key=lambda item: (item["category_name"], item["action_name"]))


def parse_ru_xiao_long_segment(segment_text: str, source_file_path: str):
    lines = [line.rstrip() for line in segment_text.splitlines() if line.strip()]
    if not lines:
        return None

    parsed_fields = {
        "action": "",
        "start_time": "",
        "end_time": "",
        "uc_import_success_times": "",
        "computer_name": "",
        "login_user": "",
        "result": "",
        "operation_details": "",
        "download_time": "",
    }
    current_field = None
    field_pattern = re.compile(r"^\s*([^:：]+?)\s*[:：]\s*(.*)$")

    for line in lines:
        matched_line = field_pattern.match(line)
        if matched_line:
            alias_name = matched_line.group(1).strip()
            field_value = matched_line.group(2).strip()
            target_field = RU_XIAO_LONG_FIELD_ALIASES.get(alias_name)
            if target_field:
                parsed_fields[target_field] = field_value
                current_field = target_field
                continue

        if current_field == "operation_details":
            parsed_fields[current_field] = f"{parsed_fields[current_field]}\n{line.strip()}".strip()

    if parsed_fields["uc_import_success_times"]:
        try:
            success_times = ast.literal_eval(parsed_fields["uc_import_success_times"])
        except (ValueError, SyntaxError):
            success_times = []

        if isinstance(success_times, list):
            if success_times and not parsed_fields["start_time"]:
                parsed_fields["start_time"] = normalize_operation_datetime_text(success_times[0])
            if len(success_times) > 1 and not parsed_fields["end_time"]:
                parsed_fields["end_time"] = normalize_operation_datetime_text(success_times[1])

    parsed_fields["start_time"] = normalize_operation_datetime_text(parsed_fields["start_time"])
    parsed_fields["end_time"] = normalize_operation_datetime_text(parsed_fields["end_time"])

    if parsed_fields["download_time"]:
        normalized_download_time = normalize_operation_datetime_text(parsed_fields["download_time"])
        if parsed_fields["operation_details"]:
            parsed_fields["operation_details"] = f"{parsed_fields['operation_details']} -- 下载时间={normalized_download_time}"
        else:
            parsed_fields["operation_details"] = f"下载时间={normalized_download_time}"

    if not parsed_fields["action"]:
        return None

    sort_datetime = parse_operation_datetime(parsed_fields["start_time"]) or parse_operation_datetime(parsed_fields["end_time"])
    action_name = str(parsed_fields["action"]).strip()

    return {
        "action_code": re.sub(r"\W+", "_", action_name.lower()).strip("_") or "ru_action",
        "category_name": "TXT操作日志",
        "action_name": action_name,
        "action_raw": action_name,
        "start_time": parsed_fields["start_time"],
        "end_time": parsed_fields["end_time"],
        "computer_name": parsed_fields["computer_name"],
        "login_user": parsed_fields["login_user"],
        "execution_user": "",
        "result": parsed_fields["result"],
        "operation_details": parsed_fields["operation_details"],
        "details": parsed_fields["operation_details"],
        "source_file": os.path.basename(source_file_path),
        "source_relative_path": os.path.basename(source_file_path),
        "sort_time": sort_datetime.strftime("%Y-%m-%d %H:%M:%S") if sort_datetime else (parsed_fields["start_time"] or parsed_fields["end_time"] or ""),
    }


def parse_ru_xiao_long_operation_records(period_folder_path: str):
    operation_records = []

    for current_root, _, files in os.walk(period_folder_path):
        for file_name in sorted(files):
            if not file_name.lower().endswith(".txt"):
                continue

            file_path = os.path.join(current_root, file_name)
            try:
                file_content = read_text_file_content(file_path)
            except Exception as ex:
                log_error(f"读取茹小龙日志文件失败：{file_path}，原因：{ex}")
                continue

            normalized_content = file_content.replace("\r\n", "\n")
            segments = [segment.strip() for segment in RU_XIAO_LONG_SEGMENT_SEPARATOR_PATTERN.split(normalized_content) if segment.strip()]
            if not segments and normalized_content.strip():
                segments = [normalized_content.strip()]

            relative_path = os.path.relpath(file_path, period_folder_path).replace("/", "\\")
            log_info(f"开始分析茹小龙日志文件：{relative_path}")
            log_info(f"茹小龙日志文件切分完成：{relative_path}，识别到片段数={len(segments)}")

            for segment_index, segment in enumerate(segments, 1):
                operation_record = parse_ru_xiao_long_segment(segment, file_path)
                if operation_record is None:
                    log_info(
                        f"茹小龙日志片段跳过：文件={relative_path}，片段序号={segment_index}，原因=未识别到操作动作字段"
                    )
                    continue

                operation_record["source_relative_path"] = relative_path
                operation_record["segment_index"] = segment_index
                operation_records.append(operation_record)

            log_info(f"茹小龙日志解析统计：文件={relative_path}，已解析片段数={len([item for item in operation_records if item['source_relative_path'] == relative_path])}")

    operation_records.sort(key=lambda item: (item["sort_time"], item["action_name"], item["source_relative_path"]))
    return operation_records


def analyze_ru_xiao_long_folder(period_folder_path: str, period_info):
    if not os.path.isdir(period_folder_path):
        return {
            "status": "missing",
            "title": "茹小龙操作日志分析",
            "details": [f"目录不存在：{period_folder_path}"],
            "action_summary": [],
            "operation_records": [],
        }

    operation_records = parse_ru_xiao_long_operation_records(period_folder_path)
    action_summary = summarize_ru_xiao_long_actions(operation_records)
    details = [
        f"目录：{period_info['folder_name']}",
        f"年月标记：{period_info['label']}",
        f"TXT日志文件数：{len([item for item in build_local_file_records(period_folder_path) if item['file_name'].lower().endswith('.txt')])}",
        f"实质性操作片段数：{len(operation_records)}",
        f"操作动作分类数：{len(action_summary)}",
    ]

    if not operation_records:
        details.append("当前目录未解析到符合格式的 TXT 操作片段。")

    return {
        "status": "completed" if operation_records else "warning",
        "title": "茹小龙操作日志分析",
        "details": details,
        "action_summary": action_summary,
        "operation_records": operation_records,
    }


def analyze_zhou_liming_period_folder(period_folder_path: str, period_info):
    if not os.path.isdir(period_folder_path):
        return {
            "status": "missing",
            "title": "周利明 PNG OCR 分析",
            "details": [f"目录不存在：{period_folder_path}"],
            "ocr_results": [],
        }

    png_files = []
    for current_root, _, files in os.walk(period_folder_path):
        for file_name in sorted(files):
            if file_name.lower().endswith(".png"):
                png_files.append(os.path.join(current_root, file_name))

    if not png_files:
        return {
            "status": "not_found",
            "title": "周利明 PNG OCR 分析",
            "details": [f"目录 {period_info['folder_name']} 下未发现 PNG 文件。"],
            "ocr_results": [],
        }

    ocr_engine = get_ocr_engine()
    if ocr_engine is None:
        return {
            "status": "ocr_skipped",
            "title": "周利明 PNG OCR 分析",
            "details": ["OCR 组件未就绪，已跳过 PNG 时间识别。"],
            "ocr_results": [],
        }

    details = []
    ocr_results = []
    matched_count = 0

    for image_path in png_files:
        relative_path = os.path.relpath(image_path, period_folder_path).replace("/", "\\")
        log_info(f"开始 OCR 识别：{image_path}")
        ocr_result = extract_time_ranges_from_png(image_path, ocr_engine)
        log_info(f"OCR 原文：\n{ocr_result['ocr_text'] if ocr_result else '(无识别结果)'}")

        if ocr_result is None:
            details.append(f"文件：{relative_path} | OCR 识别失败")
            continue

        record = {
            "file_name": os.path.basename(image_path),
            "relative_path": relative_path,
            "start_time": ocr_result["start_time"],
            "end_time": ocr_result["end_time"],
            "time_matches": ocr_result["time_matches"],
        }
        ocr_results.append(record)

        if len(ocr_result["time_matches"]) < 2:
            details.append(
                f"文件：{relative_path} | 未提取到 2 个时间，当前识别到 {len(ocr_result['time_matches'])} 个"
            )
            continue

        matched_count += 1
        details.append(
            f"文件：{relative_path} | 开始时间：{ocr_result['start_time']} | 结束时间：{ocr_result['end_time']}"
        )

    if matched_count == 0:
        details.append("未识别到符合要求的 PNG 图片。")

    return {
        "status": "completed" if matched_count else "warning",
        "title": "周利明 PNG OCR 分析",
        "details": details,
        "ocr_results": ocr_results,
    }


def analyze_dev_person_folder(person_name: str, period_folder_path: str, period_info):
    if person_name == "刘晴":
        return analyze_liu_qing_folder(period_folder_path, period_info)
    if person_name == "茹小龙":
        return analyze_ru_xiao_long_folder(period_folder_path, period_info)
    if person_name == "周利明":
        return analyze_zhou_liming_period_folder(period_folder_path, period_info)
    return {
        "status": "not_supported",
        "title": f"{person_name} 分析",
        "details": [f"暂未支持 {person_name} 的分析逻辑。"],
    }


def build_dev_period_record(snapshot_root: str, person_name: str, period_folder_name: str):
    period_info = parse_dev_period_folder_name(period_folder_name)
    if period_info is None:
        return None

    period_folder_path = os.path.join(snapshot_root, person_name, period_folder_name)
    file_records = build_local_file_records(period_folder_path)
    analysis = analyze_dev_person_folder(person_name, period_folder_path, period_info)
    return {
        "person_name": person_name,
        "folder_name": period_folder_name,
        "year": period_info["year"],
        "month": period_info["month"],
        "label": period_info["label"],
        "relative_path": os.path.relpath(period_folder_path, snapshot_root).replace("/", "\\"),
        "file_count": len(file_records),
        "files": file_records,
        "analysis": analysis,
    }


def build_dev_analysis_text(analysis_result):
    lines = [
        f"研发部门分析目录：{analysis_result['snapshot_root']}",
        f"分析生成时间：{analysis_result['generated_at']}",
        "=" * 70,
    ]

    for person in analysis_result["people"]:
        lines.append(f"人员：{person['person_name']}")
        lines.append(f"状态：{person['status']}")
        lines.append(f"子目录数：{person['period_count']}")
        if not person["periods"]:
            lines.append("  (无匹配的年月目录)")
            lines.append("-" * 70)
            continue

        for period in person["periods"]:
            lines.append(
                f"  目录：{period['folder_name']} | 年月：{period['label']} | 文件数：{period['file_count']}"
            )
            for detail in period["analysis"]["details"]:
                lines.append(f"    - {detail}")
            for action_summary in period["analysis"].get("action_summary", []):
                lines.append(
                    f"    * {action_summary['category_name']} / {action_summary['action_name']}：{action_summary['count']} 次"
                )
            parse_diagnostics = period["analysis"].get("parse_diagnostics") or {}
            diagnostic_summary = parse_diagnostics.get("summary") or {}
            if diagnostic_summary:
                lines.append(
                    "    # 解析诊断："
                    f"文件={diagnostic_summary.get('file_count', 0)}，"
                    f"片段={diagnostic_summary.get('segment_count', 0)}，"
                    f"已解析={diagnostic_summary.get('parsed_segment_count', 0)}，"
                    f"跳过={diagnostic_summary.get('skipped_segment_count', 0)}，"
                    f"未归类={diagnostic_summary.get('unclassified_action_count', 0)}"
                )
            for item in (parse_diagnostics.get("unclassified_actions") or [])[:10]:
                lines.append(
                    f"      - 未归类动作：文件={item['source_relative_path']}，片段={item['segment_index']}，原始动作={item['action_raw']}"
                )
        lines.append("-" * 70)

    return "\n".join(lines)


def write_dev_analysis_outputs(analysis_result):
    os.makedirs(log_dir, exist_ok=True)
    snapshot_name = analysis_result["snapshot_name"]
    latest_json_path = get_dev_analysis_latest_json_path()
    latest_text_path = get_dev_analysis_latest_text_path()
    timestamp_json_path = os.path.join(log_dir, f"dev_analysis_{snapshot_name}.json")
    timestamp_text_path = os.path.join(log_dir, f"dev_analysis_{snapshot_name}.txt")
    text_content = build_dev_analysis_text(analysis_result)

    for json_path in [latest_json_path, timestamp_json_path]:
        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(analysis_result, file, ensure_ascii=False, indent=2)

    for text_path in [latest_text_path, timestamp_text_path]:
        with open(text_path, "w", encoding="utf-8") as file:
            file.write(text_content)

    log_info(f"📄 研发部门 JSON 分析结果已保存：{latest_json_path}")
    log_info(f"📄 研发部门文本分析结果已保存：{latest_text_path}")


def analyze_dev_data_snapshot(snapshot_root: str):
    if not snapshot_root or not os.path.isdir(snapshot_root):
        return None

    people = []
    total_file_count = 0
    total_period_count = 0

    for person_name in DEV_TARGET_FOLDERS:
        person_root = os.path.join(snapshot_root, person_name)
        period_records = []
        if os.path.isdir(person_root):
            for folder_name in sorted(os.listdir(person_root)):
                folder_path = os.path.join(person_root, folder_name)
                if not os.path.isdir(folder_path):
                    continue
                period_record = build_dev_period_record(snapshot_root, person_name, folder_name)
                if period_record is None:
                    continue
                period_records.append(period_record)

        period_records.sort(key=lambda item: (item["year"], item["month"], item["folder_name"]), reverse=True)
        total_period_count += len(period_records)
        total_file_count += sum(item["file_count"] for item in period_records)
        people.append(
            {
                "person_name": person_name,
                "status": "completed" if period_records else "not_found",
                "period_count": len(period_records),
                "periods": period_records,
            }
        )

    analysis_result = {
        "snapshot_name": os.path.basename(snapshot_root),
        "snapshot_root": snapshot_root,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "person_count": len(DEV_TARGET_FOLDERS),
            "period_count": total_period_count,
            "file_count": total_file_count,
        },
        "people": people,
    }
    write_dev_analysis_outputs(analysis_result)
    return analysis_result


def ensure_latest_dev_analysis_output():
    latest_snapshot_root = get_latest_snapshot_root(get_dev_data_base_local(), "dev_data_")
    if not latest_snapshot_root:
        log_info(f"未找到可分析的研发快照目录：{get_dev_data_base_local()}")
        return None
    log_info(f"开始基于最新研发快照生成分析结果：{latest_snapshot_root}")
    return analyze_dev_data_snapshot(latest_snapshot_root)


def analyze_zhou_liming_png(download_root: str, analysis_lines):
    zhou_lim_ing_folder = os.path.join(download_root, "周利明")
    if not os.path.isdir(zhou_lim_ing_folder):
        log_info("OCR 分析跳过：未找到 周利明 目录。")
        return

    period_dirs = []
    for folder_name in sorted(os.listdir(zhou_lim_ing_folder)):
        folder_path = os.path.join(zhou_lim_ing_folder, folder_name)
        if os.path.isdir(folder_path) and parse_dev_period_folder_name(folder_name):
            period_dirs.append((folder_name, folder_path))

    if not period_dirs:
        analysis_lines.append("")
        analysis_lines.append("周利明目录 PNG OCR 分析结果：")
        analysis_lines.append("-" * 70)
        analysis_lines.append("  (未发现类似 2026_5B 的年月目录)")
        return

    analysis_lines.append("")
    analysis_lines.append("周利明目录 PNG OCR 分析结果：")
    analysis_lines.append("-" * 70)

    for folder_name, folder_path in period_dirs:
        period_info = parse_dev_period_folder_name(folder_name)
        analysis_lines.append(f"  月份目录：{folder_name} ({period_info['label']})")
        result = analyze_zhou_liming_period_folder(folder_path, period_info)
        for detail in result["details"]:
            analysis_lines.append(f"    - {detail}")


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

    try:
        if service_data_store_type.lower() == "ftp":
            download_service_data_from_ftp()
        elif service_data_store_type.lower() in ("smb", "windows_share", "windows share"):
            download_service_data_from_smb()
    except Exception as ex:
        log_error(f"获取 Service_Data 数据失败：{ex}")

    current_state = collect_dev_remote_state()

    if last_state is None:
        log_info("首次检测，开始执行研发目录全量比对与下载。")
        snapshot_root, changed_folders = save_changed_dev_folders_to_local()
        if snapshot_root:
            analyze_dev_data_snapshot(snapshot_root)
            log_info(f"🎉 本次研发目录同步完成，共保存变化目录：{len(changed_folders)} 个")
        else:
            ensure_latest_dev_analysis_output()
            log_info("研发目录首次检测未发现需要落地的新目录，已刷新最新分析结果。")
        if enable_upload_validation_file:
            try:
                upload_validation_file()
            except Exception as ex:
                log_error(f"上传验证文件失败：{ex}")
        return current_state

    if current_state != last_state:
        log_info("检测到研发目录内容有变化，开始同步变化目录。")
        snapshot_root, changed_folders = save_changed_dev_folders_to_local()
        if snapshot_root:
            analyze_dev_data_snapshot(snapshot_root)
            log_info(f"🎉 本次研发目录同步完成，共保存变化目录：{len(changed_folders)} 个")
        else:
            ensure_latest_dev_analysis_output()
            log_info("远端状态有变化，但研发目标目录内容与本地最新快照一致。")
        if enable_upload_validation_file:
            try:
                upload_validation_file()
            except Exception as ex:
                log_error(f"上传验证文件失败：{ex}")
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
    try:
        ensure_latest_dev_analysis_output()
    except Exception as ex:
        log_error(f"初始化研发部门历史分析结果失败：{ex}")
    log_info("配置加载完成，开始监控 SharePoint。")
    log_info(f"配置文件：{CONFIG_FILE}")
    log_info(f"轮询间隔：{poll_interval_minutes} 分钟")
    log_info(f"日志目录：{log_dir}")
    log_info(f"监控目录：{root_sub_folder}")
    log_info(f"研发部门本地目录：{get_dev_data_base_local()}")
    log_info(f"研发部门网页数据：{get_dev_analysis_latest_json_path()}")
    if service_data_store_type:
        log_info(f"Service_Data 存储类型：{service_data_store_type}")
        log_info(f"Service_Data 远程路径：{build_service_data_display_path()}")
        log_info(f"Service_Data 本地目录：{get_service_data_base_local()}")
        if service_data_store_type.lower() == "ftp":
            log_info(
                f"FTP 配置：port={service_data_ftp_port}, port_list={service_data_ftp_port_list}, timeout={service_data_ftp_timeout_seconds}s, passive={service_data_ftp_passive_mode}, retry={service_data_ftp_retry_count}"
            )
    log_info(
        "说明：为避免程序自己上传验证文件后再次触发变更，默认不自动上传验证文件；"
        "如需启用，请在 monitor_config.json 中把 enable_upload_validation_file 改为 true。"
    )
    monitor_sharepoint()


if __name__ == "__main__":
    main()