import re
from contextlib import suppress
from io import BytesIO

import aiohttp
import discord
from discord import HTTPException
from discord.ext import commands
from PIL import Image
from cachetools import TTLCache


from ..mixins import BaseCogMixin


def get_dominant_color(
        raw_img: bytes,
        colors_num: int = 15,
        resize: int = 64
) -> tuple[int, int, int] | list:
    img = Image.open(BytesIO(raw_img))
    img = img.copy()
    img.thumbnail((resize, resize))
    paletted = img.convert('P', palette=Image.ADAPTIVE, colors=colors_num)
    palette = paletted.getpalette()
    color_counts = sorted(paletted.getcolors(), reverse=True)
    for i in range(colors_num):
        palette_index = color_counts[i][1]
        dominant_color = dc = tuple(
            palette[palette_index * 3:palette_index * 3 + 3])
        sq_dist = dc[0] * dc[0] + dc[1] * dc[1] + dc[2] * dc[2]
        if sq_dist > 8:  # drop too dark colors
            return dominant_color


class GameRoleHandlers(BaseCogMixin):

    def __init__(self, bot):
        super(GameRoleHandlers, self).__init__(bot)
        self.cache = TTLCache(maxsize=100,
                              ttl=2)  # cache stores items only 2 seconds

    async def manage_roles(self, payload: discord.RawReactionActionEvent,
                           add=True) -> tuple | None:
        user_is_bot = payload.user_id == self.bot.user.id
        emoji_id = payload.emoji.id
        if user_is_bot or not emoji_id:
            return

        role = await self.db.get_emoji_role(emoji_id)
        if not role:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = guild.get_role(role['id'])

        if add:
            await member.add_roles(role)
        else:
            await member.remove_roles(role)

        return member, role

    async def add_gamerole(self, user: discord.Member) -> None:
        app_id = self.get_app_id(user)
        if app_id and (role := await self.db.get_role(app_id)):
            # role already exist
            role = user.guild.get_role(role['id'])  # get role
            if role and role not in user.roles:  # check user haven't this role
                await user.add_roles(role)
        elif user.activity.type == discord.ActivityType.playing:
            # if status isn't custom create new role
            with suppress(TypeError, AttributeError):
                # discord unregistered activity
                await self.create_activity_role(user, app_id)

    async def create_activity_role(self, user: discord.Member,
                                   app_id: int) -> None:

        if not (activity_info := await self.db.get_activityinfo(app_id)):
            raise TypeError('Adding only a roles registered by discord API')

        name = re.compile('[^a-zA-Z0-9]').sub('', activity_info['app_name'])[:32]
        icon_url = activity_info['icon_url'][:-10]

        async with aiohttp.request('get', icon_url) as response:
            content = await response.read()

        if not content:
            raise TypeError('Adding only a roles registered by discord API')

        dominant_color = get_dominant_color(content)
        guild = user.guild

        kw = dict(
            name=user.activity.name,
            hoist=True,
            mentionable=True,
            display_icon=content,
            permissions=guild.default_role.permissions,
            color=discord.Color.from_rgb(*dominant_color)
        )
        try:
            role = await guild.create_role(**kw)
        except discord.errors.Forbidden:
            kw.pop('display_icon')
            role = await guild.create_role(**kw)

        await self.db.role_create(role.id, app_id)
        await user.add_roles(role)

        with suppress(HTTPException):
            emoji = await guild.create_custom_emoji(name=name, image=content)
            await self.db.emoji_create(emoji.id, role.id)
            await self.add_emoji_rolerequest(emoji, user.activity.name)

    async def add_emoji_rolerequest(self, emoji: discord.Emoji,
                                    app_name: str) -> None:
        msg = await self.bot.channel.request.send(f'[{app_name}]')
        await msg.add_reaction(emoji)


class GameRoles(GameRoleHandlers):

    @commands.Cog.listener()
    async def on_presence_update(self, _, after: discord.Member) -> None:
        if self.user_is_playing(after) and not self.cache.get(after.id):
            self.cache[after.id] = True
            await self.add_gamerole(after)

    @commands.Cog.listener()
    async def on_raw_reaction_add(
            self,
            payload: discord.RawReactionActionEvent
    ) -> None:
        await self.manage_roles(payload, add=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(
            self,
            payload: discord.RawReactionActionEvent
    ) -> None:
        await self.manage_roles(payload, add=False)


async def setup(bot):
    await bot.add_cog(GameRoles(bot))
