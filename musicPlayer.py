import pygame
import time
import os
import threading
import queue
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from keyHandler import keyHandler
from random import shuffle

# 要加快捷键，
#     先去 processHandler init 加宏，
#     再去 analizeKey 加广播
#     再去 musicEngine runCommand 加命令
#     其它 一概不要动！！！


#TODOLIST:  按下 i 显示歌曲信息
#           按下 m 切换单曲/列表/随机播放
#           

class musicEngine:
    def __init__(self, playlist: list, Qevent: queue.Queue ):
        # 初始化基本参量
        print("尝试启动")
        self.isPlaying = False
        self.isPaused = False
        self.timeDuration = 0.0
        self.timeStart = None
        self.scroll_offset = 0
        self.scroll_counter = 0
        self.Qevent = Qevent
        self.duration = 180.0  # 默认 3 分钟
        self.timeImagine = 10.0 # 这里timeImagine是前进时间
        # 初始化播放列表
        self.playlist = playlist
        self.currentIndex = 0
        self.destination = ""
        # 初始化列表办法
        # 初始化引擎
        # 获取元数据
        if self.playlist:
            self.loadSong(self.playlist[0])
        # audioArtist, audioTitle, audioAlbum, duration

        self.running = True # 主进程
    
    # 以下模块为初始化阶段做的事情
    def loadSong(self, destination):
        #目的：重新初始化引擎基本参量
        self.destination = destination
        self.timeDuration = 0.0
        self.timeStart = None
        self.isPlaying = False
        self.isPaused = False
        self.scroll_offset = 0
        self.scroll_counter = 0
        print(f"\r{' ' * 120}\r尝试重置引擎成功，尝试加载 {self.destination}")
        self.init_engine()
        self.get_Metadata() 

    def init_engine(self):
        pygame.mixer.init()
        pygame.mixer.music.load(self.destination)
    
    def get_Metadata(self):
        destination = self.destination
        ext = os.path.splitext(destination)[1].lower()
        self.title = os.path.basename(destination)
        self.artist = "未知艺术家"
        self.album = "未知专辑"

        try:
            if ext == '.mp3':
                audio = MP3(destination)
                # MP3 用 ID3 字段名
                self.audioTitle = audio.get('TIT2', [self.title])[0] if 'TIT2' in audio else self.title
                self.audioArtist = audio.get('TPE1', ['未知艺术家'])[0] if 'TPE1' in audio else "未知艺术家"
                self.AudioAlbum = audio.get('TALB', ['未知专辑'])[0] if 'TALB' in audio else "未知专辑"
                
            elif ext == '.flac':
                audio = FLAC(destination)
                # FLAC 用 Vorbis Comment 字段名
                self.audioTitle = audio.get('title', [self.title])[0] if 'title' in audio else self.title
                self.audioArtist = audio.get('artist', ['未知艺术家'])[0] if 'artist' in audio else "未知艺术家"
                self.AudioAlbum = audio.get('album', ['未知专辑'])[0] if 'album' in audio else "未知专辑"
                
            elif ext == '.ogg':
                audio = OggVorbis(destination)
                # OGG 也是 Vorbis Comment
                self.audioTitle = audio.get('title', [self.title])[0] if 'title' in audio else self.title
                self.audioArtist = audio.get('artist', ['未知艺术家'])[0] if 'artist' in audio else "未知艺术家"
                self.AudioAlbum = audio.get('album', ['未知专辑'])[0] if 'album' in audio else "未知专辑"
            else:
                return
                
            self.duration = audio.info.length
            
        except Exception as e:
            print(f"元数据读取失败: {e}")

    # 处理流
    def play(self):
        # 判断是否开播 -> 播放
        if not self.isPlaying:
            pygame.mixer.music.play()
            # 时间戳
            self.timeStart = time.perf_counter()
            # 改布尔
            self.isPlaying = True
            print("开始播放")
        else:
            print("正在进行")
        
    # 控制模块
    def pause(self):
        # 判断是否暂停 -> 暂停
        if self.isPlaying:
            # 记录时间戳位置 !! 建立在已经开始的基础上 !!
            self.timeDuration += time.perf_counter() - self.timeStart
            pygame.mixer.music.pause()
            self.isPlaying = False
            self.isPaused = True
            print("暂停")
            # print(self.timeDuration) # Debug
        else:
            print("已经停止")
        
    def resume(self):
        if not self.isPlaying:
            if self.isPaused:
                pygame.mixer.music.unpause()
                self.timeStart = time.perf_counter()
                self.isPaused = False
                self.isPlaying = True
                print("恢复播放")
            else:
                print("不在暂停状态或初始化失效")
        else:
            print("正在播放")
    
    def stop(self):
        if self.isPlaying or self.isPaused:
            pygame.mixer.music.stop()
            self.isPlaying = False
            self.isPaused = False
            # self.current_time = 0.0
            self.timeDuration = 0.0
            self.start_time = None
            print("停止")
        else:
            print("已经停止或未初始化")

    def seek(self, direction=1):
        """
        快进或快退
        direction=1  -> 快进; 
        direction=-1 -> 快退
        """
        if not (self.isPlaying or self.isPaused):
            print("已经停止或未初始化")
            return
        # 计算目标位置
        if self.isPlaying:
            self.timeDuration += time.perf_counter() - self.timeStart
            self.timeStart = time.perf_counter()
        target = self.timeDuration + self.timeImagine * direction
        # 边界检查
        if target < 0:
            target = 0.1
        elif target > self.duration:
            target = self.duration

        # 执行跳转
        pygame.mixer.music.set_pos(target)
        self.timeDuration = target
    
    def nextSong(self):
        if len(self.playlist) > 1:
            wasPlaying = self.isPlaying
            self.currentIndex = (self.currentIndex + 1) % len(self.playlist)
            self.loadSong(self.playlist[self.currentIndex])
            self.play()
            if not wasPlaying:
                self.pause()
    def prevSong(self):
        if len(self.playlist) > 1:
            wasPlaying = self.isPlaying
            self.currentIndex = (self.currentIndex - 1) % len(self.playlist)
            self.loadSong(self.playlist[self.currentIndex])
            self.play()
            if not wasPlaying:
                self.pause()

    def showList(self):
        print("\n" + "-" * 50)
        
        # 1. 决定要显示的子列表
        total = len(self.playlist)
        if total <= 19:
            temp = self.playlist
            start_idx = 0
        else:
            if self.currentIndex < 9:
                temp = self.playlist[0:19]
                start_idx = 0
            elif self.currentIndex >= total - 9:
                temp = self.playlist[-19:]
                start_idx = total - 19
            else:
                temp = self.playlist[self.currentIndex - 9 : self.currentIndex + 10]
                start_idx = self.currentIndex - 9
        
        # 2. 计算最大编号宽度（用于对齐）
        max_digits = len(str(total))
        
        # 3. 显示上面的省略号
        if total > 19 and start_idx > 0:
            print("...")
        
        # 4. 显示列表
        for i, song in enumerate(temp):
            real_num = start_idx + i + 1  # 从 1 开始的编号
            is_current = (start_idx + i) == self.currentIndex  # 判断是否为当前歌曲
            
            # 格式化编号（右对齐）
            num_str = str(real_num).rjust(max_digits)
            
            if is_current:
                print(f"-> {num_str}. {os.path.basename(song)}")
            else:
                print(f"   {num_str}. {os.path.basename(song)}")
        
        # 5. 显示下面的省略号
        if total > 19 and start_idx + 19 < total:
            print("... ( Total "+str(len(self.playlist))+" Items )")
        
        print("-" * 50)
    
    def shuffleList(self):
        wasPlaying = self.isPlaying
        self.currentIndex = 0
        shuffle(self.playlist) # shuffle 是从 random 直接引进的方法
        self.loadSong(self.playlist[0])
        self.play()
        if not wasPlaying:
            self.pause()
    
    # 总控制器
    def runCommand(self):
        while self.running:
            if self.timeDuration >= self.duration:
                self.nextSong()
            if self.isPlaying and self.timeStart:
                self.timeDuration += time.perf_counter() - self.timeStart
                self.timeStart = time.perf_counter()
            try:
                # 过来加命令
                command = self.Qevent.get(timeout=0.1)
                if command == "start":
                    self.play()
                elif command == "toggle":
                    if self.isPlaying: self.pause()
                    else: self.resume()
                elif command == "stop":
                    self.running = False
                    self.stop()
                elif command == "fseek":
                    self.seek(1)
                elif command == "bseek":
                    self.seek(-1)
                elif command == "next_song":
                    self.nextSong()
                elif command == "prev_song":
                    self.prevSong()
                #二期
                elif command == "volume_up":
                    current = pygame.mixer.music.get_volume()
                    pygame.mixer.music.set_volume(min(1.0, current + 0.1))
                    print(f" 音量: {int(pygame.mixer.music.get_volume() * 100)}%")
                elif command == "volume_down":
                    current = pygame.mixer.music.get_volume()
                    pygame.mixer.music.set_volume(max(0.0, current - 0.1))
                    print(f" 音量: {int(pygame.mixer.music.get_volume() * 100)}%")
                elif command == "show_list":
                    self.showList()
                elif command == "random":
                    self.shuffleList()
                elif command == "show_info":
                    pass
            except queue.Empty:
                pass
            
            print(f"\r{self.get_progress_bar()}", end="")


    #进度条
    def get_progress_bar(self, length=50):
        max_display_len = 40  # 显示区域宽度

        percent = self.timeDuration / self.duration if self.duration > 0 else 0
        filled = int(percent * length)
        bar = "█" * filled + "░" * (length - filled)
        
        info = f"{self.audioArtist} - {self.audioTitle}"
        if self.AudioAlbum and self.AudioAlbum != "未知专辑":
            info += f" [ {self.AudioAlbum} ]"
        
        if len(info) > max_display_len:
            info = max_display_len*' '+info
        
        # 滚动信息：每隔几帧滚动一次
        
        if len(info) > max_display_len:
            # 滚动逻辑
            self.scroll_counter += 1
            if self.scroll_counter % 2 == 0:  # 每 3 次循环滚动 1 格
                self.scroll_offset = (self.scroll_offset + 1) % (len(info) + 1)
            
            # 取滚动后的片段
            if self.scroll_offset + max_display_len <= len(info):
                display_info = info[self.scroll_offset:self.scroll_offset + max_display_len]
            else:
                # 尾巴不够长时，前面补空格
                remaining = len(info) - self.scroll_offset
                display_info = info[self.scroll_offset:] + " " * (max_display_len - remaining)
        else:
            display_info = info.ljust(max_display_len)
            # 如果信息短，重置滚动偏移
            self.scroll_offset = 0
        
        return f"[{bar}] {percent*100:.1f}% {self._format_time(self.timeDuration)}/{self._format_time(self.duration)}  {display_info}"
    
    def _format_time(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"
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
            except:
                pass
    
    
# 免得以后的我看不懂，在没有搞清楚自己再干啥之前不要动 musicEngine
# 绝不对不要动 keyHandler 除非以后改了焦点窗口标题

# 按照注释一句一句读！！！
# 添加函数一定要写好每一个参数的类型！！！

def scanDir(path: str):
    songs = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(('.mp3', '.flac', '.ogg')):
                songs.append(os.path.join(root, file))
    return songs

if __name__ == "__main__":
    os.system("title python  music")
    Qevent = queue.Queue()
    playlist = scanDir("./")
    engine = musicEngine(playlist , Qevent)
    handler = processHandler(Qevent)
    threading.Thread(target=handler.analizeKey, daemon=True).start()
    cmd_thread = threading.Thread(target=engine.runCommand)
    cmd_thread.daemon = True
    cmd_thread.start()
    Qevent.put("start")

    # 主线程可以继续做其他事（比如等待用户输入）
    print("播放器已启动，按 Esc 退出...")
    cmd_thread.join()
    print("播放器已退出")

