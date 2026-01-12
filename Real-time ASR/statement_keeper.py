import json
from datetime import datetime, timedelta, time
import os
from pathlib import Path

LOG_BASE_DIR = "Statements"


def ensure_dir(date: datetime):
    """确保日期对应的目录存在"""
    year_dir = os.path.join(LOG_BASE_DIR, str(date.year))
    month_dir = os.path.join(year_dir, f"{date.month:02d}")
    Path(year_dir).mkdir(parents=True, exist_ok=True)
    Path(month_dir).mkdir(parents=True, exist_ok=True)
    return month_dir


def get_log_file_path(date: datetime):
    """获取日期对应的日志文件路径"""
    month_dir = ensure_dir(date)
    return os.path.join(month_dir, f"statements_{date.date()}.log")


def add_statement(content: str):
    """添加带时间戳的语句"""
    split_content = content.split('&')
    timestamp = datetime.now()
    times = split_content[0]
    speaker = split_content[1]
    content = split_content[2]
    reply_object = split_content[3]
    log_entry = {
        "timestamp": datetime.strptime(times, "%H:%M:%S").time().isoformat(),
        "speaker": speaker,
        "content": content,
        "reply_object": reply_object
    }

    log_file = get_log_file_path(timestamp)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def get_statements(start_time: time, end_time: time):
    """
    获取指定时间范围内的所有语句

    参数:
        start_time: 开始时间
        end_time: 结束时间

    返回:
        [语句列表] 按时间升序排列
    """
    results = []

    # 遍历日期范围内的所有日志文件
    timestamp = datetime.now()
    log_file = get_log_file_path(timestamp)

    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry_time = time.fromisoformat(entry["timestamp"])

                    if start_time <= entry_time <= end_time:
                        results.append(entry)
                except json.JSONDecodeError:
                    continue  # 跳过格式错误的行

    # 按时间升序排列
    results.sort(key=lambda x: x["timestamp"])
    return results
