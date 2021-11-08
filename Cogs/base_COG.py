import discord
from discord.ext import commands

import asyncio
import aiohttp

import datetime
from time import time

import re
import os
import numpy as np

from random import randint, choice
from asyncio_extras import async_contextmanager

class Base_COG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{type(self).__name__} starts')


    @async_contextmanager
    async def get_connection(self):
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cur:
                yield cur
