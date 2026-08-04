import queue
import threading

from keyHandler import keyHandler
# 解析按键
class processHandler:
    def __init__(self, Qevent: queue.Queue):
        # 用于和 keyHandler 通讯的专用 queue 
        Qevent2handler = queue.Queue()
        # 把键盘控制器拿过来
        self.Qevent2handler = Qevent2handler
        handler = keyHandler(Qevent2handler)
        handler.start()
        thread = threading.Thread(target=handler.process_events)
        thread.daemon = True
        thread.start() 
        self.Qevent = Qevent
        self.thread = thread

        # 宏定义
        self.START = "s"
        self.PAUSE = "space"
        self.RESUME = "space"
        self.STOP = "esc"
        self.FORWARD = "right"
        self.BACKWARD = "left"
        self.VOLUMEUP = "up"
        self.VOLUMEDOWN = "down"
        self.NEXTSONG = "page_down"
        self.PREVSONG = "page_up"
        self.SHOWLIST = "l"
        self.RANDOM = "r"
        self.SHOWINFO = "i"
        self.CHANGEMODE = "m"
        self.LOADPLAYLISTFILE = "f"
        self.CREATEPLATLISTFILE = "c"

    def analizeKey(self):
        while self.thread.is_alive():
            try:
                key = self.Qevent2handler.get(timeout=0.05)
                if key == self.START:
                    self.Qevent.put("start")
                
                elif key == self.PAUSE or key == self.RESUME:
                    self.Qevent.put("toggle")
                
                elif key == self.STOP:
                    self.Qevent.put("stop")
                elif key == self.FORWARD:
                    self.Qevent.put("fseek")
                elif key == self.BACKWARD:
                    self.Qevent.put("bseek")
                elif key == self.VOLUMEDOWN:
                    self.Qevent.put("volume_down")
                elif key == self.VOLUMEUP:
                    self.Qevent.put("volume_up")
                elif key == self.NEXTSONG:
                    self.Qevent.put("next_song")
                elif key == self.PREVSONG:
                    self.Qevent.put("prev_song")
                elif key == self.SHOWLIST:
                    self.Qevent.put("show_list")
                elif key == self.RANDOM:
                    self.Qevent.put("random")
                elif key == self.SHOWINFO:
                    self.Qevent.put("show_info")
                elif key == self.CHANGEMODE:
                    self.Qevent.put("change_mode")
                elif key == self.LOADPLAYLISTFILE:
                    self.Qevent.put("load_playlist")
                elif key == self.CREATEPLATLISTFILE:
                    self.Qevent.put("save_playlist")
            except Exception as e:
                print(f"捕获到错误： {e}")
    
    