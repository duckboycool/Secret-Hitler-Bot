"""
Cog for Secret Hitler games.
Manages joining, leaving, and starting games. Creates virtual games.
"""

import random, asyncio

import discord
from discord.ext import commands

chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

roles = ['Liberal', 'Fascist', 'Hitler']
Liberal = 0
Fascist = 1
Hitler = 2

def update_status(bot, games={}):
    if len(games) == 0:
        return bot.change_presence(activity=discord.Game(f'no games. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.idle)

    if len(games) == 1:
        return bot.change_presence(activity=discord.Game(f'1 game. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.online)

    return bot.change_presence(activity=discord.Game(f'{len(games)} games. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.online)

class Player:
    def __init__(self, game, user):
        self.game = game

        self.user = user
        self.name = user.name

        self.open = True #Can use commands (is not replying to game message)
    
    def send(self, *args, **kwargs):
        return self.user.send(*args, **kwargs)
    
    def teammates(self):
        return [player for player in self.game.players if player != self and player.liberal == self.liberal]

    def start(self, role):
        self.alive = True
        self.role = role

        self.hitler = False
        if role == Hitler:
            self.hitler = True
        
        if role == Liberal:
            self.liberal = True
        
        else:
            self.liberal = False

    

class Game:
    def __init__(self, code, owner):
        self.code = code
        self.owner = owner

        self.players = [Player(self, owner)]

        self.started = False
    
    def _get_player(self, user):
        usermatch = [player for player in self.players if player.user == user]

        if usermatch: #User in game
            return usermatch[0]

    def playlist(self):
        mess = '\n>>> '

        for i, player in enumerate(self.players):
            mess += f'**{i + 1}.** {player.name}\n'

        return mess
        
    def join(self, user):
        self.players.append(Player(self, user))

    def leave(self, player):
        self.players.remove(player)

    def start(self):
        fas = random.choices(self.players, k=(len(self.players) - 1) // 2)
        
        self.hit = fas[0]
        fas[0].start(Hitler)

        self.fas = fas
        for fasplayer in fas[1:]:
            fasplayer.start(Fascist)

        self.lib = {player for player in self.players if player not in self.fas} #Set, might want to change to list depending on use
        for libplayer in self.lib:
            libplayer.start(Liberal)

        self.deck = [Liberal] * 6 + [Fascist] * 11 #6 liberal policies and 11 fascist
        random.shuffle(self.deck)

        self.started = True

        self.first = True #First turn


class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.games = {}

    def _load(self, data):
        self.games = data

    def _get_game(self, user):
        gamematch = [game for game in self.games.values() if user in {player.user for player in game.players}]

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

        player = game._get_player(ctx.author)
        
        #TODO: Handle different cases for leaving while in a game
        game.leave(player)
        await ctx.send(f'Successfully left room `{game.code}`.')

        if not(len(game.players)): #No more players
            del self.games[game.code] #Remove game

            await update_status(self.bot, self.games)

    @commands.command()
    async def start(self, ctx):
        game = self._get_game(ctx.author)

        #Invalid cases
        if not(game):
            await ctx.send('You are not currently in a game. Join one with `join` or make one with `create`.')
            return

        if not(game.owner == ctx.author):
            await ctx.send('You are not the host of this game.')
            return

        #if game.started:
        #    await ctx.send('The game has already started.')
        #    return
        
        if len(game.players) < 5:
            await ctx.send('There are not enough players in the lobby to start a game.')
            return
        
        game.start()

        #Game loop
        while True:
            if game.first:
                for player in game.players:
                    await player.send('Welcome to Secret Hitler', file=discord.File('cogs/GameAssets/Banner.png'))
                
                await asyncio.sleep(1.5 - 0.1 * len(game.players)) #Delaying less with more users to send to

                for player in game.players:
                    await player.send(f'The players in your game are{game.playlist()}')

                #Hitler intro                
                await game.hit.send('Your role is **Hitler**.', file=discord.File('cogs/GameAssets/Hitler Card.png'))

                if len(game.hit.teammates()) == 1: #1 fascist and Hitler
                    await game.hit.send(f'Your fascist player is *{game.hit.teammates()[0].name}*. They know who you are, so you two should work together to enact 6 fascist policies or enact 3 fascist polices then elect you as Chancellor. However, you should stay inconspicuous as the fascists will lose if you die.', file=discord.File('cogs/GameAssets/Fascist Membership.png'))
                
                else: #2-3 fascists and Hitler
                    await game.hit.send(f'You will not know who the other *{len(game.hit.teammates())}* fascists are, but they will know who you are. You should be on the lookout for hints fascists might give to tell you who they are, then you should work with them to either enact 6 fascist polices or enact 3 fascist polices then get yourself elected as Chancellor. However, you should stay inconspicuous as the fascists will lose if you die.', file=discord.File('cogs/GameAssets/Fascist Membership.png'))

                #Fascist intros
                for fascist in game.hit.teammates():
                    await fascist.send('Your role is *fascist*.', file=discord.File('cogs/GameAssets/Fascist Card.png'))

                    if len(fascist.teammates()) == 1:
                        await fascist.send(f'The Hitler player is *{game.hit.name}*. The Hitler player will also know who you are. Work together to enact 6 fascist policies or elect Hitler as Chancellor after enacting 3.', file=discord.File('cogs/GameAssets/Fascist Membership.png'))
                    
                    elif len(fascist.teammates()) == 2:
                        await fascist.send(f'The Hitler player is *{game.hit.name}*, and your fellow fascist is *{[fas for fas in fascist.teammates() if fas.role == Fascist]}*. The Hitler player will not know who you two are, so you both will need to work together to enact 6 fascist policies or enact 3 fascist policies then elect Hitler Chancellor. You also possibly should try to alert Hitler to who you are without drawing attention.', file=discord.File('cogs/GameAssets/Fascist Membership.png'))
                    
                    else:
                        await fascist.send(f'The Hitler player is *{game.hit.name}*, and your fellow fascists are *{"* and *".join(fas.name for fas in fascist.teammates() if fas != game.hit)}*. The Hitler player will not know who any of you are, so you will all need to work together to enact 6 fascist policies or enact 3 fascist policies then elect Hitler Chancellor. You also possibly should try to alert Hitler to who you are without drawing attention.', file=discord.File('cogs/GameAssets/Fascist Membership.png'))

                #Liberal intros
                for liberal in game.lib:
                    await liberal.send('Your role is *liberal*.', file=discord.File('cogs/GameAssets/Liberal Card.png'))
                
                    if len(game.hit.teammates()) == 1:
                        await liberal.send("There is *one* fascist along with Hitler. They will both know who each other are. It's your job to stop them from either enacting 6 fascist policies or enacting 3 fascist policies and electing Hitler Chancellor. You should do your best to enact 5 liberal policies or kill Hitler, and make sure to be very careful about who is elected Chancellor once 3 fascist policies are enacted. Good luck.", file=discord.File('cogs/GameAssets/Liberal Membership.png'))
                    
                    else:
                        await liberal.send(f"There are *{len(game.hit.teammates())}* fascists along with Hitler. The fascists will know who Hitler is, but Hitler will not know who the fascists are. It's your job to stop them from either enacting 6 fascist policies or enacting 3 fascist polices and electing Hitler Chancellor. You should do your best to enact 5 liberal policies or kill Hitler, and make sure to be very careful about who it elected Chancellor once 3 fascist polices are enacted. Good luck.", file=discord.File('cogs/GameAssets/Liberal Membership.png'))
                
                await asyncio.sleep(2 - 0.1 * len(game.players))

            game.first = False #Turning off fuirst turn
            input()


def setup(bot):
    bot.add_cog(GameCommands(bot))
