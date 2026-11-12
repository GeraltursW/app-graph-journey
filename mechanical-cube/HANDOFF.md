# 项目交接说明

## 交付状态

2026-11-13 **v1.13.0**：当前主片为 `../videos/application-knowledge-graph-with-mechanical-replay.mp4`，**88.2 秒 / 1920×1080 / 60 fps**，16 幕、26 条烧录中文字幕。旁白保持正常语速，前 30 秒音乐以 0.6 秒交叉淡化循环铺满。

大学生示例只告诉观众“AI 创建了大学生场景用例”，不展开推荐浏览、同级切换与打开目标视频等操作。52.6–57.2 秒采用黑白界面、绿色完成状态，通过 0.7 秒过渡接入影响因子时序建模。原 v1.12 的 13–15 幕及对应旁白已移除。机械手仍使用“机械手操作”口播，铭牌及上下文缩略图为“服务器”。

| STEP | 主片时间 | 内容 |
| --- | --- | --- |
| 01 / 16 | 00:00.0–00:03.0 | 应用知识图谱 |
| 02 / 16 | 00:03.0–00:05.4 | 设备连接 |
| 03 / 16 | 00:05.4–00:11.0 | AI 控件探索 |
| 04 / 16 | 00:11.0–00:13.8 | 页面节点沉淀 |
| 05 / 16 | 00:13.8–00:19.0 | 向量化与知识图谱 |
| 06 / 16 | 00:19.0–00:33.0 | 探索路径演示 |
| 07 / 16 | 00:33.0–00:36.4 | 固化正确用例 |
| 08 / 16 | 00:36.4–00:41.6 | 实验室手机复现 |
| 09 / 16 | 00:41.6–00:44.0 | 单场景识别与复现 |
| 10 / 16 | 00:44.0–00:48.4 | 建设场景库 |
| 11 / 16 | 00:48.4–00:52.6 | 提取典型操作序列 |
| 12 / 16 | 00:52.6–00:57.2 | AI 创建大学生用例 |
| 13 / 16 | 00:57.2–01:03.6 | 影响因子时序建模 |
| 14 / 16 | 01:03.6–01:09.4 | 重建故障上下文 |
| 15 / 16 | 01:09.4–01:18.2 | AI 控制机械手 |
| 16 / 16 | 01:18.2–01:28.2 | 数据汇聚与报表 |

## 新电脑重建当前版本

安装 Git、Python 3.11+、FFmpeg 后克隆仓库，进入 `mechanical-cube`：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup.ps1
powershell -ExecutionPolicy Bypass -File .\tools\build-compact-full.ps1
# 修改前段后：
powershell -ExecutionPolicy Bypass -File .\tools\build-compact-full.ps1 -RebuildHead
# 修改机械手并同步衔接：
powershell -ExecutionPolicy Bypass -File .\tools\build-compact-full.ps1 -RebuildMechanical
```

默认输出 `output/compact-full-v1.13/`。构建入口检测 revision，自动更新过期缓存；配音缓存包含新版 AI 创建旁白，原文不变时可离线重建。Windows 使用微软雅黑，依赖见 `requirements.txt`；当前镜头由 Pillow / FFmpeg 生成，历史 Blender 工程继续保留。

| 修改内容 | 入口 |
| --- | --- |
| 69.4 秒前段与口播 | `config/head_compact.json`、`scripts/build_head_compact.py` |
| 简洁 AI 创建大学生用例画面 | `scripts/render_student_summary.py` |
| 黑白 AI 探索与实验室复现 | `scripts/render_control_exploration.py`、`scripts/render_lab_replay_monochrome.py` |
| 8.8 秒机械手、服务器铭牌 | `config/mechanical_compact.json`、`scripts/build_mechanical_compact.py` |
| 16 幕 STEP | `config/film_step_labels.json`、`scripts/film_step_labels.py` |
| 全片合成、配乐与字幕 | `scripts/build_compact_full_film.py` |

原始输入为仓库内历史干净母版、机械手母版、报表母版及 `assets/audio/`。`releases/latest/compact-*` 仍为 v1.11 历史缓存，不能作为当前交付；构建入口会重绘到本地输出目录。正式字幕仅烧录一次：`film-step-labels.ass` 负责 16 幕提示，SRT / ASS 负责 26 条旁白字幕。

约束：朋友与我为同级底部 Tab；只固化绿色成功路径；大学生例子只显示创建完成；之后展示网络、应用状态、负载的时序关系。机械手保留摄像头采集、AI 识别、坐标回传与操作。新增界面为原生 1080p，历史动画保持完整画幅，底部 72 px 为字幕区。

验收见 `docs/compact-main-validation.json` 和 `docs/step-label-validation.json`：5292 帧完整解码、16 幕编号连续、26 条字幕、语速与音画同步、AI 创建镜头前后转场。

## GitHub 精简交付

按 `docs/PUBLISHING.md` 同步：正式 MP4、字幕、必要源码配置、变动的原始配音缓存、时间轴、验收及说明。渲染帧、预览、干净中间片和混音 WAV 留在 `output/`。历史成片通过 Git 标签查看，不新增重复副本，不删除已有历史资源、不改写历史。

## 历史交付记录

2026-11-13 v1.12.0：98.4 秒、19 幕、29 条字幕。原 14 → 16 直接衔接，机械手口播与服务器铭牌已统一；标签 `mechanical-cube-v1.12.0`。

2026-11-13 v1.11.0：101.8 秒、20 幕、30 条字幕，版本标签 `mechanical-cube-v1.11.0`。

2026-11-08 v1.10.0：159.383 秒，45 条字幕，包含场景库、大学生 A、时序建模和故障上下文。该版合成入口为 `tools/build-integrated-main.ps1`；时间轴与验收见 `docs/main-integration-timeline-v1.10.json` 和 `docs/main-integration-validation-v1.10.json`。

以下入口和时间均属于对应历史版本；当前完整主片以本文件上方 v1.13.0 说明为准。

2026-11-05 v1.9.0：最终机械手融合版为 100.033 秒，独立主片 71.4 秒，两者均输出 1920×1080 / 60 fps，字幕已烧录。正常语速机械手使用 Yunyang、`rate=+0%`、音频变速因子 1.0，五步时长共 23.4 秒，章节过渡 6.233 秒。原 88.8 秒与 71.4 秒无字幕版分别归档在 `releases/iterations/14-mechanical-pre-subtitles-v1.8.1.mp4` 和 `13-main-pre-subtitles-v1.8.1.mp4`。

当前最终入口为 `tools/build-final-delivery.ps1`，加 `-ReuseRenders` 可使用仓库内视频和 WAV 离线重建；不加则重新渲染机械手与结尾。`prepare_natural_mechanical.py` 缓存原始 MP3、无变速 WAV、词级时间信息；`render_mechanical_natural.py` 根据真实配音长度调整动画，用光流补帧保持 60 fps。`finalize_subtitled_films.py` 重新拼接完整机械手章节、连续结尾与循环音乐，并输出字幕。

统一字体为 Microsoft YaHei（微软雅黑），配置见 `config/final_delivery.json`。主片原生场景的 174 个文字对象、图表的 21 个文字对象均使用 msyh；机械手的说明面板、铭牌和章节卡已重绘。原始手机截图属于页面内容，保留其 UI。旧动画为 1280×720，交付时放大为 1792×1008，置于 1920×1080 画布上；底部 72 像素为字幕专用区，新字幕以 1080p 原生渲染。SRT / ASS 位于 `../videos/subtitles/`。

字幕主文本和旧语音起止时间在 `config/main_caption_script.json`。新的机械手字幕依据合成服务返回的词级时间对齐。修改旁白时需同步该脚本或 `config/final_delivery.json`，不能只改画面。机械手融合版从 66.633 秒开始演示，90.033 秒进入报表过渡。独立主片保留原连续配乐；融合版将原前 30 秒配乐按 0.6 秒交叉淡化循环至新的片尾。

最终时间轴与验收结果见 `docs/final-delivery-timeline.json`、`docs/final-delivery-validation.json`。全片已通过 H.264/AAC 解码、时长同步、字幕范围和排版检查；六段新增旁白与原速 WAV 对齐，波形相关系数均为 1.0。融合版在 AAC 编码前保留 0.88 倍输出增益，解码峰值 0.9501，无削波。此增益不改变语速。

如先修改第五幕，运行 `tools/build-scenario-path.ps1` 生成新的 720p 基片，再将其两项输出作为 `build-final-delivery.ps1 -MainSource ... -MechanicalSource ...` 的输入。不能把已经带字幕的 1080p 发布片再次当作基片，以免重复字幕和重复缩放。旧命令的 88.8 秒输出只是最终处理前的基片。

2026-11-05 v1.8.1：探索过程保留朋友页查找和同级切换，但保存的测试用例只包含 ROOT → 我 → 喜欢 → 视频四个节点、三个点击步骤。`render_friends_scenario.py` 的 `ROUTE` 为成功路径；场景本地时间 18.0–18.8 秒逐步清理失败分支，18.8–20.8 秒仅展开绿色成功路径。对应预览约第 19 秒开始清理；两版主片仍为 71.4 / 88.8 秒。此次画面更新直接复制当前主片音轨，旁白和配乐不变。

2026-11-05 v1.8.0：第五幕改用“朋友 → 我”的真实底部 Tab 关系。操作为点击朋友、滑动查找未命中、直接点击我、找到喜欢列表、打开视频。朋友和我在相同 Y 坐标、相同深度，横向连接由 AI 在切换时补全；本版没有返回动作。主片仍为 71.4 / 88.8 秒，第二幕文案保持 v1.7.2。

新分镜入口为 `scripts/render_friends_scenario.py`，素材为 `assets/screenshots/myfriends.jpg`。滑动用已有截图内容区域做位移动画，底部导航固定，属于镜头演示。`tools/build-scenario-path.ps1` 已切换到新入口，并生成 21 秒探索镜头与 5 秒用例卡片。`smooth_scenario_transitions.py` 将探索与卡片一致地合入 25.2–52 秒；入场为 25.2–26.4 秒，路径到用例卡片转场为 47–48.4 秒。音频配置仍在 `config/scenario_path_voiceover.json`，26–45 秒替换，后续用例旁白保留。

2026-11-05 v1.7.2：第二幕（6–14 秒）画面和配音改为“人工智能持续探索页面，理解页面层级。”。两版完整主片均已同步，分别为 71.4 秒与 88.8 秒。第二幕以原生 30 fps 重渲染，主片保持 1280×720 / 60 fps 输出。

第二幕独立工程为 `blender/page-exploration.blend`（Eevee，中文字体已打包），文字在 `config/page_exploration.json`，配音在 `config/page_exploration_voiceover.json`。更改后运行：

```powershell
pwsh -File .\tools\build-page-exploration.ps1 -BlenderExe "D:\tools\blender-5.4.0\blender.exe"
pwsh -File .\tools\build-scenario-path.ps1
```

第二条命令从归档基片重建第五幕和转场，再合入第二幕；最终输出为 `output/scenario-path-v1/application-knowledge-graph-and-data-final.mp4` 与 `application-knowledge-graph-mechanical-final.mp4`。检查后将它们分别替换到 `../videos/` 的两版发布主片。单独运行 `integrate_page_exploration.py` 时，输入必须是尚未修改第二幕的旧基片，不能对已更新主片重复应用：它利用原始干净旁白抵消 6.6–13.2 秒的旧语音，再加入新旁白，保留背景音乐以及前一幕结束的配音。无需联网重建时可直接复用已交付的第二幕 MP4 和 WAV。

2026-11-05 更新：新第五幕已以连贯转场合入 71.4 秒主片与 88.8 秒机械手融合版。最终处理入口为 `scripts/smooth_scenario_transitions.py`，已并入 `tools/build-scenario-path.ps1`。进入转场 25.2–26.4 秒；退出转场 47–48.4 秒，匹配水平节点位置并错开文字淡化。该步骤直接复制音轨，已验证处理前后音频数据哈希一致。

2026-11-04 更新：第五幕从“输入 URL”改为“疑似问题场景”，包含 ROOT 逐层探索、同层横向查找和 AI 补全缺失连接。当前完整片仍在 `../videos/application-knowledge-graph-with-mechanical-replay.mp4`。重建这一段并合成主片使用 `tools/build-scenario-path.ps1`。早期 Blender 工程保留原 URL 分镜作为历史来源；当前最终流程必须执行这一步画面替换。

2026-10-29 更新：完整主片位于 `../videos/application-knowledge-graph-with-mechanical-replay.mp4`，88.8 秒，720p / 60 fps。第一帧完整显示“应用知识图谱”，前 30 秒音乐循环铺满全片，保留独立配音。最终处理入口是 `scripts/finalize_long_film.py`，音频参数在 `config/long_film_audio.json`；运行后检查输出再替换发布主片。

截至 2026-10-28，机械 CUBE 已完成从多关节机械臂方案到箱式三轴龙门方案的重构，并交付以下可复现镜头：

- 专业化 BOX、两侧 Y 导轨、龙门横梁、X 移动头、Z 触笔和手机固定器。
- 黑底青色半透明 X-ray 透视介绍镜头，逐部件高亮。
- 下视摄像头随移动头采集页面。
- AI 图像回传、控件识别、坐标转换、机械点击和二次验证闭环。
- 1 秒平滑转场、延长后的 AI 步骤和中文配音。

当前验收成片为 `releases/latest/mechanical-cube-main-ai-integrated-voiceover.mp4`，时长 27.25 秒，1280×720，24 fps，H.264 + AAC。它保留原主片前 14 秒的机械结构介绍，并以 0.75 秒柔和过黑转场接入新的 AI 操作分镜。

## 已验证环境

| 组件 | 已验证版本 |
| --- | --- |
| Windows | Windows 11 x64 |
| Blender | 5.4.0 Alpha，commit `7a8f04b3bb5a` |
| Python | 3.13.13 |
| FFmpeg | 8.1.2 |
| edge-tts | 7.3.1 |
| Git LFS | 3.7.1（当前文件体积无需 LFS） |

Blender 使用 Workbench 渲染 PNG 帧。这个选择是有意的：测试中 Eevee/Vulkan/Cycles 在当前 Alpha 构建上出现不稳定或显存压力，Workbench 对本项目的线框/X-ray 视觉更可靠。

## 新电脑接手清单

1. 安装 Git、Python、FFmpeg 和 Blender。
2. 克隆仓库并进入 `mechanical-cube`。
3. 运行 `tools/setup.ps1`，确认所有命令可用并创建 `.venv`。
4. 先播放 `../videos/application-knowledge-graph-with-mechanical-replay.mp4`，确认完整主片目标效果。
5. 打开 `blender/mechanical_cube_xray_intro.blend` 和 `blender/mechanical_cube_ai_control_loop.blend`，检查字体、材质和相机视图。
6. 使用 `tools/build-compact-full.ps1` 合成当前主片；修改前段时加 `-RebuildHead`，修改机械手时加 `-RebuildMechanical`。`tools/render-latest.ps1` 仅用于早期机械结构介绍。
7. 对照 `SHA256SUMS.txt` 验证交付视频、音频、图片与 Blender 素材没有损坏；源码与文档由 Git 记录。

若只需重新融合现有 AI 分镜，运行 `tools/integrate-ai-storyboard.ps1`。旁白时间轴位于 `config/mechanical_cube_integrated_voiceover.json`。

## 早期机械结构介绍重建流程

`tools/render-latest.ps1` 会依次执行：

1. `render_robot_cube_xray_intro.py`：生成 360 帧部件介绍，15 秒。
2. `render_robot_cube_ai_control_loop.py`：生成 192 帧 AI 闭环，8 秒。
3. FFmpeg 编码两段 PNG 序列。
4. 将 AI 闭环放慢到约 12 秒，使每个步骤更清楚。
5. 使用 1 秒淡化转场拼接，得到约 25.917 秒无声版。
6. `generate_mechanical_cube_voiceover.py` 按 JSON 时间轴合成中文旁白并混入视频。

逐帧目录可能占用数 GB，确认成片无误后可以手动删除 `output/**/frames/`；删除不会影响版本库。

## 关键设计约束

- BOX 内部不自行增加未经确认的结构。
- 两侧支架位于 BOX 两侧中段。
- 龙门架横跨两侧支架，并沿 Y 轴移动。
- 移动头沿横梁执行 X 轴运动；触笔只负责 Z 轴。
- 摄像头绑定移动头的 X/Y 位置，不跟随触笔 Z 轴下压。
- 每张页面只执行一次点击；页面切换后再进行下一次识别和点击。
- 视觉语言保持专业、工程化，避免卡通化。

## 主要入口

- 标题首帧与全片循环配乐：`scripts/finalize_long_film.py`，输入音乐和干净旁白已保存在 `assets/audio/`。
- 音乐参考相减提取（可选，需 NumPy）：`scripts/extract_background_music.py`。普通合成直接读取已保存的 FLAC。
- 结尾连续转场重建：`tools/build-analytics-outro.ps1`（Blender + Pillow + FFmpeg + edge-tts）
- 结尾运动与文字：`scripts/render_analytics_bridge.py`，配音：`config/analytics_outro_voiceover.json`
- 分析镜头修正：`scripts/render_final_analytics_v3.py`，从保留的 v2 Blender 工程重建 v3。
- 结尾时序：设备画面 0–1.65 秒缩放，三路数据 1.65–4 秒汇聚，4–5 秒叠化，4–10 秒展开报表。
- 全片将结尾接在 78.8 秒之后；各音轨补齐到实际画面时长，不截断最后一次点击。
- 当前结构建模：`scripts/build_robot_base_stage01.py`
- X-ray 介绍：`scripts/render_robot_cube_xray_intro.py`
- AI 闭环：`scripts/render_robot_cube_ai_control_loop.py`
- 配音生成：`scripts/generate_mechanical_cube_voiceover.py`
- 配音文案与时间轴：`config/mechanical_cube_voiceover.json`

## 已知限制

- 机械结构目前用于概念演示，不是包含电机、同步带、限位器、线缆拖链和紧固件公差的生产 CAD。
- 手机固定器和机械坐标标定为视觉表达，尚未连接真实控制器。
- AI 数据流是动画表达，尚未调用真实视觉模型或机械控制 API。
- Blender Alpha 版本可能改变渲染行为；若升级版本，应先用少量帧进行回归测试。
- edge-tts 需要联网；无法联网时可保留无声版，或把本地录音替换为 `mechanical_cube_voiceover.wav`。

## 下一阶段建议

1. 确定真实硬件行程、手机尺寸和安全高度，参数化 X/Y/Z 运动范围。
2. 加入相机内参、屏幕四角标定和像素到机械坐标的单应性变换。
3. 定义控制协议：`capture → detect → plan → move → tap → verify`。
4. 增加急停、限位、触笔压力或接触检测。
5. 将真实推理结果和机械状态通过 JSON/ROS/串口数据驱动 Blender 动画。

