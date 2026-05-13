import json
import re
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "monitor_config.json"
WEB_DIR = BASE_DIR / "web"
UNKNOWN_MONTH = "\u672a\u5206\u6708"


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_service_data_base_local(config):
    return Path(config["base_local"]) / "Service_data"


def get_service_data_smb_path(config):
    service_data_path = str(config.get("Service_Data_Path", "")).strip()
    if not service_data_path:
        return None

    if service_data_path.startswith("\\\\"):
        return Path(service_data_path)

    smb_host = str(config.get("Service_Data_Smb_Host", "")).strip()
    if not smb_host and isinstance(config.get("Service_Data_Ftp_Auth"), list) and len(config["Service_Data_Ftp_Auth"]) >= 2:
        smb_host = str(config["Service_Data_Ftp_Auth"][1]).strip()

    if not smb_host:
        return None

    normalized = service_data_path.lstrip("\\/").replace("/", "\\")
    return Path("\\\\" + smb_host + "\\" + normalized)


def resolve_service_data_source(config):
    local_base = get_service_data_base_local(config)
    if local_base.exists() and any(local_base.rglob("*")):
        return local_base

    smb_path = get_service_data_smb_path(config)
    if smb_path and smb_path.exists():
        return smb_path

    return local_base


def get_latest_snapshot_directory(service_data_base_local: Path):
    if not service_data_base_local.exists():
        return None

    candidates = [entry for entry in service_data_base_local.iterdir() if entry.is_dir()]
    if not candidates:
        return None

    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return candidates[0]


def classify_service_file(file_name: str):
    lower_name = file_name.lower()
    if lower_name.startswith("ftps_update_download_") and lower_name.endswith(".log"):
        return "ftp_hash"
    if lower_name.startswith("ucapp_env_check_") and lower_name.endswith(".log"):
        return "uc_env_check"
    if lower_name.endswith(".png") and ("\u5ba1\u6279" in file_name or "\u4e0a\u4f20" in file_name):
        return "upload_approval"
    if lower_name.startswith("windowsupdate_log_") and lower_name.endswith(".txt"):
        return "patch_validation"
    return "other"


def extract_month_from_path(path: Path):
    for part in path.parts:
        if re.match(r"^\d{4}-\d{2}$", part):
            return part
        timestamp_match = re.match(r"^(20\d{2})(\d{2})\d{2,}$", part)
        if timestamp_match:
            return f"{timestamp_match.group(1)}-{timestamp_match.group(2)}"
    return UNKNOWN_MONTH


def infer_month_from_file_name(file_name: str):
    match = re.search(r"(20\d{2})(\d{2})(\d{2})", file_name)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return UNKNOWN_MONTH


def parse_datetime_from_filename(file_name: str):
    patterns = [
        r"(20\d{2})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})",
        r"(20\d{2})(\d{2})(\d{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, file_name)
        if not match:
            continue

        groups = match.groups()
        if len(groups) == 6:
            return f"{groups[0]}-{groups[1]}-{groups[2]} {groups[3]}:{groups[4]}:{groups[5]}"
        return f"{groups[0]}-{groups[1]}-{groups[2]}"

    return None


def read_text_preview(file_path: Path, max_chars: int = 2000):
    encodings = ["utf-8", "utf-8-sig", "gbk", "mbcs"]
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                return file.read(max_chars)
        except UnicodeDecodeError:
            continue
        except OSError:
            break
    return ""


def build_file_summary(file_path: Path, category: str):
    if category == "ftp_hash":
        return "FTP\u53d6\u5305\u4e0eHash\u65e5\u5fd7"
    if category == "uc_env_check":
        return "UC\u73af\u5883\u68c0\u67e5\u65e5\u5fd7"
    if category == "upload_approval":
        return "\u8865\u4e01\u4e0a\u4f20\u4e0e\u5ba1\u6279\u622a\u56fe"
    if category == "patch_validation":
        return "\u8865\u4e01\u9a8c\u8bc1\u65e5\u5fd7"
    return f"\u539f\u59cb\u6587\u4ef6\uff1a{file_path.name}"


def build_file_analysis(file_record):
    category = file_record["category"]
    file_name = file_record["file_name"]
    detected_time = file_record["detected_time"]

    if category == "ftp_hash":
        kb_match = re.search(r"KB\d+", file_name, re.IGNORECASE)
        return {
            "status": "completed",
            "title": "\u53d6\u5305\u5e76\u8f93\u51faHash",
            "details": [
                f"\u6587\u4ef6\uff1a{file_name}",
                f"\u65e5\u5fd7\u65f6\u95f4\uff1a{detected_time or '\u5f85\u8bc6\u522b'}",
                f"\u76ee\u6807\u8865\u4e01\uff1a{kb_match.group(0).upper() if kb_match else '\u5f85\u8bc6\u522b'}",
                "\u8bf4\u660e\uff1a\u6f14\u793a\u9636\u6bb5\u9ed8\u8ba4\u89c6\u4e3a\u5df2\u8bc6\u522b\u53d6\u5305\u4e0eHash\u4fe1\u606f\u3002",
            ],
        }

    if category == "uc_env_check":
        return {
            "status": "completed",
            "title": "UC\u73af\u5883\u68c0\u67e5",
            "details": [
                f"\u6587\u4ef6\uff1a{file_name}",
                f"\u68c0\u67e5\u65f6\u95f4\uff1a{detected_time or '\u5f85\u8bc6\u522b'}",
                "\u8bf4\u660e\uff1a\u6f14\u793a\u9636\u6bb5\u9ed8\u8ba4\u89c6\u4e3a\u73af\u5883\u68c0\u67e5\u5b8c\u6210\u3002",
            ],
        }

    if category == "upload_approval":
        upload_related = "\u4e0a\u4f20" in file_name
        approval_related = "\u5ba1\u6279" in file_name
        image_type = "\u622a\u56fe"
        if upload_related and not approval_related:
            image_type = "\u4e0a\u4f20\u622a\u56fe"
        elif approval_related:
            image_type = "\u5ba1\u6279\u622a\u56fe"
        return {
            "status": "completed",
            "title": "\u8865\u4e01\u4e0a\u4f20\u4e0e\u5ba1\u6279",
            "details": [
                f"\u6587\u4ef6\uff1a{file_name}",
                f"\u7c7b\u578b\uff1a{image_type}",
                "\u8bf4\u660e\uff1a\u6f14\u793a\u9636\u6bb5\u5c55\u793aOCR/\u622a\u56fe\u5360\u4f4d\u5206\u6790\u7ed3\u679c\u3002",
            ],
        }

    if category == "patch_validation":
        return {
            "status": "completed",
            "title": "\u8865\u4e01\u9a8c\u8bc1",
            "details": [
                f"\u6587\u4ef6\uff1a{file_name}",
                f"\u9a8c\u8bc1\u65f6\u95f4\uff1a{detected_time or '\u5f85\u8bc6\u522b'}",
                "\u8bf4\u660e\uff1a\u6f14\u793a\u9636\u6bb5\u9ed8\u8ba4\u89c6\u4e3a\u9a8c\u8bc1\u65e5\u5fd7\u5df2\u8bc6\u522b\u3002",
            ],
        }

    return {
        "status": "pending",
        "title": "\u672a\u5206\u7c7b\u6587\u4ef6",
        "details": [f"\u6587\u4ef6\uff1a{file_name}", "\u8bf4\u660e\uff1a\u6682\u672a\u7eb3\u5165\u56db\u7c7b\u5206\u6790\u6a21\u677f\u3002"],
    }


def build_file_record(file_path: Path, service_data_base_local: Path):
    relative_path = file_path.relative_to(service_data_base_local)
    category = classify_service_file(file_path.name)
    modified_time = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    month = extract_month_from_path(relative_path)
    if month == UNKNOWN_MONTH:
        month = infer_month_from_file_name(file_path.name)
    file_record = {
        "file_id": str(relative_path).replace("\\", "/"),
        "month": month,
        "category": category,
        "file_name": file_path.name,
        "relative_path": str(relative_path).replace("\\", "/"),
        "file_type": file_path.suffix.lower(),
        "file_size": file_path.stat().st_size,
        "modified_time": modified_time,
        "detected_time": parse_datetime_from_filename(file_path.name),
        "summary": build_file_summary(file_path, category),
        "preview": read_text_preview(file_path) if file_path.suffix.lower() in {".log", ".txt"} else "",
    }
    file_record["analysis"] = build_file_analysis(file_record)
    return file_record


def build_service_files(service_data_base_local: Path):
    if not service_data_base_local.exists():
        return []

    records = []
    for file_path in service_data_base_local.rglob("*"):
        if file_path.is_file():
            records.append(build_file_record(file_path, service_data_base_local))

    records.sort(key=lambda item: (item["month"], item["category"], item["file_name"]), reverse=True)
    return records


def build_month_steps(files):
    mapping = {
        "ftp_hash": "\u53d6\u5305\u5e76\u8f93\u51faHash",
        "uc_env_check": "UC\u73af\u5883\u68c0\u67e5",
        "upload_approval": "\u4e0a\u4f20\u5e76\u5ba1\u6279",
        "patch_validation": "\u8865\u4e01\u9a8c\u8bc1",
    }
    steps = []
    for category, name in mapping.items():
        matched = [item for item in files if item["category"] == category]
        steps.append(
            {
                "step_code": category,
                "step_name": name,
                "status": "completed" if matched else "not_found",
                "file_count": len(matched),
                "summary": f"\u5df2\u53d1\u73b0 {len(matched)} \u4e2a\u6587\u4ef6" if matched else "\u672a\u53d1\u73b0\u5bf9\u5e94\u6587\u4ef6",
            }
        )
    return steps


def build_monthly_reports(files, config):
    grouped = {}
    for file_record in files:
        grouped.setdefault(file_record["month"], []).append(file_record)

    reports = []
    for month, month_files in sorted(grouped.items(), key=lambda item: item[0], reverse=True):
        steps = build_month_steps(month_files)
        completed_count = sum(1 for step in steps if step["status"] == "completed")
        reports.append(
            {
                "report_id": f"service-{month}",
                "department_id": "service",
                "department_name": "\u670d\u52a1\u90e8\u95e8",
                "month": month,
                "is_demo_data": True,
                "source_type": config.get("Service_Data_Store_Type", "windows_share"),
                "source_path": str(resolve_service_data_source(config)),
                "file_count": len(month_files),
                "overall_status": "completed" if completed_count == 4 else "warning",
                "steps": steps,
                "files": month_files,
                "summary": {
                    "completed_step_count": completed_count,
                    "total_step_count": 4,
                    "latest_file_time": max((item["modified_time"] for item in month_files), default=None),
                },
            }
        )
    return reports


def build_alerts(monthly_reports):
    alerts = []
    for report in monthly_reports:
        for step in report["steps"]:
            if step["status"] != "completed":
                alerts.append(
                    {
                        "alert_id": f"{report['report_id']}-{step['step_code']}",
                        "department_id": report["department_id"],
                        "month": report["month"],
                        "severity": "medium",
                        "status": "open",
                        "title": f"{step['step_name']}\u672a\u5b8c\u6210",
                        "message": step["summary"],
                    }
                )
    return alerts


def build_dashboard(config, monthly_reports, alerts):
    latest_report = monthly_reports[0] if monthly_reports else None
    resolved_source = resolve_service_data_source(config)
    latest_snapshot = get_latest_snapshot_directory(resolved_source)
    last_sync_time = None
    if latest_snapshot is not None:
        last_sync_time = datetime.fromtimestamp(latest_snapshot.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    elif resolved_source.exists():
        last_sync_time = datetime.fromtimestamp(resolved_source.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "title": "\u66f4\u65b0\u65e5\u5fd7\u5ba1\u8ba1\u6c47\u62a5\u5e73\u53f0",
        "demo_mode": True,
        "last_sync_time": last_sync_time,
        "summary_cards": {
            "department_count": 2,
            "month_count": len(monthly_reports),
            "file_count": sum(report["file_count"] for report in monthly_reports),
            "alert_count": len(alerts),
            "latest_month": latest_report["month"] if latest_report else None,
        },
        "departments": [
            {
                "department_id": "rd",
                "department_name": "\u7814\u53d1\u90e8\u95e8",
                "source_type": "sharepoint",
                "status": "placeholder",
                "summary": "\u5df2\u63a5\u5165\uff0c\u5f85\u5c55\u793a",
            },
            {
                "department_id": "service",
                "department_name": "\u670d\u52a1\u90e8\u95e8",
                "source_type": "windows_share",
                "status": "active",
                "summary": "\u4f18\u5148\u5c55\u793a\u670d\u52a1\u90e8\u95e8\u6708\u5ea6\u8865\u4e01\u6d41\u7a0b\u4fe1\u606f",
            },
        ],
        "latest_service_report": latest_report,
    }


def build_app_data():
    config = load_config()
    service_data_base_local = resolve_service_data_source(config)
    files = build_service_files(service_data_base_local)
    monthly_reports = build_monthly_reports(files, config)
    alerts = build_alerts(monthly_reports)
    dashboard = build_dashboard(config, monthly_reports, alerts)
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "service_data_base_local": str(service_data_base_local),
            "service_data_store_type": config.get("Service_Data_Store_Type"),
        },
        "dashboard": dashboard,
        "monthly_reports": monthly_reports,
        "alerts": alerts,
    }


class DemoRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def end_headers(self):
        content_type = self.headers.get("Content-Type")
        super().end_headers()

    def guess_type(self, path):
        content_type = super().guess_type(path)
        if content_type.startswith("text/html"):
            return "text/html; charset=utf-8"
        if content_type.startswith("text/css"):
            return "text/css; charset=utf-8"
        if content_type in ("text/javascript", "application/javascript"):
            return "application/javascript; charset=utf-8"
        if content_type.startswith("application/json"):
            return "application/json; charset=utf-8"
        return content_type

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path.startswith("/api/"):
            self.handle_api(parsed)
            return

        if parsed.path == "/":
            self.path = "/index.html"

        return super().do_GET()

    def handle_api(self, parsed):
        data = build_app_data()
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/dashboard":
            self.write_json(data["dashboard"])
            return

        if path == "/api/departments":
            self.write_json(data["dashboard"]["departments"])
            return

        if path == "/api/departments/service/months":
            months = [
                {
                    "month": report["month"],
                    "overall_status": report["overall_status"],
                    "file_count": report["file_count"],
                    "completed_step_count": report["summary"]["completed_step_count"],
                }
                for report in data["monthly_reports"]
            ]
            self.write_json({"department_id": "service", "months": months})
            return

        month_prefix = "/api/departments/service/months/"
        if path.startswith(month_prefix):
            month = path[len(month_prefix):].strip("/")
            files_only = False
            if month.endswith("/files"):
                files_only = True
                month = month[:-6].strip("/")

            report = next((item for item in data["monthly_reports"] if item["month"] == month), None)
            if report is None:
                self.write_json({"error": "month not found"}, status=404)
                return

            self.write_json(report["files"] if files_only else report)
            return

        if path == "/api/compare/months":
            requested = query.get("months", [""])[0]
            selected = {item for item in requested.split(",") if item}
            reports = data["monthly_reports"]
            if selected:
                reports = [item for item in reports if item["month"] in selected]

            items = []
            for report in reports:
                step_map = {step["step_code"]: step["status"] for step in report["steps"]}
                items.append(
                    {
                        "month": report["month"],
                        "hash_status": step_map.get("ftp_hash", "not_found"),
                        "env_status": step_map.get("uc_env_check", "not_found"),
                        "approval_status": step_map.get("upload_approval", "not_found"),
                        "validation_status": step_map.get("patch_validation", "not_found"),
                        "overall_status": report["overall_status"],
                    }
                )
            self.write_json({"department_id": "service", "items": items})
            return

        if path == "/api/alerts":
            self.write_json(data["alerts"])
            return

        if path == "/api/files":
            files = []
            for report in data["monthly_reports"]:
                files.extend(report["files"])
            self.write_json(files)
            return

        self.write_json({"error": "not found"}, status=404)

    def write_json(self, data, status=200):
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main():
    WEB_DIR.mkdir(exist_ok=True)
    host = "127.0.0.1"
    port = 8000
    server = ThreadingHTTPServer((host, port), DemoRequestHandler)
    print(f"Demo server running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
