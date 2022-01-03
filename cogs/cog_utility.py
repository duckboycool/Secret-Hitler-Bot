"""
Cog for owner utility commands.
Handles bot status and warnings.
"""

import discord
from discord.ext import commands, tasks
import time

embed_color = 0x59a2a1

def update_status(bot, games={}):
    if len(games) == 0:
        return bot.change_presence(activity=discord.Game(f'no games. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.idle)

    if len(games) == 1:
        return bot.change_presence(activity=discord.Game(f'1 game. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.online)

    return bot.change_presence(activity=discord.Game(f'{len(games)} games. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.online)

class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if self.status_reload.is_running(): self.status_reload.cancel()
        self.status_reload.start() # pylint: disable=no-member

        if self.clear_inactive.is_running(): self.clear_inactive.cancel()
        self.clear_inactive.start() # pylint: disable=no-member
    
    @tasks.loop(minutes=7.5)
    async def status_reload(self): #Update status periodically
        game = self.bot.get_cog('GameCommands')

        await update_status(self.bot, game.games)

    @tasks.loop(minutes=1)
    async def clear_inactive(self): #Remove game lobbies that have timed out
        games = self.bot.get_cog('GameCommands')

        for code in list(games.games):
            if games.games[code].timestamp < (time.time() - 60 * 45): #Last message more than 45 minutes ago
                for player in games.games[code].players:
                    await player.send('Your lobby has timed out and expired.')
                
                if games.games[code].started:
                    games.games[code].task.cancel()
                
                del games.games[code]

        await update_status(self.bot, games.games)
    
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

        for game in list(Game.games):
            for player in Game.games[game].players:
                await player.send(embed=embed)


def setup(bot):
    bot.add_cog(UtilityCommands(bot))