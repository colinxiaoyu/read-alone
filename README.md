# Read Alone 单词跟读

用于 85 寸电视、约 5 米观看距离的英语跟读应用，采用 React 19.3.1 和 Vite 8.3.5。支持新概念英语第二册第 62、63 课，首次打开默认进入第 63 课，后续记住上次选择。第 62、63 课均使用已保存的老师参考音色生成英文和中文音频。

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

第 62、63 课均使用 `scripts/generate_cloned_audio.py` 与 `scripts/requirements-clone.txt`，生成环境为 Apple Silicon Mac。网页直接播放已经生成的 WAV，无需运行声音模型。

## 生成下一课

调用已安装的 `$read-alone-next-lesson` 技能，例如：“使用 `$read-alone-next-lesson` 生成第二册第 64 课，并接入网页跟读。”技能源文件位于 [skills/read-alone-next-lesson/SKILL.md](skills/read-alone-next-lesson/SKILL.md)，会随项目同步。

音色参考、转写、模型与处理参数集中在 [voices/lesson-57-teacher/profile.json](voices/lesson-57-teacher/profile.json)。已保留 15 段采样、独立声音特征向量，以及第 62、63 课实际使用的原始合成 WAV、配方和截取区间。原始视频已删除，后续生成直接使用已保存素材。
