import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import requests
import time
import urllib.parse
import random
from datetime import datetime, timedelta
import base64

# Tải biến môi trường
load_dotenv()

# Lấy biến môi trường dành cho bot này
TOKEN = os.getenv('BOT_PROXYAI_ARTIST')

# Biến môi trường cho Cloudflare
CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')

# Danh sách các model hợp lệ
VALID_MODELS = [
    "flux",
    "flux-realism",
    "flux-cablyai",
    "flux-anime",
    "flux-3d",
    "any-dark",
    "flux-pro",
    "turbo",
    "stable-diffusion-xl-lightning",  # Model từ Cloudflare
    "flux-1-schnell"                  # Model từ Cloudflare
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

    # Kiểm tra role và giới hạn tốc độ
    member = interaction.guild.get_member(author.id)
    if any(role.name.lower() == member_role_name.lower() for role in member.roles):
        now = time.time()
        user_id = author.id
        user_requests = rate_limits.get(user_id, [])
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

    # Chuẩn bị tiêu đề chờ
    await interaction.followup.send("Đang tạo ảnh, vui lòng chờ...")

    image_filename = f"generated_image_{author.id}.png"  # Định dạng PNG

    try:
        if model in ["stable-diffusion-xl-lightning", "flux-1-schnell"]:
            # Sử dụng Cloudflare API
            api_url = ""
            if model == "stable-diffusion-xl-lightning":
                api_url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/bytedance/stable-diffusion-xl-lightning"
            elif model == "flux-1-schnell":
                api_url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"

            headers = {
                "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
                "Content-Type": "application/json"
            }
            data = {
                "prompt": prompt
            }

            response = requests.post(api_url, headers=headers, json=data)

            # Kiểm tra phản hồi từ Cloudflare
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if model == "stable-diffusion-xl-lightning" and content_type == "image/png":
                    # Lưu ảnh trực tiếp
                    with open(image_filename, 'wb') as f:
                        f.write(response.content)
                elif model == "flux-1-schnell" and content_type == "application/json":
                    json_response = response.json()
                    base64_image = json_response.get("result", {}).get("image")
                    if base64_image:
                        # Giải mã và lưu ảnh từ base64
                        image_data = base64.b64decode(base64_image)
                        with open(image_filename, 'wb') as f:
                            f.write(image_data)
                    else:
                        raise ValueError("Không tìm thấy trường 'result.image' trong phản hồi JSON.")
                else:
                    raise ValueError(f"Không nhận được định dạng phản hồi mong muốn từ Cloudflare: {content_type}")
            else:
                await interaction.followup.send("Không thể tạo ảnh. Vui lòng thử lại sau.")
                print(f"Lỗi {response.status_code}: {response.text}")
                return
        else:
            # Sử dụng API của Pollinations
            encoded_prompt = urllib.parse.quote(prompt)
            api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=poll&nofeed=yes&model={model}"

            response = requests.get(api_url)
            if response.status_code == 200:
                # Lưu ảnh
                with open(image_filename, 'wb') as f:
                    f.write(response.content)
            else:
                await interaction.followup.send("Không thể tạo ảnh. Vui lòng thử lại sau.")
                print(f"Lỗi {response.status_code}: {response.text}")
                return

        # Lấy thời gian hiện tại và chuyển sang múi giờ Việt Nam (UTC+7)
        creation_time = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S")

        # Tính tổng thời gian tạo ảnh
        end_time = time.time()
        total_duration = round(end_time - start_time, 2)

        # Tạo embed để hiển thị thông tin
        embed = discord.Embed(title="Ảnh được tạo thành công!", color=0x00ff00)
        embed.add_field(name="🖼️ Model", value=model, inline=True)
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
    except Exception as e:
        await interaction.followup.send("Đã xảy ra lỗi trong quá trình tạo ảnh.")
        print(f"Lỗi: {e}")

# Chạy bot
bot.run(TOKEN)