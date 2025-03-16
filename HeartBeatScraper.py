import json, discord, time, datetime, re
from discord.ext import tasks

def load_bot_values(config_path):
    with open(config_path, 'r') as config:
        return json.load(config)

config = load_bot_values("bot_values.json")

webhook_id = config["webhook_id"]
heart_beat_channel_id = config["heart_beat_channel_id"]
destination_channel_id = config["destination_channel_id"]
off_status = config["off_status"]
status_map = config["status_map"]
status_order = config["status_order"]
hidden_users = config["hidden_users"]
group_emojis = config["group_emojis"]
bot_token = config["bot_token"]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Client(intents=intents)

class Reroller:
    def __init__(self):
        self.user_id = 0
        self.timestamp = ""
        self.instances = 0
        self.status = off_status
        self.hours = 0
        self.minutes = 0
        self.packs = 0
        self.pph = 0
        self.previous_packs = 0

    def set_values(self, user_id, timestamp, instances, hours, minutes, packs, pph):
        self.user_id = user_id
        self.timestamp = timestamp
        self.instances = instances
        self.hours = hours
        self.minutes = minutes
        self.packs = packs
        self.pph = pph

    def set_previous_packs(self, packs):
        self.previous_packs = packs

message_edit_timer = 20  # Message update frequency
offline_timer = 60 * 33  # 33 minutes offline threshold

user_messages = {
    heart_beat_channel_id[0]: {},
    heart_beat_channel_id[1]: {}
}
latest_sent_message = {
    heart_beat_channel_id[0]: None,
    heart_beat_channel_id[1]: None
}
total_packs = {
    heart_beat_channel_id[0]: 0,
    heart_beat_channel_id[1]: 0
}
previous_total_packs = {
    heart_beat_channel_id[0]: 0,
    heart_beat_channel_id[1]: 0
}
message_title = {
    heart_beat_channel_id[0]: f"Monitor Stati Reroll - Gruppo Rubino {group_emojis[0]}",
    heart_beat_channel_id[1]: f"Monitor Stati Reroll - Gruppo Zaffiro {group_emojis[1]}"
}

async def reset_packs():
    global total_packs, previous_total_packs

    current_time = datetime.datetime.now()

    if current_time.hour == 0 and current_time.minute == 0 and current_time.second == 0:
        previous_total_packs[heart_beat_channel_id[0]] = total_packs[heart_beat_channel_id[0]]
        previous_total_packs[heart_beat_channel_id[1]] = total_packs[heart_beat_channel_id[1]]

async def send_message_list(index):
    global latest_sent_message, total_packs, previous_total_packs

    active_messages, message_list, total_instances, total_pph = {}, [], 0, 0

    for user_id, data in user_messages[index].items():
        if int(time.time()) - int(data.timestamp.split(":")[1]) <= offline_timer:
            member = bot.guilds[0].get_member(int(re.sub(r'[-+*/:]', '', data.user_id)))

            for role in member.roles:
                if str(role.id) in status_map:
                    data.status = status_map[str(role.id)]
                    break

            if not (data.user_id in hidden_users or data.status == off_status):
                active_messages[user_id] = data

    sorted_messages = sorted(active_messages.values(), key=lambda x: (status_order[x.status], -x.instances, -x.hours, -x.minutes))

    for data in sorted_messages:
        total_instances += data.instances
        total_pph += data.pph
        instances_string = f"{data.instances} Instances" if data.instances > 2 else f"__**{data.instances} Instances**__"
        line = f"- {data.status} <@{re.sub(r'[-+*/:]', '', data.user_id)}>: {instances_string} | {data.packs} Packs | {data.hours:02d}:{data.minutes:02d} Hours | {data.pph} Packs/Hours"
        message_list.append(line)

    message_content = (f"**Total: {len(sorted_messages)} Rollers | {total_instances} Instances | {total_packs[index] - previous_total_packs[index]} Packs | {total_pph} Packs/Hours** \n" + "\n".join(message_list))
    embed = discord.Embed(
        title= message_title[index],
        description=message_content,
        color=0x2B2D31
    )

    if latest_sent_message[index]:
        await latest_sent_message[index].edit(embed=embed)
    else:
        channel = bot.get_channel(destination_channel_id[index])
        latest_sent_message[index] = await channel.send(message_content, allowed_mentions=discord.AllowedMentions(users=True))

@bot.event
async def on_ready():
    global latest_sent_message
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

    embed = discord.Embed(
        description="🔄 **Initializing...**",
        color=0x2B2D31
    )
    channel_ruby = bot.get_channel(destination_channel_id[0])
    channel_sapphire = bot.get_channel(destination_channel_id[1])
    latest_sent_message[heart_beat_channel_id[0]] = await channel_ruby.send(embed=embed)
    latest_sent_message[heart_beat_channel_id[1]] = await channel_sapphire.send(embed=embed)
    reset_packs_task.start()
    send_message_list_task_1.start()
    send_message_list_task_2.start()

@bot.event
async def on_message(message):
    global user_messages, total_packs
    hb_channel_id = str(message.channel.id)

    if message.author.id in webhook_id and hb_channel_id in heart_beat_channel_id:
        lines = message.content.split("\n")

        if len(lines) < 4:
            return

        user_id = lines[0]
        timestamp = f"<t:{int(message.created_at.timestamp())}:R>"
        instances = len(re.findall(r'\d+', lines[1].strip()))
        minutes_packs = re.findall(r'\d+', lines[3].strip())
        total_minutes = int(minutes_packs[0])
        hours = int(minutes_packs[0]) // 60
        minutes = int(minutes_packs[0]) % 60
        packs = int(minutes_packs[1])
        pph = round(packs / total_minutes * 60) if total_minutes != 0 else 0

        if user_messages[hb_channel_id].get(user_id):
            user_messages[hb_channel_id][user_id].set_values(user_id, timestamp, instances, hours, minutes, packs, pph)
        else:
            user = Reroller()
            user.set_values(user_id, timestamp, instances, hours, minutes, packs, pph)
            user_messages[hb_channel_id][user_id] = user

        total_packs[hb_channel_id] += user_messages[hb_channel_id][user_id].packs - user_messages[hb_channel_id][user_id].previous_packs if user_messages[hb_channel_id][user_id].packs - user_messages[hb_channel_id][user_id].previous_packs >= 0 else user_messages[hb_channel_id][user_id].packs
        user_messages[hb_channel_id][user_id].previous_packs = user_messages[hb_channel_id][user_id].packs

@tasks.loop(seconds=1)
async def reset_packs_task():
    await reset_packs()

@tasks.loop(seconds=message_edit_timer)
async def send_message_list_task_1():
    await send_message_list(heart_beat_channel_id[0])

@tasks.loop(seconds=message_edit_timer)
async def send_message_list_task_2():
    await send_message_list(heart_beat_channel_id[1])

bot.run(bot_token)
