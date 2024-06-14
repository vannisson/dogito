import os
import discord
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Definir intents
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.reactions = True

# Classe do Cliente do Discord
class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role_message_id = 1249945213095378985  # ID da mensagem de reação
        self.emoji_to_role = {
            '✅': 1108027416418451587,  # ID do cargo associado ao emoji ✅
            '❌': 1110962059857899570,  # ID do cargo associado ao emoji ❌
        }

    async def on_ready(self):
        print(f'{self.user} está online! 🚀')
        print(f'ID: {self.user.id}')
        print('------------------------------')

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id != self.role_message_id:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            return

        role_id = self.emoji_to_role.get(payload.emoji.name)
        if role_id is None:
            return

        role = guild.get_role(role_id)
        if role is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        try:
            print(f'Adicionando cargo {role.name} a {member.name}')
            await member.add_roles(role)
        except discord.HTTPException as e:
            print(f'Erro ao adicionar cargo: {e}')

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id != self.role_message_id:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            return

        role_id = self.emoji_to_role.get(payload.emoji.name)
        if role_id is None:
            return

        role = guild.get_role(role_id)
        if role is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        try:
            print(f'Removendo cargo {role.name} de {member.name}')
            await member.remove_roles(role)
        except discord.HTTPException as e:
            print(f'Erro ao remover cargo: {e}')

# Inicializar cliente e rodar o bot
client = MyClient(intents=intents)
client.run(TOKEN)
