# 环境与文件

## 同步项目

- Linux：`/home/colin/read-alone`。
- Mac：`/Volumes/SSD/Projects/project/read-alone`。
- 在 Mac 直接执行合成；在 Linux 可通过既有 SSH 别名 `easydish-mac` 执行同一项目的合成命令。
- 源码、`voices/`、参考 WAV 与 `public/` 成品通过现有 Syncthing 同步。`dist/` 与虚拟环境各设备独立准备。

## 已保存的运行环境

Mac 生成环境：

```bash
VOICE_TOOLS=/Volumes/SSD/Projects/.tools/read-alone-voice
VOICE_PY="$VOICE_TOOLS/venv/bin/python"
VOICE_MODEL="$VOICE_TOOLS/models/Qwen3-TTS-12Hz-1.7B-Base-8bit"
```

使用现有模型缓存。权重的 SHA-256、模型 ID、参考音频 SHA-256 均在 `voices/lesson-57-teacher/profile.json`。模型或环境需要重建时，在 Python 3.12 Apple Silicon 环境安装 `scripts/requirements-clone.txt`，从 profile 指定的 Hugging Face 模型仓库下载并校验权重。

Linux 识别环境：

```bash
REVIEW_PY=/home/colin/.cache/read-alone/tools/review-venv/bin/python
```

模型缓存位于 `~/.cache/read-alone/whisper`，已保留 faster-whisper-small。需要重建时在 Python 3.12 环境安装 `scripts/requirements-clone-review.txt`。识别脚本直接读取 WAV 为数组，英文与中文分别指定语言。

## 持久文件

| 文件 | 用途 |
| --- | --- |
| `voices/lesson-57-teacher/profile.json` | 音色参考、转写、模型、语速、音量与留白参数 |
| `voices/lesson-57-teacher/speaker-embeddings.npz` | 中英文参考对应的模型专用声音特征向量 |
| `voices/lesson-57-teacher/features.json` | 向量形状、模型版本、输入和输出校验值 |
| `public/audio/reference/lesson-57/` | 15 段独立保存的采样 WAV 及来源、时间点清单 |
| `voices/lesson-57-teacher/recipes/book2-63.json` | 已确认的第 63 课输入文字与参数入口 |
| `voices/lesson-57-teacher/lessons/book2-63/raw/` | 第 63 课实际使用的 12 段原始合成 WAV 与输入记录 |
| `scripts/lesson-63-trims.json` | 第 63 课实际使用的英文截取区间 |
| `public/audio/book2/lesson-63/generation.json` | 已确认成品的音频与整课校验值 |

参考 WAV 和转写是生成输入；声音特征向量按 profile 中记录的模型版本使用。`scripts/export_voice_features.py` 可从参考 WAV 和已校验的模型重新提取向量。

原始视频的文件名、大小、SHA-256 及采样来源继续保留在 `public/audio/reference/lesson-57/source.json`，视频文件可删除。网页只读取已导出的课程 JSON 与 WAV。
