"""视频解析线程：通过 DrissionPage 监听接口提取视频信息。"""

import json

from DrissionPage import ChromiumPage, ChromiumOptions
from PySide6.QtCore import QThread, Signal

from cofig import HEADERS
from utils import extract_video_id

class DouyinParser(QThread):
    """解析抖音视频链接，提取视频信息。"""

    log = Signal(str)
    parse_finished = Signal(dict)
    error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._co = self._init_options()
        self._page: ChromiumPage | None = None
        self._url = ''
        self._is_cancelled = False

    def setup(self, url: str) -> None:
        self._url = url
        self._is_cancelled = False

    def cancel(self) -> None:
        self._is_cancelled = True
        self.log.emit('[*] 正在取消...')

    def close(self) -> None:
        if self._page:
            try:
                self._page.quit()
            except (AttributeError, ConnectionError, RuntimeError) as e:
                self.log.emit(f'[*] 关闭浏览器时发生预期内异常: {e}')
            except Exception as e:
                self.log.emit(f'[-] 关闭浏览器时发生未知异常: {e}')

    def run(self) -> None:
        try:
            self._ensure_page()
            video_id = extract_video_id(self._url)
            self.log.emit('[*] 正在解析视频!')

            self._page.listen.start('aweme/v1/web/aweme/detail/')
            self._page.get(self._url)
            self._page.wait.ele_displayed('tag=body', timeout=10)
            resp = self._page.listen.wait(timeout=15, count=1)

            if self._is_cancelled:
                self.error.emit('解析已取消')
                return

            if resp is None or resp is False:
                raise RuntimeError('未监听到数据包，可能被风控或网络超时')
            if isinstance(resp, list):
                if not resp:
                    raise RuntimeError('监听到的数据包列表为空')
                resp = resp[0]

            body = resp.response.body
            if isinstance(body, (bytes, str)):
                body = json.loads(body)
            if not isinstance(body, dict) or 'aweme_detail' not in body:
                raise RuntimeError(f'响应结构异常: {str(body)[:200]}')

            detail = body['aweme_detail']
            url_list = detail.get('video', {}).get('play_addr', {}).get('url_list') or []
            if not url_list:
                raise RuntimeError('未取到视频播放地址')

            playaddr = url_list[0].replace('playwm', 'play')
            desc = detail.get('desc', '')
            info = {'video_id': video_id, 'desc': desc, 'playaddr': playaddr}
            self.log.emit('[*] 解析成功!')
            self.parse_finished.emit(info)
        except Exception as e:
            self.log.emit('[-] 解析失败!')
            self.error.emit(str(e))

    @staticmethod
    def _init_options() -> ChromiumOptions:
        """构建无头浏览器配置。"""
        co = ChromiumOptions()
        co.headless(True)  # 不显示浏览器窗口
        co.set_argument('--disable-gpu')  # 禁用 GPU 加速
        co.set_argument('--no-sandbox')  # 关闭沙箱
        co.set_argument('--disable-dev-shm-usage')  # 避免 /dev/shm 不足崩溃
        co.set_argument('--disable-blink-features=AutomationControlled')  # 隐藏自动化特征
        co.set_argument('--exclude-switches=enable-automation')  # 移除自动化标记
        co.set_argument('--disable-features=IsolateOrigins,site-per-process')  # 降低站点隔离
        co.set_argument('--disable-site-isolation-trials')  # 减少站点隔离影响
        co.set_argument('--disable-web-security')  # 关闭同源策略
        co.set_argument('--ignore-certificate-errors')  # 忽略证书错误
        co.set_argument('--remote-allow-origins=*')  # 允许 CDP 跨域连接
        co.set_argument('--window-size=1920,1080')  # 设置窗口尺寸
        co.set_argument('--disable-infobars')  # 隐藏自动化提示条
        co.set_argument('--disable-extensions')  # 禁用扩展
        co.set_argument('--mute-audio')  # 静音
        co.set_argument('--lang=zh-CN')  # 设置语言
        co.set_argument('--timezone=Asia/Shanghai')  # 设置时区
        co.set_user_agent(HEADERS.get('User-Agent', ''))  # 设置 User-Agent

        return co

    def _ensure_page(self) -> None:
        if self._page is None:
            self._page = ChromiumPage(self._co)
