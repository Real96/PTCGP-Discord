import discord, json, random
from discord.ext import commands
from discord import app_commands

def load_bot_values(config_path):
    with open(config_path, 'r') as config:
        return json.load(config)

config = load_bot_values("bot_values.json")

forum_id = config["forum_id"]
live_tag_id = config["live_tag_id"]
testing_tag_id = config["testing_tag_id"]
dedicated_channel_id = config["dedicated_channel_id"]
notify_role_id = config["notify_role_id"]

bot_token = config["bot_token"]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

image_links = [
    "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExNWx1Ym5iNmViZjh2d3VrYmllbjBsbnJ5amg2c3lnM2NlY2VoNnl1dCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/1cQMlSncDxzwc/giphy.gif",
    "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExbXFtbHgycHdscDF2MmV3dXUwaDQ3NXJjMWUydm8wMXc1MDMxYjY4diZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/tXPAH9cNL91Nm/giphy.gif",
    "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExZm01Y2JraWt0bjU3ZnFjYnlsZGZjMzltcnlpbDd3eTF1ZWlpOHg5ayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/TL0h9l7hdotF1O3pCv/giphy.gif",
    "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExZmthYWg5amVwMHVqejBvanR4NXV6aXM0dGdpZWFrb2FudmxreHJvNyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/I2nZMy0sI0ySA/giphy.gif",
    "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExMHNxemw3ZXdzbjZ5cGJ5ZjFvM2Z0ZjFwdWNoNmp6OXhkNzBuMGV5aSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3f8sk4CB0RtOU/giphy.gif"
]

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

@bot.tree.command(name="live", description="Aggiunge il tag 'live' al thread e inoltra un messaggio in un canale dedicato")
async def live(interaction: discord.Interaction):
    if not isinstance(interaction.channel, discord.Thread):
        await interaction.response.send_message(
            "Questo comando può essere usato solo all'interno di un thread del canale di test.",
            ephemeral=True
        )

        return

    thread: discord.Thread = interaction.channel
    thread_id = str(thread.parent.id)

    if thread_id not in forum_id:
        await interaction.response.send_message(
            "Questo comando può essere usato solo all'interno di un thread del canale di test.",
            ephemeral=True
        )

        return

    forum_tags = thread.parent.available_tags
    live_tag_obj = discord.utils.get(forum_tags, id=live_tag_id[thread_id])

    current_tags = thread.applied_tags or []
    filtered_tags = [tag for tag in current_tags if tag.id != testing_tag_id[thread_id]]
    
    if live_tag_obj in filtered_tags:
        await interaction.response.send_message("Il tag *live* è già presente in questo thread.", ephemeral=True)

        return

    new_tags = filtered_tags + [live_tag_obj]

    await thread.edit(applied_tags=new_tags)
    await interaction.response.send_message("Il tag *live* è stato aggiunto e il tag 'testing' è stato rimosso.", ephemeral=True)
    dedicated_channel = bot.get_channel(dedicated_channel_id)

    role_mention = f"<@&{notify_role_id[thread_id]}>"
    selected_image = random.choice(image_links)
    embed = discord.Embed(
        title="God Pack LIVE!!!",
        description=f"**→** {thread.jump_url}",
        color=discord.Color.dark_theme()
    )
    embed.set_thumbnail(url=selected_image)
    embed.set_footer(
        text="Free Rerollers",
        icon_url="https://media.discordapp.net/attachments/891642127753285663/1338921127963263026/LOGO.png?format=webp&quality=lossless&width=669&height=669"
    )
    await dedicated_channel.send(content=role_mention, embed=embed)

bot.run(bot_token)
