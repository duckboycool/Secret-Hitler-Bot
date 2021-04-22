"""
Overall commands cog.
Loads in other cogs and manages cog reloading.
"""

import os

import discord
from discord.ext import commands, tasks

embed_color = 0x59a2a1

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

    @tasks.loop(minutes=30.0)
    async def status_reload(self): #Update status periodically
        await update_status(self.bot)

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

    @commands.command()
    @commands.is_owner()
    async def gamestatus(self, ctx):
        game = self.bot.get_cog('GameCommands')

        games = game.games

        await ctx.send(({game.code: (game.started, len(game.players)) for game in games.values()}))

    @commands.command()
    @commands.is_owner()
    async def warn(self, ctx, minutes=None):
        Game = self.bot.get_cog('GameCommands')

        embed = discord.Embed(
            title='Info',
            description=f"The bot will be restarted in {minutes if minutes else 'a few'} minutes. If you are playing a started game by then, the lobby will reset.",
            color=embed_color
        )

        embed.set_thumbnail(url='https://cdn.discordapp.com/avatars/691007847416201217/31b3c53065bdb536bc9d59d73f14a202.png?size=256')

        for game in Game.games:
            for player in Game.games[game].players:
                await player.send(embed=embed)


def setup(bot):
    bot.add_cog(SecHitComms(bot))

    for cog in os.listdir('./cogs'):
        if cog.startswith('cog_'): #Cog prefix
            print(f"Loading cog {os.path.splitext(cog)[0]}")

            bot.load_extension(f'cogs.{os.path.splitext(cog)[0]}') #Stripping .py from cog name
