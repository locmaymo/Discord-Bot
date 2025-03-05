import os
import asyncio
import discord
from discord import app_commands
from dotenv import load_dotenv
from discord.ext import commands
from pymongo import MongoClient

# Lấy biến môi trường cho bot và MongoDB
load_dotenv()
TOKEN = os.getenv('BOT_SILLYTAVERN')
MONGO_URI = os.getenv('MONGO_URI')  # Ví dụ: mongodb+srv://<user>:<password>@cluster0.mongodb.net/myFirstDatabase?retryWrites=true&w=majority

# Kết nối MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["discord_bot"]
color_roles_collection = db["color_roles"]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ID của kênh verify và role member
VERIFY_CHANNEL_ID = 1346034261391708204
MEMBER_ROLE_ID = None  # Thay bằng ID role member nếu cần

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
    # Tạo kênh riêng để xác thực
    overwrites = {
        member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(
            read_messages=True, 
            send_messages=True,
            read_message_history=True
        ),
        member.guild.me: discord.PermissionOverwrite(
            read_messages=True, 
            send_messages=True,
            read_message_history=True,
            manage_channels=True
        )
    }
    
    verify_category = None
    verify_channel = member.guild.get_channel(VERIFY_CHANNEL_ID)
    if verify_channel:
        verify_category = verify_channel.category
    
    try:
        temp_channel = await member.guild.create_text_channel(
            f'verify-{member.name}',
            overwrites=overwrites,
            category=verify_category,
            topic=f"Kênh xác thực cho {member.name}"
        )
        
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
        
        await temp_channel.send(embed=embed)
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
            channel = await member.create_dm()
            await channel.send("Có lỗi xảy ra khi tạo kênh xác thực. Vui lòng liên hệ quản trị viên.")
        except:
            pass

# Lệnh slash tạo role màu sử dụng MongoDB để lưu dữ liệu
@bot.tree.command(name="namecolor", description="Tạo role màu cho bạn (chỉ dùng để hiển thị màu)")
@app_commands.describe(
    color="Mã màu theo dạng HEX (ví dụ: #FF0000). Truy cập https://www.color-hex.com/ để chọn màu."
)
async def namecolor(interaction: discord.Interaction, color: str):
    member = interaction.user

    # Kiểm tra nếu người dùng có role '😀 Member'
    member_role = discord.utils.get(member.guild.roles, name="😀 Member")
    if member_role not in member.roles:
        await interaction.response.send_message("Bạn cần có role '😀 Member' để sử dụng lệnh này.", ephemeral=True)
        return

    if not color.startswith('#') or len(color) != 7:
        await interaction.response.send_message(
            "Mã màu không hợp lệ. Vui lòng sử dụng định dạng HEX (ví dụ: #FF0000). Truy cập https://www.color-hex.com/ để chọn màu.",
            ephemeral=True
        )
        return

    # Kiểm tra trong MongoDB xem người dùng đã có role màu nào trong server này chưa
    existing = color_roles_collection.find_one({"user_id": member.id, "guild_id": member.guild.id})
    if existing:
        old_role = member.guild.get_role(existing["role_id"])
        if old_role:
            try:
                await old_role.delete(reason="Thay thế role màu cũ bởi role mới")
            except Exception as e:
                await interaction.response.send_message("Không thể xóa role màu cũ. Vui lòng thử lại.", ephemeral=True)
                return
        color_roles_collection.delete_one({"user_id": member.id, "guild_id": member.guild.id})

    try:
        color_value = int(color[1:], 16)
        discord_color = discord.Color(color_value)
    except ValueError:
        await interaction.response.send_message("Mã màu không hợp lệ. Vui lòng kiểm tra lại.", ephemeral=True)
        return

    # Đặt tên role cố định là "name color" cho tất cả các role màu
    role_name = "name color"
    try:
        new_role = await interaction.guild.create_role(
            name=role_name,
            color=discord_color,
            permissions=discord.Permissions.none(),  # Role chỉ mang tính thẩm mỹ
            reason=f"Được tạo bởi {interaction.user.name} để tạo màu cho tên"
        )

        # chờ 1 giây để role được cập nhật
        await asyncio.sleep(1)
        
        # Đẩy role lên vị trí cao để ưu tiên hiển thị màu
        bot_top_role = member.guild.me.top_role
        try:
            await new_role.edit(position=bot_top_role.position - 1)
        except Exception as e:
            print(f"Không thể thay đổi vị trí role: {e}")

        await member.add_roles(new_role)
        # Lưu thông tin role vào MongoDB
        color_roles_collection.insert_one({
            "user_id": member.id,
            "guild_id": member.guild.id,
            "role_id": new_role.id,
            "role_name": new_role.name,
            "color": color
        })

        embed = discord.Embed(
            title="✅ Role màu đã được tạo",
            description=f"{member.mention} đã tạo role màu **{new_role.name}** với màu {color}.",
            color=discord_color
        )
        embed.set_footer(text="Truy cập https://www.color-hex.com/ để chọn màu.")
        # Phản hồi công khai cho mọi người cùng thấy
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Không thể tạo role: {str(e)}", ephemeral=True)

# Lệnh slash xóa role màu dựa trên dữ liệu trong MongoDB
@bot.tree.command(name="deletecolor", description="Xóa role màu mà bạn đã tạo")
async def deletecolor(interaction: discord.Interaction):
    member = interaction.user
    existing = color_roles_collection.find_one({"user_id": member.id, "guild_id": member.guild.id})
    if not existing:
        await interaction.response.send_message("Bạn không có role màu nào được tạo sẵn.", ephemeral=True)
        return
    role_to_delete = member.guild.get_role(existing["role_id"])
    if not role_to_delete:
        await interaction.response.send_message("Role của bạn không tồn tại.", ephemeral=True)
        color_roles_collection.delete_one({"user_id": member.id, "guild_id": member.guild.id})
        return
    try:
        await role_to_delete.delete(reason="Xóa role màu theo yêu cầu của người dùng")
        color_roles_collection.delete_one({"user_id": member.id, "guild_id": member.guild.id})
        await interaction.response.send_message("Role màu của bạn đã được xóa thành công.")
    except Exception as e:
        await interaction.response.send_message(f"Không thể xóa role của bạn: {e}", ephemeral=True)

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