# tinyAudioPlayer

一个基于 Python + Pygame 的命令行音乐播放器，通过键盘快捷键控制。

## 功能

- 支持 MP3 / FLAC / OGG 格式
- 键盘快捷键控制（播放/暂停/切歌/快进快退）
- 播放列表管理（保存/加载 .m3u 文件）
- 退出时自动保存播放进度
- 实时进度条显示（支持全角/半角字符）
- 播放列表随机打乱
- 四种播放模式切换

## 播放模式

按 `M` 键循环切换：

| 模式 | 说明 |
|------|------|
| 单曲循环 | 重复播放当前歌曲 |
| 顺序播放 | 按列表顺序播放 |
| 随机播放 | 随机选择歌曲（可能重复） |
| 列表循环 | 播完最后一首回到第一首 |

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
| `R` | 随机打乱播放列表 |
| `I` | 显示歌曲信息 |
| `F` | 加载 .m3u 播放列表 |
| `C` | 保存 .m3u 播放列表 |
| `M` | 切换播放模式 |

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```
### 运行
```bash
git clone https://github.com/jichachisc/tinyAudioPlayer.git
cd tinyAudioPlayer
python main.py # 用户模式
python main.py --debug # 调试模式
```
### 项目结构
```
tinyAudioPlayer/
  ├── main.py           # 程序入口
  ├── musicEngine.py    # 核心播放引擎
  ├── processHandler.py # 按键事件处理
  ├── keyHandler.py     # 键盘监听
  ├── fileHandler.py    # 文件读写（缓存、M3U）
  ├── utils.py          # 工具函数
  ├── ui.py             # UI 渲染
  ├── requirements.txt  # 依赖列表
  └── README.md         # 项目说明
```
### 文件说明
| 文件 | 说明 |
| :-----: | :-----: |
| metadata_cache.json | 歌曲元数据缓存（自动生成） |
| stateBeforeExit.json | 退出时的播放状态（自动生成） |
| *.m3u | 用户保存的播放列表 |

### 依赖
```
pygame >= 2.0.0
pynput >= 1.7.0
easygui >= 0.98.0
mutagen >= 1.45.0
m3u-parser >= 0.1.0
pywinctl >= 0.5.0
```

### License

MIT
