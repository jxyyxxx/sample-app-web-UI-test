# ============================================================
# 断言工具类
# 作用：封装常用 UI 断言，统一报错信息，减少页面层重复代码
#      断言都包在 allure.step 里，报告里能直接看到"哪一步断言失败"
# ============================================================

import allure
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# 在浏览器上下文里判断列表是否已按目标顺序排列。
# 说明：排序是前端异步重渲染，"选中下拉框"返回并不等于 DOM 已经重排。
#      直接取一次快照再比大小，在慢机器或 performance_glitch_user 上要么偶发
#      失败，要么更糟——读到旧顺序而假通过。所以交给 Playwright 自动重试。
# 注意：Playwright 的 Python 版没有 JS 里的 expect.poll，这里用 wait_for_function 实现。
SORTED_JS = """
([selector, mode, reverse]) => {
  const nodes = Array.from(document.querySelectorAll(selector));
  if (nodes.length === 0) return false;   // 列表还没渲染出来
  if (nodes.length === 1) return true;    // 单个元素天然有序
  const keyOf = mode === 'number'
    ? (text) => parseFloat(text.replace(/[^0-9.]/g, ''))
    : (text) => text.trim();
  const keys = nodes.map((node) => keyOf(node.textContent || ''));
  for (let i = 1; i < keys.length; i++) {
    const ordered = reverse ? keys[i] <= keys[i - 1] : keys[i] >= keys[i - 1];
    if (!ordered) return false;
  }
  return true;
}
"""


class AssertUtils:
    """断言工具类"""

    def assert_sorted(self, page, selector, mode="number", reverse=False, label="列表", timeout=5000):
        """
        断言元素列表已按目标顺序排列（轮询等待，超时给出实际顺序）

        :param page: Playwright Page 对象
        :param selector: 列表元素选择器
        :param mode: number = 按数值比较（价格），text = 按字典序比较（名称）
        :param reverse: True = 降序，False = 升序
        :param label: 失败信息里的业务名称，如"商品价格"
        :param timeout: 最长等待毫秒数
        """
        order = "降序" if reverse else "升序"
        with allure.step(f"断言：{label}按{order}排列"):
            try:
                page.wait_for_function(SORTED_JS, arg=[selector, mode, reverse], timeout=timeout)
            except PlaywrightTimeoutError:
                actual = [text.strip() for text in page.locator(selector).all_inner_texts()]
                raise AssertionError(f"{label}未按{order}排列，实际顺序：{actual}") from None


# 全局实例，页面层直接导入使用
assert_utils = AssertUtils()
