# ============================================================
# 配置：被测地址、账号数据、报告目录
# 被测地址可用环境变量 BASE_URL 覆盖（例如指向自己部署的实例）
# ============================================================

import os

import yaml

BASE_URL = os.getenv("BASE_URL", "https://www.saucedemo.com")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")

RESULTS_DIR = "reports/allure-results"
REPORT_DIR = "reports/allure-html"


def _load_accounts():
    path = os.path.join(DATA_DIR, "accounts.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 账号数据：standard / locked / wrong_password
ACCOUNTS = _load_accounts()
