import re
from contextlib import suppress
from io import BytesIO

import aiohttp
import discord
from discord.ext import tasks, commands
from PIL import Image

from ..mixins import BaseCogMixin


def get_dominant_color(raw_img, colors_num=5, resize=64) -> tuple[int, int, int] | list:
    img = Image.open(BytesIO(raw_img))
    img = img.copy()
    img.thumbnail((resize, resize))
    paletted = img.convert('P', palette=Image.ADAPTIVE, colors=colors_num)
    palette = paletted.getpalette()
    color_counts = sorted(paletted.getcolors(), reverse=True)
    colors = []
    for i in range(colors_num):
        palette_index = color_counts[i][1]
        dominant_color = dc = tuple(palette[palette_index * 3:palette_index * 3 + 3])
        sq_dist = dc[0] * dc[0] + dc[1] * dc[1] + dc[2] * dc[2]
        if sq_dist > 8:  # drop too dark colors
            colors.append(dominant_color)
    return colors[0]


class GameRoles(BaseCogMixin):
    def __init__(self, bot):
        super(GameRoles, self).__init__(bot)
        bot.loop.create_task(self.remove_unused_activities_loop())
        self.remove_unused_activities_loop.start()

    @tasks.loop(hours=3)
    async def remove_unused_activities_loop(self) -> None:
        await self.delete_unused_roles()

    @remove_unused_activities_loop.before_loop
    async def distribute_create_channel_members(self):
        guild = self.bot.guilds[0]
        for role in guild.roles:
            if ((db_role := await self.db.get_role_id(role.id)) and
                    not role.icon and
                    (info := self.db.get_activity_info(db_role['app_id']))):
                await role.edit(display_icon=info['icon_url'])

    @commands.Cog.listener()
    async def on_presence_update(self, _, after: discord.Member) -> None:
        if self.user_is_playing(after):
            await self.add_gamerole(after)

    async def manage_roles(self, payload: discord.RawReactionActionEvent, add=True) -> tuple | None:
        user_is_bot = payload.user_id == self.bot.user.id
        emoji_id = payload.emoji.id
        if user_is_bot or not emoji_id:
            return

        role = await self.db.get_emoji_role(emoji_id)
        if not role:
            return

        guild = self.db.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = guild.get_role(role.id)

        if add:
            await member.add_roles(role)
        else:
            await member.remove_roles(role)

        return member, role

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await self.manage_roles(payload, add=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        await self.manage_roles(payload, add=False)

    async def add_gamerole(self, user: discord.Member) -> None:
        app_id = self.get_app_id(user)
        guild = user.guild
        if role := await self.db.get_role(app_id):  # role already exist
            role = guild.get_role(role['id'])  # get role
            if role and role not in user.roles:  # check user haven't this role
                with suppress(discord.Forbidden):
                    await user.add_roles(role)
        elif user.activity.type == discord.ActivityType.playing:  # if status isn't custom create new role
            with suppress(TypeError):    # discord unregistered activity
                await self.create_activity_role(guild, app_id, user.activity.name)
                await self.db.role_create(role.id, app_id)
                await user.add_roles(role)

    async def create_activity_role(self, guild: discord.Guild, app_id: int, role_name: str) -> None:

        if not (activity_info := await self.db.get_activityinfo(app_id)):
            raise TypeError('Adding only a roles registered by discord API')

        name = re.compile('[^a-zA-Z0-9]').sub('', activity_info['app_name'])[:32]
        icon_url = activity_info['icon_url'][:-10]

        async with aiohttp.request('get', icon_url) as response:
            content = await response.read()

        if not content:
            raise TypeError('Adding only a roles registered by discord API')

        dominant_color = get_dominant_color(content)

        role = await guild.create_role(name=role_name,
                                       permissions=guild.default_role.permissions,
                                       hoist=True, mentionable=True,
                                       color=dominant_color,
                                       display_icon=content)

        emoji = await guild.create_custom_emoji(name=name, image=content)
        await self.add_emoji_rolerequest(emoji.id, name)
        await self.db.emoji_create(emoji.id, role.id)

    async def add_emoji_rolerequest(self, emoji_id: int, app_name: str) -> None:
        emoji = self.bot.emoji(emoji_id)
        msg = await self.bot.request_channel.send(f'[{app_name}]')
        await msg.add_reaction(emoji)

    async def delete_unused_roles(self) -> None:
        """Delete role if it cant reach greater than 1 member for 60 days from creation moment"""
        guild = self.bot.create_channel.guild

        roles = await self.db.get_all_roles()
        for db_role in roles:
            if not guild.get_role(db_role['id']):
                await self.db.role_delete(db_role['id'])
                print('Deleted ', db_role['id'])


async def setup(bot):
    await bot.add_cog(GameRoles(bot))
