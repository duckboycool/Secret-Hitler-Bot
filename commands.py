"""
Overall commands cog.
Loads in other cogs and manages cog reloading.
"""

import os, asyncio

import discord
from discord.ext import commands

class SecHitComms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Sechit Running")

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, cogName=None):
        print("Reloading Cogs")

        game = self.bot.get_cog('GameCommands')

        games = game.games

        if cogName:
            if f'cog_{cogName}.py' in os.listdir('./cogs'):
                print(f'Reloading cog {cogName}')

                self.bot.reload_extension(f'cogs.cog_{cogName}')

            else:
                await ctx.send(f'Did not find cog {cogName}.')
                return

        else:
            for cog in os.listdir('./cogs'):
                if cog.startswith('cog_'):
                    print(f'Reloading cog {os.path.splitext(cog)[0]}')

                    self.bot.reload_extension(f'cogs.{os.path.splitext(cog)[0]}')

        if not(cogName) or cogName == 'games':
            game = self.bot.get_cog('GameCommands')

            game._load(games)

        await ctx.send("Reloaded sucessfully.\n")


def setup(bot):
    bot.add_cog(SecHitComms(bot))

    for cog in os.listdir('./cogs'):
        if cog.startswith('cog_'): #Cog prefix
            print(f"Loading cog {os.path.splitext(cog)[0]}")

            bot.load_extension(f'cogs.{os.path.splitext(cog)[0]}') #Stripping .py from cog name
