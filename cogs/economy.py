import time
from numpy import random
from stoat.ext import commands


class Economy(commands.Gear):
    """Daily / weekly / monthly rewards. Stoat port of the Discord Economy cog."""

    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank
        self._daily_cd: dict = {}
        self._weekly_cd: dict = {}
        self._monthly_cd: dict = {}

    async def _do_reward(self, ctx, cd_dict, cd_seconds, lo, hi, label):
        uid, now = ctx.author.id, time.time()
        remaining = cd_seconds - (now - cd_dict.get(uid, 0))
        if remaining > 0:
            d = int(remaining) // 86400
            h = (int(remaining) % 86400) // 3600
            m = (int(remaining) % 3600) // 60
            parts = []
            if d:
                parts.append(f"{d}d")
            if h:
                parts.append(f"{h}h")
            if m or not parts:
                parts.append(f"{m}m")
            return await ctx.send(f"⏳ Come back in **{' '.join(parts)}**")
        cd_dict[uid] = now
        await self.bank.open_acc(ctx.author)
        base = int(random.randint(lo, hi))
        mult = await self.bank.get_rank_multiplier(ctx.author)
        final = int(base * mult)
        added, lost = await self.bank.add_to_wallet(ctx.author, final)
        msg = f"💵 {label}: **{added:,} Pesos** (base {base:,} • rank x{mult:.2f})"
        if lost > 0:
            msg += f"\n❗ Wallet capped — **{lost:,}** Pesos lost. Deposit more often."
        await ctx.send(msg)

    @commands.command(name="daily")
    async def daily(self, ctx):
        await self._do_reward(ctx, self._daily_cd, 86400, 600, 1300, "Daily")

    @commands.command(name="weekly")
    async def weekly(self, ctx):
        await self._do_reward(ctx, self._weekly_cd, 604800, 2800, 4800, "Weekly")

    @commands.command(name="monthly")
    async def monthly(self, ctx):
        await self._do_reward(ctx, self._monthly_cd, 2592000, 12000, 22000, "Monthly")


async def setup(bot):
    await bot.add_gear(Economy(bot))
