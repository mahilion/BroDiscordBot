import discord
from discord.ext import commands

from youtube_dl import YoutubeDL
from utils import embed_send
from base_logger import logger

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # all the music related stuff
        self.is_playing = False

        # 2d array containing [song, channel]
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}

        self.vc = ""

    # searching the item on youtube
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                full = ydl.extract_info("ytsearch:%s" % item, download=False)
                logger.debug(full)
                info = full['entries'][0]
            except Exception:
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            # get the first url
            m_url = self.music_queue[0][0]['source']
            # embed = discord.Embed(title="Now Playing",
            #                      description=self.music_queue[0][0]['title'])
            # await embed_send(ctx, embed)
            # remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    # infinite loop checking
    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']

            # try to connect to voice channel if you are not already connected

            if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                self.vc = await self.music_queue[0][1].connect()
            else:
                await self.vc.move_to(self.music_queue[0][1])

            print(self.music_queue)
            embed = discord.Embed(title="Now Playing",
                                  description=self.music_queue[0][0]['title'])
            await embed_send(ctx, embed)
            # remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    @commands.command(aliases=['p'], help="Plays a selected song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)

        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            # you need to be connected so that the bot knows where to go
            embed = discord.Embed(title="Join voice channel and try again")
            await embed_send(ctx, embed)
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                embed = discord.Embed(title="Could not play song, try different keyword")
                await embed_send(ctx, embed)
            else:
                embed = discord.Embed(title="Song added to the queue")
                await embed_send(ctx, embed)
                self.music_queue.append([song, voice_channel])

                if self.is_playing == False:
                    await self.play_music(ctx)

    @commands.command(aliases=['q'], help="Displays the current songs in queue")
    async def queue(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += (str(i + 1) + ". " + self.music_queue[i][0]['title']) + "\n\n"

        print(retval)
        if retval != "":
            embed = discord.Embed(title="Playing Next",
                                  description=retval)
            await embed_send(ctx, embed)
        else:
            embed = discord.Embed(title="No music in queue")
            await embed_send(ctx, embed)

    @commands.command(aliases=['s'], help="Skips the current song being played")
    async def skip(self, ctx):
        if self.vc != "" and self.vc:
            self.vc.stop()
            # try to play next in the queue if it exists
            await self.play_music(ctx)


def setup(bot):
    bot.add_cog(Music(bot))
