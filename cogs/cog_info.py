"""
Cog for information commands.
Gives help message, rules, and credits.
"""

import discord
from discord.ext import commands

embed_color = 0x59a2a1

class InfoCommands(commands.Cog):
    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(
            title='Help',
            description='• **help** - This command.\n• **rules** - Sends a link to the rules of the game.\n• **credits** - Sends a message with the credits and legal info for the bot.\n• **create** - Creates a lobby with a randomly generated code.\n• **join** *code* - Joins a lobby with the specified code.\n• **leave** - Leaves the lobby you are currently in.\n• **lobby** - Send the current people in the lobby you are in.\n• **start** - Starts the game you are in. Can only be used by the creator of the lobby.',
            color=embed_color
        )

        embed.add_field(
            name='Additional Support',
            value='You can go to the [Secret Hitler Bot discord](https://discord.gg/kjD8DMJ) for more help, to report something, or to find people to play a game with.'
        )
        
        embed.set_thumbnail(url='https://cdn.discordapp.com/avatars/691007847416201217/31b3c53065bdb536bc9d59d73f14a202.png?size=256')

        await ctx.send(embed=embed)

    @commands.command()
    async def rules(self, ctx):
        embed = discord.Embed(
            title='Rules',
            description='The [Secret Hitler website](https://www.secrethitler.com/) has [a pdf](https://secrethitler.com/assets/Secret_Hitler_Rules.pdf) of the rules to view.\n\nIf you are still confused, there are videos online of the game you could watch to get an understanding of how it is played.',
            color=embed_color
        )
        
        embed.set_thumbnail(url='https://cdn.discordapp.com/avatars/691007847416201217/31b3c53065bdb536bc9d59d73f14a202.png?size=256')

        await ctx.send(embed=embed)

    @commands.command()
    async def credits(self, ctx):
        embed = discord.Embed(
            title='Credits',
            description='This bot was made by duckboycool#7682.\n\nAll art and gameplay concepts used by this bot are from [Secret Hitler](https://www.secrethitler.com/). (© 2016–2021 GOAT, WOLF, & CABBAGE)\n\nSecret Hitler was illustrated by Mac Schubert, and designed by Mike Boxleiter, Tommy Maranges, and Max Temkin.\n\nThis bot is adapted from Secret Hitler under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 liscence](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode), which the bot is also under.',
            color=embed_color
        )
        
        embed.set_thumbnail(url='https://cdn.discordapp.com/avatars/691007847416201217/31b3c53065bdb536bc9d59d73f14a202.png?size=256')

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(InfoCommands(bot))
