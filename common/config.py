# ============================================================
# 配置：被测地址、账号数据、报告目录
# 默认打本地部署的实例（npm run start 起在 3000 端口）；
# 需要打线上时用环境变量覆盖：BASE_URL=https://www.saucedemo.com
# ============================================================

import os

import yaml

BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")

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
