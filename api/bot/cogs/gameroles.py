import asyncio
import datetime

import aiohttp
import discord
from discord.ext import tasks, commands
import re

from api.bot.mixins import BaseCogMixin
from api.bot.misc import get_pseudo_random_color, get_app_id, tzMoscow, get_dominant_color, user_is_playing

HANDLE_UNUSED_CONTENT_PERIOD = 60 * 60 * 3  # in seconds 3 hours


class GameRoles(BaseCogMixin):
    def __init__(self, bot):
        super(GameRoles, self).__init__(bot)
        bot.loop.create_task(self.remove_unused_activities_loop())
        self.remove_unused_activities_loop.start()

    @tasks.loop(seconds=HANDLE_UNUSED_CONTENT_PERIOD)
    async def remove_unused_activities_loop(self) -> None:
        await self.delete_unused_roles()
        # await self.delete_unused_emoji()

    @commands.Cog.listener()
    async def on_presence_update(self, _, after: discord.Member) -> None:
        if user_is_playing(after):
            await self.add_gamerole(after)

    async def manage_roles(self, payload: discord.RawReactionActionEvent, add_flag=True) -> tuple:
        user_is_bot = payload.user_id == self.bot.user.id
        emoji_id = payload.emoji.id
        if user_is_bot or not emoji_id:
            return

        role = self._client.get(f'v1/emoji/{emoji_id}/role')
        if not self._object_exist(role):
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = guild.get_role(role.id)

        if add_flag:
            await member.add_roles(role)
        else:
            await member.remove_roles(role)

        return member, role

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await self.manage_roles(payload, add_flag=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        await self.manage_roles(payload, add_flag=False)

    async def add_gamerole(self, user: discord.Member) -> None:
        app_id, is_real = get_app_id(user)
        role_name = user.activity.name
        guild = user.guild
        db_role = self._client.get(f'v1/role/byapp/{app_id}').json()
        if self._object_exist(db_role):  # role already exist
            role = guild.get_role(db_role['id'])  # get role
            if role and role not in user.roles:  # check user have these role
                try:
                    await user.add_roles(role)
                except discord.errors.Forbidden:
                    pass
        elif user.activity.type == discord.ActivityType.playing:  # if status isn't custom create new role
            role = await guild.create_role(name=role_name, permissions=guild.default_role.permissions,
                                           hoist=True, mentionable=True)
            await asyncio.sleep(10)
            self._client.post(f'v1/role/', json={'id': role.id, 'app_id': app_id})
            await self.create_activity_emoji(guild, app_id, role)
            await user.add_roles(role)

    async def create_activity_emoji(self, guild: discord.Guild, app_id: int, role: discord.Role) -> None:
        activity_info = self._client.get(f'v1/activity/{app_id}/info').json()
        if not activity_info:
            await role.edit(color=discord.Colour(1).from_rgb(*get_pseudo_random_color()))
            return
        name, thumbnail_url = activity_info['app_name'], activity_info['icon_url']
        cutted_name = re.compile('[^a-zA-Z0-9]').sub('', name)[:32]
        thumbnail_url = thumbnail_url[:-10]

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as response:
                content = await response.read()

        if content:
            dominant_color = get_dominant_color(content)
            emoji = await guild.create_custom_emoji(name=cutted_name, image=content)
            self._client.post(f'v1/emoji/', json={'id': emoji.id, 'role_id': role.id})
            await self.add_emoji_rolerequest(emoji.id, name)
            try:
                await role.edit(color=discord.Colour(1).from_rgb(*dominant_color), display_icon=content)
            finally:
                pass
            return
        await role.edit(color=discord.Colour(1).from_rgb(*get_pseudo_random_color()))

    async def add_emoji_rolerequest(self, emoji_id: int, app_name: str) -> None:
        emoji = self.bot.get_emoji(emoji_id)
        msg = await self.bot.request_channel.send(f'[{app_name}]')
        await msg.add_reaction(emoji)

    async def delete_unused_roles(self) -> None:
        """Delete role if it cant reach greater than 1 members for 60 days from creation moment"""
        guild = self.bot.create_channel.guild
        roles = guild.roles
        cur_time = datetime.datetime.now(tz=tzMoscow)
        for role in roles:
            if len(role.members) < 2 and (cur_time - role.created_at).days > 60:
                try:
                    await role.delete()
                except:
                    pass

    # async def delete_unused_emoji(self) -> None:
    #     """Clear emoji from request channel if it origin were deleted for some reason"""
    #     guild = self.bot.request_channel.guild
    #     async for msg, reaction in ((msg, reaction) async for msg in self.bot.request_channel.history(limit=None)
    #                           for reaction in msg.reactions if reaction.emoji not in guild.emojis):
    #         try:
    #             await msg.remove_reaction(reaction.emoji, guild.get_member(self.bot.user.id))
    #             await self.execute_sql(f"DELETE FROM CreatedEmoji WHERE emoji_id = {reaction.emoji.id}")
    #         except:
    #             pass


async def setup(bot):
    await bot.add_cog(GameRoles(bot))