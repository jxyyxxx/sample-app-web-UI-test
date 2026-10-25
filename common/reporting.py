# ============================================================
# 工具层：Allure 报告相关（环境面板、失败分类、运行器、历史趋势、报告归档、生成）
#
# conftest.py 只负责在 pytest 钩子里调用这里的函数，具体实现都在这里。
#
# 命令行用法（CI 里单独调用）：
#   python -m common.reporting allure-report            # 设置默认语言为中文
#   python -m common.reporting <dir> --lang en          # 需要时切回英文
# ============================================================

import argparse
import json
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

# 失败分类规则的仓库内路径（跑测试时拷进结果目录）
CATEGORIES_SRC = os.path.join("config", "allure", "categories.json")

# 历史（趋势）的仓库内位置。必须放在结果目录之外：
# pytest.ini 的 --clean-alluredir 每次会话开始都会清空结果目录。
HISTORY_DIR = "reports/allure-history"
HISTORY_KEEP = 20  # 趋势图与每条用例的历史，只保留最近 20 次运行

# 报告归档：每次运行把 HTML 报告复制一份，便于事后回看"第 N 次"的现场。
# allure-html 每次 generate --clean 都会覆盖，不归档就只剩最新一次。
ARCHIVE_ROOT = "reports/archive"
ARCHIVE_KEEP_PASS = 20  # 通过的运行只留最近 20 份
ARCHIVE_KEEP_FAIL = 30  # 有 failed/broken 的运行留最近 30 份（防服务全挂时无限增长）

# 这四个文件都是"每跑一次追加一条"的数组，截断时必须同步处理，否则各图点数会不一致
TREND_FILES = (
    "history-trend.json",
    "duration-trend.json",
    "categories-trend.json",
    "retry-trend.json",
)

# 执行范围 -> 中文短标签（趋势图横轴、运行器名称、归档目录名里用）
SCOPE_LABELS = {
    "full": "全量",
    "smoke": "冒烟",
    "login": "登录",
    "inventory": "商品列表",
    "cart": "购物车",
    "checkout": "结算",
    "compat": "兼容性",
    "catalog": "动态目录",
    "filtered": "筛选",
}

# 能被 -m 直接命中的标记（full / filtered 是回落值，不作为标记名）
SCOPE_MARKERS = {name for name in SCOPE_LABELS if name not in ("full", "filtered")}

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


# ---- 执行范围 --------------------------------------------------------------
def detect_scope(session):
    """
    从 pytest 命令行推断本次执行范围

    - 没有 -m / -k：full
    - -m 命中已注册的标记：直接用标记名（smoke / checkout / login ...）
    - 其他 -m 表达式或 -k：filtered

    运行器名称、归档目录都依赖这个值，所以只能有一处实现，
    避免两处各算一套导致对不上。
    """
    markexpr = (getattr(session.config.option, "markexpr", "") or "").strip()
    keyword = (getattr(session.config.option, "keyword", "") or "").strip()

    if not markexpr and not keyword:
        return "full"
    if markexpr in SCOPE_MARKERS:
        return markexpr
    return "filtered"


def _scope_text(scope, collected):
    """趋势图/运行器上的范围描述，例如「全量24条」"""
    label = SCOPE_LABELS.get(scope, scope)
    return f"{label}{collected}条" if collected else label


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


def _repo_commit():
    """测试框架自身的 commit：同一台机器上不同代码版本跑出来的报告要能区分开"""
    try:
        result = subprocess.run(
            ["git", "-C", ROOT_DIR, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _browser_name(session):
    """当前指定的浏览器，取不到时按 pytest-playwright 的默认值处理"""
    try:
        return session.config.getoption("browser") or "chromium"
    except (ValueError, AttributeError):
        return "chromium"


def write_allure_metadata(session):
    """
    往结果目录写两份元数据：

    1. environment.properties —— Allure 报告左侧「环境」面板的数据源
    2. categories.json —— 失败分类规则，报告里「分类」页靠它把失败归到
       「应用不可用 / 元素超时 / 断言失败 / 用例异常」

    两个 commit 都在这里：AppCommit 是被测应用，FrameworkCommit 是本框架。
    运行器标签上不再带 commit（太长），需要时看这里。

    时机：必须在 allure 的 --clean-alluredir 之后写，所以放在会话结束时调用；
         它是会话开始时清空结果目录的，先写会被清掉。

    :param session: pytest 会话对象
    :return: environment.properties 的生成路径
    """
    # 以实际生效的 --alluredir 为准：pytest.ini 里是默认值，命令行可能覆盖
    results_dir = resolve_results_dir(session)

    properties = {
        "BASE_URL": BASE_URL,
        "Browser": _browser_name(session),
        "AppCommit": _app_commit(),
        "FrameworkCommit": _repo_commit() or "unknown",
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

    # 分类规则常驻 config/，每次跑测试时拷进结果目录。
    # 不直接放在结果目录里，是因为 --clean-alluredir 会在会话开始时清空它。
    if os.path.exists(CATEGORIES_SRC):
        shutil.copyfile(CATEGORIES_SRC, os.path.join(results_dir, "categories.json"))

    return path


# ---- 历史（趋势）-----------------------------------------------------------
def resolve_results_dir(session):
    """
    本次运行实际生效的结果目录

    pytest.ini 里写的是默认值，命令行可以覆盖（--alluredir=xxx），
    写文件、生成报告、读 executor.json 都必须用同一个目录，否则会写错地方。
    """
    return getattr(session.config.option, "allure_report_dir", None) or RESULTS_DIR


def _read_json(path):
    """读 json，读不到或格式不对统一返回 None（报告辅助本身不该让用例失败）"""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def sync_history_in(results_dir=RESULTS_DIR):
    """
    把上一轮的历史拷进结果目录（生成前调用）

    Allure 只从「输入目录」（--alluredir 指向的地方）读历史，不看输出目录，
    也不是"不删输出目录就会自动累积"——那套写法在 2.30 上会直接报错。
    所以历史必须先落到结果目录里，再执行 generate --clean 才能接上。

    :return: True 表示拷了历史；False 表示还没有历史（首次运行）
    """
    if not os.path.isdir(HISTORY_DIR) or not os.listdir(HISTORY_DIR):
        return False

    dst = os.path.join(results_dir, "history")
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(HISTORY_DIR, dst)
    return True


def _truncate_history(history_dir, keep=HISTORY_KEEP):
    """把趋势数组和每个用例的历史条目截断到最近 keep 条（原地改写）"""
    for name in TREND_FILES:
        path = os.path.join(history_dir, name)
        data = _read_json(path)
        if isinstance(data, list) and len(data) > keep:
            _write_json(path, data[-keep:])

    path = os.path.join(history_dir, "history.json")
    data = _read_json(path)
    if not isinstance(data, dict):
        return

    changed = False
    for entry in data.values():
        items = entry.get("items") if isinstance(entry, dict) else None
        if isinstance(items, list) and len(items) > keep:
            entry["items"] = items[-keep:]
            changed = True
    if changed:
        _write_json(path, data)


def sync_history_out(report_dir=REPORT_DIR):
    """
    把本次生成的历史存回仓库目录，并截断到最近 HISTORY_KEEP 次（生成后调用）

    存回的位置独立于报告目录，所以删掉 allure-html 不会把历史一起丢掉。

    :return: True 表示已保存
    """
    src = os.path.join(report_dir, "history")
    if not os.path.isdir(src):
        return False

    os.makedirs(HISTORY_DIR, exist_ok=True)
    for name in os.listdir(src):
        shutil.copyfile(os.path.join(src, name), os.path.join(HISTORY_DIR, name))

    _truncate_history(HISTORY_DIR)
    return True


# ---- 运行器 ----------------------------------------------------------------
def _build_order(results_dir):
    """
    buildOrder：第几次运行 = 历史里最大的序号 + 1

    不能用"历史条数 + 1"：历史只保留最近 20 条，跑到第 21 次时条数会一直
    卡在 20，序号就停在 21 不再增长，趋势图横轴会重复、归档目录会重名。
    """
    data = _read_json(os.path.join(results_dir, "history", "history-trend.json"))
    if not isinstance(data, list) or not data:
        return 1

    orders = []
    for entry in data:
        try:
            orders.append(int(entry.get("buildOrder")))
        except (AttributeError, TypeError, ValueError):
            continue

    # 老数据可能缺 buildOrder，此时退回"条数 + 1"，至少保证本次序号不重复
    return max(orders) + 1 if orders else len(data) + 1


def _run_time_text(started_at):
    """运行开始时间，标签里精确到秒（批量跑时相邻两次可能只差几十秒）"""
    moment = datetime.fromtimestamp(started_at) if started_at else datetime.now()
    return moment.strftime("%m-%d %H:%M:%S")


def write_executor(results_dir=RESULTS_DIR, scope="full", collected=0, started_at=None):
    """
    写 executor.json：报告的「运行器」面板 + 趋势图的横轴标签

    趋势图每个点靠 buildOrder 排序、靠 buildName 标注。缺这个文件时，
    历史条目里只有 data 没有名字，趋势图就是一串无名点——所以它和历史是一件事。

    本地标签带运行时间（精确到秒），因为批量跑时相邻两次可能只差几十秒；
    commit 不进标签（太长，环境面板的 AppCommit / FrameworkCommit 里有）。
    CI 标签用 workflow 名 + run number，链接直接能跳到 Actions，不再重复时间。

    :param results_dir: 结果目录（跟随实际 --alluredir）
    :param scope: 执行范围（full / smoke / checkout ...）
    :param collected: 本次收集到的用例数，用于「全量24条」这样的标签
    :param started_at: 本次会话开始时间（epoch 秒），用于标签上的时间
    :return: executor.json 的生成路径
    """
    scope_text = _scope_text(scope, collected)

    if os.getenv("GITHUB_ACTIONS") == "true":
        server = os.getenv("GITHUB_SERVER_URL", "")
        repo = os.getenv("GITHUB_REPOSITORY", "")
        run_id = os.getenv("GITHUB_RUN_ID", "")
        number = os.getenv("GITHUB_RUN_NUMBER", "")
        workflow = os.getenv("GITHUB_WORKFLOW", "CI")
        name = f"{workflow} #{number}" if number else workflow
        executor = {
            "name": "GitHub Actions",
            "type": "github",
            # CI 的 run number 天然单调递增，比本地推算更可靠
            "buildOrder": int(number) if number.isdigit() else _build_order(results_dir),
            "buildName": f"{name} · {scope_text}",
            "buildUrl": f"{server}/{repo}/actions/runs/{run_id}" if run_id else "",
            "reportName": name,
        }
    else:
        order = _build_order(results_dir)
        label = f"本地 第{order}次 · {scope_text} · {_run_time_text(started_at)}"
        executor = {
            "name": "本地运行",
            "type": "local",
            "buildOrder": order,
            "buildName": label,
            "reportName": label,
        }

    os.makedirs(results_dir, exist_ok=True)
    path = os.path.join(results_dir, "executor.json")
    _write_json(path, executor)
    return path


def prepare_allure_inputs(session):
    """
    会话结束时的报告准备：历史 → 环境面板/分类 → 运行器

    顺序有依赖：先拷历史，write_executor 才能按"已经跑过几次"算出 buildOrder。

    :param session: pytest 会话对象
    """
    # 以实际生效的 --alluredir 为准：pytest.ini 里是默认值，命令行可能覆盖
    results_dir = resolve_results_dir(session)

    sync_history_in(results_dir)
    write_allure_metadata(session)
    write_executor(
        results_dir,
        scope=detect_scope(session),
        collected=getattr(session, "testscollected", 0),
        started_at=getattr(session, "start_time", None),
    )


# ---- 报告归档 --------------------------------------------------------------
def _report_status(report_dir):
    """
    读报告自己的 summary.json 判定这次运行是 PASS 还是 FAIL

    不在 pytest 侧数失败：session.testsfailed 分不清 failed/broken，
    而 summary.json 是报告实际渲染用的口径，两边一定一致。

    :return: "PASS" / "FAIL"；读不到 summary.json 时返回 None
    """
    data = _read_json(os.path.join(report_dir, "widgets", "summary.json"))
    if not isinstance(data, dict):
        return None

    stat = data.get("statistic") or {}
    bad = (stat.get("failed") or 0) + (stat.get("broken") or 0)
    return "FAIL" if bad else "PASS"


def _prune_archive(scope):
    """按规则清理旧归档：通过的留最近 N 份，失败的留最近 N 份"""
    base = os.path.join(ARCHIVE_ROOT, scope)
    if not os.path.isdir(base):
        return

    names = sorted(
        (name for name in os.listdir(base)
         if os.path.isdir(os.path.join(base, name))),
        # 按目录名里的序号（整数）排序，不依赖字符串比较：
        # 跑到第 1000 次时 "1000_..." 按字符会排到 "999_..." 前面
        key=lambda name: int(name.split("_")[0]) if name.split("_")[0].isdigit() else 0,
    )

    for suffix, keep in (("_PASS", ARCHIVE_KEEP_PASS), ("_FAIL", ARCHIVE_KEEP_FAIL)):
        if keep <= 0:
            continue
        group = [name for name in names if name.endswith(suffix)]
        # 序号是零填充的，整数排序后最旧的排在最前，直接切片即可
        for name in group[:-keep]:
            shutil.rmtree(os.path.join(base, name), ignore_errors=True)


def archive_report(results_dir=RESULTS_DIR, report_dir=REPORT_DIR, scope="full", started_at=None):
    """
    把本次生成的报告复制一份到 reports/archive/{scope}/，供事后回看

    目录名：{序号:03d}_{日期}_{时间}_{PASS|FAIL}
      - 序号零填充，整数排序即运行顺序，清理时直接切片
      - FAIL 一眼可见，便于挑出有问题的运行

    :return: 归档目录路径；判定失败或复制出错时返回 None
    """
    status = _report_status(report_dir)
    if status is None:
        print("读不到报告的 summary.json，跳过归档")
        return None

    executor = _read_json(os.path.join(results_dir, "executor.json")) or {}
    try:
        order = int(executor.get("buildOrder"))
    except (TypeError, ValueError):
        order = 0

    moment = datetime.fromtimestamp(started_at) if started_at else datetime.now()
    name = f"{order:03d}_{moment.strftime('%Y-%m-%d_%H-%M-%S')}_{status}"
    dest = os.path.join(ARCHIVE_ROOT, scope, name)

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest):
        shutil.rmtree(dest, ignore_errors=True)

    try:
        shutil.copytree(report_dir, dest)
    except OSError as e:
        print(f"报告归档失败：{e}")
        return None

    _prune_archive(scope)
    print(f"报告已归档：{dest}")
    return dest


# ---- 报告生成 --------------------------------------------------------------
def generate_local_report(results_dir=RESULTS_DIR, report_dir=REPORT_DIR, scope="full", started_at=None):
    """
    本地跑完测试后生成 Allure 报告、把历史存回仓库、归档报告、设中文、打开浏览器

    CI 里不要调用：workflow 会显式执行 allure generate，且没有浏览器可开。

    :param scope: 执行范围，决定归档存进哪个子目录
    :param started_at: 会话开始时间（epoch 秒），用于归档目录名
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

    # 生成后把历史存回仓库目录，下一次运行才有趋势可接
    sync_history_out(report_dir)

    # 归档一份：allure-html 下次会被 --clean 覆盖，不归档就查不到"第 N 次"的现场。
    # 必须放在 sync_history_out 之后：归档要复制的是已写回历史的成品报告。
    archive_report(results_dir, report_dir, scope, started_at)

    set_default_language(report_dir)
    index = os.path.join(report_dir, "index.html")
    if os.path.exists(index):
        print("正在打开报告...")
        # stdout/stderr 必须断开：allure open 起的是常驻服务，继承父进程管道的话
        # `pytest | tail`、`pytest > log` 这类写法会一直等不到 EOF 而卡住
        subprocess.Popen(
            f'allure open {report_dir}',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
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
