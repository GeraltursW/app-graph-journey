# Mechanical CUBE AI Control

用于手机自动化测试的三轴机械 CUBE，可通过龙门结构完成 X/Y 定位、Z 轴触笔点击，并由下视摄像头把页面图像回传给 AI，形成“识别—坐标转换—执行—二次验证”的控制闭环。

![机械 CUBE 预览](docs/mechanical-cube-preview.png)

## 当前交付

- 约 89 秒完整主片：[`../videos/application-knowledge-graph-with-mechanical-replay.mp4`](../videos/application-knowledge-graph-with-mechanical-replay.mp4)
- 当前主片第一帧直接显示“应用知识图谱”；原片前 30 秒背景音乐循环铺满全片，独立旁白保留。
- 最新融合配音成片：[`releases/latest/mechanical-cube-main-ai-integrated-voiceover.mp4`](releases/latest/mechanical-cube-main-ai-integrated-voiceover.mp4)
- 最新融合无声成片：[`releases/latest/mechanical-cube-main-ai-integrated-clean.mp4`](releases/latest/mechanical-cube-main-ai-integrated-clean.mp4)
- AI 操作分镜源片：[`releases/latest/c159cc4d19a03485a4677970789f6f1a.mp4`](releases/latest/c159cc4d19a03485a4677970789f6f1a.mp4)
- 最新结尾（测试完成 → 数据汇聚 → 报表，含旁白）：[`releases/latest/analytics-outro-voiceover.mp4`](releases/latest/analytics-outro-voiceover.mp4)
- 最新分析镜头 Blender 源文件：[`blender/final_analytics_v3.blend`](blender/final_analytics_v3.blend)
- 上一版配音成片：[`releases/latest/mechanical-cube-ai-control-voiceover.mp4`](releases/latest/mechanical-cube-ai-control-voiceover.mp4)
- 当前基础模型：[`blender/robot_base_stage01_professional.blend`](blender/robot_base_stage01_professional.blend)
- 透视介绍镜头：[`blender/mechanical_cube_xray_intro.blend`](blender/mechanical_cube_xray_intro.blend)
- AI 控制闭环镜头：[`blender/mechanical_cube_ai_control_loop.blend`](blender/mechanical_cube_ai_control_loop.blend)

## 结构与运动关系

- BOX：长方体底座与中空壳体，内部保持开放，用于容纳手机和运动机构。
- 手机固定器：保证屏幕平面和机械坐标系之间的标定关系稳定。
- Y 轴：两侧导轨承载龙门架，使整根横梁前后移动。
- X 轴：移动头沿龙门横梁左右移动。
- Z 轴：移动头控制触笔垂直升降，每次只点击一个目标。
- 下视摄像头：固定在移动头上，随 X/Y 移动但不随触笔下压。
- AI 闭环：拍照回传、控件识别、像素坐标到机械坐标转换、点击、再次拍照验证。

## 在另一台 Windows 电脑上开始开发

```powershell
git clone https://github.com/GeraltursW/app-graph-journey.git
cd app-graph-journey\mechanical-cube
powershell -ExecutionPolicy Bypass -File .\tools\setup.ps1
```

安装 Blender 5.4 Alpha、Python 3.11+ 和 FFmpeg 后，可直接打开 `blender/` 中的工程继续修改。要从脚本完整重建当前成片：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\render-latest.ps1 `
  -BlenderExe "D:\tools\blender-5.4.0\blender.exe"
```

首次运行会生成 `output/`。该目录是可再生缓存，不提交到 Git。完整接手步骤、已知限制和验收方法见 [HANDOFF.md](HANDOFF.md)。

将新的 AI 操作分镜重新融合进主片：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\integrate-ai-storyboard.ps1
```

该脚本保留主片前 14 秒结构介绍，以 0.75 秒柔和过黑转场接入 AI 分镜，并根据 `config/mechanical_cube_integrated_voiceover.json` 重新生成同步旁白。

要把机械手复现方案插入 10 月 27 日长片的 09 镜头之后：

```powershell
pwsh -File .\mechanical-cube\tools\insert-into-long-film-after-shot09.ps1
```

插入后顺序为“09 实验室手机复现 → 4 秒章节过渡 → 机械手 AI 复现方案 → 测试完成与数据汇聚 → 10 数据分析”，成片时长约 88.8 秒。机械手最后一帧连续缩放为设备卡片，性能、功耗、热三路数据流向报表，以 1 秒叠化进入黑白斜纹背景的图表。旁白为“测试完成后，性能、功耗、热等数据同步汇聚，数据报表一目了然”。

从源文件重建这一段：

```powershell
pwsh -File .\mechanical-cube\tools\build-analytics-outro.ps1 -BlenderExe "D:\tools\blender-5.4.0\blender.exe"
```

生成文件位于 `mechanical-cube/output/final-analytics-v3/`。检查后将 `analytics-outro-voiceover.mp4` 复制到 `releases/latest/`，再运行长片合成脚本。初次需要执行 `tools/setup.ps1` 安装 Pillow 和 edge-tts。图表数值为演示数据。

最后处理片头和循环背景音乐（不需要重新渲染 Blender，也不需要联网）：

```powershell
python .\mechanical-cube\scripts\finalize_long_film.py
```

输出为 `mechanical-cube/output/application-knowledge-graph-final-music.mp4`，检查后可替换发布主片。脚本用完整标题画面覆盖首秒，保持 88.8 秒时长和配音同步。音乐源为 `assets/audio/music-first-30s.flac`，重复三次，在 29.4 秒及 58.8 秒开始 0.6 秒交叉淡化，末尾柔和淡出。参数位于 `config/long_film_audio.json`。

原片音乐与配音已混在同一音轨，音乐素材使用匹配的干净旁白参考进行相减提取；无损 FLAC 已随工程保存。需要重新提取时，安装 NumPy 并运行 `scripts/extract_background_music.py`。普通合成仅依赖 Python 标准库和 FFmpeg。

## 目录说明

```text
mechanical-cube/
├─ assets/             必要参考图与手机页面素材
├─ blender/            各阶段可编辑 .blend 工程
├─ config/             字幕与中文配音时间轴
├─ docs/               架构、迭代史、排障和预览图
├─ releases/           代表性迭代视频与最终成片
├─ scripts/            Blender 建模、动画、渲染和配音脚本
└─ tools/              环境检查与一键重建脚本
```

## 推荐工作流

1. 修改 `scripts/`，让模型变化可以重复生成；必要时同步保存新的 `.blend`。
2. 先低分辨率验证运动和构图，再生成完整 PNG 帧序列。
3. 使用 FFmpeg 编码和转场，最后生成配音版。
4. 新迭代放入 `releases/iterations/`，稳定版本放入 `releases/latest/`。
5. 更新 `CHANGELOG.md` 和 `HANDOFF.md` 后再提交。

