import random
from stoat.ext import commands
from modules.ui import send_embed

REELS = ["🍒", "🍋", "🔔", "🍀", "💎", "⭐"]
PAYOUTS_3 = {"⭐": 15.0, "💎": 8.0, "🍀": 5.0, "🔔": 3.0, "🍋": 2.5, "🍒": 2.0}
PAYOUT_2 = 1.2


class Slots(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank

    @commands.command(name="slots")
    async def slots(self, ctx, bet: int):
        """Spin the slot machine (200–25,000 Pesos)"""
        if bet < 200 or bet > 25_000:
            return await ctx.send("❌ Bet must be between **200** and **25,000** Pesos.")
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        if users[1] < bet:
            return await ctx.send("❌ You don't have enough Pesos!")

        await self.bank.update_acc(ctx.author, -bet)
        reels = [random.choice(REELS) for _ in range(3)]
        line = f"｜ {reels[0]} ｜ {reels[1]} ｜ {reels[2]} ｜"

        if reels[0] == reels[1] == reels[2]:
            mult = PAYOUTS_3[reels[0]]
            added, lost = await self.bank.add_to_wallet(ctx.author, int(bet * mult))
            color = 0xffd700
            title = f"🎰 JACKPOT! Triple {reels[0]}"
            result = f"You won **{added:,} Pesos** ({mult}x)!"
            if lost > 0:
                result += f"\n❗ Wallet cap hit — **{lost:,}** Pesos lost. Deposit more often!"
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            added, lost = await self.bank.add_to_wallet(ctx.author, int(bet * PAYOUT_2))
            color = 0x00ff88
            title = "🎰 Pair! Small win"
            result = f"You won **{added:,} Pesos** ({PAYOUT_2}x)"
            if lost > 0:
                result += f"\n❗ Wallet cap hit — **{lost:,}** Pesos lost."
        else:
            color = 0xff0000
            title = "🎰 No match — house wins"
            result = f"You lost **{bet:,} Pesos** 💸"

        await send_embed(ctx, title=title, color=color,
                         fields=[("Reels", line), ("Result", result)])


async def setup(bot):
    await bot.add_gear(Slots(bot))
