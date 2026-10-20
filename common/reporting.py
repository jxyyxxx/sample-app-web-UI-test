# ============================================================
# Allure 报告辅助：本地生成报告并把默认语言设为中文
# 用法：python -m common.reporting [report_dir] [--lang en]
# ============================================================

import argparse
import os
import shutil
import subprocess
import sys

MARKER = "<!-- allure-default-language -->"

SCRIPT_TEMPLATE = (
    MARKER + "\n"
    "<script>\n"
    "  try {\n"
    "    var k = 'ALLURE_REPORT_SETTINGS';\n"
    "    var s = JSON.parse(localStorage.getItem(k) || '{}');\n"
    "    s.language = '__LANG__';\n"
    "    localStorage.setItem(k, JSON.stringify(s));\n"
    "  } catch (e) { /* 隐私模式下忽略 */ }\n"
    "</script>\n"
)

APP_JS_ANCHOR = '<script src="app.js"></script>'


def set_default_language(report_dir, lang="zh"):
    """往 index.html 注入默认语言脚本（幂等）"""
    index_path = os.path.join(report_dir, "index.html")
    if not os.path.exists(index_path):
        return False

    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    if MARKER in html:
        return True
    if APP_JS_ANCHOR not in html:
        return False

    script = SCRIPT_TEMPLATE.replace("__LANG__", lang)
    html = html.replace(APP_JS_ANCHOR, "    " + script + "    " + APP_JS_ANCHOR, 1)
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    return True


def generate_local_report(results_dir="reports/allure-results", report_dir="reports/allure-html"):
    """本地生成报告、设中文、用 allure open 打开；CI 里不要调用"""
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
    parser = argparse.ArgumentParser(description="设置 Allure 报告的默认语言")
    parser.add_argument("report_dir", nargs="?", default="reports/allure-html")
    parser.add_argument("--lang", default="zh")
    args = parser.parse_args(argv)
    ok = set_default_language(args.report_dir, args.lang)
    print(("已设置默认语言 %s：%s" % (args.lang, args.report_dir)) if ok else "跳过（报告不存在）")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
