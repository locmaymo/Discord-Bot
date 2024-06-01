@bot.event
async def on_member_join(member):
    def check(m):
        return m.author == member and m.channel == channel

    channel = await member.create_dm()
    await channel.send("Trước khi tham gia server bạn cần trả lời câu hỏi sau lưu ý câu hỏi được viết để người nước ngoài khó đọc: Em. chai của m?_ẹ gọi l.à j?")

    for i in range(3):  # Cho phép người dùng thử lại 3 lần
        try:
            msg = await bot.wait_for('message', check=check, timeout=300.0)
            if msg.content.lower() == "cậu":
                role = discord.utils.get(member.guild.roles, name="😀 Member")
                await member.add_roles(role)
                await channel.send("Xác thực thành công! Bạn đã được cấp quyền truy cập.")
                return  # Người dùng đã trả lời đúng, thoát khỏi hàm
            else:
                await channel.send("Xác thực thất bại. Vui lòng thử lại.")
        except:
            await channel.send("Thời gian xác thực đã hết. Vui lòng thoát server rồi join để thử lại.")
            return  # Thời gian đã hết, thoát khỏi hàm

    # Nếu người dùng không trả lời đúng sau 3 lần thử, thông báo cho họ
    await channel.send("Bạn đã thử sai quá nhiều lần. Vui lòng tham gia lại bằng lời mời.")

bot.run(BOT_TOKEN)