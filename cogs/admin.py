import stoat
from stoat.ext import commands
from base import Auth


class Admin(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank

    def _is_owner(self, ctx) -> bool:
        owner = str(getattr(self.bot, "owner_id", "") or "")
        cfg = str(Auth.OWNER_ID or "")
        uid = str(ctx.author.id)
        return uid == owner or (bool(cfg) and uid == cfg)

    @commands.command(name="addmoney")
    async def add_money(self, ctx, member: stoat.User, amount: int, mode: str = "wallet"):
        """[Owner] Add money to a member's account"""
        if not self._is_owner(ctx):
            return await ctx.send("You cannot use this command")
        mode = mode.lower()
        if mode not in ("wallet", "bank"):
            return await ctx.send("Mode must be `wallet` or `bank`.")
        if amount < 1 or amount > 100000:
            return await ctx.send("Amount must be between 1 and 100,000.")
        if getattr(member, "bot", None):
            return await ctx.send("You can't add money to a bot")
        await self.bank.open_acc(member)
        await self.bank.update_acc(member, +amount, mode)
        await ctx.send(f"Added **{amount:,}** to {member.mention}'s {mode}")

    @commands.command(name="removemoney")
    async def remove_money(self, ctx, member: stoat.User, amount: int, mode: str = "wallet"):
        """[Owner] Remove money from a member's account"""
        if not self._is_owner(ctx):
            return await ctx.send("You cannot use this command")
        mode = mode.lower()
        if mode not in ("wallet", "bank"):
            return await ctx.send("Mode must be `wallet` or `bank`.")
        if amount < 1:
            return await ctx.send("Amount must be at least 1.")
        if getattr(member, "bot", None):
            return await ctx.send("You can't remove money from a bot")
        await self.bank.open_acc(member)
        users = await self.bank.get_acc(member)
        current = users[2 if mode == "bank" else 1]
        if current < amount:
            return await ctx.send(f"You can only remove **{current:,}** from {member.mention}'s {mode}")
        await self.bank.update_acc(member, -amount, mode)
        await ctx.send(f"Removed **{amount:,}** from {member.mention}'s {mode}")

    @commands.command(name="resetuser")
    async def reset_user(self, ctx, member: stoat.User):
        """[Owner] Reset a member's account to zero"""
        if not self._is_owner(ctx):
            return await ctx.send("You cannot use this command")
        if getattr(member, "bot", None):
            return await ctx.send("Bots don't have an account")
        users = await self.bank.get_acc(member)
        if users is None:
            await self.bank.open_acc(member)
        else:
            await self.bank.reset_acc(member)
        await ctx.send(f"{member.mention}'s account has been reset")


async def setup(bot):
    await bot.add_gear(Admin(bot))
