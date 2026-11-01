# 新概念英语电视跟读实施方案

使用 React 与 Vite 构建的 Web 应用，在 85 寸电视、约 5 米观看距离下练习新概念英语第二册单词。已提供第 62 课（15 个词）和第 63 课（6 个词）；后续范围为第 64 至 96 课。首次打开默认进入第 63 课，并保存用户之后选择的课程。

## 电视页面

页面使用全屏宽度，左侧默认约 66% 展示本课单词列表，右侧展示当前单词；通过中间分隔条或设置中的宽度滑块，将左侧宽度调整为 30% 至 75%。使用白底、深色文字，当前单词与列表中的对应词标红。

- 每个列表词条横向展示序号、英文单词、音标、词性及中文释义。字段按实际文字宽度排列，长单词与音标保持间隔。
- 列表上方提供缩小、字号滑块和放大控件，缩放范围为 60% 至 180%。100% 时，1080p 的英文约 70 像素、音标约 41 像素、释义约 42 像素，4K 下等比例放大。
- 列表在自身区域滚动，播放时自动将当前词滚动至可见位置。列表宽度和字号分别保存，刷新页面时恢复。
- 右侧用大字展示当前英文词，字号随可用宽度自适应，保持长单词完整显示。下方显示音标、词性、中文释义。
- 右侧上方展示当前进度和“英文示范第几遍”“中文释义”“请跟读”等状态。
- 底部保留上一词、播放或暂停、下一词、重读、音量和全屏控件。
- 速度、留白、中文释义开关和循环开关放在“设置”中。
- 在实际电视上按 5 米视距检查字号和阅读舒适度。

## 播放内容与顺序

播放内容为英文单词和中文词性释义。点击开始即从所选单词开始。

1. 第一遍英文清晰慢读。
2. 朗读中文词性和释义，可在设置中开关。
3. 留白供用户跟读，默认 2.2 秒。
4. 第二遍英文慢读。
5. 再次留白供用户跟读，默认 2.2 秒。
6. 进入下一个单词。

切换课程会取消旧音频、跟读计时与旧数据请求，恢复新课程的首词。

默认开启整课循环，最后一个词完成后直接回到第一个词。用户可关闭循环并保存该设置。播放列表包含上述单词内容，课名、册数、课号和完成状态通过页面文字展示。

## 发音与音色

第 62 课英文采用 Piper 的 `en_GB-cori-high` 英音女声音色。第一遍和第二遍均为慢读，通过生成模型的时长参数控制，保留音高、音节和词尾。初始生成速度系数分别为 0.35、0.45，使用倒数作为 Piper 的 `length_scale`。

第 62 课中文采用 Kokoro-82M v1.1-zh 的 `zf_001` 普通话女声，生成速度为 1.0。中文发音、音色和节奏通过词条试听确认。

每词生成两段英文及一段中文。第 62 课共 45 段，第 63 课共 18 段。音频输入只包含目标词或对应中文词性释义，英文记录实际输入音素。生成后检查额外起音、缺音、词尾、静音和文件完整性。

第 62 课的 desolate 按形容词 `/ˈdesələt/` 生成，源 HTML、源 JSON 与课程数据保持一致。[词典依据](https://dictionary.cambridge.org/dictionary/english/desolate)。

模型及来源：[Piper Cori 模型](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_GB/cori/high)、[Piper 项目](https://github.com/OHF-Voice/piper1-gpl)、[Kokoro 中文模型](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh)。音色与工具许可记录在 `public/THIRD_PARTY_NOTICES.txt`。

第 63 课采用 Qwen3-TTS-12Hz-1.7B-Base 的 MLX 8 位模型，运行于 Apple Silicon Mac，英文与中文分别使用第 57 课视频的对应参考片段。保留参考样本、输入文字、校验值和生成参数。英文以 FFmpeg `atempo` 制作 0.72、0.86 两档慢读，保持音高；中文保持生成速度。

第 63 课需要词性提示的英文先通过短句生成，其余词独立生成，再按 `scripts/lesson-63-trims.json` 截取目标词。重新生成后需核对这些截取边界。

第 63 课的 close 使用形容词 `/kləʊs/`，先使用 `The adjective: close.` 这一词性提示生成，再截取目标词；reception 的中文释义为“招待会”。源词表与课程 JSON 保持一致。[close 词典依据](https://dictionary.cambridge.org/dictionary/english/close)、[reception 词典依据](https://dictionary.cambridge.org/dictionary/english/reception)。

## 播放同步与设置

当前词状态同时驱动右侧单词和左侧列表。音频触发 `playing` 后标红，播放结束后进入中文释义、留白或下一遍。跟读和暂停期间保留当前词标红。

上一词、下一词、跳词和重读会取消旧播放及旧计时，始终保持一条有效播放流程。暂停同时适用于音频和跟读倒计时，继续后保留原位置。加载失败时在当前词重试。

音量范围为 0 至 100%，默认 70%，实时作用于当前和后续声音。支持静音及恢复。英文播放速度可在 0.6、0.75、0.85、1.0 倍之间调整；中文保持录制时的速度。留白范围为 1 至 5 秒。

音量、英文速度、留白、中文释义和循环设置保存到浏览器。空格控制播放或暂停，左右方向键切词；聚焦分隔条时，左右方向键调整列表宽度。全屏按钮用于电视显示。

## 文件与运行

| 路径 | 内容 |
| --- | --- |
| `index.html` | Vite HTML 入口 |
| `src/main.jsx` | React 挂载入口 |
| `src/App.jsx` | 课程切换、加载与页面布局 |
| `src/lessons.js` | 可用课程与课程选择保存 |
| `src/WordList.jsx` | 横向词条、列表缩放及自动滚动 |
| `src/PlayerControls.jsx` | 播放设置、音量与全屏控件 |
| `src/useLessonPlayer.js` | React 播放状态、键盘和设置保存 |
| `src/useLayoutSettings.js` | 列表宽度、字号与本地保存 |
| `src/CurrentWord.jsx` | 当前单词自适应字号 |
| `src/styles.css` | 大屏布局与字号 |
| `src/player.js` | 单词播放、两遍示范、留白、暂停与循环 |
| `public/data/book2/lesson-62.json` | 第 62 课词条与音频索引 |
| `public/data/book2/lesson-63.json` | 第 63 课词条与音频索引 |
| `public/audio/book2/lesson-62/` | 第 62 课的 45 段音频、整课音频及生成参数 |
| `public/audio/book2/lesson-63/` | 第 63 课的 18 段参考音色音频、整课音频及生成参数 |
| `public/audio/reference/` | 参考视频音频、30 秒采样及分析数据 |
| `scripts/generate_audio.py` | 第 62 课音频生成和整课合成 |
| `scripts/generate_cloned_audio.py` | 参考声音合成、单词截取与第 63 课整课合成 |
| `scripts/requirements-clone.txt` | Apple Silicon 声音克隆依赖 |
| `scripts/lesson-63-trims.json` | 第 63 课英文目标词的截取时间 |
| `scripts/requirements-audio.txt` | 音频生成依赖 |
| `vite.config.js` | React 插件、开发服务与预览配置 |
| `scripts/start.mjs` | 依赖检查、构建与本地预览启动 |
| `package-lock.json` | npm 依赖版本锁定 |
| `start.command` | Mac 启动入口 |
| `tests/player.test.js` | 播放流程测试 |

前端采用 React 19.3.1、Vite 8.3.5 和 React 插件 6.1.2，版本通过 `package.json` 和 `package-lock.json` 锁定。Node.js 要求为 `^20.19.0 || >=22.12.0`。

Mac 双击 `start.command`，执行依赖检查、构建并启动 Vite 预览，自动打开浏览器。首次声音播放由用户点击触发。默认地址为 `http://127.0.0.1:8765/`，端口占用时自动选择后续端口。

开发使用 `npm run dev`，构建使用 `npm run build`，构建后可通过 `npm run preview` 启动预览；`npm start` 执行完整的日常启动流程。Vite 的 `public/` 目录保存 WAV、课程 JSON 和许可文件，构建时复制到 `dist/`。

播放器使用本地 WAV 和 JSON。生成环境使用 Python 3.10 至 3.12，模型缓存在用户缓存目录；所有播放音频通过项目同步。

## 自动同步

通过现有 Syncthing 自动双向同步，文件夹 ID 为 `read-alone`。

- Mac：`/Volumes/SSD/Projects/project/read-alone`
- 本机：`/home/colin/read-alone`

启用文件系统监听，变化合并延迟 2 秒，每小时自动扫描。跨系统同步忽略权限位差异。两端 `.stignore` 引用同一份 `.stignore-shared`。源码、课程数据、音频、文档、`package.json` 和 `package-lock.json` 参与同步。

依赖目录 `node_modules`、包管理器缓存、Vite 缓存、`dist`、测试覆盖率、Python 虚拟环境与工具缓存不参与同步。两端分别安装依赖和构建项目。

## 验收要求

- 1080p 和 4K 横屏下，词条中的单词、音标、释义保持横向排列，文字互不重叠。
- 字号缩放和列表宽度调整独立生效，拖动或缩放不重启当前音频，设置刷新后恢复。
- 列表滚动保持在自身区域，当前词自动进入可见范围；循环回首词时列表回到顶部。
- React 严格模式下只创建一条有效播放流程，组件清理时释放音频、计时及事件监听。
- Vite 开发服务、生产构建和生产预览均可运行，右侧最长词与主要控件位于屏幕内。
- 实际 85 寸电视、5 米视距下，列表和当前词清楚可读。
- 点击开始直接朗读单词，所有词按顺序示范两遍，中文词性释义按设置播放。
- 英文慢读清晰，无多余起音，音节和词尾完整；中文音色自然。
- 课程默认连续循环，回到首词时声音与标红一致。
- 暂停、继续、切词、重读和连续点击均不会造成声音重叠。
- 音量实时生效，英文速度调整保持音高，中文速度稳定，设置能够恢复。
- 两端文件及音频校验一致，Mac 可打开页面并播放。
