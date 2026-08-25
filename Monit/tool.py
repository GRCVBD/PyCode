import os
import sys
from pathlib import Path

def get_respath(relpath: str) -> str:
    """
    获取资源路径，自动区分开发环境与打包环境下的资源路径

    :param relpath:资源的相对路径
    :return:资源的绝对路径
    """
    meipass: str = getattr(sys, "_MEIPASS", "")
    if getattr(sys, "frozen", False) and meipass:
        basepath = Path(meipass)
    else:
        basepath = Path(__file__).resolve().parent

    abspath = str((basepath / relpath.lstrip("/\\")).resolve())
    if not os.path.exists(abspath):
        raise Exception(f"Relative Path '{relpath}' Not Exist")
    return abspath
