"""
Overall commands cog.
Loads in other cogs and manages cog reloading.
"""

import os

import discord
from discord.ext import commands

def update_status(bot, games={}):
    if len(games) == 0:
        return bot.change_presence(activity=discord.Game(f'No active games. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.idle)

    if len(games) == 1:
        return bot.change_presence(activity=discord.Game(f'1 active game. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.online)

    return bot.change_presence(activity=discord.Game(f'{len(games)} active games. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.online)

class SecHitComms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Sechit Running")

        await update_status(self.bot)

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx):
        print("Reloading Cogs")

        game = self.bot.get_cog('GameCommands')

        games = game.games

        for cog in os.listdir('./cogs'):
            if cog.startswith('cog_'):
                print(f"Reloading cog {os.path.splitext(cog)[0]}")

                self.bot.reload_extension(f'cogs.{os.path.splitext(cog)[0]}')
        
        game = self.bot.get_cog('GameCommands')

        game._load(games)

        await ctx.send("Reloaded sucessfully.")

def setup(bot):
    bot.add_cog(SecHitComms(bot))

    for cog in os.listdir('./cogs'):
        if cog.startswith('cog_'): #Cog prefix
            print(f"Loading cog {os.path.splitext(cog)[0]}")

            bot.load_extension(f'cogs.{os.path.splitext(cog)[0]}') #Stripping .py from cog name