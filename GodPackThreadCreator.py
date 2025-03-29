import json, discord, re

def load_bot_values(config_path):
    with open(config_path, 'r') as config:
        return json.load(config)

config = load_bot_values("bot_values.json")

tag_ids = config["tag_ids"]
testing_tag_id = config["testing_tag_id"]
webhook_id = config["webhook_id"]
god_pack_alert_channel_id = config["god_pack_alert_channel_id"]
destination_channel_ids = config["destination_channel_ids"]
bot_token = config["bot_token"]

message_pattern = re.compile(
    r"@(?P<user_id>\S+) .*\n"
    r"(?P<rerolling_name>[\w\d]+) \((?P<ig_user_id>\d+)\)\n"
    r"\[(?P<rare_cards>\d/5)]\[(?P<packs>\d+P)](?:\[(?P<booster>[\w\s]+) Booster])?  God pack found in instance: \d+\n"
    r"File name: (?P<file_name>.+\.xml)\n"
    r".*"
)

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

@bot.event
async def on_message(message):
    gp_channel_id = str(message.channel.id)

    if message.author.id not in webhook_id or gp_channel_id not in god_pack_alert_channel_id:
        return
    
    match = message_pattern.search(message.content)

    if match and len(message.attachments):
        rerolling_name = match.group("rerolling_name")
        ig_user_id = match.group("ig_user_id")
        rare_cards = match.group("rare_cards")
        packs = match.group("packs")
        member = message.mentions[0]

        thread_title = f"{rerolling_name} [{rare_cards}][{packs}]"
        thread_body = (f"**User**: {member.mention}\n**IGN**: {rerolling_name}\n**ID**: {ig_user_id}\n\n{message.jump_url}")
        embed = discord.Embed(
            title="VALID GOD PACK",
            description=thread_body,
            color=0x2B2D31
        )
        embed.set_image(url=message.attachments[0].url)
        destination_channel_id = destination_channel_ids[gp_channel_id]
        target_channel = bot.get_channel(destination_channel_id)

        if target_channel:
            tag_obj = [discord.Object(testing_tag_id[gp_channel_id]), discord.Object(tag_ids[gp_channel_id].get(rare_cards))]
            thread = await target_channel.create_thread(name=thread_title, embed=embed, applied_tags=tag_obj)

bot.run(bot_token)
