# 排障

## Blender 启动后无画面或崩溃

当前镜头使用 Workbench，避免切换到需要 Vulkan/大量显存的渲染设置。先只渲染 1–3 帧，确认驱动和 Blender 构建可用，再执行完整动画。

## FFmpeg 找不到帧

确认目录中存在 `frame_0001.png`，并确认使用 24 fps、`-start_number 1` 和 `%04d` 序号格式。完整渲染脚本会自动使用正确参数。

## 中文配音无法生成

运行 `tools/setup.ps1` 安装 `edge-tts`。它需要联网；如网络必须经过代理，可先设置 `HTTPS_PROXY`，脚本也会在直连失败时尝试本机 `127.0.0.1:7897`。

## Blender 路径不同

通过 `-BlenderExe` 明确传入 `blender.exe`，或设置环境变量 `BLENDER_EXE`。不要把个人电脑的绝对路径写回 Python 脚本。

## 成片时长有少量帧差

FFmpeg 的 `setpts` 与帧率取整可能造成一个帧周期的差异。交付版目标为约 25.917 秒；验收重点是声音不截断、转场无闪烁、最后验证状态完整显示。

