# 电视跟读使用步骤

使用场景为 85 寸电视、约 5 米观看距离。左侧词条将单词、音标、词性和中文意思横向排列，随播放自动滚动；右侧大字显示当前词、音标和中文释义。

## 第一步 打开页面

在 Mac 项目目录双击 `start.command`：

```text
/Volumes/SSD/Projects/project/read-alone/start.command
```

也可以在终端执行：

```bash
cd /Volumes/SSD/Projects/project/read-alone
bash start.command
```

启动脚本会检查 npm 依赖并构建 React 页面。浏览器默认打开 `http://127.0.0.1:8765/`。将浏览器窗口放到电视屏幕，点击“全屏”。

## 第二步 开始跟读

在页面右上方选择第 62 或 63 课。首次打开默认进入第 63 课，之后记住上次选择；切换课程会停止当前声音并回到该课第一个词。

点击“开始跟读”，直接从第一个单词开始。每词播放第一遍慢读、中文释义、跟读留白、第二遍慢读和跟读留白。当前词在左右两侧同步标红。

第 62 课共 15 个词，第 63 课共 6 个词，中英文均使用已保存的老师参考音色合成。两课默认循环播放。点击任意列表单词，可以从该词开始。使用“上一词”“下一词”“重读”调整位置。

## 第三步 调整声音

拖动底部音量滑块调整大小。点击“静音”可关闭声音，再次点击恢复。

在“设置”中调整英文播放速度和留白时间。两遍英文已经按慢读制作，第 62、63 课的中英文均使用参考老师的音色。英文速度设置只影响英文声音，留白默认 2.2 秒。

“朗读中文释义”控制中文词性释义。“整课循环”控制课程反复播放。设置会保存在当前浏览器。

## 第四步 检查电视观看效果

站到约 5 米的位置，检查列表及当前词是否清晰、最长单词是否完整。优先试听第 63 课的 circle、close、wedding、reception，检查起音、音节、词尾、速度及跟读时间。

键盘空格可暂停或继续，左右方向键可切词。页面“设置”中可下载包含单词、释义和留白的整课音频。

## 开发命令

项目使用 React 19.3.1 与 Vite 8.3.5，Node.js 要求为 `^20.19.0 || >=22.12.0`。在项目根目录使用：

```bash
npm ci
npm run dev
```

生产构建使用 `npm run build`，预览使用 `npm run preview`，播放流程测试使用 `npm test`。音频与课程 JSON 位于 `public/`，构建结果位于 `dist/`。

## 调整左侧列表

- 点击列表上方的“−”或“＋”，或者拖动字号滑块，将列表文字缩小或放大到 60% 至 180%。
- 拖动左右区域之间的竖向分隔条，调整列表宽度；也可在“设置”中拖动“左侧列表宽度”滑块。
- 调整宽度与字号后，页面会自动保存；刷新后恢复上次设置。
- 大字号时可在列表自身区域内滚动查看内容，当前播放的单词会自动滚动进入可见范围。

## 第 63 课音频生成

在 Apple Silicon Mac 的 Python 3.12 环境中安装 `scripts/requirements-clone.txt`。使用 `scripts/generate_cloned_audio.py --synthesize-only` 生成参考音色原始片段，核对英文目标词边界后，执行 `scripts/generate_cloned_audio.py --finalize-only --trim-json scripts/lesson-63-trims.json`。两次运行使用同一个模型和原始音频缓存目录，可通过 `--model` 与 `--raw-dir` 指定。

脚本生成两档保持音高的英文慢读、中文词性释义、课程 JSON、生成记录和带默认 2.2 秒留白的整课 WAV。成品位于 `public/audio/book2/lesson-63/` 与 `public/data/book2/lesson-63.json`，随项目同步；日常打开网页直接播放成品。

## 复用老师音色

通过项目技能 [read-alone-next-lesson](../skills/read-alone-next-lesson/SKILL.md) 生成下一课。音色数据与模型参数在 `voices/lesson-57-teacher/profile.json`，中英文参考音频、转写与 SHA-256 保留在其中。模型对应的中英文声音特征向量在 `speaker-embeddings.npz`，来源与版本信息在 `features.json`。

本次第 63 课的实际输入文字、12 段原始合成 WAV 和配方均归档在 `voices/lesson-57-teacher/`，可用 `scripts/validate_lesson_audio.py --compare-approved` 检查重新导出的成品。已验证 18 段音频与整课 WAV 字节级一致。原始视频已删除，15 段采样与来源校验记录继续保留。

## 第 62 课音频生成

第 62 课使用 `voices/lesson-57-teacher/recipes/book2-62.json` 配方和 `scripts/lesson-62-trims.json` 截取区间，保持老师参考音色、两档英文慢读和默认 2.2 秒跟读留白。实际使用的 30 段原始合成片段与识别报告保存在 `voices/lesson-57-teacher/lessons/book2-62/raw/`。网页播放目录为 `public/audio/book2/lesson-62/`，其中包括 45 段单词音频及整课 WAV。
