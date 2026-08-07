import os
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis

import os

def normalizePath(path, base_dir="./"):
    """
    将路径转换为统一的相对路径格式：
    - 统一使用正斜杠 `/`
    - 统一以 `./` 开头
    - 统一为相对路径（相对于 base_dir）
    """
    # 1. 统一为正斜杠
    path = path.replace('\\', '/')
    
    # 2. 如果是绝对路径，转为相对路径
    if os.path.isabs(path):
        try:
            rel_path = os.path.relpath(path, base_dir)
            # 统一为正斜杠
            rel_path = rel_path.replace('\\', '/')
            # 如果不在 base_dir 下，直接返回绝对路径
            if rel_path.startswith('..'):
                print(f"\n提醒：文件在程序目录外: {path}")
                return path
            path = rel_path
        except ValueError:
            print(f"跨驱动器路径无法转换: {path}")
            return path
    
    # 3. 确保以 ./ 开头（但不要变成 ././）
    if not path.startswith('./') and not path.startswith('../'):
        path = './' + path
    
    # 4. 去除多余的斜杠（避免 ././ 或 //）
    while '/./' in path:
        path = path.replace('/./', '/')
    
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
