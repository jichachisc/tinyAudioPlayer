import os
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis

def normalizePath(path, base_dir="./"):
    """
    将路径转换为相对于 base_dir 的相对路径

    如果 path 已经是相对路径，直接返回
    如果是绝对路径，计算相对路径
    """
    # 如果已经是相对路径（不以盘符或 / 开头）
    if not os.path.isabs(path):
        return path
    
    # 绝对路径 → 相对路径
    try:
        rel_path = os.path.relpath(path, base_dir)
        # 如果 rel_path 以 .. 开头，说明文件在 base_dir 外面
        # 这种情况下 fallback 到绝对路径（可能匹配不到 cache）
        if rel_path.startswith('..'):
            print("\n" + f"提醒：本文件不在程序扫描目录内: {path}")
            return path
        return rel_path
    except ValueError:
        # 不同驱动器（Windows 上 C:\ 和 D:\ 之间无法 relpath）
        print(f"跨驱动器路径无法转换: {path}")
        return path

def getFileMetadata(destination : str):
        ext = os.path.splitext(destination)[1].lower()
        title = os.path.basename(destination)
        artist = "未知艺术家"
        album = "未知专辑"

        try:
            if ext == '.mp3':
                audio = MP3(destination)
                # MP3 用 ID3 字段名
                audioTitle = audio.get('TIT2', [title])[0] if 'TIT2' in audio else title
                audioArtist = audio.get('TPE1', ['未知艺术家'])[0] if 'TPE1' in audio else "未知艺术家"
                AudioAlbum = audio.get('TALB', ['未知专辑'])[0] if 'TALB' in audio else "未知专辑"
                
            elif ext == '.flac':
                audio = FLAC(destination)
                # FLAC 用 Vorbis Comment 字段名
                audioTitle = audio.get('title', [title])[0] if 'title' in audio else title
                audioArtist = audio.get('artist', ['未知艺术家'])[0] if 'artist' in audio else "未知艺术家"
                AudioAlbum = audio.get('album', ['未知专辑'])[0] if 'album' in audio else "未知专辑"
                
            elif ext == '.ogg':
                audio = OggVorbis(destination)
                # OGG 也是 Vorbis Comment
                audioTitle = audio.get('title', [title])[0] if 'title' in audio else title
                audioArtist = audio.get('artist', ['未知艺术家'])[0] if 'artist' in audio else "未知艺术家"
                AudioAlbum = audio.get('album', ['未知专辑'])[0] if 'album' in audio else "未知专辑"
            else:
                return
                
            duration = audio.info.length
            bitrate = audio.info.bitrate / 1000 if hasattr(audio.info, 'bitrate') else None
            sampleRate = audio.info.sample_rate
            channels = audio.info.channels
            
        except Exception as e:
            print(f"元数据读取失败: {e}")
        
        """return {"title": f"{audioArtist} - {audioTitle}",
                "url": destination,
                "duration": duration
                }"""
        return {
            "title": audioTitle,
            "artist": audioArtist,
            "album": AudioAlbum,
            "url": destination,
            "duration": duration,
            "bitrate": bitrate,
            "sampleRate": sampleRate,
            "channels": channels
        }

def _format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

def scanDir(path: str):
    songs = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(('.mp3', '.flac', '.ogg')):
                songs.append(os.path.join(root, file))
    return songs
