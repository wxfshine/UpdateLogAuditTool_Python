import json
import logging
import hashlib
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


def get_latest_service_data_snapshot_root(service_data_base_local: str):
    if not os.path.isdir(service_data_base_local):
        return None

    candidate_dirs = []
    for entry in os.listdir(service_data_base_local):
        entry_path = os.path.join(service_data_base_local, entry)
        if os.path.isdir(entry_path) and not entry.startswith("service_data_"):
            candidate_dirs.append(entry_path)

    if not candidate_dirs:
        return None

    candidate_dirs.sort(key=os.path.getmtime, reverse=True)
    return candidate_dirs[0]


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

    try:
        if service_data_store_type.lower() == "ftp":
            download_service_data_from_ftp()
        elif service_data_store_type.lower() in ("smb", "windows_share", "windows share"):
            download_service_data_from_smb()
    except Exception as ex:
        log_error(f"获取 Service_Data 数据失败：{ex}")

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