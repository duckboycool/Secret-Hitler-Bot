"""
Cog for Secret Hitler games.
Manages joining, leaving, and starting games. Creates virtual games.
"""

import random, asyncio

import discord
from discord.ext import commands

#Ignore pylint import-error (extension loaded from path of main.py)
from cogs.GameClasses import Player, Game # pylint: disable=import-error

chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

#Role values
roles = ['Liberal', 'Fascist', 'Hitler']
Liberal = 0
Fascist = 1
Hitler = 2

#Powers
search = 1
choose = 2
examine = 3
shoot = 4
shootv = 5

ords = [None, 'first', 'second', 'third', 'fourth', 'fifth']

def update_status(bot, games={}):
    if len(games) == 0:
        return bot.change_presence(activity=discord.Game(f'no games. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.idle)

    if len(games) == 1:
        return bot.change_presence(activity=discord.Game(f'1 game. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.online)

    return bot.change_presence(activity=discord.Game(f'{len(games)} games. In {len(bot.guilds)} servers, and influencing governments of {len(bot.users)} people.'), status=discord.Status.online)


class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.games = {}

    def _load(self, data):
        self.games = data

        for game in data.values():
            game.reset() #Reset back to lobby

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

            self.games[code] = Game(code, ctx.author, self)

            await ctx.send(f'Created game with code `{code}`.')

            await update_status(self.bot, self.games)
        
        else:
            await ctx.send('You are already in a game. Use the `leave` command to exit.')
    
    @commands.command()
    async def lobby(self, ctx):
        game = self._get_game(ctx.author)

        if game:
            await ctx.send(f"These are the players currently {'alive' if game.started else 'in your lobby'}.{game.playlist()}")
        
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

        code = code.upper() #Capitalize code

        if code not in self.games: #Code not found
            await ctx.send(f'Did not find game `{code}`.')
            return
        
        if self.games[code].started: #Game has started
            await ctx.send(f'Game `{code}` has already started.')
            return
        
        if len(self.games[code].players) >= 10: #Game is full
            await ctx.send(f'Game `{code}` is full.')
            return

        game = self.games[code]

        game.join(ctx.author)

        joined = game._get_player(ctx.author)
        
        for player in game.players:
            if player != joined:
                await player.send(f'*{joined.name}* has joined the game.')

        await ctx.send(f'Joined game `{code}`. Here is the current player list.{game.playlist()}')

    @commands.command()
    async def leave(self, ctx):
        game = self._get_game(ctx.author)

        if not(game):
            await ctx.send('You are not in a game.')
            return

        player = game._get_player(ctx.author)

        if game.started and player.alive: #Alive in a current game
            if player in {game.president, game.chancellor}:
                await player.send('You cannot leave while you are a part of the current government. Wait for your term to finish.')
                return

            if player == game.hit: #Hitler leaves
                name = player.name

                game.leave(player)
                await ctx.send(f'Successfully left room `{game.code}`.')

                game.owner = game.players[0].user

                for player in game.players:
                    await player.send(f'Because the Hitler player (*{name}*) left the game, the Liberals have won.', file=discord.File(f'cogs/GameAssets/Liberal Win.png'))

                rolelist = game.rolelist(Liberal)
                    
                for player in game.players:
                    await player.send(rolelist)

                self.games[game.code].task.cancel()
                game.reset() #Reset to lobby

                return
            
            if all(alive.team for alive in game.alive if player != alive): #No more alive liberals
                name = player.name

                game.leave(player)
                await ctx.send(f'Successfully left room `{game.code}`.')

                game.owner = game.players[0].user

                for player in game.players:
                    await player.send(f'Because the last Liberal player (*{name}*) left the game, the Fascists have won.', file=discord.File(f'cogs/GameAssets/Fascist Win.png'))

                rolelist = game.rolelist(Fascist)
                    
                for player in game.players:
                    await player.send(rolelist)

                self.games[game.code].task.cancel()
                game.reset() #Reset to lobby

                return
            
            if len(game.players) <= 3: #Not enough players after leaving
                name = player.name

                game.leave(player)
                await ctx.send(f'Successfully left room `{game.code}`.')

                game.owner = game.players[0].user

                for player in game.players:
                    await player.send(f'Because *{name}* left the game, there are not enough players left to continue. Now, the top policies will be passed until one side wins.', file=discord.File(f'cogs/GameAssets/Fascist Tracker {game.passed[Fascist]}.png'))
                    await player.send(file=discord.File(f'cogs/GameAssets/Liberal Tracker {game.instability}-{game.passed[Liberal]}.png'))
                
                while not(game.victorycheck()[0]): #No winner yet
                    passed = game.chaos()

                    for player in game.players:
                        await player.send(f'A **{roles[passed]}** policy was passed into law.', file=discord.File(f'cogs/GameAssets/{roles[passed]} Article.png'))

                result, vicmessage = game.victorycheck()

                for player in game.players:
                    await player.send(vicmessage, file=discord.File(f'cogs/GameAssets/{roles[result]} Win.png'))
                
                rolelist = game.rolelist(Liberal)
                    
                for player in game.players:
                    await player.send(rolelist)

                self.games[game.code].task.cancel()
                game.reset() #Reset to lobby

                return

        name = player.name

        game.leave(player)

        await ctx.send(f'Successfully left room `{game.code}`.')

        for player in game.players:
            await player.send(f'*{name}* has left the game.')

        if not(len(game.players)): #No more players
            #Remove game
            if game.code in self.games:
                if game.started:
                    self.games[game.code].task.cancel()
                
                del self.games[game.code]

            await update_status(self.bot, self.games)
        
        else:
            game.owner = game.players[0].user #Reset owner

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

        if game.started:
            await ctx.send('The game has already started.')
            return
        
        if len(game.players) < 5:
            await ctx.send('There are not enough players in the lobby to start a game.')
            return
        
        game.start()

        task = self.bot.loop.create_task(self.gametask(game))

        game.task = task

    async def gametask(self, game): #Game loop
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
                        await fascist.send(f'The Hitler player is *{game.hit.name}*, and your fellow fascist is *{[fas.name for fas in fascist.teammates() if fas.role == Fascist][0]}*. The Hitler player will not know who you two are, so you both will need to work together to enact 6 fascist policies or enact 3 fascist policies then elect Hitler Chancellor. You also possibly should try to alert Hitler to who you are without drawing attention.', file=discord.File('cogs/GameAssets/Fascist Membership.png'))
                    
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

            #President picking Chancellor
            for player in game.players:
                if player != game.president:
                    await player.send(f"The {'first' if game.first else 'next'} president is **{game.president.name}**. Wait for their pick for Chancellor.")
            
            await game.president.send(f"You are the {'first' if game.first else 'next'} President. Choose who you want to nominate for Chancellor with these numbers.{game.playlist()}", file=discord.File('cogs/GameAssets/President.png'))
                            
            game.president.open = False #Disable commands during reply

            while True:
                pick = game.alive[int((await game.president.wait(self.bot, lambda message: message.content.isdigit() and int(message.content) in range(1, len(game.alive) + 1), 'Did not find player `{message.content}`. Make sure to pick using the above numbers.')).content) - 1]

                if pick == game.president:
                    await game.president.send('You cannot nominate yourself for Chancellor.')

                elif pick in game.lastgov:
                    if pick == game.lastgov[1]:
                        await game.president.send('You cannot nominate the last elected Chancellor.')

                    elif pick == game.lastgov[0] and len(game.alive) > 5:
                        await game.president.send('You cannot nominate the last elected President while there are more than 5 people alive.')
                    
                    else: #Special rule to allow last President to be elected Chancellor when there are 5 or less people alive
                        break
                
                else: #Valid Chancellor chosen
                    break

            game.chancellor = pick

            for player in game.alive:
                player.open = False

            #Notifying Chancellor choice
            await game.chancellor.send('The President chose you as their Chancellor nominee. Everybody, including you, will now vote with `ja` or `nein` on if they want your government.', file=discord.File('cogs/GameAssets/Chancellor.png'))
            await game.chancellor.send(file=discord.File('cogs/GameAssets/Votes.png'))

            for player in game.players:
                if player not in {game.president, game.chancellor}:
                    if player.alive:
                        await player.send(f'The President chose *{game.chancellor.name}* as their Chancellor nominee. Vote with `ja` or `nein` on if you want this government.', file=discord.File('cogs/GameAssets/Votes.png'))
                    
                    else:
                        await player.send(f'The President chose *{game.chancellor.name}* as their Chancellor nominee.')
                                
            await game.president.send(f'You chose *{game.chancellor.name}* as your Chancellor nominee. Everybody, including you, will now vote with `ja` or `nein` on if they want your government.', file=discord.File('cogs/GameAssets/Votes.png'))

            #Vote on government            
            result, votemessage = await game.votes(self.bot) #Result is net votes

            for player in game.players:
                await player.send(votemessage)
            
            if result > 0:
                if game.passed[Fascist] >= 3 and game.chancellor == game.hit: #At least 3 Fascist policies and Hitler elected Chancellor
                    for player in game.players:
                        await player.send('Hitler has been elected Chancellor after 3 Fascist polices were enacted, meaning that Fascists have won.', file=discord.File(f'cogs/GameAssets/Fascist Win.png'))
                    
                    rolelist = game.rolelist(Fascist)
                        
                    for player in game.players:
                        await player.send(rolelist)

                    break #Game end
                
                for player in game.players:
                    await player.send('The government has won the election and will now take office.')

                game.instability = 0

            else: #Government lost
                for player in game.players:
                    await player.send(f"{'The government has' if result < 0 else 'The vote has tied, so the government'} lost the election. The Presidency will now go to the next person, and the government will become less stable.")
                
                game.nextpres(False) #Don't update last government

                game.instability += 1

                if game.instability == 3:
                    for player in game.players:
                        await player.send("But first, because the government hasn't been able to be successfully elected in the past 3 elections, the country has plunged into chaos and the top policy from the deck will be passed.")
                    
                    passed = game.chaos()

                    for player in game.players:
                        await player.send(f'The populace passed a **{roles[passed]}** policy into law.', file=discord.File(f'cogs/GameAssets/{roles[passed]} Article.png'))

                game.first = False

                for player in game.players:
                    await player.send(file=discord.File(f'cogs/GameAssets/Fascist Tracker {game.passed[Fascist]}.png'))
                    await player.send(file=discord.File(f'cogs/GameAssets/Liberal Tracker {game.instability}-{game.passed[Liberal]}.png'))

                result, vicmessage = game.victorycheck()

                if result is not None:
                    for player in game.players:
                        await player.send(vicmessage, file=discord.File(f'cogs/GameAssets/{roles[result]} Win.png'))
                
                    rolelist = game.rolelist(Liberal)
                        
                    for player in game.players:
                        await player.send(rolelist)

                    break

                continue #Restart game loop
                
            await asyncio.sleep(1 - 0.05 * len(game.players))

            #Post trackers
            for player in game.players:
                await player.send(file=discord.File(f'cogs/GameAssets/Fascist Tracker {game.passed[Fascist]}.png'))
                await player.send(file=discord.File(f'cogs/GameAssets/Liberal Tracker {game.instability}-{game.passed[Liberal]}.png'))
            
            await game.chancellor.send('Wait for the President to pick the policy they want to remove before sending the other two over to you.')

            for player in game.players:
                if player not in {game.president, game.chancellor}:
                    await player.send('The government will now decide on which policy to enact. Wait for the President to pick a policy to remove.')
            
            game.president.open = False

            if game.passed[Fascist] == 5: #Veto power available
                await game.president.send('Since you are President, you will chose which policy from the top 3 policies you want to remove before sending the remaining ones to your Chancellor. **However, because 5 Fascist policies have been passed, if you your Chancellor calls for a veto after seeing their policies and you agree, you two can veto the policies.** Type the number of the policy you want to *remove* from the ones below.')
            
            else:
                await game.president.send('Since you are President, you will chose which policy from the top 3 policies you want to remove before sending the remaining ones to your Chancellor. Type the number of the policy you want to *remove* from the ones below.')

            #Pick policy to pass
            hand = [game.deck.pop(0) for i in range(3)]

            for i, article in enumerate(hand):
                await game.president.send(f'**{i + 1}.**', file=discord.File(f'cogs/GameAssets/{roles[article]} Article.png'))
            
            removed = int((await game.president.wait(self.bot, lambda message: message.content.isdigit() and int(message.content) in range(1, 4), 'Did not find policy `{message.content}`. Make sure to pick using the above numbers.')).content) - 1

            popped = hand.pop(removed)

            game.discard.append(popped)

            await game.president.send(f'Successfully removed a *{roles[popped]}* policy. The remaining articles will now be sent to your Chancellor.')

            game.president.open = True

            for player in game.players:
                if player not in {game.president, game.chancellor}:
                    await player.send('The President chose which policy to remove. Now wait for the Chancellor to pick which of the remaining policies to pass.')

            game.chancellor.open = False
            
            if game.passed[Fascist] == 5:
                await game.chancellor.send('The President chose which policy to remove. Now you have to choose which of the two following policies to enact into law. **However, because 5 Fascist policies have been passed, you can call for a veto, and if the President agrees you two can veto the policies.** Type the number of the policy you want to *enact*, or `veto`.')

            else:
                await game.chancellor.send('The President chose which policy to remove. Now you have to choose which of the two following policies to enact into law. Type the number of the policy you want to *enact*.')
            
            for i, article in enumerate(hand):
                await game.chancellor.send(f'**{i + 1}.**', file=discord.File(f'cogs/GameAssets/{roles[article]} Article.png'))

            if game.passed[Fascist] == 5:
                response = await game.chancellor.wait(self.bot, lambda message: (message.content.isdigit() and int(message.content) in range(1, 3)) or message.content.casefold() == 'veto', 'Did not find policy `{message.content}`. Make sure to pick using the above numbers, or type `veto` to veto.')

                if response.content.casefold() == 'veto': #Chancellor veto
                    await game.chancellor.send('You have chosen to veto this vote. If the President agrees to a veto, then all of the policies will be discarded.')

                    game.chancellor.open = True

                    for player in game.players:
                        if player not in {game.president, game.chancellor}:
                            await player.send('The Chancellor has decided to veto. Because 5 Fascist policies have been passed, if the President agrees to a veto, then all of the policies will be discarded.')

                    game.president.open = False

                    await game.president.send('The Chancellor has decided to veto. Reply with whether or not you want a veto.')

                    choice = await game.president.wait(self.bot, lambda message: message.content.casefold() in {'y', 'yes', 'n', 'no'}, 'Reply with yes or no on if you want the veto.')

                    if choice.content.casefold() in {'y', 'yes'}:
                        await game.president.send('The current policies have been vetoed.')

                        game.president.open = False

                        for player in game.players:
                            if player != game.president:
                                await player.send('The President agreed to the veto, so the current policies have been vetoed.')

                        game.instability += 1

                        if game.instability == 3:
                            for player in game.players:
                                await player.send("But first, because the government hasn't been able to successfully pass policy in the past 3 elections, the country has plunged into chaos and the top policy from the deck will be passed.")
                            
                            passed = game.chaos()

                            for player in game.players:
                                await player.send(f'The populace passed a **{roles[passed]}** policy into law.', file=discord.File(f'cogs/GameAssets/{roles[passed]} Article.png'))

                        game.first = False

                        for player in game.players:
                            await player.send(file=discord.File(f'cogs/GameAssets/Fascist Tracker {game.passed[Fascist]}.png'))
                            await player.send(file=discord.File(f'cogs/GameAssets/Liberal Tracker {game.instability}-{game.passed[Liberal]}.png'))

                        result, vicmessage = game.victorycheck()

                        if result is not None:
                            for player in game.players:
                                await player.send(vicmessage, file=discord.File(f'cogs/GameAssets/{roles[result]} Win.png'))
                        
                            rolelist = game.rolelist(Liberal)
                                
                            for player in game.players:
                                await player.send(rolelist)

                            break

                        game.nextpres()
                        continue #Restart game loop

                    else:
                        await game.president.send('You have rejected the veto, and the Chancellor will now choose one of the remaining policies normally.')

                        game.president.open = True

                        for player in game.players:
                            if player not in {game.president, game.chancellor}:
                                await player.send('The president has rejected the veto, and the Chancellor will now choose a policy normally.')

                        game.chancellor.open = False
                        
                        await game.chancellor.send('The President rejected your veto, and you will now have to choose a policy normally.')

                        passed = int((await game.chancellor.wait(self.bot, lambda message: message.content.isdigit() and int(message.content) in range(1, 3), 'Did not find policy `{message.content}`. Make sure to pick using the above numbers.')).content) - 1
                
                else:
                    passed = int(response.content) - 1
                        
            else:
                passed = int((await game.chancellor.wait(self.bot, lambda message: message.content.isdigit() and int(message.content) in range(1, 3), 'Did not find policy `{message.content}`. Make sure to pick using the above numbers.')).content) - 1

            game.discard.append(hand.pop(not(passed))) #Since articles are 0 and 1, not will give the one not chosen

            game.passed[hand[0]] += 1

            await game.chancellor.send(f'Successfully passed a *{roles[hand[0]]}* policy into law.')

            game.chancellor.open = True

            #Announce results
            for player in game.players:
                if player != game.chancellor:
                    await player.send(f'The government passed a **{roles[hand[0]]}** policy into law.', file=discord.File(f'cogs/GameAssets/{roles[hand[0]]} Article.png'))

            result, vicmessage = game.victorycheck()

            if result is not None:
                for player in game.players:
                    await player.send(vicmessage, file=discord.File(f'cogs/GameAssets/{roles[result]} Win.png'))
                
                rolelist = game.rolelist(Liberal)
                    
                for player in game.players:
                    await player.send(rolelist)

                break

            if len(game.deck) < 3: #Shuffle discard back if deck is too small
                game.deck += game.discard
                random.shuffle(game.deck)

                game.discard = []
            
            for player in game.players:
                await player.send('Here is the current state of the article trackers.', file=discord.File(f'cogs/GameAssets/Fascist Tracker {game.passed[Fascist]}.png'))
                await player.send(file=discord.File(f'cogs/GameAssets/Liberal Tracker {game.instability}-{game.passed[Liberal]}.png'))

            if hand[0] == Fascist:
                power = game.executive()

                if power == search:
                    await game.president.send(f'Because your government passed the {ords[game.passed[Fascist]]} Fascist policy, you now get to choose someone to search and find out their membership (Liberal or Fascist) with the numbers below.{game.playlist()}')

                    for player in game.players:
                        if player != game.president:
                            await player.send(f'Because the {ords[game.passed[Fascist]]} Fascist policy was passed, the President now gets to choose a player and find out their membership (Liberal or Fascist).')
                    
                    game.president.open = False

                    while True:
                        pick = game.alive[int((await game.president.wait(self.bot, lambda message: message.content.isdigit() and int(message.content) in range(1, len(game.alive) + 1), 'Did not find player `{message.content}`. Make sure to pick using the above numbers.')).content) - 1]

                        if pick == game.president:
                            await game.president.send('You cannot search yourself.')
                        
                        else:
                            break
                    
                    await game.president.send(f"*{pick.name}*'s membership is *{roles[pick.team]}*.", file=discord.File(f'cogs/GameAssets/{roles[pick.team]} Membership.png'))

                    game.president.open = True

                    for player in game.players:
                        if player != game.president:
                            if player == pick:
                                await player.send('The President chose to search **you**. Be careful, as the President may lie about what they saw.')
                            
                            else:
                                await player.send(f'The President chose to search *{pick.name}*. Wait to see what party the President claims they were.')
                
                elif power == choose:
                    await game.president.send(f'Because your government passed the {ords[game.passed[Fascist]]} Fascist policy, you now get to choose the next President with the numbers below.{game.playlist()}')

                    for player in game.players:
                        if player != game.president:
                            await player.send(f'Because the {ords[game.passed[Fascist]]} Fascist policy was passed, the President now gets to choose any other player to be the next President.')
                    
                    game.president.open = False

                    while True:
                        pick = game.alive[int((await game.president.wait(self.bot, lambda message: message.content.isdigit() and int(message.content) in range(1, len(game.alive) + 1), 'Did not find player `{message.content}`. Make sure to pick using the above numbers.')).content) - 1]

                        if pick == game.president:
                            await game.president.send('You cannot elect yourself.')
                        
                        else:
                            break

                    await game.president.send(f'*{pick.name}* is now the next President.')

                    game.president.open = True

                    for player in game.players:
                        if player != game.president:
                            if player == pick:
                                await player.send('The President chose to make **you** the next President')
                            
                            else:
                                await player.send(f'The President chose to make *{pick.name}* the next President.')
                    
                    #Set President
                    game.lastgov = [game.president, game.chancellor]
                    game.president = pick

                    #Next round without iterating president
                    game.first = False
                    continue

                elif power == examine:
                    await game.president.send(f'Because your government passed the {ords[game.passed[Fascist]]} Fascist policy, you now get to look at the next 3 policies.')

                    for player in game.players:
                        if player != game.president:
                            await player.send(f'Because the {ords[game.passed[Fascist]]} Fascist policy was passed, the President now gets to look at the next 3 policies.')
                    
                    for i, article in enumerate(game.deck[:3]):
                        await game.president.send(f'**{i + 1}.**', file=discord.File(f'cogs/GameAssets/{roles[article]} Article.png'))

                elif power in {shoot, shootv}:
                    await game.president.send(f"Because your government passed the {ords[game.passed[Fascist]]} Fascist policy, you must choose a different player to kill{'.' if power == shoot else ', and the government has now unlocked veto power.'}{game.playlist()}")

                    for player in game.players:
                        if player != game.president:
                            await player.send(f"Because the {ords[game.passed[Fascist]]} Fascist policy was passed, the President must choose a different player to kill{'.' if power == shoot else ', and the government has now unlocked veto power.'}")
                    
                    game.president.open = False
                    
                    while True:
                        pick = game.alive[int((await game.president.wait(self.bot, lambda message: message.content.isdigit() and int(message.content) in range(1, len(game.alive) + 1), 'Did not find player `{message.content}`. Make sure to pick using the above numbers.')).content) - 1]

                        if pick == game.president:
                            await game.president.send('Unfortunately, you cannot shoot yourself.')
                        
                        else:
                            break

                    game.alive.remove(pick) #Kill player

                    await game.president.send(f'You successfully executed *{pick.name}*.')

                    game.president.open = True

                    for player in game.players:
                        if player != game.president:
                            if player == pick:
                                await player.send("The President chose to execute **you**. Hopefully you aren't as much of a target next time. *Since you are dead, you should stop talking.*")

                                player.alive = False
                            
                            else:
                                await player.send(f'The President chose to execute *{pick.name}*.')

                    if game.hit == pick: #Killed Hitler
                        for player in game.players:
                            await player.send('Hitler has been executed by the President, and therefore, the Liberals win.', file=discord.File(f'cogs/GameAssets/Liberal Win.png'))

                        rolelist = game.rolelist(Liberal)
                            
                        for player in game.players:
                            await player.send(rolelist)
                        
                        break
            
            game.nextpres()

            game.first = False #Turning off first turn
    
        game.reset() #Reset game to lobby


def setup(bot):
    bot.add_cog(GameCommands(bot))
