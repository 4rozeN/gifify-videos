import os
import subprocess
from pathlib import Path
from tabulate import tabulate

# 支持的视频格式
SUPPORTED_FORMATS = [".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"]

# 默认参数（稍后由用户输入覆盖）
DEFAULT_WIDTH = 400
DEFAULT_FPS = {"high": 15, "low": 10}
DEFAULT_SCALE_QUALITY = {
    "high": "flags=lanczos",
    "low": "flags=bicubic"
}
DEFAULT_DITHER = {
    "high": "dither=bayer:bayer_scale=5",
    "low": "dither=none"
}
DEFAULT_MAX_SIZE_MB = 2  # 默认最大文件大小限制（MB）
OUTPUT_DIR = Path("gifs")


def prompt_user():
    """
    交互式获取用户输入：
    - 输出GIF宽度（保持比例自适应高度）
    - 压缩模式（高质量或小体积）
    - 最大GIF文件大小限制（MB）
    """
    while True:
        try:
            width = int(input(f"请输入输出GIF宽度（建议300-500，默认{DEFAULT_WIDTH}）：") or DEFAULT_WIDTH)
            if 100 <= width <= 1000:
                break
            else:
                print("宽度应在100~1000之间")
        except ValueError:
            print("请输入一个有效数字")

    while True:
        mode = input("请选择压缩模式：\n1. 高质量（较大体积）\n2. 小体积（低质量）\n请输入 1 或 2（默认1）：") or "1"
        if mode in ["1", "2"]:
            mode = "high" if mode == "1" else "low"
            break
        else:
            print("请输入1或2")

    while True:
        try:
            size_limit = float(input(f"请输入最大GIF文件大小限制（单位MB，默认{DEFAULT_MAX_SIZE_MB}）：") or str(DEFAULT_MAX_SIZE_MB))
            if 0.5 <= size_limit <= 10:
                break
            else:
                print("建议输入在 0.5 ~ 10 MB 范围")
        except ValueError:
            print("请输入有效数字")

    return width, mode, size_limit


def find_video_files():
    """
    自动在当前目录查找支持格式的视频文件。
    如果找不到，则让用户输入扩展名尝试查找。
    """
    files = [f for ext in SUPPORTED_FORMATS for f in Path(".").glob(f"*{ext}")]
    if not files:
        print("❌ 未发现任何支持的视频格式。你可以输入文件扩展名来手动查找。")
        ext = input("请输入文件扩展名（如 .mkv、.mp4）：").strip()
        if not ext.startswith("."):
            ext = "." + ext
        files = list(Path(".").glob(f"*{ext}"))
    return files


def check_and_prepare_output_dir():
    """
    检查输出目录是否存在及是否为空。
    如果存在且不为空，提示用户是否覆盖或重命名新文件。
    返回：overwrite(bool)，表示用户是否同意覆盖同名文件
    """
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir()
        return True

    files_in_output = list(OUTPUT_DIR.glob("*"))
    if not files_in_output:
        # 目录存在但为空，直接用
        return True

    # 目录非空，询问用户处理策略
    while True:
        choice = input(f"检测到 '{OUTPUT_DIR}' 目录中已有文件。\n"
                       "你希望如何处理？\n"
                       "1. 覆盖同名文件（生成的GIF将覆盖同名文件）\n"
                       "2. 自动重命名新生成的GIF，避免覆盖\n"
                       "请输入 1 或 2（默认2）：") or "2"
        if choice in ["1", "2"]:
            return choice == "1"
        else:
            print("请输入1或2")


def run_ffmpeg_palette(input_path, palette_path, fps, scale_flag, width):
    """
    使用 ffmpeg 生成调色板（palette）图片，提高GIF颜色表现
    """
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", f"fps={fps},scale={width}:-1:{scale_flag},palettegen",
        str(palette_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def run_ffmpeg_gif(input_path, palette_path, output_path, fps, scale_flag, dither, width):
    """
    使用 ffmpeg 利用调色板生成最终GIF文件
    """
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path), "-i", str(palette_path),
        "-filter_complex", f"fps={fps},scale={width}:-1:{scale_flag}[x];[x][1:v]paletteuse={dither}",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def get_file_size(path):
    """
    返回文件大小，单位MB
    """
    return os.path.getsize(path) / 1024 / 1024  # MB


def generate_output_path(base_name, overwrite):
    """
    根据用户是否同意覆盖，生成输出GIF的路径。
    如果不覆盖，尝试自动给文件名添加数字后缀避免覆盖。
    """
    output_path = OUTPUT_DIR / f"{base_name}.gif"
    if overwrite or not output_path.exists():
        return output_path

    # 自动重命名，避免覆盖
    for i in range(1, 1000):
        candidate = OUTPUT_DIR / f"{base_name}_{i}.gif"
        if not candidate.exists():
            return candidate

    # 万一一千个都存在，返回原始名（会覆盖）
    return output_path


def process_video(file_path, width, mode, max_size_mb, overwrite):
    """
    处理单个视频文件：
    - 生成调色板
    - 生成GIF（使用用户选定参数）
    - 判断大小是否合规
    返回处理结果字典
    """
    name = file_path.stem
    palette_path = Path(f"{name}_palette.png")
    output_path = generate_output_path(name, overwrite)

    fps = DEFAULT_FPS[mode]
    scale_flag = DEFAULT_SCALE_QUALITY[mode]
    dither = DEFAULT_DITHER[mode]

    try:
        run_ffmpeg_palette(file_path, palette_path, fps, scale_flag, width)
        run_ffmpeg_gif(file_path, palette_path, output_path, fps, scale_flag, dither, width)
        size = get_file_size(output_path)
        status = "✅ 合格" if size <= max_size_mb else "⚠️ 超出限制"
    except Exception as e:
        status = f"❌ 错误：{e}"
        size = 0
    finally:
        if palette_path.exists():
            palette_path.unlink()

    return {"文件名": file_path.name, "GIF大小(MB)": f"{size:.2f}", "状态": status}


def print_summary_table(summary):
    """
    使用 tabulate 打印总结表格
    """
    headers = ["文件名", "GIF大小(MB)", "状态"]
    rows = [[item["文件名"], item["GIF大小(MB)"], item["状态"]] for item in summary]
    print(tabulate(rows, headers=headers, tablefmt="github"))


def main():
    print("📦 正在扫描视频文件...")
    videos = find_video_files()
    if not videos:
        print("❌ 没有可处理的视频，程序终止。")
        return

    width, mode, max_size_mb = prompt_user()

    overwrite = check_and_prepare_output_dir()

    print(f"\n🚀 开始处理 {len(videos)} 个视频...\n")

    summary = []
    for i, video in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] 正在处理：{video.name}")
        result = process_video(video, width, mode, max_size_mb, overwrite)
        summary.append(result)

    print("\n📊 总结结果：\n")
    print_summary_table(summary)

    print(f"\n🎉 处理完成，所有 GIF 已保存至：{OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
