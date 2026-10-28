# Read Alone 单词跟读

用于 85 寸电视、约 5 米观看距离的英语跟读应用，采用 React 19.3.1 和 Vite 8.3.5。首课为新概念英语第二册第 62 课。

左侧词条将单词、音标、词性与中文意思横向排列，随播放自动滚动。列表上方支持字号缩放，中间分隔条可拖动调整宽度，设置会自动保存。右侧大字显示当前词，播放时两侧同步标红。每词两遍慢读，配中文释义及跟读留白，默认整课循环。

## 运行

Node.js 版本要求：`^20.19.0 || >=22.12.0`。

```bash
npm ci
npm run dev
```

Mac 日常使用可双击 `start.command`，或执行 `npm start`，自动检查依赖、构建并打开浏览器。默认本地地址为 `http://127.0.0.1:8765/`。

## 构建与验证

```bash
npm run build
npm run preview
npm test
```

音频及课程数据位于 `public/`，Vite 将其复制到构建目录 `dist/`。Syncthing 同步源码、音频、文档与 npm 锁文件。依赖目录、构建产物、包管理器缓存、Vite 缓存和 Python 工具缓存通过 `.stignore-shared` 统一忽略，在各设备本地准备。

## 文档

- [实施方案](docs/implementation-plan.md)
- [电视使用步骤](docs/voice-recording.md)
- [语音模型与许可](public/THIRD_PARTY_NOTICES.txt)

音频生成脚本为 `scripts/generate_audio.py`，依赖记录在 `scripts/requirements-audio.txt`。
