import subprocess
import threading
import re
import sys
import time

def read_stream(stream, callback):
    """读取子进程的输出流并通过回调处理每一行"""
    for line in iter(stream.readline, ''):
        decoded_line = line.rstrip()
        callback(decoded_line)
    stream.close()

def main():
    print("Starting main.py...")
    try:
        # 启动 main.py 子进程
        main_process = subprocess.Popen(
            ['python', '/content/cnm/main.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True  # 确保输出为文本模式
        )
    except Exception as e:
        print(f"Failed to start main.py: {e}")
        sys.exit(1)

    zrok_process = None
    public_link = None
    zrok_started_event = threading.Event()

    def handle_main_output(line):
        nonlocal zrok_process, public_link
        print(f"{line}")  # 仅打印 main.py 的输出
        # 检测 main.py 是否已完全启动
        if "本地访问链接" in line or "127.0.0.1:8188" in line:
            if not zrok_process:
                print("Detected main.py startup. Starting zrok share...")
                try:
                    # 启动 zrok share 子进程
                    zrok_process = subprocess.Popen(
                        ['zrok', 'share', 'public', 'localhost:8188'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        bufsize=1,
                        universal_newlines=True  # 确保输出为文本模式
                    )
                    # 启动一个线程来读取 zrok 的输出
                    threading.Thread(target=read_stream, args=(zrok_process.stdout, handle_zrok_output), daemon=True).start()
                except Exception as e:
                    print(f"Failed to start zrok share: {e}")

    def handle_zrok_output(line):
        nonlocal public_link
        # 使用正则表达式提取公网链接
        match = re.search(r'https://\S+\.share\.zrok\.io', line)
        if match and not public_link:
            public_link = match.group(0)
            print(f"公网访问链接: {public_link}")
            zrok_started_event.set()  # 标记 zrok 已启动并获取到链接

    # 启动一个线程来读取 main.py 的输出
    threading.Thread(target=read_stream, args=(main_process.stdout, handle_main_output), daemon=True).start()

    try:
        # 等待 zrok 分享的公网链接被获取
        while not zrok_started_event.is_set():
            if main_process.poll() is not None:
                # main.py 已退出但未启动 zrok
                print("main.py exited unexpectedly. Exiting...")
                sys.exit(1)
            time.sleep(0.1)  # 避免忙等待

        print("zrok share is running. Press Ctrl+C to stop.")

        # 等待 main.py 和 zrok share 都结束（实际上它们是持续运行的）
        main_process.wait()
        if zrok_process:
            zrok_process.wait()
    except KeyboardInterrupt:
        print("\n检测到中断，正在关闭子进程...")
        if main_process:
            main_process.terminate()
            try:
                main_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                main_process.kill()
        if zrok_process:
            zrok_process.terminate()
            try:
                zrok_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                zrok_process.kill()
        sys.exit(0)

if __name__ == "__main__":
    main()
