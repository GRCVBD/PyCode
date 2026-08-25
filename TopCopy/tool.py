import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> str:
    """
    获取资源路径，自动区分开发环境与打包环境下的资源路径

    :param relative_path:资源的相对路径
    :return:资源的绝对路径
    """
    meipass: str = getattr(sys, "_MEIPASS", "")
    if getattr(sys, "frozen", False) and meipass:
        base_path = Path(meipass)
    else:
        base_path = Path(__file__).resolve().parent
    return str((base_path / relative_path.lstrip("/\\")).resolve())
