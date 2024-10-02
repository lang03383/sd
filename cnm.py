import subprocess
import threading
import re
import sys
import time
import os
import signal

def read_stream(stream, callback):
    """读取子进程的输出流并通过回调处理每一行"""
    for line in iter(stream.readline, ''):
        line = line.rstrip()
        callback(line)
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
    tg_process = None
    public_link = None
    zrok_started_event = threading.Event()

    def handle_main_output(line):
        nonlocal zrok_process, public_link, tg_process
        print(f"main.py: {line}")  # 仅打印 main.py 的输出
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
            if not tg_process:
                print("Starting tg.py...")
                try:
                    # 启动 tg.py 子进程
                    tg_process = subprocess.Popen(
                        ['python', '/content/tg.py'],
                        stdout=subprocess.PIPE,  # 如果需要调试，可以改为 subprocess.PIPE
                        stderr=subprocess.PIPE,
                        bufsize=1,
                        universal_newlines=True
                    )
                    # 可选：启动线程读取 tg.py 的输出（如果需要调试）
                    # threading.Thread(target=read_stream, args=(tg_process.stdout, lambda x: print(f"tg.py: {x}")), daemon=True).start()
                except Exception as e:
                    print(f"Failed to start tg.py: {e}")

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
        # 等待 zrok 获取到公网链接
        while not zrok_started_event.is_set():
            if main_process.poll() is not None:
                # main.py 已退出但未启动 zrok
                print("main.py exited unexpectedly. Exiting...")
                sys.exit(1)
            time.sleep(0.1)  # 避免忙等待
        print("zrok share is running. Press Ctrl+C to stop.")

        # 持续运行，等待 main.py 和 zrok share 结束
        while True:
            if main_process.poll() is not None:
                print("main.py exited.")
                break
            if zrok_process and zrok_process.poll() is not None:
                print("zrok share exited.")
                break
            time.sleep(1)
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
        if tg_process:
            tg_process.terminate()
            try:
                tg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tg_process.kill()
        sys.exit(0)

if __name__ == "__main__":
    # 处理终止信号，确保子进程被终止
    def handle_signal(signum, frame):
        print(f"Received signal {signum}. Exiting...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    main()
