import telegram
import asyncio
import os
import time

# 替换为你的机器人 API Token 和目标频道 ID
BOT_TOKEN = "7629844474:AAEwngL62udaJFe4ygKgVx_7N19JMn15YkY"  # 请确保不要公开分享你的 BOT_TOKEN
CHANNEL_ID = "-1002289779569"

# 初始化机器人
bot = telegram.Bot(token=BOT_TOKEN)

# 文件记录路径
SENT_FILES_RECORD = "/content/sent_files.txt"

# 发送文件到频道 (异步函数)
async def send_file_to_channel(file_path):
    try:
        with open(file_path, 'rb') as f:
            await bot.send_document(chat_id=CHANNEL_ID, document=f)
        print(f"文件 {file_path} 已发送到频道！")
        return True
    except Exception as e:
        print(f"发送文件 {file_path} 失败: {e}")
        return False

# 加载已发送文件列表
def load_sent_files(record_path):
    sent = set()
    if os.path.exists(record_path):
        with open(record_path, 'r', encoding='utf-8') as f:
            for line in f:
                sent.add(line.strip())
    return sent

# 保存已发送文件列表
def save_sent_files(sent, record_path):
    with open(record_path, 'w', encoding='utf-8') as f:
        for file_path in sent:
            f.write(f"{file_path}\n")

# 删除空文件的函数
def delete_empty_files(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) and os.path.getsize(file_path) == 0:
            os.remove(file_path)
            print(f"已删除空文件: {file_path}")

# 持续同步上传文件夹中的新文件
async def sync_folder_to_channel(folder_path, interval=60):
    sent_files = load_sent_files(SENT_FILES_RECORD)
    print(f"已加载 {len(sent_files)} 个已发送文件。")

    while True:
        # 删除空文件
        delete_empty_files(folder_path) 

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            # 使用绝对路径确保唯一性
            abs_file_path = os.path.abspath(file_path)
            if os.path.isfile(abs_file_path) and abs_file_path not in sent_files:
                success = await send_file_to_channel(abs_file_path)
                if success:
                    sent_files.add(abs_file_path)
                    save_sent_files(sent_files, SENT_FILES_RECORD)
        await asyncio.sleep(interval)

# 主函数
if __name__ == "__main__":
    folder_path = "/content/cnm/output"  # 替换为你的文件夹路径
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sync_folder_to_channel(folder_path))
