# App Graph Journey

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

## 机械臂演示

- [`videos/robot-four-clicks-v07-page-switch.mp4`](videos/robot-four-clicks-v07-page-switch.mp4)

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
