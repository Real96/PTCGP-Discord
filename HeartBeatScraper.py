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
group_emoji = config["group_emoji"]
bot_token = config["bot_token"]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Client(intents=intents)

class Reroller:
    def __init__(self, user_id, status, timestamp, instances, hours, minutes, packs, pph, boosters):
        self.user_id = user_id
        self.status = status
        self.timestamp = timestamp
        self.instances = instances
        self.hours = hours
        self.minutes = minutes
        self.packs = packs
        self.pph = pph
        self.boosters = boosters
        self.previous_packs = 0

    def update_values(self, user_id, status, timestamp, instances, hours, minutes, packs, pph, boosters):
        self.user_id = user_id
        self.status = status
        self.timestamp = timestamp
        self.instances = instances
        self.hours = hours
        self.minutes = minutes
        self.packs = packs
        self.pph = pph
        self.boosters = boosters

message_edit_timer = 20  # Message update frequency
offline_timer = 13 * 60  # 13 minutes offline threshold

user_messages = {}
latest_sent_message = None
total_packs, previous_total_packs = 0, 0

def add_boosters(counter, boosters):
    for name in boosters:
        if name in counter:
            counter[name] += 1

def get_member_status(user_id):
    member = bot.guilds[0].get_member(int(re.sub(r'[-+*/:]', '', user_id)))

    for role in member.roles:
        if str(role.id) in status_map:
            return status_map[str(role.id)]

async def reset_packs():
    global previous_total_packs

    current_time = datetime.datetime.now()

    if current_time.hour == 0 and current_time.minute == 0 and current_time.second == 0:
        previous_total_packs = total_packs

async def send_message_list():
    global latest_sent_message

    active_messages, message_list, total_instances, total_pph = {}, [], 0, 0

    for user_id, data in user_messages.items():
        if int(time.time()) - int(data.timestamp.split(":")[1]) <= offline_timer:
            data.status = get_member_status(user_id)

            if (data.user_id not in hidden_users or data.instances) and data.status != off_status and data.instances:
                active_messages[user_id] = data

    sorted_messages = sorted(active_messages.values(), key=lambda x: (status_order[x.status], -x.instances, -x.hours, -x.minutes))
    boosters_counter = {
        "Charizard": 0,
        "Mewtwo": 0,
        "Pikachu": 0,
        "Mew": 0,
        "Dialga": 0,
        "Palkia": 0,
        "Arceus": 0,
        "Shining": 0
    }

    for data in sorted_messages:
        total_instances += data.instances
        total_pph += data.pph
        instances_string = f"{data.instances} Instances" if data.instances > 2 else f"__**{data.instances} Instances**__"
        line = f"- {data.status} <@{re.sub(r'[-+*/:]', '', data.user_id)}>: {instances_string} | {data.packs} Packs | {data.hours:02d}:{data.minutes:02d} Hours | {data.pph} Packs/Hours"
        message_list.append(line)
        add_boosters(boosters_counter, data.boosters)

    message_content = (f"**Total: {len(sorted_messages)} Rollers | {total_instances} Instances | {total_packs - previous_total_packs} Packs | {total_pph} Packs/Hours** \n" + "\n".join(message_list))
    embed = discord.Embed(
        title=f"Monitor Stati Reroll - Gruppo Smeraldo {group_emoji}",
        description=message_content,
        color=0x2B2D31
    )
    embed.set_footer(
        text="\n".join(f"{name}: {boosters_counter[name]}" for name in boosters_counter)
    )

    if latest_sent_message:
        await latest_sent_message.edit(embed=embed)
    else:
        channel = bot.get_channel(destination_channel_id)
        latest_sent_message = await channel.send(message_content, allowed_mentions=discord.AllowedMentions(users=True))

@bot.event
async def on_ready():
    global latest_sent_message
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

    embed = discord.Embed(
        description="🔄 **Initializing...**",
        color=0x2B2D31
    )
    channel = bot.get_channel(destination_channel_id)
    latest_sent_message = await channel.send(embed=embed)
    reset_packs_task.start()
    send_message_list_task.start()

@bot.event
async def on_message(message):
    global user_messages, total_packs

    if message.author.id in webhook_id and message.channel.id == heart_beat_channel_id:
        lines = message.content.split("\n")

        if len(lines) < 7:
            return

        user_id = lines[0]
        status = get_member_status(user_id)
        timestamp = f"<t:{int(message.created_at.timestamp())}:R>"
        instances = len(re.findall(r'\d+', lines[1].strip()))
        minutes_packs = re.findall(r'\d+', lines[3].strip())
        total_minutes = int(minutes_packs[0])
        hours = int(minutes_packs[0]) // 60
        minutes = int(minutes_packs[0]) % 60
        packs = int(minutes_packs[1])
        pph = round(packs / total_minutes * 60) if total_minutes != 0 else 0
        boosters = [b.strip() for b in lines[6].replace("Select:", "").split(",")]

        if user_messages.get(user_id):
            user_messages[user_id].update_values(user_id, status, timestamp, instances, hours, minutes, packs, pph, boosters)
        else:
            user = Reroller(user_id, status, timestamp, instances, hours, minutes, packs, pph, boosters)
            user_messages[user_id] = user

        if user_messages[user_id].packs:
            total_packs += user_messages[user_id].packs - user_messages[user_id].previous_packs

        user_messages[user_id].previous_packs = user_messages[user_id].packs

@tasks.loop(seconds=1)
async def reset_packs_task():
    await reset_packs()

@tasks.loop(seconds=message_edit_timer)
async def send_message_list_task():
    await send_message_list()

bot.run(bot_token)
