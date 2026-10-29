# App Graph Journey

## 最新视频交付（2026-10-29）

- [应用知识图谱与数据呈现 · 71.4 秒](videos/application-knowledge-graph-and-data.mp4)
- [Test Cube 独立 AI 操作流程 · 17.4 秒](videos/test-cube-ai-operation-standalone.mp4)
- [Test Cube 旋转透视介绍与 AI 流程 · 33.05 秒](videos/test-cube-orbit-xray.mp4)

[交付说明](videos/DELIVERY-2026-10-29.md)。三段均为 720p / 60 fps；Test Cube 视频已统一内部主机名称为“服务器”。

## Mechanical CUBE

机械手/CUBE 的完整迭代工程、Blender 源文件、AI 控制闭环视频与跨电脑交接文档位于 [`mechanical-cube/`](mechanical-cube/README.md)。

此前的融合主片在 09 实验室手机复现之后加入机械手 AI 复现方案：[`videos/application-knowledge-graph-with-mechanical-replay.mp4`](videos/application-knowledge-graph-with-mechanical-replay.mp4)。

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
