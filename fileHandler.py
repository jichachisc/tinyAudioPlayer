import json
import os
import queue

from m3u_parser import M3uParser
from utils import getFileMetadata, scanDir, normalizePath

class MetadataScanner:
    def __init__(self, direction: str):
        self.playlist = scanDir(direction)
        self.jsonDict = self.summonDict()

    def summonDict(self):
        jsonDict = {}
        # value = {"artist": "", "title": "", "album": "", "nameCheck": ""}
        for index, songName in enumerate(self.playlist, 1):
            metadata = getFileMetadata(songName)
            jsonDict[songName] = {
                "artist": metadata.get("artist"),
                "album": metadata.get("album"),
                "title": metadata.get("title")
            }
            print("\r" + f"加载播放列表 已完成 {index} / {len(self.playlist)}", end="")
        return jsonDict


class cacheHandler:
    def __init__(self, cacheFileName: str, direction="./"):
        self.cacheFile = cacheFileName
        self.direction = direction
    def writeJson(self) -> None:
        cacheReader = MetadataScanner(self.direction)
        cache = cacheReader.jsonDict
        with open(self.cacheFile, "w", encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        print(f"\n尝试创建缓存成功，保存在 {self.cacheFile}")
    def readJson(self) -> dict:
        if not os.path.exists(self.cacheFile):
            print(f"\n缓存文件 {self.cacheFile} 不存在，创建缓存")
            return {}
        try:
            with open(self.cacheFile, "r", encoding='utf-8') as f:
                cache = json.load(f)
            print(f"成功加载缓存文件: {self.cacheFile}")
            return cache
        except json.JSONDecodeError as e:
            print(f"缓存文件损坏: {e}")
            return {}

class M3UHandler:
    def __init__(self):
        self.parser = M3uParser()
    
    def writeM3UFile(self, m3uFile: str, metadata : list):
        """导出播放列表为 .m3u，保存元数据"""
        with open(m3uFile, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for songMetadata in metadata:
                f.write(f"#EXTINF:{songMetadata.get('duration')},{songMetadata.get('title')}\n")
                f.write(f"{songMetadata.get('url')}\n")
        print(f"已导出播放列表: {m3uFile}")
    def readM3UFile(self, m3uFile: str):
        paths = []
        metadata = {}
        
        with open(m3uFile, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('#EXTM3U'):
                i += 1
                continue
            if line.startswith('#EXTINF:'):
                # 解析 #EXTINF:时长,标题
                parts = line[8:].split(',', 1)  # 去掉 "#EXTINF:"
                duration = float(parts[0]) if parts[0].replace('.', '').isdigit() else -1
                title = parts[1] if len(parts) > 1 else '未知'
                
                # 下一行是路径
                i += 1
                if i < len(lines):
                    path = lines[i].strip()
                    # 处理反斜杠
                    path = path.replace('\\', '/')
                    paths.append(path)
                    metadata[path] = {
                        'artist': title.split(' - ')[0] if ' - ' in title else '未知艺术家',
                        'title': title.split(' - ')[-1] if ' - ' in title else title,
                        'duration': duration,
                        'from_m3u': True
                    }
            i += 1
        
        print(f"解析到 {len(paths)} 首歌")
        return paths, metadata
