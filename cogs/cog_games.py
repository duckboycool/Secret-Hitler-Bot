"""
Cog for Secret Hitler games.
Manages joining, leaving, and starting games. Creates virtual games.
"""

from discord.ext import commands

roles = ['Liberal', 'Fascist', 'Hitler']

class Player:
    def __init__(self, user):
        self.me = user

    def start(self, role):
        self.role = role

        if role == 0:
            self.liberal = True
        
        else:
            self.liberal = False

        

class Game:
    def __init__(self, code, user):
        self.code = code
        self.owner = user

        self.players = [Player(user)]


class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.games = {}

    def _load(self, data):
        self.games = data

    @commands.command()
    async def create(self, ctx):
        if 
    
    @commands.command()
    async def join(self, ctx):
        await ctx.send("Joining lobby.")

def setup(bot):
    bot.add_cog(GameCommands(bot))