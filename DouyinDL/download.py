"""视频下载线程：通过 requests 流式下载视频文件。"""

import os
import time

import requests
from PySide6.QtCore import QThread, Signal

from cofig import HEADERS
from utils import sanitize_title, get_unique_path

class VideoDownloader(QThread):
    """下载抖音视频文件，支持取消、重试与进度回调。"""

    log = Signal(str)
    progress = Signal(int)
    download_finished = Signal(str)
    error = Signal(str)

    MAX_RETRIES = 3

    def __init__(self) -> None:
        super().__init__()
        self._info: dict | None = None
        self._save_dir = ''
        self._is_cancelled = False

    def setup(self, info: dict, save_dir: str) -> None:
        self._info = info
        self._save_dir = save_dir
        self._is_cancelled = False

    def cancel(self) -> None:
        self._is_cancelled = True
        self.log.emit('[*] 正在取消...')

    def run(self) -> None:
        save_path = ''
        try:
            title = sanitize_title(self._info['desc'], self._info['video_id'])
            save_path = get_unique_path(self._save_dir, title)
            self.log.emit(f'[*] 开始下载...')

            headers = {**HEADERS, 'Referer': 'https://www.douyin.com/', 'Accept': '*/*'}
            url = self._info['playaddr']
            last_err = self._download_with_retry(url, headers, save_path)

            if self._is_cancelled:
                self._cleanup(save_path)
                self.error.emit('下载已取消')
            elif last_err is not None:
                self._cleanup(save_path)
                self.log.emit(f'[-] 下载失败: {last_err}')
                self.error.emit(str(last_err))
            else:
                self.log.emit(f'[+] 下载完成!')
                self.download_finished.emit(save_path)
        except Exception as e:
            self._cleanup(save_path)
            self.log.emit(f'[-] 下载失败: {e}')
            self.error.emit(str(e))

    def _download_with_retry(self, url: str, headers: dict, save_path: str) -> Exception | None:
        last_err = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            if self._is_cancelled:
                break
            try:
                downloaded, total_size = self._fetch_and_save(url, headers, save_path)
                if self._is_cancelled:
                    break
                if total_size > 0 and downloaded < total_size:
                    last_err = RuntimeError(f'文件不完整({downloaded}/{total_size})')
                    if attempt < self.MAX_RETRIES:
                        self.log.emit(f'[!] 第{attempt}次下载不完整，重试中...')
                        time.sleep(2 ** (attempt - 1))
                    continue
                last_err = None
                break
            except (requests.RequestException, ConnectionError, OSError) as e:
                last_err = e
                if attempt < self.MAX_RETRIES:
                    if self._is_cancelled:
                        break
                    self.log.emit(f'[!] 第{attempt}次下载失败({e})，重试中...')
                    time.sleep(2 ** (attempt - 1))
                else:
                    raise
        return last_err

    def _fetch_and_save(self, url: str, headers: dict, save_path: str) -> tuple[int, int]:
        with requests.get(url, headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded, last_percent = 0, -1
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if self._is_cancelled:
                        break
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int(downloaded * 100 / total_size)
                            if percent > last_percent:
                                last_percent = percent
                                self.progress.emit(percent)
        return downloaded, total_size

    @staticmethod
    def _cleanup(save_path: str) -> None:
        if save_path and os.path.exists(save_path):
            os.remove(save_path)
