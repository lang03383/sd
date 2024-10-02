import telegram
import asyncio
import os
import time

# 替换为你的机器人 API Token 和目标频道 ID
BOT_TOKEN = "7629844474:AAEwngL62udaJFe4ygKgVx_7N19JMn15YkY"
CHANNEL_ID = "-1002289779569"

# 初始化机器人
bot = telegram.Bot(token=BOT_TOKEN)

# 发送文件到频道 (异步函数)
async def send_file_to_channel(file_path):
  with open(file_path, 'rb') as f:
    await bot.send_document(chat_id=CHANNEL_ID, document=f)
  print(f"文件 {file_path} 已发送到频道！")

# 存储已发送文件的列表
sent_files = set()

# 删除空文件的函数
def delete_empty_files(folder_path):
  for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)
    if os.path.isfile(file_path) and os.path.getsize(file_path) == 0:
      os.remove(file_path)
      print(f"已删除空文件: {file_path}")

# 持续同步上传文件夹中的新文件
async def sync_folder_to_channel(folder_path, interval=60):
  while True:
    # 删除空文件
    delete_empty_files(folder_path) 

    for filename in os.listdir(folder_path):
      file_path = os.path.join(folder_path, filename)
      if os.path.isfile(file_path) and file_path not in sent_files:
        await send_file_to_channel(file_path)
        sent_files.add(file_path)
    await asyncio.sleep(interval)

# 主函数
if __name__ == "__main__":
  folder_path = "/content/cnm/output"  # 替换为你的文件夹路径
  loop = asyncio.get_event_loop()
  loop.run_until_complete(sync_folder_to_channel(folder_path))
