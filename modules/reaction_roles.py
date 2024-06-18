import discord
from discord.ext import commands
import json

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_message_id_to_roles = {}
        self.load_reaction_roles()

    def load_reaction_roles(self):
        with open('data/reaction_role.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            for entry in data['messages']:
                self.role_message_id_to_roles[entry['message_id']] = entry['roles']

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id not in self.role_message_id_to_roles:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        role_id = self.role_message_id_to_roles[payload.message_id].get(payload.emoji.name)
        if role_id is None:
            return

        role = guild.get_role(role_id)
        if role is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        try:
            print(f'Adding role {role.name} to {member.name}')
            await member.add_roles(role)
        except discord.HTTPException as e:
            print(f'Error adding role: {e}')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id not in self.role_message_id_to_roles:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        role_id = self.role_message_id_to_roles[payload.message_id].get(payload.emoji.name)
        if role_id is None:
            return

        role = guild.get_role(role_id)
        if role is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        try:
            print(f'Removing role {role.name} from {member.name}')
            await member.remove_roles(role)
        except discord.HTTPException as e:
            print(f'Error removing role: {e}')
