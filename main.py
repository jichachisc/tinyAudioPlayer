import os
import queue
import threading
from utils import scanDir
from musicEngine import musicEngine
from processHandler import processHandler
from easygui import diropenbox
from config import DEBUG, log

if __name__ == "__main__":
    if DEBUG:
        os.system("title tinyAudioPlayer (debug)")
        log("以调试模式启动", "debug")
    else:
        os.system("title tinyAudioPlayer")
    
    Qevent = queue.Queue()
    dir = diropenbox(
        msg = "选择媒体库目录",
        title = "选择文件夹",
        default = "./"
    )
    if dir:
        playlistDir = dir
    else:
        playlistDir = "./"
    playlist = scanDir(playlistDir)
    
    if playlist:
        engine = musicEngine(playlist, Qevent, playlistDir)
        
        if os.path.exists("stateBeforeExit.json"):
            engine.loadState()
        else:
            engine.loadSong(playlist[0])
        
        handler = processHandler(Qevent)
        threading.Thread(target=handler.analizeKey, daemon=True).start()
        cmd_thread = threading.Thread(target=engine.runCommand)
        cmd_thread.daemon = True
        cmd_thread.start()

        # 用户提示（简短的帮助信息）
        print("\n" + "=" * 50)
        print("tinyAudioPlayer")
        print("=" * 50)
        print("  快捷键:")
        print("  Space  播放/暂停    PageDown  下一首")
        print("  →/←    快进/后退    PageUp    上一首")
        print("  ↑/↓    音量调节     M         切换模式")
        print("  L      显示列表     I         歌曲信息")
        print("  F      加载列表     C         保存列表")
        print("  Esc    退出")
        print("-" * 50)
        Qevent.put("start")
        cmd_thread.join()
        log("播放器已退出", "info")