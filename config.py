import sys

# 检查是否以调试模式运行
DEBUG = "--debug" in sys.argv

def log(msg, level="info"):
    """统一的日志输出"""
    if DEBUG:
        # 调试模式：所有信息都输出，带 [DEBUG] 前缀
        print(f"[DEBUG] {msg}")
    else:
        # 普通模式：只输出 info、success、error
        if level == "error":
            print(f"X {msg}")
        elif level == "success":
            print(f"√ {msg}")
        elif level == "info":
            print(f"- {msg}")
        # debug 级别在普通模式下什么都不输出