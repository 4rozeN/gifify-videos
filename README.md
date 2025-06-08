# 视频转GIF 脚本

这是一个使用 Python 和 FFmpeg 实现的视频批量转 GIF 脚本，支持多种视频格式（mp4、mkv、mov 等），允许用户自定义输出宽度、压缩质量和文件大小限制。

## 功能

- 自动扫描当前目录支持的视频文件
- 支持高质量和小体积两种压缩模式
- 用户自定义 GIF 宽度，保持纵横比
- GIF 最大文件大小限制输入
- 支持自动覆盖或自动重命名避免文件冲突
- 输出整齐美观的转换总结表格（使用 `tabulate`）
- 依赖 FFmpeg，确保系统已安装并可用

## 使用方法

1. 克隆或下载本项目代码。
2. 安装 Python 依赖：

   ```sh
   pip install tabulate
   ```

3. 确保系统安装了 `ffmpeg` 并在环境变量中。

4. 将你的视频文件放入脚本同一目录。

5. 运行脚本：

   ```bash
   python convert_videos_to_gif.py
   ```

6. 按提示输入输出 GIF 宽度、压缩模式、最大大小等。

7. 转换完成后，GIF 文件位于 `./gifs/` 目录。

## 备注

- 输出 GIF 宽度范围建议 100 - 1000 像素，过大体积和加载时间会增加。
- 若 GIF 超出大小限制，需手动调整参数或分割视频。
- 脚本自动判断是否覆盖已有文件，避免误删。

## 依赖

- Python 3.6+
- [FFmpeg](https://github.com/FFmpeg/FFmpeg)
- tabulate (`pip install tabulate`)