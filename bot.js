const { Client, Intents } = require('discord.js');
const BOT_TOKEN = process.env.BOT_TOKEN;

const client = new Client({
    intents: [
        Intents.FLAGS.GUILDS,
        Intents.FLAGS.GUILD_MEMBERS,
        Intents.FLAGS.GUILD_MESSAGES,
        Intents.FLAGS.MESSAGE_CONTENT
    ]
});

client.on('guildMemberAdd', async (member) => {
    const check = (m) => m.author.id === member.id && m.channel.id === dmChannel.id;
    const dmChannel = await member.createDM();
    await dmChannel.send("Trước khi tham gia server bạn cần trả lời câu hỏi sau, lưu ý câu hỏi được viết để người nước ngoài khó đọc: Em. chai của m?_ẹ gọi l.à j?");

    for (let i = 0; i < 3; i++) {
        try {
            const collected = await dmChannel.awaitMessages({
                filter: check,
                max: 1,
                time: 300000,
                errors: ['time']
            });

            const msg = collected.first();
            if (msg.content.toLowerCase() === "cậu") {
                const role = member.guild.roles.cache.find(role => role.name === "😀 Member");
                if (role) {
                    await member.roles.add(role);
                    await dmChannel.send("Xác thực thành công! Bạn đã được cấp quyền truy cập.");
                }
                return;
            } else {
                await dmChannel.send("Xác thực thất bại. Vui lòng thử lại.");
            }
        } catch (err) {
            await dmChannel.send("Thời gian xác thực đã hết. Vui lòng thoát server rồi join để thử lại.");
            return;
        }
    }

    await dmChannel.send("Bạn đã thử sai quá nhiều lần. Vui lòng tham gia lại bằng lời mời.");
});

client.login(BOT_TOKEN);
