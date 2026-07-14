import traceback
from stoat.ext import commands


class Events(commands.Gear):
    """Global command-error logger. Prints tracebacks to the console and tells
    the user something went wrong (Stoat has no ephemeral, so it's a normal msg)."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Gear.listener()
    async def on_command_error(self, event: commands.CommandErrorEvent):
        ctx = getattr(event, "context", None) or getattr(event, "ctx", None)
        error = getattr(event, "error", None) or event
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        cmd = getattr(getattr(ctx, "command", None), "name", "?")
        author = getattr(ctx, "author", "?")
        print(f"\n❌ [ERROR] {cmd} by {author}:")
        traceback.print_exception(type(error), error, error.__traceback__)

        if ctx is not None:
            try:
                await ctx.send(f"❗ Something went wrong: `{error}`")
            except Exception:
                pass


async def setup(bot):
    await bot.add_gear(Events(bot))
