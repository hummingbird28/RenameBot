import logging, json, os

logging.basicConfig(level=logging.INFO)

from anitopy import parse
from decouple import config
from swibots import Client, BotContext, CommandEvent, BotCommand as RegisterCommand

BOT_TOKEN = config("BOT_TOKEN", default="")

app = Client(
    token=BOT_TOKEN
).set_bot_commands(
    [
        RegisterCommand("start", "Get Start message", True),
        RegisterCommand("rename", "Rename multiple file with format", True),
        RegisterCommand("renameone", "Rename the file with name you provide", True),
        RegisterCommand("parse", "parse the replied file and get parsed info", True),
    ]
)


@app.on_command("start")
async def onMessage(ctx: BotContext[CommandEvent]):
    event = ctx.event.message
    await event.reply_text(
        """Hi I can rename existing files based on format your provide!

*Example of Renaming*
Before:
file Name: `[Anime Time] One Piece - 0213 - Round 3! The Round-and-Round Roller Race!.mkv`\

Formats:
'episode_number': '0213'
'anime_title': 'One Piece'
'release_group': 'Anime Time'
'episode_title': 'Round 3! The Round-and-Round Roller Race!'

*Setting format*
/rename [@Switch] {episode_title} ({release_group}).{file_extension}
"""
    )


@app.on_command("parse")
async def renameBot(ctx: BotContext[CommandEvent]):
    m = ctx.event.message
    replied = await m.get_replied_message()
    if not (replied and replied.media_info):
        return await m.reply_text("Reply to a file")
    name = replied.media_info.description
    par = parse(name)
    await m.reply_text(json.dumps(par, indent=1))

@app.on_command("renameone")
async def renameOneBot(ctx: BotContext[CommandEvent]):
    event = ctx.event.message
    replied = await event.get_replied_message()
    if not (replied and replied.media_id):
        await event.reply_text("Reply to a media file!")
        return
    media = await app.get_media(replied.media_id)
    param = ctx.event.params
    file_name = media.description
    _, ext = os.path.splitext(file_name)
    if not param:
        return await event.reply_text("Provide a file name to rename!")
    n, et = os.path.splitext(param)
    if not et and not param.lower().endswith(ext):
        param += ext
    await media.edit(caption=param, description=param)
    await event.reply_text("Renamed!")


@app.on_command("rename")
async def renameBot(ctx: BotContext[CommandEvent]):
    event = ctx.event.message
    param = ctx.event.params
    if not param:
        return await event.reply_text("Provide a file format to rename!")
    if event.group_id:
        history = await ctx.get_group_chat_history(
            event.channel_id or event.group_id, event.community_id, page_limit=10000000
        )
    elif event.channel_id:
        history = await ctx.get_channel_chat_history(
            event.channel_id, event.community_id, page_limit=100000000
        )
    else:
        return await event.reply_text("Use this command in community!")
    msg = None
    if history.messages:
        msg = await event.reply_text("Started renaming!")
    for message in history.messages:
        if message.media_link:
            media = message.media_info
            description = media.description
            if not description:
                continue

            parsed = parse(description)
            try:
                for key in ["episode_number", "anime_title", "release_group", "episode_title", "file_extension"]:
                    if key not in parsed:
                        parsed[key] = ""
                new_name = param.format(**parsed)
                if parsed.get("file_extension") and not new_name.endswith(parsed['file_extension']):
                    new_name += "." + parsed['file_extension']
                await media.edit(caption=new_name, description=new_name)
            except KeyError as er:
                await event.reply_text("Invalid Format!")
                break
            except Exception as er:
                print(er)
    if msg:
        await msg.delete()


app.run()
