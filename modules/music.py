import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import threading

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn -bufsize 64k -threads 4 -probesize 10M -analyzeduration 20M',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        except youtube_dl.DownloadError:
            return None
        
        if 'entries' in data:
            entries = data['entries']
        else:
            entries = [data]

        first_entry = entries.pop(0)
        if stream:
            source = cls(discord.FFmpegPCMAudio(first_entry['url'], **ffmpeg_options), data=first_entry)
        else:
            source = cls(discord.FFmpegPCMAudio(ytdl.prepare_filename(first_entry)), data=first_entry)
        
        return source, entries

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.current = None

    async def play_next(self, ctx):
        if self.queue:
            self.current = self.queue.pop(0)
            ctx.voice_client.play(self.current, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
            await ctx.send(f'>>> 📢 Now playing: {self.current.title}')
        else:
            self.current = None
            await ctx.send(">>> 💨 Queue ended. No more songs to play.")

    def load_remaining_songs(self, ctx, entries):
        for entry in entries:
            if ctx.voice_client is None:
                break  # Stop loading if the bot has disconnected
            source = YTDLSource(discord.FFmpegPCMAudio(entry['url'], **ffmpeg_options), data=entry)
            self.queue.append(source)
        asyncio.run_coroutine_threadsafe(ctx.send(">>> ✅ All songs in the playlist have been loaded."), self.bot.loop)

    @commands.hybrid_command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()

    @commands.hybrid_command(name="play", description="Plays a song from a URL")
    async def play(self, ctx, *, url):
        """Plays from a url and adds to queue"""
        async with ctx.typing():
            source, entries = await YTDLSource.from_url(url, loop=self.bot.loop)
            if not source:
                await ctx.send(">>> 🚫 Could not load the playlist or song.")
                return
            
            self.queue.append(source)
            await ctx.send(f'>>> 🎵 Added to queue: {source.title}')

        if not ctx.voice_client.is_playing() and not self.current:
            await self.play_next(ctx)

        if entries:
            threading.Thread(target=self.load_remaining_songs, args=(ctx, entries)).start()

    @commands.hybrid_command(name="pause", description="Pauses the current song")
    async def pause(self, ctx):
        """Pauses the current song"""
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(">>> ⏸ Paused the song")

    @commands.hybrid_command(name="resume", description="Resumes the current song")
    async def resume(self, ctx):
        """Resumes the current song"""
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send(">>> 👍 Resumed the song")

    @commands.hybrid_command(name="skip", description="Skips the current song")
    async def skip(self, ctx):
        """Skips the current song"""
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send(">>> ⏭ Skipped the song")

    @commands.hybrid_command(name="stop", description="Stops the current song and clears the queue")
    async def stop(self, ctx):
        """Stops the bot and clears the queue"""
        self.queue.clear()
        self.current = None
        ctx.voice_client.stop()
        await ctx.send(">>> 🤚 Stopped the music and cleared the queue")

    @commands.hybrid_command(name="leave", description="Leaves the voice channel")
    async def leave(self, ctx):
        """Disconnects the bot from the voice channel"""
        self.queue.clear()
        self.current = None
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
            await ctx.send(">>> 👋 Disconnected from the voice channel")

    @commands.hybrid_command(name="queue", description="Lists the songs in the queue")
    async def queue(self, ctx):
        """Lists the songs in the queue"""
        if self.current:
            queue_list = f'>>> ⭕ Now playing: {self.current.title}\n'
        else:
            queue_list = '>>> 💤 No song is currently playing.\n'

        if self.queue:
            queue_list += '\n'.join([f'{idx + 1}. {song.title}' for idx, song in enumerate(self.queue)])
        else:
            queue_list += "💀 The queue is empty."

        await ctx.send(queue_list)

    @commands.hybrid_command(name="clear", description="Clears the queue")
    async def clear(self, ctx):
        """Clears the queue"""
        self.queue.clear()
        await ctx.send(">>> 🧹 Cleared the queue")

    @commands.hybrid_command(name="remove", description="Remove the selected song")
    async def remove(self, ctx, index: int):
        """Removes a song from the queue by index"""
        index -= 1  # Adjust the index to match the list displayed to the user
        if 0 <= index < len(self.queue):
            removed = self.queue.pop(index)
            await ctx.send(f'>>> ⛔ Removed from queue: {removed.title}')
        else:
            await ctx.send(f'>>> 🚫 Invalid index: {index + 1}')

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send(">>> 🚫 You are not connected to a voice channel.")
                raise commands.CommandError("🚫 Author not connected to a voice channel.")

    @skip.before_invoke
    @pause.before_invoke
    @resume.before_invoke
    @stop.before_invoke
    @remove.before_invoke
    async def ensure_voice_playing(self, ctx):
        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            await ctx.send(">>> 🚫 Not playing any music right now.")
            raise commands.CommandError("🚫 Not playing any music right now.")
