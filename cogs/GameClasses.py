"""
File containing classes used for active games.
Loaded by game cog and then used.
"""

import random

roles = ['Liberal', 'Fascist', 'Hitler']
Liberal = 0
Fascist = 1
Hitler = 2

class Player:
    def __init__(self, game, user):
        self.game = game

        self.user = user
        self.name = user.name

        self.open = True #Can use commands (is not replying to game message)
    
    def send(self, *args, **kwargs):
        return self.user.send(*args, **kwargs)

    async def wait(self, bot, check=(lambda x: True), fail=None): #Takes in message check and fail message which is formatted with vars
        while True:
            message = await bot.wait_for('message', check=(lambda message: message.author == self.user))

            if check(message):
                return message
            
            else:
                if fail:
                    await self.send(fail.format_map(vars()))
    
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
        self.alive = self.players #Reference for now if needed before game starts

        self.started = False
    
    def _get_player(self, user):
        usermatch = [player for player in self.players if player.user == user]

        if usermatch: #User in game
            return usermatch[0]

    def playlist(self):
        mess = '\n>>> '

        for i, player in enumerate(self.alive):
            mess += f'**{i + 1}.** {player.name}\n'

        return mess
    
    def nextpres(self):
        index = self.players.index(self.president) + 1

        while self.players[index % len(self.players)] in self.lastgov:
            index += 1

        self.lastgov = [self.president, self.chancellor]

        self.president = self.players[index]
    
    async def votes(self, bot):
        unvoted = self.alive.copy() #Getting people who can vote

        voters = {'ja': [], 'nein': []}

        while unvoted:
            vote = await bot.wait_for('message', check=(lambda message: message.author in self.alive))

            if vote.content in voters: #Vote is ja or nein
                player = self._get_player(vote.author)
                voters[vote.content].append(player)
            
                unvoted.remove(player)

                
        
    def join(self, user):
        self.players.append(Player(self, user))

    def leave(self, player):
        self.players.remove(player)

    def start(self): #Handles whether game can start and begins game loop if so
        self.alive = self.players.copy() #Make list of alive players

        fas = random.choices(self.players, k=(len(self.players) - 1) // 2)
        
        print(fas) #Temp test

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

        self.president = random.choice(self.players) #Choose president randomly
        self.chancellor = None

        self.lastgov = [None, None] #No last elected government

        self.started = True

        self.first = True #First turn

        print(fas) #^^^