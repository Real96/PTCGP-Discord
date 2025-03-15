import discord, json, requests

def load_bot_values(config_path):
    with open(config_path, 'r') as config:
        return json.load(config)

config = load_bot_values("bot_values.json")


green_status = config["green_status"]
orange_status = config["orange_status"]
red_status = config["red_status"]
api_url = config["api_url"]
bot_token = config["bot_token"]

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_member_update(before, after):
    if len(before.roles) < len(after.roles):
        new_role = next(role for role in after.roles if role not in before.roles)

        if new_role.id == green_status or new_role.id == orange_status or new_role.id == red_status:
            data = {
                'id': str(after.id),
                'role': str(new_role.id)
            }

            response = requests.post(api_url, json=data)

client.run(bot_token)