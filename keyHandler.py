from pynput import keyboard
import queue
import threading
import pywinctl

class keyHandler:
    def __init__(self, Qevent2handler, Qkey=keyboard.Key.esc, inDebug = False, nameIncluded="python  music"):
        self.pressed_keys = set()
        self.key_queue = queue.Queue()
        self.running = True
        self.listener = None
        self.inDebug = inDebug
        self.controlEvent = Qevent2handler
        self.nameIncluded = nameIncluded
        if not isinstance(Qkey, keyboard.Key):
            raise TypeError(f"Expected Key enum, got {type(Qkey).__name__}: {Qkey}")  
        else:
            self.quitKey = Qkey
        self.stopRequest = False
        #self.Qevent = Qevent

    def on_press(self, key):
        try:
            active_window = pywinctl.getActiveWindow()
            if not active_window or self.nameIncluded not in active_window.title.lower():
                #print(active_window.title.lower())
                return  # 窗口未激活，直接返回，不处理任何按键
        except Exception as e:
            print(e)  # 万一 get_active_window 出错，也不影响其他程序

        try:
            key_name = key.char
        except AttributeError:
            key_name = str(key).replace('Key.', '')
        
        if key_name not in self.pressed_keys:
            self.pressed_keys.add(key_name)
            self.key_queue.put(("press", key_name))
            if self.inDebug: print(f"按下: {key_name}")
            # self.controlEvent.put(key_name)
        
        if key == self.quitKey and not self.stopRequest:
            self.stopRequest = True
            self.key_queue.put(("quit", "esc"))
            if self.inDebug: print("收到退出信号")
    
    def on_release(self, key):
        try:
            key_name = key.char
        except AttributeError:
            key_name = str(key).replace('Key.', '')
        
        if key_name in self.pressed_keys:
            self.pressed_keys.remove(key_name)
            self.key_queue.put(("release", key_name))
            if self.inDebug: print(f"释放: {key_name}")
    
    def start(self):
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        self.listener.start()
    
    def process_events(self):
        while self.running:
            try:
                event_type, key = self.key_queue.get(timeout=0.1)
                if event_type == "press":
                    if self.inDebug: print(f"触发: {key}")
                    self.controlEvent.put(key)
                if event_type == "quit":
                    self.controlEvent.put("quit")
                    self.running = False
                    break
            except queue.Empty:
                pass
    
    # def stop(self):
    #     self.running = False
    #     if self.listener:
    #         self.listener.stop()
    #         return False

# 使用
if __name__ == "__main__":
    Qevent = queue.Queue()
    handler = keyHandler(Qevent, inDebug=True, nameIncluded=" ")
    handler.start()
    thread = threading.Thread(target=handler.process_events)
    thread.daemon = True
    thread.start()

    print("按任意键测试，按 ESC 退出")
    thread.join()  # 等待线程结束