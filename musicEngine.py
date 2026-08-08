import pygame
import time
import os
import threading
import queue
from random import shuffle, randint
import easygui
import json

from fileHandler import cacheHandler, M3UHandler
from utils import getFileMetadata, _format_time, normalizePath
from ui import showLists, progressBar
from config import DEBUG, log


class musicEngine:
    # 播放模式常量
    MODE_SINGLE = 0b0001       # 单曲循环
    MODE_SEQUENTIAL = 0b0010   # 顺序播放
    MODE_SHUFFLE = 0b0100      # 随机播放
    MODE_LIST = 0b1000         # 列表循环

    def __init__(self, playlist: list, Qevent: queue.Queue):
        log("尝试启动", "debug")
        self.isStarted = False
        self.isPlaying = False
        self.isPaused = False
        self.scroll_offset = 0
        self.scroll_counter = 0
        self.Qevent = Qevent
        self.duration = 180.0
        self.timeImagine = 10.0
        self.play_start_pos = 0.0
        self.current_pos = 0.0

        self.playlist = playlist
        self.currentIndex = 0
        self.playMode = self.MODE_SINGLE
        self.seek_accumulator = 0
        self.seek_timer = None
        self.destination = ""
        self.loadJump = 0.0

        # 创建 cache
        self.handler = cacheHandler("metadata_cache.json", "./")
        if os.path.exists("metadata_cache.json"):
            self.cache = self.handler.readJson()
            songLists = self.cache.keys()
            # 用 normalizePath 统一路径格式再比较
            normalized_playlist = set(normalizePath(p) for p in playlist)
            normalized_cache = set(normalizePath(s) for s in songLists)
            added = normalized_playlist - normalized_cache
            removed = normalized_cache - normalized_playlist

            if added or removed:
                log(f"新增 {len(added)} 首，删除 {len(removed)} 首，重建缓存", "debug")
                self.handler.writeJson()
                self.cache = self.handler.readJson()
            else:
                log("缓存与当前目录一致", "debug")
        else:
            self.handler.writeJson()
            self.cache = self.handler.readJson()

        self.init_engine()
        self.running = True

    def loadSong(self, destination, keep_position=False):
        """加载歌曲
        keep_position: 是否保留 loadJump 位置（用于恢复状态）
        """
        self.destination = destination
        self.isPlaying = False
        self.isPaused = False
        self.isStarted = False
        if not keep_position:
            self.loadJump = 0.0
            self.play_start_pos = 0.0
        self.scroll_offset = 0
        self.scroll_counter = 0
        log(f"\r{' ' * 120}\r尝试重置引擎成功，尝试加载 {self.destination}", "debug")
        self.get_Metadata()
        pygame.mixer.music.load(self.destination)

    def init_engine(self):
        pygame.mixer.init()

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
            self.audioTitle = os.path.basename(self.destination)
            self.audioArtist = "未知艺术家"
            self.AudioAlbum = "未知专辑"
            self.duration = 180.0
            self.bitrate = None
            self.sampleRate = None
            self.channels = None

    def play(self):
        if not self.isStarted:
            pygame.mixer.music.play(start=self.loadJump)
            self.current_pos = self.loadJump
            self.play_start_pos = self.loadJump
            self.isPlaying = True
            self.isStarted = True
            log("开始播放", "info")
        else:
            log("正在进行", "info")

    def pause(self):
        if self.isPlaying:
            pygame.mixer.music.pause()
            self.isPlaying = False
            self.isPaused = True
            log("暂停", "info")
        else:
            log("已经停止", "error")

    def resume(self):
        if not self.isPlaying:
            if self.isPaused:
                pygame.mixer.music.unpause()
                self.isPaused = False
                self.isPlaying = True
                log("恢复播放", "info")
            else:
                log("不在暂停状态或初始化失效", "error")
        else:
            log("正在播放", "info")

    def stop(self):
        if self.isPlaying or self.isPaused:
            pygame.mixer.music.stop()
            self.isPlaying = False
            self.isPaused = False
            self.start_time = None
            log("停止", "debug")
        else:
            log("已经停止或未初始化", "debug")

    def seek(self, direction=1):
        self.seek_accumulator += direction * self.timeImagine

        if self.seek_timer is not None:
            self.seek_timer.cancel()

        self.seek_timer = threading.Timer(0.5, self._apply_seek)
        self.seek_timer.daemon = True
        self.seek_timer.start()

    def _apply_seek(self):
        if self.seek_accumulator == 0:
            return

        if not (self.isPlaying or self.isPaused):
            self.seek_accumulator = 0
            return

        pos_offset = pygame.mixer.music.get_pos() / 1000.0
        if pos_offset < 0:
            pos_offset = 0
        current_pos = self.play_start_pos + pos_offset

        target = current_pos + self.seek_accumulator
        target = max(0.1, min(target, self.duration))

        was_paused = self.isPaused

        pygame.mixer.music.stop()
        pygame.mixer.music.play(start=target)
        self.play_start_pos = target

        if was_paused:
            pygame.mixer.music.pause()
            self.isPlaying = False
            self.isPaused = True
        else:
            self.isPlaying = True
            self.isPaused = False

        log(f"跳转到 {target:.2f} 秒 (累计偏移 {self.seek_accumulator:.1f} 秒)", "info")
        self.seek_accumulator = 0

    def nextSong(self):
        wasPlaying = self.isPlaying
        wasPaused = self.isPaused

        if len(self.playlist) <= 1:
            if self.playMode == self.MODE_SINGLE:
                self.loadSong(self.destination)
                self.play_start_pos = 0
                self.play()
            return

        # 根据模式选择下一首
        if self.playMode == self.MODE_SEQUENTIAL:
            self.currentIndex = (self.currentIndex + 1) % len(self.playlist)
        elif self.playMode == self.MODE_LIST:
            self.currentIndex = (self.currentIndex + 1) % len(self.playlist)
        elif self.playMode == self.MODE_SHUFFLE:
            self.currentIndex = randint(0, len(self.playlist) - 1)
        elif self.playMode == self.MODE_SINGLE:
            self.loadSong(self.destination)
            self.play_start_pos = 0
            self.play()
            return

        # 加载并播放新歌
        self.loadSong(self.playlist[self.currentIndex])
        pygame.mixer.music.load(self.destination)
        self.play_start_pos = 0
        self.play()
        if not wasPlaying or wasPaused:
            self.pause()

    def prevSong(self):
        wasPlaying = self.isPlaying
        wasPaused = self.isPaused

        if len(self.playlist) <= 1:
            if self.playMode == self.MODE_SINGLE:
                self.loadSong(self.destination)
                self.play_start_pos = 0
                self.play()
            return

        if self.playMode == self.MODE_SHUFFLE:
            new_idx = randint(0, len(self.playlist) - 1)
            while new_idx == self.currentIndex and len(self.playlist) > 1:
                new_idx = randint(0, len(self.playlist) - 1)
            self.currentIndex = new_idx
        else:
            self.currentIndex = (self.currentIndex - 1) % len(self.playlist)

        self.loadSong(self.playlist[self.currentIndex])
        pygame.mixer.music.load(self.destination)
        self.play_start_pos = 0
        self.play()
        if not wasPlaying or wasPaused:
            self.pause()

    def shuffleList(self):
        wasPlaying = self.isPlaying
        wasPaused = self.isPaused
        self.currentIndex = 0
        shuffle(self.playlist)
        self.loadSong(self.playlist[0])
        self.play()
        if not wasPlaying or wasPaused:
            self.pause()

    def showInfo(self):
        print("\n" + "-" * 50)
        print(f"正在播放：{self.audioTitle}")
        print(f"创作者  ：{self.audioArtist}")
        print(f"专辑    ：{self.AudioAlbum}")
        print(f"文件    ：{self.destination}")
        print(f"比特率  ：{f'{self.bitrate:.0f} kbps' if self.bitrate else '未知'}")
        print(f"采样率  ：{f'{self.sampleRate} Hz' if self.sampleRate else '未知'}")
        print(f"声道数  ：{self.channels if self.channels else '未知'}")
        print(f"总时长  ：{_format_time(self.duration)}")

        mode_names = {
            self.MODE_SINGLE: "单曲循环",
            self.MODE_SEQUENTIAL: "顺序播放",
            self.MODE_SHUFFLE: "随机播放",
            self.MODE_LIST: "列表循环"
        }
        print(f"播放模式：{mode_names.get(self.playMode, '未知')}")
        print("-" * 50)

    def createPlaylist(self):
        log("尝试打开 easygui 对话框 ... ", "debug")
        files = easygui.fileopenbox(
            title="选择要添加到播放列表的歌曲",
            default="*.mp3",
            filetypes=["*.mp3", "*.flac", "*.ogg"],
            multiple=True
        )
        if not files:
            log("没有选择文件", "debug")
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

        relatedFiles = [normalizePath(song) for song in files]

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
        log("尝试打开 easygui 对话框 ...", "debug")
        file = easygui.fileopenbox(
            title="选择播放列表",
            default="*.m3u",
            filetypes=["*.m3u"]
        )
        if not file:
            log("未选择文件", "debug")
            return False

        m3uhandle = M3UHandler()
        playlist, metadatas = m3uhandle.readM3UFile(file)
        return self.reloadPlaylist(playlist, metadatas)

    def reloadPlaylist(self, playlist, metadatas):
        if not playlist:
            return False

        pygame.mixer.music.stop()

        self.playlist = playlist
        self.currentIndex = 0

        for path, meta in metadatas.items():
            if path not in self.cache:
                self.cache[path] = meta

        self.loadSong(self.playlist[0])
        self.play()

        log(f"已加载播放列表 ({len(playlist)} 首歌)", "info")
        showLists(self.currentIndex, self.playlist, self.cache)
        return True

    def switchMode(self):
        # 循环左移 1 位，保留低 4 位
        self.playMode = ((self.playMode << 1) | (self.playMode >> 3)) & 0b1111
        if self.playMode == 0:
            self.playMode = self.MODE_SINGLE

        mode_names = {
            self.MODE_SINGLE: "单曲循环",
            self.MODE_SEQUENTIAL: "顺序播放",
            self.MODE_SHUFFLE: "随机播放",
            self.MODE_LIST: "列表循环"
        }
        log(f"播放模式: {mode_names.get(self.playMode)}", "info")

    def runCommand(self):
        while self.running:
            # 检查是否播放完毕
            if self.current_pos >= self.duration - 0.2:
                self.nextSong()

            try:
                command = self.Qevent.get(timeout=0.1)
                if command == "start":
                    self.play()
                elif command == "toggle":
                    if self.isPlaying:
                        self.pause()
                    else:
                        self.resume()
                elif command == "stop":
                    self.running = False
                    self.saveState()
                    self.stop()
                elif command == "fseek":
                    self.seek(1)
                elif command == "bseek":
                    self.seek(-1)
                elif command == "next_song":
                    self.nextSong()
                elif command == "prev_song":
                    self.prevSong()
                elif command == "volume_up":
                    current = pygame.mixer.music.get_volume()
                    if current is None:
                        current = 0.7
                    pygame.mixer.music.set_volume(min(1.0, current + 0.1))
                    log(f" 音量: {int(pygame.mixer.music.get_volume() * 100)}%", "info")
                elif command == "volume_down":
                    current = pygame.mixer.music.get_volume()
                    if current is None:
                        current = 0.7
                    pygame.mixer.music.set_volume(max(0.0, current - 0.1))
                    log(f" 音量: {int(pygame.mixer.music.get_volume() * 100)}%", "info")
                elif command == "show_list":
                    showLists(self.currentIndex, self.playlist, self.cache)
                elif command == "random":
                    self.shuffleList()
                elif command == "show_info":
                    self.showInfo()
                elif command == "change_mode":
                    self.switchMode()
                elif command == "save_playlist":
                    self.createPlaylist()
                elif command == "load_playlist":
                    wasPlaying = self.isPlaying
                    if self.loadPlaylist():
                        self.currentIndex = 0
                        showLists(self.currentIndex, self.playlist, self.cache)
                        self.loadSong(self.playlist[0])
                        self.play()
                        if not wasPlaying:
                            self.pause()
            except queue.Empty:
                pass

            print(f"\r{self.get_progress_bar()}", end="")

    def saveState(self):
        volume = pygame.mixer.music.get_volume()
        if volume is None:
            volume = 0.7

        state = {
            "wasPlaying": self.isPlaying,
            "wasPaused": self.isPaused,
            "timeDuration": self.current_pos,
            "currentIndex": self.currentIndex,
            "playlist": self.playlist,
            "volume": volume,
            "playMode": self.playMode
        }
        with open("stateBeforeExit.json", "w", encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        log("已保存此次播放进度至 stateBeforeExit.json", "info")

    def loadState(self) -> bool:
        if not os.path.exists("stateBeforeExit.json"):
            return False

        with open("stateBeforeExit.json", "r", encoding='utf-8') as f:
            state = json.load(f)

        self.playlist = state.get("playlist", self.playlist)
        self.currentIndex = state.get("currentIndex", 0)
        self.loadJump = state.get("timeDuration", 0.0)
        if self.loadJump < 0:
            self.loadJump = 0.0
        self.isPlaying = state.get("wasPlaying", False)
        self.isPaused = state.get("wasPaused", True)
        self.playMode = state.get("playMode", self.MODE_SINGLE)
        if self.playMode is None:
            self.playMode = self.MODE_SINGLE

        volume = state.get("volume", 0.7)
        if volume is not None:
            pygame.mixer.music.set_volume(volume)

        pygame.mixer.music.stop()
        self.loadSong(self.playlist[self.currentIndex], keep_position=True)
        pygame.mixer.music.load(self.playlist[self.currentIndex])
        self.play_start_pos = self.loadJump

        self.play()

        if not self.isPlaying or self.isPaused:
            self.pause()

        log(f"已恢复播放列表 ({len(self.playlist)} 首歌)", "debug")
        showLists(self.currentIndex, self.playlist, self.cache)

        return True

    def get_progress_bar(self, length=50):
        pos_offset = pygame.mixer.music.get_pos() / 1000.0
        if pos_offset < 0:
            pos_offset = 0

        self.current_pos = self.play_start_pos + pos_offset

        percent = self.current_pos / self.duration if self.duration > 0 else 0
        percent = max(0, min(1, percent))
        filled = int(percent * length)
        bar = "█" * filled + "░" * (length - filled)

        info = f"{self.audioArtist} - {self.audioTitle}"
        if self.AudioAlbum and self.AudioAlbum != "未知专辑":
            info += f" [ {self.AudioAlbum} ]"

        display_info, self.scroll_offset, self.scroll_counter = progressBar(
            info,
            self.scroll_offset,
            self.scroll_counter
        )

        return f"[{bar}] {percent*100:>4.1f}% {_format_time(self.current_pos)}/{_format_time(self.duration)}  {display_info}"