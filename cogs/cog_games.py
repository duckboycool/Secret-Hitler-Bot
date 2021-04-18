"""
Cog for Secret Hitler games.
Manages joining, leaving, and starting games. Creates virtual games.
"""

import random

import discord
from discord.ext import commands

chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

roles = ['Liberal', 'Fascist', 'Hitler']

def update_status(bot, games={}):
    if len(games) == 0:
        return bot.change_presence(activity=discord.Game(f'No active games. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.idle)

    if len(games) == 1:
        return bot.change_presence(activity=discord.Game(f'1 active game. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.online)

    return bot.change_presence(activity=discord.Game(f'{len(games)} active games. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.online)

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
    def __init__(self, code, owner):
        self.code = code
        self.owner = owner

        self.players = [Player(owner)]

        self.started = False

    def playlist(self):
        mess = '\n>>> '

        for player in self.players:
            mess += player.me.name + '\n' #Might have name attribute later

        return mess
    
    def join(self, user):
        self.players.append(Player(user))

    def leave(self, player):
        self.players.remove(player)

    def start(self):
        fas = random.choices(self.players, k=(len(self.players) - 3) // 2)
        
        self.hit = fas[0]
        fas[0].start(2)

        self.fas = fas
        for fasplayer in fas[1:]:
            fasplayer.start(1)

        self.lib = {player for player in self.players if player not in fas} #Set, might want to change to list depending on use
        for libplayer in self.lib:
            libplayer.start(0)

        self.started = True


class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.games = {}

    def _load(self, data):
        self.games = data

    def _get_game(self, user):
        gamematch = [game for game in self.games.values() if user in {player.me for player in game.players}]

        if gamematch: #In a game
            return gamematch[0]

    @commands.command()
    async def create(self, ctx):
        game = self._get_game(ctx.author)

        if not(game):
            code = ''
            while code in self.games or not(code): #No duplicate codes
                code = ''.join(random.choices(chars, k=5))

            self.games[code] = Game(code, ctx.author)

            await ctx.send(f'Created game with code `{code}`.')

            await update_status(self.bot, self.games)
        
        else:
            await ctx.send('You are already in a game. Use the `leave` command to exit.')
    
    @commands.command()
    async def lobby(self, ctx):
        game = self._get_game(ctx.author)

        if game:
            await ctx.send(f'These are the players currently in your lobby.{game.playlist()}')
        
        else:
            await ctx.send('You are not currently in a lobby.')
    
    @commands.command()
    async def join(self, ctx, code=None):
        game = self._get_game(ctx.author)

        if game:
            await ctx.send('You are already in a game. Use the `leave` command to exit.')
            return

        if not(code): #No code given
            await ctx.send('No game code provided.')
            return

        if code.upper() not in self.games: #Code not found
            await ctx.send(f'Did not find game `{code}`.')
            return
        
        if self.games[code].started: #Game has started
            await ctx.send(f'Game `{code}` has already started.')
            return
        
        if len(self.games[code].players) >= 10: #Game is full
            await ctx.send(f'Game `{code}` is full.')
            return
        
        self.games[code].join(ctx.author)

        await ctx.send(f'Joined game `{code}`. Here is the current player list.{self.games[code].playlist()}')

    @commands.command()
    async def leave(self, ctx):
        game = self._get_game(ctx.author)

        if not(game):
            await ctx.send('You are not in a game.')
            return

        player = [player for player in game.players if player.me == ctx.author][0] #Get player
        
        #TODO: Handle different cases for leaving while in a game
        game.leave(player)
        await ctx.send(f'Successfully left room `{game.code}`.')

        if not(len(game.players)): #No more players
            del self.games[game.code] #Remove game

            await update_status(self.bot, self.games)


def setup(bot):
    bot.add_cog(GameCommands(bot))