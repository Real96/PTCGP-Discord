import discord, json
from discord.ui import View, Button

def load_bot_values(config_path):
    with open(config_path, 'r') as config:
        return json.load(config)

config = load_bot_values("bot_values.json")

destination_channel_id = config["destination_channel_id"]
role_ids = config["role_ids"]
role_emojis = config["role_emojis"]
group_emojis = config["group_emojis"]
ruby_group_id = config["ruby_group_id"]
sapphire_group_id = config["sapphire_group_id"]
image_url = config["image_url"]
footer_icon_url = config["footer_icon_url"]
bot_token = config["bot_token"]

intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.members = True
bot = discord.Client(intents=intents)

class RoleButton(Button):
    def __init__(self, role_name):
        super().__init__(label=f"{role_name}", emoji=role_emojis[role_name], style=discord.ButtonStyle.secondary)
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = guild.get_role(role_ids[self.role_name])
        member = interaction.user

        if role in member.roles:
            await interaction.response.send_message(
                f"{role_emojis[self.role_name]} {self.role_name} è già assegnato, cambia stato!",
                ephemeral=True
            )
        else:
            current_role = next(r for r in member.roles if r.id in role_ids.values())
            await member.remove_roles(current_role)
            await member.add_roles(role)
            await interaction.response.send_message(
                f"{role_emojis[self.role_name]} {self.role_name} assegnato!",
                ephemeral=True
            )

class RoleView(View):
    def __init__(self):
        super().__init__(timeout=None)

        for role_name in role_ids.keys():
            self.add_item(RoleButton(role_name))

async def count_role_members_by_group(guild):
    rubino_counts = {key: 0 for key in role_ids}
    zaffiro_counts = {key: 0 for key in role_ids}

    for member in guild.members:
        if discord.utils.get(member.roles, id=ruby_group_id):
            group_counts = rubino_counts
        elif discord.utils.get(member.roles, id=sapphire_group_id):
            group_counts = zaffiro_counts
        else:
            continue

        member_role_ids = {role.id for role in member.roles}

        for role_name, role_id in role_ids.items():
            if role_id in member_role_ids:
                group_counts[role_name] += 1

    return rubino_counts, zaffiro_counts

latest_sent_message = None

async def generate_button_embed(guild):
    rubino_counts, zaffiro_counts = await count_role_members_by_group(guild)
    embed = discord.Embed(
        title="Cambio Stati Reroll",
        color=0x2B2D31
    )

    embed.add_field(
        name="**Seleziona il tuo stato reroller**\n",
        value=(
            f"{role_emojis['Bot + Main ON']} **Bot + Main ON** → ricevi ed invii richieste.\n"
            f"{role_emojis['Bot ON']} **Bot ON** → non ricevi ma invii richieste.\n"
            f"{role_emojis['OFF']} **OFF** → non ricevi e non invii richieste."
        ),
        inline=False
    )

    embed.add_field(
        name=f"**{group_emojis[0]} Gruppo Rubino**",
        value=(
            f"{role_emojis['Bot + Main ON']}**: {rubino_counts['Bot + Main ON']}** utenti\n"
            f"{role_emojis['Bot ON']}**: {rubino_counts['Bot ON']}** utenti\n"
            f"{role_emojis['OFF']}**: {rubino_counts['OFF']}** utenti"
        ),
        inline=True
    )

    embed.add_field(
        name=f"**{group_emojis[1]} Gruppo Zaffiro**",
        value=(
            f"{role_emojis['Bot + Main ON']}**: {zaffiro_counts['Bot + Main ON']}** utenti\n"
            f"{role_emojis['Bot ON']}**: {zaffiro_counts['Bot ON']}** utenti\n"
            f"{role_emojis['OFF']}**: {zaffiro_counts['OFF']}** utenti"
        ),
        inline=True
    )

    embed.set_image(url=image_url)
    embed.set_footer(
        text="Free Rerollers",
        icon_url=footer_icon_url
    )
    return embed

async def update_embed(guild):
    channel = bot.get_channel(destination_channel_id)
    embed = await generate_button_embed(guild)
    await latest_sent_message.edit(embed=embed)

@bot.event
async def on_member_update(before, after):
    if before.roles != after.roles:
        guild = after.guild
        await update_embed(guild)

@bot.event
async def on_ready():
    global latest_sent_message
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

    guild = bot.guilds[0]
    channel = bot.get_channel(destination_channel_id)

    embed = await generate_button_embed(guild)
    view = RoleView()
    latest_sent_message = await channel.send(embed=embed, view=view)

bot.run(bot_token)
