from numpy import random
from stoat.ext import commands


class Fun(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank

    @commands.command(name="roll")
    async def roll(self, ctx, amount: int):
        """High-risk dice gambling (1,000–15,000 Pesos)"""
        if amount < 1000 or amount > 15000:
            return await ctx.send("Bet must be between **1,000** and **15,000** Pesos.")
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        if users[1] < amount:
            return await ctx.send("You don't have enough money!")

        await self.bank.update_acc(ctx.author, -amount)  # take the bet first
        result = int(random.randint(1, 7))  # 1..6
        if result == 6:
            added, lost = await self.bank.add_to_wallet(ctx.author, int(amount * 3))
            msg = f"🎲 You rolled **6** → **JACKPOT!** You win **{added:,} Pesos** (3×) 🔥"
        elif result >= 4:
            added, lost = await self.bank.add_to_wallet(ctx.author, int(amount * 1.4))
            msg = f"🎲 You rolled **{result}** → Win! You get **{added:,} Pesos** (1.4×)"
        else:
            return await ctx.send(f"🎲 You rolled **{result}** → You lost **{amount:,} Pesos** 💸")
        if lost > 0:
            msg += f"\n❗ Wallet capped — {lost:,} Pesos lost."
        await ctx.send(msg)


async def setup(bot):
    await bot.add_gear(Fun(bot))
