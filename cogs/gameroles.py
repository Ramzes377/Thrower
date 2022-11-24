import asyncio
import datetime
import discord
import re

from api.mixins import BaseCogMixin, commands, ConnectionMixin
from api.misc import get_pseudo_random_color, get_app_id, zone_Moscow, get_dominant_color, user_is_playing


class GameRoles(BaseCogMixin, ConnectionMixin):
    HANDLE_UNUSED_CONTENT_PERIOD = 60 * 60 * 3  # in seconds 3 hours

    def __init__(self, bot):
        super(GameRoles, self).__init__(bot)
        bot.loop.create_task(self.remove_unused_activities_loop())

    async def remove_unused_activities_loop(self) -> None:
        while True:
            await self.delete_unused_roles()
            await self.delete_unused_emoji()
            await asyncio.sleep(GameRoles.HANDLE_UNUSED_CONTENT_PERIOD)

    @commands.Cog.listener()
    async def on_presence_update(self, _, after: discord.Member) -> None:
        if user_is_playing(after):
            await self.add_gamerole(after)

    async def get_gamerole_link_data(self, payload: discord.RawReactionActionEvent) -> None:
        user_is_bot = payload.user_id == self.bot.user.id
        emoji_id = payload.emoji.id
        if user_is_bot or not emoji_id:
            return
        role_id = await self.execute_sql(
            f'''SELECT CreatedEmoji.role_id 
                    FROM CreatedEmoji
                        JOIN CreatedRoles 
                            USING(role_id)
                WHERE emoji_id = {emoji_id}''')
        if role_id:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = guild.get_role(role_id)
            return member, role

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        data = await self.get_gamerole_link_data(payload)
        if data:
            member, role = data
            await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        data = await self.get_gamerole_link_data(payload)
        if data:
            member, role = data
            await member.remove_roles(role)

    async def add_gamerole(self, user: discord.Member) -> None:
        app_id, is_real = get_app_id(user)
        role_name = user.activity.name
        guild = user.guild
        created_role = await self.execute_sql(f"SELECT role_id FROM CreatedRoles WHERE app_id = {app_id}")
        if created_role:  # role already exist
            role = guild.get_role(created_role)  # get role
            if role and role not in user.roles:  # check user have these role
                await user.add_roles(role)
        elif user.activity.type == discord.ActivityType.playing:  # if status isn't custom create new role
            role = await guild.create_role(name=role_name, permissions=guild.default_role.permissions,
                                           hoist=True, mentionable=True)
            await self.execute_sql(f"INSERT INTO CreatedRoles (app_id, role_id) VALUES ({app_id}, {role.id})")
            await self.create_activity_emoji(guild, app_id, role)
            await user.add_roles(role)

    async def create_activity_emoji(self, guild: discord.Guild, app_id: int, role: discord.Role) -> None:
        activity_info = await self.execute_sql(f'SELECT app_name, icon_url FROM ActivitiesINFO WHERE app_id = {app_id}')
        if not activity_info:
            await role.edit(color=discord.Colour(1).from_rgb(*get_pseudo_random_color()))
            return
        name, thumbnail_url = activity_info
        cutted_name = re.compile('[^a-zA-Z0-9]').sub('', name)[:32]
        thumbnail_url = thumbnail_url[:-10]
        async with self.url_request(thumbnail_url) as response:
            content = await response.read()
        if content:
            dominant_color = get_dominant_color(content)
            emoji = await guild.create_custom_emoji(name=cutted_name, image=content)
            await self.execute_sql(f"INSERT INTO CreatedEmoji (role_id, emoji_id) VALUES ({role.id}, {emoji.id})")
            await self.add_emoji_rolerequest(emoji.id, name)
            await role.edit(color=discord.Colour(1).from_rgb(*dominant_color), display_icon=content)
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
        cur_time = datetime.datetime.now(tz=zone_Moscow)
        for role in roles:
            if len(role.members) < 2 and (cur_time - role.created_at).days > 60:
                try:
                    await role.delete()
                    await self.execute_sql(f'DELETE FROM CreatedRoles WHERE role_id = {role.id}')
                except:
                    pass

    async def delete_unused_emoji(self) -> None:
        """Clear emoji from request channel if it origin were deleted for some reason"""
        guild = self.bot.request_channel.guild
        async for msg, reaction in ((msg, reaction) async for msg in self.bot.request_channel.history(limit=None)
                              for reaction in msg.reactions if reaction.emoji not in guild.emojis):
            try:
                await msg.remove_reaction(reaction.emoji, guild.get_member(self.bot.user.id))
                await self.execute_sql(f"DELETE FROM CreatedEmoji WHERE emoji_id = {reaction.emoji.id}")
            except:
                pass


async def setup(bot):
    await bot.add_cog(GameRoles(bot))

