import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import requests
import time
import urllib.parse
import os
import random
from datetime import datetime, timedelta


# Định nghĩa đường dẫn tới tệp .env trong thư mục gốc
dotenv_path = Path(__file__).parents[1] / '.env'
load_dotenv(dotenv_path=dotenv_path)

# Lấy biến môi trường dành cho bot này
TOKEN = os.getenv('BOT_PROXYAI_ARTIST')

# Danh sách các model hợp lệ
VALID_MODELS = [
    "flux",
    "flux-realism",
    "flux-cablyai",
    "flux-anime",
    "flux-3d",
    "any-dark",
    "flux-pro",
    "turbo"
]

# Cài đặt intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Cần thiết để truy cập thông tin member và role

# Tạo bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Từ điển để theo dõi giới hạn tốc độ
rate_limits = {}

# Các hằng số giới hạn tốc độ
RATE_LIMIT = 3  # Số yêu cầu tối đa
TIME_PERIOD = 60  # Trong bao nhiêu giây

@bot.event
async def on_ready():
    print(f'Bot đã sẵn sàng. Đăng nhập dưới tên {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Đã đồng bộ {len(synced)} lệnh slash.')
    except Exception as e:
        print(f'Lỗi khi đồng bộ lệnh: {e}')

@bot.tree.command(name="imagine", description="Tạo ảnh từ prompt và model")
@app_commands.describe(
    prompt="Mô tả ảnh bạn muốn tạo",
    model="Chọn model để tạo ảnh"
)
@app_commands.choices(model=[
    app_commands.Choice(name=model_name, value=model_name) for model_name in VALID_MODELS
])
async def imagine(interaction: discord.Interaction, prompt: str, model: str):
    author = interaction.user
    member_role_name = '😀 Member'  # Tên của role cần giới hạn tốc độ

    # Kiểm tra xem người dùng có role 'member' hay không
    member = interaction.guild.get_member(author.id)
    if any(role.name.lower() == member_role_name.lower() for role in member.roles):
        now = time.time()
        user_id = author.id
        user_requests = rate_limits.get(user_id, [])

        # Loại bỏ các yêu cầu cũ hơn TIME_PERIOD giây
        user_requests = [t for t in user_requests if now - t < TIME_PERIOD]

        if len(user_requests) >= RATE_LIMIT:
            await interaction.response.send_message(f"Bạn đã đạt giới hạn {RATE_LIMIT} yêu cầu mỗi phút.", ephemeral=True)
            return
        else:
            user_requests.append(now)
            rate_limits[user_id] = user_requests

    await interaction.response.defer()  # Trì hoãn phản hồi

    # Bắt đầu thời gian tính tổng thời gian tạo ảnh
    start_time = time.time()

    await interaction.followup.send("Đang tạo ảnh, vui lòng chờ...")

    # Chuẩn bị tham số cho việc tạo ảnh
    width = 1024
    height = 1024
    seed = random.randint(0, 999999)
    # Mã hóa URL cho prompt
    encoded_prompt = urllib.parse.quote(prompt)

    # Tạo URL yêu cầu ảnh
    api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=poll&nofeed=yes&model={model}"

    try:
        # Gửi yêu cầu tới API của Pollinations
        response = requests.get(api_url)

        # Kiểm tra xem phản hồi có thành công hay không
        if response.status_code == 200:
            # Lưu ảnh
            image_filename = f"generated_image_{author.id}.jpg"
            with open(image_filename, 'wb') as f:
                f.write(response.content)

            # Lấy thời gian hiện tại và chuyển sang múi giờ Việt Nam (UTC+7)
            creation_time = (datetime.now() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S")

            # Tính tổng thời gian tạo ảnh
            end_time = time.time()
            total_duration = round(end_time - start_time, 2)

            # Tạo embed để hiển thị thông tin
            embed = discord.Embed(title="Ảnh được tạo thành công!", color=0x00ff00)
            embed.add_field(name="🖼️ Model", value=model, inline=True)
            embed.add_field(name="📐 Kích thước", value=f"{width}x{height}", inline=True)
            embed.add_field(name="⏰ Thời gian tạo", value=creation_time, inline=True)
            embed.add_field(name="⏳ Tổng thời lượng", value=f"{total_duration} giây", inline=False)
            embed.add_field(name="💬 Prompt", value=prompt, inline=False)
            embed.set_image(url=f"attachment://{image_filename}")

            # Gửi file ảnh và embed trở lại kênh Discord
            with open(image_filename, 'rb') as f:
                picture = discord.File(f, filename=image_filename)
                await interaction.followup.send(file=picture, embed=embed)

            # Xóa file ảnh sau khi gửi
            os.remove(image_filename)
        else:
            await interaction.followup.send("Không thể tạo ảnh. Vui lòng thử lại sau.")
            print(f"Lỗi {response.status_code}: {response.text}")
    except Exception as e:
        await interaction.followup.send("Đã xảy ra lỗi trong quá trình tạo ảnh.")
        print(e)

# Chạy bot
bot.run(TOKEN)