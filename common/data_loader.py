# ============================================================
# 数据加载工具类
# 作用：读取 YAML 格式的测试数据，按模块分目录存放
# 优势：数据与代码分离，换账号、加账号不用改代码
# ============================================================

import os

import yaml


class DataLoader:
    """YAML 测试数据加载器"""

    def __init__(self, yaml_dir=None):
        """
        初始化
        :param yaml_dir: YAML 文件目录，不传则用项目根目录下的 data
        """
        if yaml_dir is None:
            # 默认路径：项目根目录下的 data（按模块分目录，如 data/login/accounts.yaml）
            self.yaml_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data",
            )
        else:
            self.yaml_dir = yaml_dir

    def load(self, filename, key=None):
        """
        读取 YAML 文件
        :param filename: 相对 data 目录的路径，如 "login/accounts.yaml"
        :param key: 要读取的子节点 key，不传则返回整个文件内容
        :return: 读取到的数据
        """
        filepath = os.path.join(self.yaml_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if key is not None:
            if key not in data:
                raise KeyError(f"YAML 文件 {filename} 中找不到 key: {key}")
            data = data[key]

        return data


# 全局实例，其他模块直接导入使用
data_loader = DataLoader()
