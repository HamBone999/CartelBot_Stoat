import time
from stoat.ext import commands
from base import Auth
from modules.ui import send_embed


class TrapHouseTycoon(commands.Gear):
    BASE_INCOME = 800
    NEW_SPOT_COST = 80_000
    BASE_UPGRADE = 12_000

    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank
        self.last_collect: dict = {}

    def _upgrade_cost(self, houses):
        return int(self.BASE_UPGRADE * (1.1 ** (houses - 1)))

    @commands.command(name="tycoon", aliases=["traptycoon"])
    async def tycoon(self, ctx):
        """Open your Trap House Tycoon empire"""
        houses, level = await self.bank.get_tycoon(ctx.author)
        income = self.BASE_INCOME * houses
        p = Auth.COMMAND_PREFIX
        fields = [
            ("🏠 Houses", f"**{houses}**"), ("📈 Level", f"**{level}**"),
            ("💵 Per 10 min", f"**{income:,}₱**"),
            ("🔨 Upgrade", f"**{self._upgrade_cost(houses):,}₱**"),
            ("🛒 New Spot", "**80,000₱**"), ("🎒 Cap Bonus", f"**+{houses*10_000:,}₱**"),
        ]
        await send_embed(ctx, title="🏠  Trap House Tycoon", color=0x16a085,
                         description=f"*Your empire of trap houses.*\nUse `{p}collect`, `{p}upgrade`, `{p}buyspot`.",
                         fields=fields)

    @commands.command(name="collect")
    async def collect(self, ctx):
        """Collect income from your trap houses (10-min cooldown)"""
        houses, _ = await self.bank.get_tycoon(ctx.author)
        now = time.time()
        last = self.last_collect.get(ctx.author.id, 0)
        if now - last < 600:
            r = int(600 - (now - last))
            return await ctx.send(f"⏳ **Cooldown active!** {r//60}m {r%60}s left.")
        self.last_collect[ctx.author.id] = now
        income = self.BASE_INCOME * houses
        await self.bank.update_acc(ctx.author, income)
        await ctx.send(f"💰 Collected **{income:,} Pesos** from your trap houses!")

    @commands.command(name="upgrade")
    async def upgrade(self, ctx):
        """Upgrade a trap house"""
        houses, level = await self.bank.get_tycoon(ctx.author)
        cost = self._upgrade_cost(houses)
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        if users[1] < cost:
            return await ctx.send(f"❌ You need **{cost:,} Pesos** to upgrade!")
        await self.bank.update_acc(ctx.author, -cost)
        await self.bank.update_tycoon(ctx.author, houses + 1, level + 1)
        await ctx.send(f"🏠 Trap House upgraded! You now have **{houses+1}** houses.")

    @commands.command(name="buyspot")
    async def buyspot(self, ctx):
        """Buy a new trap spot"""
        houses, level = await self.bank.get_tycoon(ctx.author)
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        if users[1] < self.NEW_SPOT_COST:
            return await ctx.send(f"❌ You need **{self.NEW_SPOT_COST:,} Pesos** for a new spot!")
        await self.bank.update_acc(ctx.author, -self.NEW_SPOT_COST)
        await self.bank.update_tycoon(ctx.author, houses + 1, level + 1)
        await ctx.send(f"🛒 New trap spot acquired! Total houses: **{houses+1}**")


async def setup(bot):
    await bot.add_gear(TrapHouseTycoon(bot))
