"""工具模块：整合文件名处理、资源加载与浏览器路径配置等功能。"""

import os
import re
import sys
from DrissionPage import ChromiumOptions


# 文件名工具
_MAX_TITLE_LEN = 80

_EMOJI_RE = re.compile(
    '['
    '\U0001F000-\U0001FAFF'
    '\U00002600-\U000027BF'
    '\U0001F1E0-\U0001F1FF'
    '\U00002B00-\U00002BFF'
    ']',
    flags=re.UNICODE,
)

_VIDEO_ID_RE = re.compile(r'video/(\d+)')


def extract_video_id(video_url: str) -> str:
    """从抖音链接中提取视频ID。"""
    match = _VIDEO_ID_RE.search(video_url)
    if not match:
        raise ValueError('未发现视频ID，请检查链接是否正确')
    return match.group(1)


def sanitize_title(desc: str, video_id: str) -> str:
    """净化视频描述为合法文件名。"""
    title = desc or ''
    title = re.sub(r'#[^#\n]*#?', '', title)
    title = re.sub(r'@[\w\-_\u4e00-\u9fa5]+', '', title)
    title = _EMOJI_RE.sub('', title)
    title = re.sub(r'[\\/:*?"<>|]', '', title)
    title = re.sub(r'[\x00-\x1f\x7f]', '', title)
    title = re.sub(r'\s+', '', title)
    title = re.sub(r'[·.、,_-]{2,}', '', title)
    title = title.strip('. _-·、,')
    if len(title) > _MAX_TITLE_LEN:
        title = title[:_MAX_TITLE_LEN].strip('. _-·、,')
    return title if title else f'douyin_{video_id}'


def get_unique_path(save_dir: str, title: str, ext: str = 'mp4') -> str:
    """生成不冲突的保存路径，若已存在则追加序号。"""
    base_path = os.path.join(save_dir, f'{title}.{ext}')
    if not os.path.exists(base_path):
        return base_path
    idx = 1
    while True:
        candidate = os.path.join(save_dir, f'{title}_{idx}.{ext}')
        if not os.path.exists(candidate):
            return candidate
        idx += 1


# 资源加载工具

def get_resource_path(relative_path: str) -> str:
    """获取资源绝对路径，兼容 PyInstaller 打包环境。"""
    base_path: str = getattr(sys, '_MEIPASS', '')
    if not base_path:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return str(os.path.join(base_path, relative_path))


# 浏览器路径配置

def set_browser_path(webpath: str) -> bool:
    """设置并永久保存浏览器路径。"""
    if webpath:
        ChromiumOptions().set_browser_path(webpath).save()
        return True
    return False


