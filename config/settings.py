# ============================================================
# 配置层：所有环境配置、全局常量统一放这里
# 设计要点：
#   1. 环境由环境变量 ENV 决定，默认 local；白名单校验，写错环境名直接报错
#   2. 被测地址支持 BASE_URL 覆盖，切环境不用改代码
#      （CI 的 workflow 里声明了 BASE_URL，这里读取后那行才真正生效）
# ============================================================

import os

# 允许的环境白名单。local = 本地部署（npm run start），prod = Sauce Labs 线上站点
ALLOWED_ENVS = ("local", "prod")

# 当前运行环境：默认本地
ENV = os.getenv("ENV", "local")
if ENV not in ALLOWED_ENVS:
    raise ValueError(f"未知环境 ENV={ENV}，可选值：{ALLOWED_ENVS}")

# 各环境的默认配置（单项可被同名环境变量覆盖，见下方导出的变量）
ENV_CONFIG = {
    "local": {
        "base_url": "http://localhost:3000",       # 本地部署的 sample-app-web
    },
    "prod": {
        "base_url": "https://www.saucedemo.com",   # 线上对照环境
    },
}

# 对外导出的最终配置：优先级 环境变量 > ENV_CONFIG 默认值
BASE_URL = os.getenv("BASE_URL", ENV_CONFIG[ENV]["base_url"])

# 项目根目录：data 定位、被测应用 commit 探测都基于它
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 兼容性用例的移动端视口（与 Chrome DevTools 的 iPhone 12/13 逻辑分辨率一致）
MOBILE_VIEWPORT = {"width": 390, "height": 844}
