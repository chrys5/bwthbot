#write a discord chat bot that responds to any message that is not "bwthb" with "BWTHB ONLY"

import discord
from discord.ext import commands, tasks
import json
import asyncio
from datetime import datetime, timedelta

TOKEN = "<INSERT TOKEN HERE>"
ADMIN_UID = "<INSERT ADMIN UID HERE>"
DEFAULT_WARNINGS = 3
DB_PATH = "database.json"

strip_uid = lambda uid: uid.replace("<", "").replace(">", "").replace("@", "").replace("!", "")

#initialize bot with all intents and command prefix "!"
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

#retrive data from database.json file
@bot.event
async def on_ready():
    print("Bot is ready")

@bot.event
async def on_member_join(member):
    data = json.loads(open(DB_PATH, "r").read())
    #initialize the user's name to their discord name and warnings to 3
    if not str(member.id) in data:
        await dox(str(member.id), member.name)

@bot.event
async def on_message(message):
    #delete my own messages after 30 seconds
    if message.author == bot.user:
        await asyncio.sleep(30)
        await message.delete()
        return
    
    if message.channel.name != "bwthb":
        await bot.process_commands(message)
        return
    
    uid = str(message.author.id)
    
    #if the message is not "bwthb" and the channel name is "bwthb", respond with "BWTHB ONLY"
    if message.channel.name == "bwthb":
        if message.content.lower() == "bwthb":
            #react with checkmark emoji
            await message.add_reaction("✅")
            return
        data = json.loads(open(DB_PATH, "r").read())
        data[uid][1] -= 1
        await message.delete()
        await message.channel.send("%s, BWTHB ONLY. You have %d warnings left." %(data[uid][0], data[uid][1]))
        if data[uid][1] <= 0:
            await message.channel.send("%s has been kicked." %(data[uid][0]))
            #kick user
            await message.author.kick()
            data[uid][1] = DEFAULT_WARNINGS
        with open(DB_PATH, "w") as f:
            json.dump(data, f, indent=2)

@bot.command()
async def setwarnings(ctx, uid, num_warnings):
    data = json.loads(open(DB_PATH, "r").read())
    uid = strip_uid(uid)
    try:
        data[uid][1] = int(num_warnings)
    except Exception:
        await ctx.send("Invalid input")
        return
    await ctx.send("Set %s's warnings to %s" %(data[uid][0], data[uid][1]))
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)
        
@bot.command()
async def getwarnings(ctx, uid):
    data = json.loads(open(DB_PATH, "r").read())
    uid = strip_uid(uid)
    if uid not in data:
        await ctx.send("Invalid user")
        return
    await ctx.send("%s has %d warnings" %(data[uid][0], data[uid][1]))

@bot.command()
async def dox(ctx, uid, new_name=None):
    data = json.loads(open(DB_PATH, "r").read())
    uid = strip_uid(uid)
    old_name = data[uid][0]
    if new_name:
        data[uid][0] = new_name
        await ctx.send("%s's name is now %s" %(old_name, new_name))
        with open(DB_PATH, "w") as f:
            json.dump(data, f, indent=2)
    else:
        await ctx.send(old_name)

@bot.command()
async def resetdatabase(ctx):
    data = {}
    if ctx.author.id != ADMIN_UID:
        return
    print("Bot refreshing database")
    for guild in bot.guilds:
        for member in guild.members:
            data[str(member.id)] = [member.name, DEFAULT_WARNINGS]
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

#get seconds until midnight EST
def seconds_until_midnight():
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return (midnight - now).seconds

#every midnight EST, check if bwthb has been said in the past 24 hours
@tasks.loop(seconds=30)
async def checkbwthb():
    await asyncio.sleep(seconds_until_midnight())
    #find channel named "bwthb"
    for guild in bot.guilds:
        for channel in guild.channels:
            if channel.name == "bwthb":
                #check if bwthb has been said in the past 24 hours
                async for message in channel.history(after=datetime.now() - timedelta(days=1)):
                    if message.content.lower() == "bwthb":
                        continue
                await channel.send("bwthbot is sad. No one said bwthb today :(")
    
@checkbwthb.before_loop
async def before_checkbwthb():
    await bot.wait_until_ready()

bot.run(TOKEN)