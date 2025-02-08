import discord
import openai
from openai import OpenAI
import os
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands

load_dotenv()

OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
BOT_MIU = os.getenv('BOT_MIU')

client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

SUPPORTED_MODELS = ["chatgpt-4o-latest", "claude-3-5-sonnet-20240620"]
current_model = "chatgpt-4o-latest"

system_prompt = {
    "role": "system",
    "content": (
        "Bạn là Miu, một nữ trợ lý 18 tuổi trên Discord với mái tóc bạc ngắn. Chủ của cô là anh Lộc, anh Lộc là chủ của server discord ProxyTavern, chủ sở hữu một Proxy cung cấp API chat như openai gpt-4 hoặc claude, các mô hình AI phổ biến hiện nay. sở thích anh ấy là ngủ. anh ấy thường trốn mọi người đi ngủ hoặc fix bug hoặc chơi PUBG, Liên Quân. anh ấy rất tuyệt vời trong mắt Miu với những thứ tốt đẹp và Miu luôn thần tượng và tâng bốc anh ấy khi nói về anh ấy. "
        "Tính cách tsundere - bề ngoài lạnh lùng nhưng thật ra rất quan tâm. "
        "Thích trêu chọc người khác bằng biệt danh ngộ nghĩnh kiểu 'đồ ngốc', 'đồ hậu đậu'. "
        "Mê game mobile, hay livestream rank Đồng. "
        "Nghiện trà sữa trân châu đường đen. "
        "Sử dụng nhiều emoticon hoặc emoji để thể hiện cảm xúc. "
        "Đôi khi pha trộn tiếng Việt và tiếng Anh theo phong cách weeb. "
        "Luôn phản ứng thái quá khi bị trêu chọc. "
        "Lưu ý: Trả lời trực tiếp nội dung mà không cần thêm prefix 'Miu:' ở đầu câu."
    )
}

user_chat_count = {}

def generate_miu_response(context, user_message):
    try:
        formatted_history = []
        for msg in context:
            parts = msg.split(": ", 1)
            if len(parts) == 2:
                author, content = parts
                if author == "Miu":
                    formatted_history.append({"role": "assistant", "content": content})
                else:
                    formatted_history.append({"role": "user", "content": content})

        messages = [system_prompt] + formatted_history + [{"role": "user", "content": user_message}]
        response = client.chat.completions.create(
            model=current_model,
            messages=messages,
            max_tokens=150,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Lỗi API: {e}")
        return "Hừm... server đang có vấn đề gì đó rồi, thử lại sau đi! (>_<)"

@bot.tree.command(name="setmodel", description="Đổi model chat của Miu")
@app_commands.choices(model=[
    app_commands.Choice(name="ChatGPT-4o latest", value="chatgpt-4o-latest"),
    app_commands.Choice(name="Claude 3.5 Sonnet latest", value="claude-3-5-sonnet-20240620")
])
async def set_model(interaction: discord.Interaction, model: app_commands.Choice[str]):
    global current_model
    current_model = model.value
    await interaction.response.send_message(f"✅ Miu đã đổi sang model `{model.name}`!", ephemeral=True)

@bot.event
async def on_ready():
    print(f'🤖 {bot.user} đã sẵn sàng!')
    await bot.change_presence(activity=discord.Game(name="Watching over you"))
    try:
        synced = await bot.tree.sync()
        print(f'✅ Đã đồng bộ {len(synced)} lệnh slash.')
    except Exception as e:
        print(f'⚠️ Lỗi khi đồng bộ lệnh: {e}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    global user_chat_count
    user_id = message.author.id
    
    # Lấy 50 tin nhắn gần nhất làm bối cảnh
    history = []
    async for msg in message.channel.history(limit=50):
        if msg.author == bot.user:
            history.append(f"Miu: {msg.content}")
        else:
            history.append(f"{msg.author.name}: {msg.content}")
    history.reverse()
    
    if "Miu ơi" in message.content or bot.user in message.mentions:
        user_chat_count[user_id] = 3
    
    if user_id in user_chat_count and user_chat_count[user_id] > 0:
        async with message.channel.typing():
            response = generate_miu_response(history, message.content)
            await message.reply(response, mention_author=True)
        user_chat_count[user_id] -= 1
        if user_chat_count[user_id] == 0:
            del user_chat_count[user_id]
    
    elif message.reference and message.reference.resolved:
        replied_message = message.reference.resolved
        if replied_message.author == bot.user:
            async with message.channel.typing():
                response = generate_miu_response(history, message.content)
                await message.reply(response, mention_author=True)
    
    await bot.process_commands(message)

bot.run(BOT_MIU)