from stoat.ext import commands
from base import Auth
from modules.ui import send_embed


class Crew(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank

    @commands.command(name="createcrew")
    async def createcrew(self, ctx, *, name: str = ""):
        """Create a new crew (costs 50,000 Pesos)"""
        name = name.strip()
        if not (3 <= len(name) <= 20):
            return await ctx.send("Crew name must be 3–20 characters.")
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        if users[1] < 50000:
            return await ctx.send("❌ You need **50,000 Pesos** to create a crew!")
        if users[6] is not None:
            return await ctx.send(f"❌ You are already in a crew! Use `{Auth.COMMAND_PREFIX}leavecrew` first.")
        await self.bank.update_acc(ctx.author, -50000)
        await self.bank.update_acc(ctx.author, name, mode="crew")
        await ctx.send(f"🏴 **{name}** crew has been created!\nYou are now the leader.")

    @commands.command(name="joincrew")
    async def joincrew(self, ctx, *, name: str = ""):
        """Join an existing crew"""
        name = name.strip()
        if not name:
            return await ctx.send(f"Usage: `{Auth.COMMAND_PREFIX}joincrew <name>`")
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        if users[6] is not None:
            return await ctx.send(f"❌ You are already in a crew! Use `{Auth.COMMAND_PREFIX}leavecrew` first.")
        if not await self.bank.crew_exists(name):
            return await ctx.send(f"❌ No crew named **{name}** exists. Someone must create it first with `{Auth.COMMAND_PREFIX}createcrew`.")
        await self.bank.update_acc(ctx.author, name, mode="crew")
        await ctx.send(f"✅ You joined the **{name}** crew!")

    @commands.command(name="leavecrew")
    async def leavecrew(self, ctx):
        """Leave your current crew"""
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        if users[6] is None:
            return await ctx.send("❌ You are not in any crew.")
        await self.bank.update_acc(ctx.author, None, mode="crew")
        await ctx.send("✅ You have left your crew.")

    @commands.command(name="crew")
    async def crew(self, ctx):
        """Show your current crew info"""
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        crew_name = users[6]
        if crew_name is None:
            return await ctx.send(f"You are not in any crew.\nUse `{Auth.COMMAND_PREFIX}createcrew` or `{Auth.COMMAND_PREFIX}joincrew`")
        name = getattr(ctx.author, "display_name", None) or ctx.author.name
        await send_embed(ctx, title=f"🏴 {crew_name} Crew", color=0xff8800,
                         fields=[("Leader", name), ("Members", "1 (You)")])


async def setup(bot):
    await bot.add_gear(Crew(bot))
