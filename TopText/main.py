"""TopTop 入口程序。"""
import sys

from app import App

def main() -> int:
    app = App()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
