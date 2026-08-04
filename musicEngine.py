import pygame
import time
import os
import threading
import queue
from random import shuffle
import easygui

from fileHandler import cacheHandler, M3UHandler
from utils import getFileMetadata, _format_time, normalizePath
from ui import showLists, progressBar

# 要加快捷键，
#     先去 processHandler init 加宏，
#     再去                analizeKey 加广播
#     再去 musicEngine runCommand 加命令
#     其它 记得备份！！！


#TODOLIST:  
#           按下 m 切换单曲/列表/随机播放
#           按下 f 加载，按下 e 保存 m3u 播放列表

class musicEngine:
    def __init__(self, playlist: list, Qevent: queue.Queue):
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
        self.playMode = 0b0001  # 0b 单曲循环 顺序播放 随机播放 列表循环
        self.destination = ""
        # 创建 cache
        self.handler = cacheHandler("metadata_cache.json")
        self.cache = self.handler.readJson()
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
        data = getFileMetadata(self.destination)
        if data:
            self.__dict__.update({
                'audioTitle': data['title'],
                'audioArtist': data['artist'],
                'AudioAlbum': data['album'],
                'duration': data['duration'],
                'bitrate': data['bitrate'],
                'sampleRate': data['sampleRate'],
                'channels': data['channels']
            })
        else:
            # fallback
            self.audioTitle = os.path.basename(self.destination)
            self.audioArtist = "未知艺术家"
            self.AudioAlbum = "未知专辑"
            self.duration = 180.0
            self.bitrate = None
            self.sampleRate = None
            self.channels = None

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
    
    def shuffleList(self):
        wasPlaying = self.isPlaying
        self.currentIndex = 0
        shuffle(self.playlist) # shuffle 是从 random 直接引进的方法
        self.loadSong(self.playlist[0])
        self.play()
        if not wasPlaying:
            self.pause()
    
    def showInfo(self):
        print("\n"+"-" * 50)
        print(f"正在播放：{self.audioTitle}")
        print(f"创作者  ：{self.audioArtist}")
        print(f"专辑    ：{self.AudioAlbum}")
        print(f"文件    ：{self.destination}")
        print(f"比特率  ：{f'{self.bitrate:.0f} kbps' if self.bitrate else '未知'}")
        print(f"采样率  ：{f'{self.sampleRate} Hz' if self.sampleRate else '未知'}")
        print(f"声道数  ：{self.channels if self.channels else '未知'}")
        print(f"总时长  ：{_format_time(self.duration)}")
        print("-" * 50)

    def createPlaylist(self):
        """创建播放列表（同样不需要线程）"""
        print("尝试打开 easygui 对话框 ... ")
        files = easygui.fileopenbox(
            title="选择要添加到播放列表的歌曲",
            default="*.mp3",
            filetypes=["*.mp3", "*.flac", "*.ogg"],
            multiple=True  # 多选
        )
        if not files:
            print("没有选择文件")
            return
        
        filename = easygui.filesavebox(
            title="保存播放列表",
            default="播放列表.m3u",
            filetypes="*.m3u"
        )
        if not filename:
            return
        if not filename.endswith('.m3u'):
            filename += '.m3u'
        # 给 m3u 供应文件数据
        relatedFiles = []
        # 首先转化相对路径
        for song in files:
            relatedFiles.append(normalizePath(song))
        # 检查文件是否在 cache 里
        # 如果在，直接存 m3u 大词典
        # 如果不在，读一下元数据
        streamsInfo = []
        for song in relatedFiles:
            if song in self.cache:
                metadata = self.cache.get(song)
            else:
                metadata = getFileMetadata(song)
            streamsInfo.append({
                "title": f"{metadata.get('artist')} - {metadata.get('title')}",
                "url": song,
                "duration": metadata.get('duration'),
            })
            
        
        m3uHandler = M3UHandler()
        m3uHandler.writeM3UFile(filename, streamsInfo)

    def loadPlaylist(self):
        print("尝试打开 easygui 对话框 ...")
        """加载播放列表（直接在主线程调用，不需要子线程）"""
        # 选择文件（阻塞，但不依赖主循环）
        file = easygui.fileopenbox(
            title="选择播放列表",
            default="*.m3u",
            filetypes=["*.m3u"]
        )
        if not file:
            print("未选择文件")
            return 1
        
        # 解析 M3U
        m3uhandle = M3UHandler()
        playlist, metadatas = m3uhandle.readM3UFile(file)
        
        if playlist:
            self.playlist = playlist
            self.currentIndex = 0
            for path, meta in metadatas.items():
                if path not in self.cache:
                    self.cache[path] = meta
            self.loadSong(self.playlist[0])
            if self.isPlaying:
                self.play()
            print(f"已加载播放列表 ({len(playlist)} 首歌)")
        else:
            return 1
    
    def switchMode(self):
        self.playMode
            
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
                    showLists(self.currentIndex, self.playlist, self.cache)
                elif command == "random":
                    self.shuffleList()
                elif command == "show_info":
                    self.showInfo()
                elif command == "change_mode":
                    # 没做完
                    pass
                elif command == "save_playlist":
                    self.createPlaylist()
                elif command == "load_playlist":
                    wasPlaying = self.isPlaying
                    if not self.loadPlaylist():
                        self.currentIndex = 0
                        showLists(self.currentIndex, self.playlist, self.cache)
                        self.loadSong(self.playlist[0])
                        self.play()
                        if not wasPlaying:
                            self.pause()
                    else:
                        pass
            except queue.Empty:
                pass
            
            print(f"\r{self.get_progress_bar()}", end="")


    #进度条
    def get_progress_bar(self, length=50):
        percent = self.timeDuration / self.duration if self.duration > 0 else 0
        filled = int(percent * length)
        bar = "█" * filled + "░" * (length - filled)
        
        info = f"{self.audioArtist} - {self.audioTitle}"
        if self.AudioAlbum and self.AudioAlbum != "未知专辑":
            info += f" [ {self.AudioAlbum} ]"
        
        # 生成显示信息（带滚动）
        display_info, self.scroll_offset, self.scroll_counter = progressBar(
            info, 
            self.scroll_offset, 
            self.scroll_counter
        )
        
        return f"[{bar}] {percent*100:.1f}% {_format_time(self.timeDuration)}/{_format_time(self.duration)}  {display_info}             "


# 免得以后的我看不懂，在没有搞清楚自己再干啥之前不要动 musicEngine
# 绝不对不要动 keyHandler 除非以后改了焦点窗口标题

# 按照注释一句一句读！！！
# 添加函数一定要写好每一个参数的类型！！！
