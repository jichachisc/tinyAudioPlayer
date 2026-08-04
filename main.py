import os
import queue
import threading
from utils import scanDir
from musicEngine import musicEngine
from processHandler import processHandler

if __name__ == "__main__":
    os.system("title python  music")
    Qevent = queue.Queue()
    playlistDir = "./"
    playlist = scanDir(playlistDir)
    if playlist != [] and playlist:
        engine = musicEngine(playlist , Qevent)
        engine.loadState()
        handler = processHandler(Qevent)
        threading.Thread(target=handler.analizeKey, daemon=True).start()
        cmd_thread = threading.Thread(target=engine.runCommand)
        cmd_thread.daemon = True
        cmd_thread.start()
        Qevent.put("start")

        # 主线程继续做其他事
        print("播放器已启动，按 Esc 退出...")
        cmd_thread.join()
        print("播放器已退出")