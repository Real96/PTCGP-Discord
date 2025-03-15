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
bot_token = config["bot_token"]

intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.members = True
bot = discord.Client(intents=intents)

class RoleButton(Button):
    def __init__(self, role_name: str, bot):
        emoji = role_emojis.get(role_name, "")
        super().__init__(label=f"{role_name}", emoji=emoji, style=discord.ButtonStyle.secondary)
        self.role_name = role_name
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = guild.get_role(role_ids[self.role_name])
        member = interaction.user

        roles_to_remove = [guild.get_role(r) for r in role_ids.values() if r != role_ids[self.role_name]]
        await member.remove_roles(*roles_to_remove)

        if role in member.roles:
            await interaction.response.send_message(
                f"{role_emojis[self.role_name]} {self.role_name} è già assegnato, cambia stato!",
                ephemeral=True
            )
        else:
            await member.add_roles(role)
            await interaction.response.send_message(
                f"{role_emojis[self.role_name]} {self.role_name} assegnato!",
                ephemeral=True
            )

class RoleView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

        for role_name in role_ids.keys():
            self.add_item(RoleButton(role_name, bot))

async def count_role_members_by_group(guild):
    rubino_counts = {key: 0 for key in role_ids.keys()}
    zaffiro_counts = {key: 0 for key in role_ids.keys()}
    
    for member in guild.members:
        if any(role.id == ruby_group_id for role in member.roles):
            for role_name, role_id in role_ids.items():
                if discord.utils.get(member.roles, id=role_id):
                    rubino_counts[role_name] += 1
        elif any(role.id == sapphire_group_id for role in member.roles):
            for role_name, role_id in role_ids.items():
                if discord.utils.get(member.roles, id=role_id):
                    zaffiro_counts[role_name] += 1
    
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

    embed.set_image(url="https://pa1.aminoapps.com/7517/e4090edde65bcc73988fa6ac83bd22f2827e6507r1-500-233_hq.gif")
    embed.set_footer(
        text="Free Rerollers",
        icon_url="https://media.discordapp.net/attachments/891642127753285663/1338921127963263026/LOGO.png?format=webp&quality=lossless&width=669&height=669"
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
    view = RoleView(bot)
    latest_sent_message = await channel.send(embed=embed, view=view)

bot.run(bot_token)
