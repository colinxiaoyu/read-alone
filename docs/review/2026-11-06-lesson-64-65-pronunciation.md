# 第 64、65 课单词音频待确认项

两课都按「单词单独一句」的提示合成；trim 起点跳过词首杂音点，终点取 raw 时长。英文严格 ASR（slow、normal 两档）的口径：去掉大小写和标点后与目标词一致，且不带 `?`。

- 64 课：13 词，全部通过。换过 seed 的有 port、ventilation、officially、connect（64101/64102）、sea level（64102）。
- 65 课：9 词，7 个通过。换过 seed 的有 circus 2065、present 3065、approach 4065、weigh 1065。present 用 `The noun: present.` 合成后截出，重音在第一音节（/ˈprezənt/）。

候选与测量记录在各课的 `voices/lesson-57-teacher/lessons/book2-6x/pronunciation-review/`（`summary.json`、`candidates/`）。

## 待 colin 试听裁定

| 课 | 词 | 问题 | 现选版本 |
|---|---|---|---|
| 65 | ought | 7 个 seed 都没识别成 ought：art / 8. Art 3. / Aught. / www.mooji.org / I / I / on.。唯一同音的 2065 `Aught.` 是升调（172→250 Hz） | 默认 seed 6512，识别为 `art`，元音可能偏 /ɑː/；降调 220→114 Hz，有 t 除阻 |
| 65 | weigh | 7 个 seed 都识别成 way（5065 为 `Wait.`）。weigh 和 way 同音，ASR 区分不了 | 1065，降调 286→126 Hz |
| 65 | circus | 句末 8 帧有 +0.5 / +1.2 st 的小上扬，整体从 268 Hz 降到 114 Hz | 2065 |
| 64 | connect | 7 版里句末降幅都不到 6 st | 64102，降约 4.2 st，没有上扬 |
| 64 | sea level | 64102 词尾 0.75–0.89 s 的谐噪比很低（HNR 1.7 dB），截掉后 ASR 就认不出 level；64104 语调更平滑（238→107 Hz），但成品被识别成 `C-Level` | 64102 |
| 64 | 中文「动词」 | ventilate、connect 的 meaning 被识别成「冻死」，fear 识别正常；换中文 seed 需要改脚本，所以没有重新生成中文 | 默认 seed |

ought 如果要继续试，可以换个提示，比如 `You ought to.` 或者 `ought, ought.`。这样改等于换了输入，raw 要放进新的缓存目录，换哪种由 colin 定。

## 脚本行为与文档不一致

- `scripts/generate_cloned_audio.py`：`--recipe` 指向的文件不存在时不报错，会静默用默认提示词 `The noun: X.` 合成。64 课第一次合成时，Mac 上的配方还没同步过去，就出现了这种情况；那批输出已经删掉。要不要改成直接报错，等 colin 定。
- `scripts/review_cloned_audio.py`：模型缓存路径写死为 `~/.cache/read-alone/whisper`（流程文档里的 Linux 路径），Mac 上没有这个目录。另外 final 模式只查 slow 一档，也不检查 `?`。这次的 normal 档和问号检查都是另外补跑的。
