# 生成与验收

## 保存本课配方

从词表取本课完整词条并核对发音、词性和中文释义。标题使用本课标题。保存 `voices/lesson-57-teacher/recipes/book2-N.json`，包括 `book`、`lesson`、`title`、`seed_base`、`english_text`、`trim_file`、`raw_archive`；`seed_base` 默认课号乘 100。

英文默认输入 `The <词性>: <单词>.`；本课需要的独立单词或其他明确语义上下文写入 `english_text`。上下文用于确定发音，最终只保留目标词。中文按词性加释义生成。参考第 63 课配方的 JSON 结构。

## 合成与截取

以下命令在项目根目录运行，`N`、路径与标题替换为实际课程。

```bash
"$VOICE_PY" scripts/generate_cloned_audio.py --lesson N --synthesize-only \
  --recipe voices/lesson-57-teacher/recipes/book2-N.json \
  --model "$VOICE_MODEL" --raw-dir "$RAW_DIR"
```

每词生成英文与中文原始 WAV，保存 `raw-generation.json`。输入变化时使用新的 `RAW_DIR`。使用同一参考音色与 profile 中的参数：temperature 0.65、top_p 0.9、max_tokens 192。

将完整原始片段复制到可运行识别工具的位置，执行：

```bash
"$REVIEW_PY" scripts/review_cloned_audio.py --lesson N --mode raw \
  --raw-dir "$RAW_DIR" --output "$RAW_DIR/review-raw.json"
```

`review-raw.json` 保存分语言转写、词级时间戳和建议截取区间。结合静音段核对边界，再写入本课 `scripts/lesson-N-trims.json`。上下文末词的结束位置可保留到原始音频结束，由导出脚本处理尾部静音。独立词的截取区间可覆盖整段原始音频。

## 导出与检查

在 Mac 暂存目录导出：

```bash
"$VOICE_PY" scripts/generate_cloned_audio.py --lesson N --finalize-only \
  --recipe voices/lesson-57-teacher/recipes/book2-N.json \
  --model "$VOICE_MODEL" --raw-dir "$RAW_DIR" \
  --trim-json scripts/lesson-N-trims.json --output-public "$STAGE_PUBLIC"
```

每词导出 `slow`、`normal`、`meaning` 三段：英文 atempo 0.72 与 0.86，中文 1.0；单声道、24 kHz、PCM16。生成时保留完整起音、词尾，使用 4 ms 边缘淡入淡出与固定保护留白。整课顺序为英文第一遍、中文释义、2.2 秒跟读、英文第二遍、2.2 秒跟读。

```bash
python3 scripts/validate_lesson_audio.py --lesson N --public-dir "$STAGE_PUBLIC"
"$REVIEW_PY" scripts/review_cloned_audio.py --lesson N --mode final \
  --public-dir "$STAGE_PUBLIC" --output "$RAW_DIR/review-final.json"
```

验证每个英文只包含目标词；中文的词性和释义与词表一致。自动识别歧义结合词性、发音和波形复核。修改过的词单独复查。确认音频完整、无多余起音、无削波、无异常静音，音频片段数量为本课词数的三倍，整课字节顺序和留白一致。

## 网页与归档

把验收完成的音频目录与课程 JSON 放入 `public/audio/book2/lesson-N/`、`public/data/book2/lesson-N.json`。在 `src/lessons.js` 追加课程并按课号排序。首次打开默认最新课程，已有用户继续保留上次选择。切课停止旧声音并回到首词。

将本课实际使用的原始 WAV、`raw-generation.json` 和识别报告保存到 `voices/lesson-57-teacher/lessons/book2-N/raw/`。配方指向该归档及本课的截取文件；成品校验值保存在 `generation.json`。依赖环境、模型权重保留在工具缓存目录。

运行 `npm test`、`npm run build`。Mac 的 `dist/` 也需要本地构建：设置 `PATH=/opt/homebrew/bin:/usr/local/bin:$PATH` 后执行 `npm run build`。验证浏览器真实解码所有新音频、首词播放顺序、切换课程停止旧声音，以及选课刷新后保留。下次用户双击 `start.command`，选择课程并点“开始跟读”。

## 复现第 63 课

使用归档原始 WAV 进行字节级复现检查：

```bash
"$VOICE_PY" scripts/generate_cloned_audio.py --lesson 63 --finalize-only \
  --model "$VOICE_MODEL" --raw-dir voices/lesson-57-teacher/lessons/book2-63/raw \
  --output-public "$STAGE_PUBLIC"
python3 scripts/validate_lesson_audio.py --lesson 63 --public-dir "$STAGE_PUBLIC" \
  --compare-approved public/audio/book2/lesson-63/generation.json
```

在已保存的 Mac 环境中执行，18 段音频和整课 WAV 必须与已确认成品的 SHA-256 完全相同。当前已确认整课时长为 55.286125 秒。
