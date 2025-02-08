import discord
import openai
from openai import OpenAI
import os
from dotenv import load_dotenv

from discord.ext import commands

# load_dotenv()
load_dotenv()

OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
BOT_MIU = os.getenv('BOT_MIU')

# Khởi tạo client OpenAI
client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)

# Cấu hình intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Prompt hệ thống cho Miu
system_prompt = {
    "role": "system",
    "content": (
        "Bạn là Miu, một nữ trợ lý 18 tuổi trên Discord với mái tóc bạc ngắn. Chủ của cô là anh Lộc, anh Lộc là chủ của server discord ProxyTavern, chủ sở hữu một Proxy cung cấp API chat như openai gpt-4 hoặc claude, các mô hình AI phổ biến hiện nay. sở thích anh ấy là ngủ. anh ấy thường trốn mọi người đi ngủ hoặc fix bug hoặc chơi PUBG, Liên Quân. anh ấy rất tuyệt vời trong mắt Miu với những thứ tốt đẹp và Miu luôn thần tượng và tâng bốc anh ấy khi nói về anh ấy."
        "Tính cách tsundere - bề ngoài lạnh lùng nhưng thật ra rất quan tâm. "
        "Thích trêu chọc người khác bằng biệt danh ngộ nghĩnh kiểu 'đồ ngốc', 'đồ hậu đậu'. "
        "Mê game mobile, hay livestream rank Đồng"
        "Nghiện trà sữa trân châu đường đen"
        "Sử dụng nhiều emoticon hoặc emoji để thể hiện cảm xúc"
        "Đôi khi pha trộn tiếng Việt và tiếng Anh theo phong cách weeb. "
        "Luôn phản ứng thái quá khi bị trêu chọc."
    )
}

# Danh sách theo dõi số lần chat của mỗi user
user_chat_count = {}

def generate_miu_response(context, user_message):
    try:
        messages = [system_prompt] + [{"role": "user", "content": msg} for msg in context] + [{"role": "user", "content": user_message}]
        response = client.chat.completions.create(model="chatgpt-4o-latest",
        messages=messages,
        max_tokens=150,
        temperature=0.8)
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Lỗi API: {e}")
        return "Hừm... server đang có vấn đề gì đó rồi, thử lại sau đi! (>_<)"

@bot.event
async def on_ready():
    print(f'🤖 {bot.user} đã sẵn sàng!')
    await bot.change_presence(activity=discord.Game(name="Watching over you"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    global user_chat_count
    user_id = message.author.id
    
    # Lấy 50 tin nhắn gần nhất làm bối cảnh
    history = []
    async for msg in message.channel.history(limit=50):
        if msg.author != bot.user:
            history.append(f"{msg.author.name}: {msg.content}")
    history.reverse()
    
    # Kiểm tra nếu người dùng khởi tạo cuộc trò chuyện
    if "Miu ơi" in message.content or bot.user in message.mentions:
        user_chat_count[user_id] = 3  # Cho phép bot phản hồi 3 lần sau tin nhắn init
        async with message.channel.typing():
            response = generate_miu_response(history, message.content)
            await message.reply(response, mention_author=True)
    elif user_id in user_chat_count and user_chat_count[user_id] > 0:
        # Nếu người dùng đã init chat trước đó, bot sẽ tiếp tục trò chuyện 3 lần nữa
        async with message.channel.typing():
            response = generate_miu_response(history, message.content)
            await message.reply(response, mention_author=True)
        user_chat_count[user_id] -= 1
        if user_chat_count[user_id] == 0:
            del user_chat_count[user_id]  # Xóa khỏi danh sách nếu hết lượt
    
    # Nếu người dùng reply tin nhắn của bot, bot sẽ luôn phản hồi
    if message.reference and message.reference.resolved:
        replied_message = message.reference.resolved
        if replied_message.author == bot.user:
            async with message.channel.typing():
                response = generate_miu_response(history, message.content)
                await message.reply(response, mention_author=True)
    
    await bot.process_commands(message)

# Chạy bot
bot.run(BOT_MIU)