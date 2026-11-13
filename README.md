# App Graph Journey

## 最新视频交付（2026-11-13 · v1.15.0）

- [应用知识图谱完整主片 · 83.6 秒](videos/application-knowledge-graph-with-mechanical-replay.mp4)
- [中文字幕与 STEP 提示](videos/subtitles/)
- [15 幕完整时间轴](mechanical-cube/docs/compact-main-timeline.json) · [交付验收](mechanical-cube/docs/compact-main-validation.json)
- [项目交接](mechanical-cube/HANDOFF.md) · [精简同步规则](mechanical-cube/docs/PUBLISHING.md)

完整版为 1920×1080 / 60 fps，15 幕、26 条字幕。主线调整为“创建单个用例 → 扩展多个用例 → 形成场景库 → 提取典型操作序列 → 影响因子时序建模”。删除原 STEP 12 大学生示例，序列提取后以 0.5 秒淡化直接进入建模；后续场景文字全部通用化。保留正常语速、“机械手操作”口播、“服务器”铭牌及连续音乐。结尾“数据报表一目了然”仅保留底部字幕，画面内绿色重复文字已移除。历史成片通过 Git 标签查看。

## Mechanical CUBE

机械手/CUBE 的完整迭代工程、Blender 源文件、AI 控制闭环视频与跨电脑交接文档位于 [`mechanical-cube/`](mechanical-cube/README.md)。

当前完整主片的重建入口为 [`mechanical-cube/tools/build-compact-full.ps1`](mechanical-cube/tools/build-compact-full.ps1)，使用仓库内原始素材和语音缓存可离线重建；首次运行会自动更新过期的画面缓存；加 `-RebuildHead` 可重绘前段 13 幕，加 `-RebuildMechanical` 可重绘机械手并更新衔接。用例与故障情境为动画示意，不代表限定人群。时间轴与交接说明见 [`mechanical-cube/HANDOFF.md`](mechanical-cube/HANDOFF.md)。

App Graph Journey 是从 App Graph 主项目中独立出来的三维演进展示页，用滚动叙事呈现移动应用页面图谱从采集、探索、场景功能匹配、用例编排到执行结果回流的完整过程。

## 功能

- Three.js WebGL 三维页面关系树
- GSAP ScrollTrigger 滚动章节动画
- 抖音主页截图作为 `ROOT` 页面节点
- 页面树自上而下生长与下层分支展开
- 场景功能与测试用例从两侧注入
- 执行数据回流时高亮当前路径、降低其他分支亮度
- 鼠标拖拽旋转、惯性反馈和视角重置
- 桌面端与移动端响应式布局
- `prefers-reduced-motion` 降低动画支持
- 机械臂用例复现演示：四张页面逐页点击、点击后切换页面并返回验证结果
- 机械 CUBE AI 控制闭环：摄像头采集、坐标转换、机械点击与二次拍照验证

## 机械臂演示

- [`videos/robot-four-clicks-v07-page-switch.mp4`](videos/robot-four-clicks-v07-page-switch.mp4)
- [`videos/mechanical-cube-ai-control-voiceover.mp4`](videos/mechanical-cube-ai-control-voiceover.mp4)（中文配音版）

## 本地运行

```bash
npm install
npm run dev
```

浏览器访问 Vite 输出的本地地址。

## 生产构建

```bash
npm run build
npm run preview
```

构建结果位于 `dist/`。

## 技术栈

- Vue 3
- Vite
- Three.js
- GSAP / ScrollTrigger

## 操作

- 鼠标滚轮：推进或回退项目演进章节
- 拖拽空白区域：旋转三维图谱树
- 右上角重置按钮：恢复默认观察角度
- `↑` / `↓`、`PageUp` / `PageDown`：切换章节
