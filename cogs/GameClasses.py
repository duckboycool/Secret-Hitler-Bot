"""
File containing classes used for active games.
Loaded by game cog and then used.
"""

import random

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

class Player:
    def __init__(self, game, user):
        self.game = game

        self.user = user

        self.name = user.name

        #Add discriminators if multiple players have the same name
        samenames = [player for player in game.players if player.name == self.name and player.user != user]

        if samenames:
            samenames[0].name = str(samenames[0].user) #Change found user as well

            self.name = str(self.user)

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
        return [player for player in self.game.players if player != self and player.team == self.team]

    def start(self, role):
        self.alive = True
        self.role = role

        self.hitler = False
        if role == Hitler:
            self.hitler = True
        
        if role == Liberal:
            self.team = Liberal
        
        else:
            self.team = Fascist

class Game:
    def __init__(self, code, owner):
        self.code = code
        self.owner = owner

        self.players = [] #Initialize for player init

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
    
    def nextpres(self, elected=True):
        index = self.alive.index(self.president) + 1

        if elected: #Don't update last government if not elected
            self.lastgov = [self.president, self.chancellor]

        self.chancellor = None #Clear chancellor until next one is chosen

        self.president = self.alive[index % len(self.alive)]

    def chaos(self): #Government thrown into chaos after 3 unsucessful
        self.instability = 0 #Reset tracker

        passed = self.deck.pop(0)

        self.passed[passed] += 1 #Pass top policy

        if len(self.deck) < 3:
            self.deck += self.discard
            random.shuffle(self.deck)

            self.discard = []

        self.lastgov = [None, None] #Return eligibility for Chancellor

        return passed

    def victorycheck(self): #Returns result, message or None for result
        if self.passed[Fascist] == 6: #Fascist win
            return (Fascist, 'There have been 6 Fascist policies passed, meaning that Fascists have won.')
        
        if self.passed[Liberal] == 5: #Liberal win
            return (Liberal, 'There have been 5 Liberal policies passed, meaning that Liberals have won.')
        
        return (None, None) #No victory

    def rolelist(self, result): #Gets rolelist showing winning team
        message = 'Congratulations to the winners.\n>>> '

        message += f'**{roles[result]}s** - Winners\n\n'

        if result == Liberal:
            message += '\n'.join([liberal.name for liberal in self.lib]) + '\n\n'

            message += '**Fascists**\n\n'
            message += f'{self.hit.name} - *Hitler*\n'
            message += '\n'.join([fascist.name for fascist in self.hit.teammates()])

        else:
            message += f'{self.hit.name} - *Hitler*\n'
            message += '\n'.join([fascist.name for fascist in self.hit.teammates()]) + '\n\n'

            message += '**Liberals**\n\n'
            message += '\n'.join([liberal.name for liberal in self.lib])
        
        return message
    
    async def votes(self, bot):
        unvoted = self.alive.copy() #Getting people who can vote

        voters = {'ja': [], 'nein': []}

        while unvoted:
            vote = await bot.wait_for('message', check=(lambda message: self._get_player(message.author) in unvoted))

            player = self._get_player(vote.author)

            if vote.content.casefold() in voters: #Vote is ja or nein
                voters[vote.content.casefold()].append(player)
            
                unvoted.remove(player)

                await player.send(f'Counted vote as *{vote.content.casefold()}*.')

                player.open = True
            
            else:
                await player.send('Vote not recognized. Make sure to vote with `ja` or `nein`.')
            
        message = 'The votes are in, and here is how everybody voted:\n'

        jas = len(voters['ja'])
        neins = len(voters['nein'])

        message += f'>>> **Ja** - *{jas}*' #Begin quote

        if voters['ja']: #Add whitespace if there is a ja voter
            message += '\n\n'
            message += '\n'.join(player.name for player in voters['ja'])

        message += f'\n\n**Nein** - *{neins}*\n\n'
        message += '\n'.join(player.name for player in voters['nein'])

        return (jas - neins, message) #Result, message

    def executive(self): #Return what executive power the President can use for enacting a Fascist policy (or None)
        if len(self.hit.teammates()) == 3:
            return [search, search, choose, shoot, shootv][self.passed[Fascist] - 1] #Get power for policy passed
        
        elif len(self.hit.teammates()) == 2:
            return [None, search, choose, shoot, shootv][self.passed[Fascist] - 1]
        
        else:
            return [None, None, examine, shoot, shootv][self.passed[Fascist] - 1]
        
    def join(self, user):
        self.players.append(Player(self, user))

    def leave(self, player):
        self.players.remove(player)

        if self.started: #Remove player from alive if started
            self.alive.remove(player)

    def start(self): #Handles whether game can start and begins game loop if so
        self.alive = self.players.copy() #Make list of alive players

        fas = random.sample(self.players, (len(self.players) - 1) // 2) #Get two random players to be Fascist

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

        self.discard = [] #Cards removed by government (to be shuffled back in when needed)

        self.passed = [0, 0] #Liberal, Fascist

        self.instability = 0

        self.president = random.choice(self.players) #Choose president randomly
        self.chancellor = None

        self.lastgov = [None, None] #No last elected government

        self.started = True

        self.first = True #First turn
    
    def reset(self): #Resets game to lobby state
        players = [Player(self, player.user) for player in self.players] #Store reset players

        self.__init__(self.code, self.owner) #Reset game

        self.players = players #Reset players
        self.alive = self.players
