import datetime
import discord
import re

from .tools.base_cog import BaseCog, commands
from .tools.utils import get_pseudo_random_color, get_median_color, get_app_id, role_request_id, zone_Moscow


class GameRolesManager(BaseCog):
    msg = None

    @commands.Cog.listener()
    async def on_ready(self):
        await self.delete_unused_roles()
        await self.delete_unused_emoji()

    async def get_gamerole_link_data(self, payload):
        user_is_bot = payload.user_id == self.bot.user.id
        emoji_id = payload.emoji.id
        if user_is_bot or not emoji_id:
            return
        associated_role = await self.execute_sql(
            f'''SELECT CreatedEmoji.role_id 
                    FROM CreatedEmoji
                        JOIN CreatedRoles 
                            USING(role_id)
                WHERE emoji_id = {emoji_id}''')
        if associated_role:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = guild.get_role(associated_role[0])
            return member, role

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        data = await self.get_gamerole_link_data(payload)
        if data:
            member, role = data
            member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        data = await self.get_gamerole_link_data(payload)
        if data:
            member, role = data
            member.remove_roles(role)

    async def sort_roles_by_quantity(self):
        guild = self.bot.create_channel.guild
        roles = guild.roles
        sorted_roles = sorted(roles, key=lambda r: len(r.members), reverse=True)
        for role in filter(lambda r: r.hoist, sorted_roles):
            role_exist = await self.execute_sql(f"SELECT role_id FROM CreatedRoles WHERE role_id = {role.id}")
            if role_exist:
                await role.edit(position=len(role.members) if len(role.members) > 0 else 1)

    async def add_gamerole(self, user):
        app_id, is_real = get_app_id(user)
        role_name = user.activity.name
        guild = user.guild
        created_role = await self.execute_sql(f"SELECT role_id FROM CreatedRoles WHERE app_id = {app_id}")
        if created_role:  # role already exist
            role = guild.get_role(created_role[0])  # get role
            if role not in user.roles:  # check user have these role
                await user.add_roles(role)
        elif user.activity.type != discord.ActivityType.custom:  # if status isn't custom create new role
            color = await self.create_activity_emoji(guild, app_id) if is_real else get_pseudo_random_color()
            if color.all():
                role = await guild.create_role(name=role_name, permissions=guild.default_role.permissions,
                                               colour=discord.Colour(1).from_rgb(*color), hoist=True,
                                               mentionable=True)
                await self.execute_sql(f"INSERT INTO CreatedRoles (app_id, role_id) VALUES ({app_id}, {role.id})")
                await user.add_roles(role)

    async def create_activity_emoji(self, guild, app_id):
        activity_info = await self.execute_sql(
            f'''SELECT name, icon_url
                FROM ActivitiesINFO
                    JOIN CreatedRoles cr on ActivitiesINFO.app_id = CreatedRoles.app_id
                WHERE app_id = {app_id}'''
        )
        if activity_info:
            name, thumbnail_url = activity_info
            name = re.compile('[^a-zA-Z0-9]').sub('', name)[:32]
            thumbnail_url = thumbnail_url[:-10]
            async with self.url_request(thumbnail_url) as response:
                content = await response.read()
            if content:
                emoji = await guild.create_custom_emoji(name=name, image=content)
                await self.execute_sql(
                    f"INSERT INTO CreatedEmoji (role_id, emoji_id) VALUES ((SELECT role_id FROM CreatedRoles WHERE app_id = {app_id}), {emoji.id})"
                )
                await self.add_gamerole_emoji(emoji.id)
                return get_median_color(content)
        return get_pseudo_random_color()

    async def delete_unused_roles(self):
        guild = self.bot.create_channel.guild
        roles = guild.roles
        cur_time = datetime.datetime.now(tz=zone_Moscow)
        for role in roles:
            if len(role.members) < 2 and (cur_time - role.created_at).days > 60:
                await self.execute_sql(f'''DELETE FROM CreatedRoles WHERE role_id = {role.id}''')
                await role.delete()

    async def delete_unused_emoji(self):
        channel = self.bot.get_channel(role_request_id)
        story = await channel.history(limit=None)
        if len(story) > 0:
            self.msg = story[0]
            guild = self.msg.guild
            for msg, reaction in ((msg, reaction) for msg in story for reaction in msg.reactions if reaction.emoji not in guild.emojis):
                await msg.remove_reaction(reaction.emoji, guild.get_member(self.bot.user.id))
                async with self.get_connection() as cur:
                    await cur.execute(f"DELETE FROM CreatedEmoji WHERE emoji_id = {reaction.emoji.id}")
        else:
            self.msg = await channel.send("Нажмите на иконку игры, чтобы получить соответствующую игровую роль!")

    async def add_gamerole_emoji(self, emoji_id):
        emoji = self.bot.get_emoji(emoji_id)
        try:
            await self.msg.add_reaction(emoji)
        except discord.errors.Forbidden:
            channel = self.msg.channel
            self.msg = await channel.send("Нажмите на иконку игры, чтобы получить соответствующую игровую роль!")
            await self.msg.add_reaction(emoji)


async def setup(bot):
    await bot.add_cog(GameRolesManager(bot))