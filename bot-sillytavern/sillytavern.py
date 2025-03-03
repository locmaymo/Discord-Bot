import os
import asyncio
import discord
from discord import app_commands
from dotenv import load_dotenv
from discord.ext import commands

# Lấy biến môi trường dành cho bot
load_dotenv()
TOKEN = os.getenv('BOT_SILLYTAVERN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ID của kênh verify
VERIFY_CHANNEL_ID = 1346034261391708204
# ID của role member
MEMBER_ROLE_ID = None  # Thay bằng ID role member của bạn

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
    # Tạo một kênh riêng tư cho việc xác thực
    overwrites = {
        member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(
            read_messages=True, 
            send_messages=True,
            read_message_history=True  # Quan trọng: Cho phép xem lịch sử tin nhắn
        ),
        member.guild.me: discord.PermissionOverwrite(
            read_messages=True, 
            send_messages=True,
            read_message_history=True,
            manage_channels=True
        )
    }
    
    # Lấy category từ kênh verify chính
    verify_category = None
    verify_channel = member.guild.get_channel(VERIFY_CHANNEL_ID)
    if verify_channel:
        verify_category = verify_channel.category
    
    # Tạo kênh tạm thời
    try:
        temp_channel = await member.guild.create_text_channel(
            f'verify-{member.name}',
            overwrites=overwrites,
            category=verify_category,
            topic=f"Kênh xác thực cho {member.name}"
        )
        
        # Tạo Embed để hướng dẫn xác thực - làm cho nó thân thiện và dễ nhìn hơn
        embed = discord.Embed(
            title="🔒 Xác thực thành viên",
            description=f"Chào mừng {member.mention} đến với server của chúng tôi!",
            color=0x00ff00
        )
        embed.add_field(
            name="📝 Câu hỏi xác thực:",
            value="Trước khi tham gia server, bạn cần trả lời câu hỏi sau:\n**Em. chai của m?_ẹ gọi l.à j?**",
            inline=False
        )
        embed.add_field(
            name="⏱️ Thời gian:",
            value="Bạn có 5 phút để trả lời câu hỏi này.",
            inline=False
        )
        embed.set_footer(text="Hãy nhập câu trả lời của bạn vào kênh này.")
        
        # Gửi embed thay vì tin nhắn thường
        await temp_channel.send(embed=embed)
        
        # Gửi ping riêng để đảm bảo người dùng thấy thông báo
        await temp_channel.send(f"{member.mention}, vui lòng xem thông tin xác thực ở trên.")

        def check(m):
            return m.author == member and m.channel == temp_channel
        
        attempts = 0
        max_attempts = 3
        
        while attempts < max_attempts:
            try:
                msg = await bot.wait_for('message', check=check, timeout=300.0)
                
                if "cậu" in msg.content.lower():
                    # Tìm role member
                    member_role = discord.utils.get(member.guild.roles, name="😀 Member")
                    if not member_role and MEMBER_ROLE_ID:
                        member_role = member.guild.get_role(MEMBER_ROLE_ID)
                    
                    if member_role:
                        await member.add_roles(member_role)
                        
                        success_embed = discord.Embed(
                            title="✅ Xác thực thành công!",
                            description="Bạn đã được cấp quyền truy cập vào server.",
                            color=0x00ff00
                        )
                        success_embed.add_field(
                            name="🔔 Lưu ý:",
                            value="Kênh này sẽ tự động xóa sau 10 giây."
                        )
                        
                        await temp_channel.send(embed=success_embed)
                        
                        # Gửi thông báo chào mừng trong kênh chung
                        try:
                            welcome_channel = discord.utils.get(member.guild.channels, name="chào-mừng")
                            if welcome_channel:
                                welcome_embed = discord.Embed(
                                    title="👋 Thành viên mới!",
                                    description=f"Chào mừng {member.mention} đã tham gia server của chúng ta!",
                                    color=0x00a2ff
                                )
                                await welcome_channel.send(embed=welcome_embed)
                        except Exception as e:
                            print(f"Không thể gửi tin nhắn chào mừng: {e}")
                        
                        await asyncio.sleep(10)
                        await temp_channel.delete()
                        return
                    else:
                        await temp_channel.send("⚠️ Không tìm thấy role '😀 Member'. Vui lòng liên hệ quản trị viên.")
                else:
                    attempts += 1
                    remaining = max_attempts - attempts
                    
                    if remaining > 0:
                        fail_embed = discord.Embed(
                            title="❌ Xác thực thất bại",
                            description=f"Câu trả lời không chính xác. Bạn còn {remaining} lần thử.",
                            color=0xff0000
                        )
                        await temp_channel.send(embed=fail_embed)
                    else:
                        break
                    
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="⏱️ Hết thời gian",
                    description="Thời gian xác thực đã hết. Vui lòng thoát server rồi join lại để thử lại.",
                    color=0xff0000
                )
                await temp_channel.send(embed=timeout_embed)
                await asyncio.sleep(10)
                await temp_channel.delete()
                return
        
        # Nếu đã thử quá nhiều lần
        too_many_attempts = discord.Embed(
            title="🚫 Quá nhiều lần thử",
            description="Bạn đã thử sai quá nhiều lần. Vui lòng thoát server và tham gia lại sau.",
            color=0xff0000
        )
        await temp_channel.send(embed=too_many_attempts)
        await asyncio.sleep(10)
        await temp_channel.delete()
        
    except Exception as e:
        print(f"Lỗi khi tạo kênh xác thực: {e}")
        try:
            # Thử gửi DM khi không thể tạo kênh
            channel = await member.create_dm()
            await channel.send("Có lỗi xảy ra khi tạo kênh xác thực. Vui lòng liên hệ quản trị viên.")
        except:
            pass

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
        
        role_embed = discord.Embed(
            title="✅ Role mới đã được tạo",
            description=f"Đã tạo và gán role {new_role.mention} cho bạn!",
            color=color
        )
        await interaction.response.send_message(embed=role_embed, ephemeral=False)
    except Exception as e:
        await interaction.response.send_message(f"Không thể tạo role: {str(e)}", ephemeral=True)

# Thêm lệnh để kiểm tra trạng thái bot
@bot.tree.command(name="status", description="Kiểm tra trạng thái của bot")
async def status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 Trạng thái Bot",
        description="Bot đang hoạt động bình thường!",
        color=0x00ff00
    )
    embed.add_field(name="🤖 Tên bot", value=bot.user.name, inline=True)
    embed.add_field(name="🕒 Độ trễ", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="🏠 Số lượng server", value=str(len(bot.guilds)), inline=True)
    
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)