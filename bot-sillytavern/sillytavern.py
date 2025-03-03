import os
import discord
from discord import app_commands
from dotenv import load_dotenv
from discord.ext import commands

# Lấy biến môi trường dành cho bot
load_dotenv()
TOKEN = os.getenv('BOT_SILLYTAVERN')

intents = discord.Intents.default()
intents.members = True  # Bật intents.members để sử dụng Server Members Intent
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ID của kênh verify
VERIFY_CHANNEL_ID = 1346034261391708204  # Thay thế bằng ID kênh verify của bạn

@bot.event
async def on_ready():
    print(f'{bot.user} đã kết nối thành công!')
    try:
        synced = await bot.tree.sync()
        print(f"Đã đồng bộ {len(synced)} lệnh!")
    except Exception as e:
        print(e)

@bot.event
async def on_member_join(member):
    # Lấy kênh verify
    verify_channel = discord.utils.get(member.guild.channels, name="verify")
    if not verify_channel:
        # Nếu không tìm thấy kênh bằng tên, thử tìm bằng ID
        if VERIFY_CHANNEL_ID:
            verify_channel = member.guild.get_channel(VERIFY_CHANNEL_ID)
    
    if not verify_channel:
        # Nếu vẫn không tìm thấy kênh, gửi tin nhắn DM
        channel = await member.create_dm()
        await channel.send("Không tìm thấy kênh xác thực. Vui lòng liên hệ quản trị viên.")
        return

    # Tạo một kênh riêng tư chỉ người dùng đó và quản trị viên có thể nhìn thấy
    overwrites = {
        member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        member.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    # Tạo một kênh tạm thời cho việc xác thực
    temp_channel = await member.guild.create_text_channel(
        f'verify-{member.name}',
        overwrites=overwrites,
        category=verify_channel.category
    )
    
    # Gửi câu hỏi xác thực trong kênh tạm thời
    await temp_channel.send(f"{member.mention}, trước khi tham gia server bạn cần trả lời câu hỏi sau, lưu ý câu hỏi được viết để người nước ngoài khó đọc: Em. chai của m?_ẹ gọi l.à j?")
    
    def check(m):
        return m.author == member and m.channel == temp_channel
    
    for i in range(3):  # Cho phép người dùng thử lại 3 lần
        try:
            msg = await bot.wait_for('message', check=check, timeout=300.0)
            # Kiểm tra nếu câu trả lời có chứa từ "cậu"
            if "cậu" in msg.content.lower():
                role = discord.utils.get(member.guild.roles, name="😀 Member")
                if role:
                    await member.add_roles(role)
                    await temp_channel.send("Xác thực thành công! Bạn đã được cấp quyền truy cập.")
                    await temp_channel.send("Kênh này sẽ bị xóa sau 10 giây.")
                    import asyncio
                    await asyncio.sleep(10)
                    await temp_channel.delete()
                    return
                else:
                    await temp_channel.send("Không tìm thấy role '😀 Member'. Vui lòng liên hệ quản trị viên.")
            else:
                await temp_channel.send("Xác thực thất bại. Vui lòng thử lại.")
        except asyncio.TimeoutError:
            await temp_channel.send("Thời gian xác thực đã hết. Vui lòng thoát server rồi join để thử lại.")
            await temp_channel.send("Kênh này sẽ bị xóa sau 10 giây.")
            import asyncio
            await asyncio.sleep(10)
            await temp_channel.delete()
            return
    
    # Nếu người dùng không trả lời đúng sau 3 lần thử
    await temp_channel.send("Bạn đã thử sai quá nhiều lần. Vui lòng tham gia lại bằng lời mời.")
    await temp_channel.send("Kênh này sẽ bị xóa sau 10 giây.")
    import asyncio
    await asyncio.sleep(10)
    await temp_channel.delete()

# Lệnh slash tạo role tùy chỉnh
@bot.tree.command(name="addrole", description="Tạo role với tên và màu tùy chỉnh")
@app_commands.describe(
    role_name="Tên của role bạn muốn tạo",
    color="Mã màu theo định dạng HEX (ví dụ: #FF0000 cho màu đỏ)"
)
async def addrole(interaction: discord.Interaction, role_name: str, color: str):
    # Kiểm tra nếu người dùng có role Member
    member = interaction.user
    member_role = discord.utils.get(member.guild.roles, name="😀 Member")
    if member_role not in member.roles:
        await interaction.response.send_message("Bạn cần có role '😀 Member' để sử dụng lệnh này.", ephemeral=True)
        return
    
    # Kiểm tra định dạng màu
    if not color.startswith('#') or len(color) != 7:
        await interaction.response.send_message("Mã màu không hợp lệ. Vui lòng sử dụng định dạng HEX (ví dụ: #FF0000).", ephemeral=True)
        return
    
    try:
        # Chuyển đổi mã màu HEX sang Discord Color
        color_value = int(color[1:], 16)
        color = discord.Color(color_value)
        
        # Tạo role mới
        new_role = await interaction.guild.create_role(
            name=role_name,
            color=color,
            reason=f"Được tạo bởi {interaction.user.name}"
        )
        
        # Gán role cho người dùng
        await member.add_roles(new_role)
        
        await interaction.response.send_message(f"Đã tạo và gán role {new_role.mention} cho bạn!", ephemeral=False)
    except Exception as e:
        await interaction.response.send_message(f"Không thể tạo role: {str(e)}", ephemeral=True)

bot.run(TOKEN)