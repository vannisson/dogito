import discord
from discord.ext import commands
from config import TOKEN, intents
from modules.music import Music
from modules.reaction_roles import ReactionRoles
import asyncio

class MyClient(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        await self.add_cog(Music(self))
        await self.add_cog(ReactionRoles(self))
        await self.tree.sync()

    async def on_ready(self):
        print(f'{self.user} is online! 🚀')
        print(f'ID: {self.user.id}')
        print('------------------------------')

# Initialize client and run the bot
client = MyClient(command_prefix=commands.when_mentioned_or("!"), intents=intents)

async def main():
    try:
        async with client:
            await client.start(TOKEN)
    except Exception as e:
        print(f'Error starting the bot: {e}')

asyncio.run(main())