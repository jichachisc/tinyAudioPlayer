# 命令行音乐播放器 (tinyAudioPlayer)

一个基于 Python + Pygame 的命令行音乐播放器，支持键盘快捷键控制。

## 功能

- 支持 MP3 / FLAC / OGG 格式
- 键盘快捷键控制（播放/暂停/切歌/快进快退）
- 播放列表管理（保存/加载 .m3u 文件）
- 退出时自动保存播放进度
- 实时进度条显示
- 播放列表随机播放
- 可切换单曲循环、列表循环与顺序、随机播放

## 快捷键

| 按键 | 功能 |
|------|------|
| `Space` | 播放/暂停 |
| `S` | 开始播放 |
| `Esc` | 退出程序 |
| `→` | 快进 10 秒 |
| `←` | 后退 10 秒 |
| `↑` | 音量 +10% |
| `↓` | 音量 -10% |
| `PageDown` | 下一首 |
| `PageUp` | 上一首 |
| `L` | 显示播放列表 |
| `R` | 随机播放列表 |
| `I` | 显示歌曲信息 |
| `F` | 加载 .m3u 播放列表 |
| `C` | 保存 .m3u 播放列表 |
| `M` | 切换播放模式 |

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 下载使用

```bash
git clone https://github.com/jichachisc/tinyAudioPlayer.git
cd tinyAudioPlayer
python ./main.py
```