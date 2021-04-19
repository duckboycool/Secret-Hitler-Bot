"""
Main bot file for Secret Hitler discord bot.
Runs bot and loads in commands.
"""

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='', #Prefixless
                   intents=intents,
                   owner_id=251092222831755264,
                   case_insensitive=True,
                   help_command=None
)

bot.load_extension('commands') #Command extension that handles cogs

games = bot.get_cog('GameCommands') #For seeing who can use commands

def useropen(user): #Seeing if someone can use commands
    game = games._get_game(user)

    if not(game):
        return True
    
    return game._get_player(user).open

@bot.event
async def on_message(message):
    if not(isinstance(message.channel, discord.DMChannel)) or message.author.bot: #Only users in DMs
        return

    if not(useropen(message.author)): #Currently replying to bot in game
        return

    await bot.process_commands(message) #Process commands normally through bot class

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(error.args[0] + '.') #Error message passed (Command "command" is not found)
        return

    if isinstance(error, commands.NotOwner):
        await ctx.send('You cannot use this command.')
        return
    
    raise error

bot.run(open('token.txt').read())
