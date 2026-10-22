# ============================================================
# 定位工具
# 作用：统一用被测应用预留的 data-test 属性生成选择器
#
# 为什么不用 CSS 类名（.title / .cart_item / .summary_subtotal_label 之类）：
#   类名属于样式实现，改版、换主题、调布局都可能被重命名；
#   data-test 是应用专门留给自动化的契约，稳定性高得多。
# 应用侧确实没有 data-test 的元素，才退回 id（见 pages/inventory_page.py 的菜单按钮）。
#
# 命名注意：这里叫 by_test_id 而不是 test_id —— pytest 会把测试模块里
# 以 test_ 开头的可调用对象当作用例收集，test_id 一旦被 import 进用例文件
# 就会凭空多出一条用例。
# ============================================================


def by_test_id(value):
    """
    按 data-test 属性生成选择器

    :param value: data-test 的值，如 "title"
    :return: CSS 选择器，如 [data-test='title']
    """
    return f"[data-test='{value}']"
