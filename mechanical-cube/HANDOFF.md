# 项目交接说明

## 交付状态

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
4. 先播放 `releases/latest/mechanical-cube-main-ai-integrated-voiceover.mp4`，确认目标效果。
5. 打开 `blender/mechanical_cube_xray_intro.blend` 和 `blender/mechanical_cube_ai_control_loop.blend`，检查字体、材质和相机视图。
6. 使用 `tools/render-latest.ps1` 完整重建，或加 `-SkipBlender` 只重做编码、转场和配音。
7. 对照 `SHA256SUMS.txt` 验证交付文件没有损坏。

若只需重新融合现有 AI 分镜，运行 `tools/integrate-ai-storyboard.ps1`。旁白时间轴位于 `config/mechanical_cube_integrated_voiceover.json`。

## 完整重建流程

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

