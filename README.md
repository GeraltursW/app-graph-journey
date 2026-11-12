# App Graph Journey

## 最新视频交付（2026-11-13 · v1.11.0）

- [应用知识图谱完整主片 · 101.8 秒](videos/application-knowledge-graph-with-mechanical-replay.mp4)
- [实验室手机复现与前后转场 · 11 秒预览](mechanical-cube/releases/latest/lab-replay-compact-preview.mp4)
- [AI 控制机械手 · 8.8 秒](mechanical-cube/releases/latest/compact-mechanical/mechanical-compact-preview.mp4)
- [中文字幕 SRT / ASS 与 STEP 提示](videos/subtitles/)
- [20 幕完整时间轴](mechanical-cube/docs/compact-main-timeline.json) · [交付验收](mechanical-cube/docs/compact-main-validation.json)
- [历史 v1.10 完整片 · 159.38 秒](mechanical-cube/releases/iterations/16-main-before-compact-v1.10.0.mp4)
- [保留短版 · 71.4 秒](videos/application-knowledge-graph-and-data.mp4)

完整版为 1920×1080 / 60 fps，前 18 幕压缩为 83 秒，接 8.8 秒机械手和 10 秒数据报表。AI 探索、页面节点与实验室复现统一黑白界面、绿色控件反馈；左上角按当前 20 幕统一编号。包含正常语速旁白、30 条中文字幕及连续循环背景音乐。完整制作文件和重建说明见 [HANDOFF.md](mechanical-cube/HANDOFF.md)。

## Mechanical CUBE

机械手/CUBE 的完整迭代工程、Blender 源文件、AI 控制闭环视频与跨电脑交接文档位于 [`mechanical-cube/`](mechanical-cube/README.md)。

当前完整主片的重建入口为 [`mechanical-cube/tools/build-compact-full.ps1`](mechanical-cube/tools/build-compact-full.ps1)，使用仓库内干净母版和语音缓存可离线合成；加 `-RebuildHead` 可重绘前 18 幕，加 `-RebuildMechanical` 可重绘机械手并更新衔接。大学生 A 为 AI 生成的示例用例，手机画面为动画演示。时间轴与交接说明见 [`mechanical-cube/HANDOFF.md`](mechanical-cube/HANDOFF.md)。

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
