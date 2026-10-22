# ============================================================
# 工具层：Allure 报告相关（环境面板、生成、默认语言）
#
# conftest.py 只负责在 pytest 钩子里调用这里的函数，具体实现都在这里。
#
# 命令行用法（CI 里单独调用）：
#   python -m common.reporting allure-report            # 设置默认语言为中文
#   python -m common.reporting <dir> --lang en          # 需要时切回英文
# ============================================================

import argparse
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime

from config.settings import BASE_URL, ROOT_DIR

# 结果目录与报告目录（与 pytest.ini 的 --alluredir 保持一致）
RESULTS_DIR = "reports/allure-results"
REPORT_DIR = "reports/allure-html"

# ---- 默认语言注入 ----------------------------------------------------------
MARKER = "<!-- allure-default-language -->"

SCRIPT_TEMPLATE = (
    MARKER + "\n"
    "<script>\n"
    "  try {\n"
    "    var k = 'ALLURE_REPORT_SETTINGS';\n"
    "    var s = JSON.parse(localStorage.getItem(k) || '{}');\n"
    "    s.language = '__LANG__';\n"
    "    localStorage.setItem(k, JSON.stringify(s));\n"
    "  } catch (e) {\n"
    "    /* 浏览器隐私模式禁用 localStorage 时忽略，报告仍可正常打开 */\n"
    "  }\n"
    "</script>\n"
)

APP_JS_ANCHOR = '<script src="app.js"></script>'


def set_default_language(report_dir, lang="zh"):
    """
    往 Allure 报告的 index.html 注入"默认语言"脚本（幂等）

    原理：报告前端的语言选择存在 localStorage 的 ALLURE_REPORT_SETTINGS.language，
    默认是 en；在 app.js 之前先写成 zh，打开即中文。

    :param report_dir: 报告目录（含 index.html）
    :param lang: 语言代码，中文用 zh
    :return: True 表示已设置或已存在；False 表示目录/结构不匹配
    """
    index_path = os.path.join(report_dir, "index.html")
    if not os.path.exists(index_path):
        return False

    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 幂等：已经注入过就不重复写
    if MARKER in html:
        return True

    if APP_JS_ANCHOR not in html:
        return False

    script = SCRIPT_TEMPLATE.replace("__LANG__", lang)
    html = html.replace(APP_JS_ANCHOR, "    " + script + "    " + APP_JS_ANCHOR, 1)
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    return True


# ---- 环境面板 --------------------------------------------------------------
def _package_version(name):
    """取已安装包版本，取不到就返回 unknown（不让报告辅助本身失败）"""
    try:
        from importlib.metadata import version

        return version(name)
    except Exception:
        return "unknown"


def _app_commit():
    """
    被测应用当前 commit

    作用：同一套用例可能跑的是不同版本的应用，报告里带上 commit 才能定位
    "这次红了是应用改坏了还是用例改坏了"。应用仓库放在本项目的同级目录。
    """
    candidates = [
        os.getenv("APP_DIR"),
        os.path.join(os.path.dirname(ROOT_DIR), "sample-app-web"),  # 本地：同级目录
        os.path.join(ROOT_DIR, "app"),                              # CI：克隆进仓库内
    ]
    for app_dir in candidates:
        if not app_dir or not os.path.isdir(os.path.join(app_dir, ".git")):
            continue
        try:
            result = subprocess.run(
                ["git", "-C", app_dir, "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=5,
            )
            commit = result.stdout.strip()
            if commit:
                return commit
        except Exception:
            continue
    return "unknown"


def _browser_name(session):
    """当前指定的浏览器，取不到时按 pytest-playwright 的默认值处理"""
    try:
        return session.config.getoption("browser") or "chromium"
    except (ValueError, AttributeError):
        return "chromium"


def write_allure_metadata(session):
    """
    写入 Allure 环境面板（Allure 的 Environment 栏读的就是这个文件）

    时机：必须在 allure 的 --clean-alluredir 之后写，所以放在会话结束时调用；
         它是会话开始时清空结果目录的，先写会被清掉。

    :param session: pytest 会话对象
    :return: 生成的文件路径
    """
    # 以实际生效的 --alluredir 为准：pytest.ini 里是默认值，命令行可能覆盖
    results_dir = getattr(session.config.option, "allure_report_dir", None) or RESULTS_DIR

    properties = {
        "BASE_URL": BASE_URL,
        "Browser": _browser_name(session),
        "AppCommit": _app_commit(),
        "Python": platform.python_version(),
        "pytest": _package_version("pytest"),
        "Playwright": _package_version("playwright"),
        "Platform": platform.platform(),
        "RunAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    os.makedirs(results_dir, exist_ok=True)
    path = os.path.join(results_dir, "environment.properties")
    with open(path, "w", encoding="utf-8") as f:
        for key, value in properties.items():
            f.write(f"{key}={value}\n")
    return path


# ---- 报告生成 --------------------------------------------------------------
def generate_local_report(results_dir=RESULTS_DIR, report_dir=REPORT_DIR):
    """
    本地生成 Allure 报告、设中文、用 allure open 打开

    CI 里不要调用：workflow 会自己 generate，且没有浏览器可开。
    :return: True 表示成功；False 表示缺少 allure 命令或生成失败
    """
    if not shutil.which("allure"):
        print("未检测到 allure 命令行工具，跳过报告生成")
        return False

    print("正在生成 Allure 报告...")
    try:
        subprocess.run(
            f'allure generate {results_dir} -o {report_dir} --clean',
            shell=True, check=True, capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Allure 报告生成失败：{e}")
        return False

    set_default_language(report_dir)
    index = os.path.join(report_dir, "index.html")
    if os.path.exists(index):
        print("正在打开报告...")
        subprocess.Popen(f'allure open {report_dir}', shell=True)
    return True


def main(argv=None):
    """命令行入口：只做"设置报告默认语言"这一件事"""
    parser = argparse.ArgumentParser(description="设置 Allure 报告的默认语言")
    parser.add_argument("report_dir", nargs="?", default=REPORT_DIR)
    parser.add_argument("--lang", default="zh")
    args = parser.parse_args(argv)
    ok = set_default_language(args.report_dir, args.lang)
    print(("已设置默认语言 %s：%s" % (args.lang, args.report_dir)) if ok else "跳过（报告不存在）")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
