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

        result = int(random.randint(1, 7))  # 1..6
        if result >= 5:
            profit = int(amount * 3.5)
            await self.bank.update_acc(ctx.author, profit)
            await ctx.send(f"🎲 You rolled **{result}** → **JACKPOT!** +**{profit:,} Pesos** 🔥")
        elif result >= 3:
            profit = int(amount * 1.8)
            await self.bank.update_acc(ctx.author, profit)
            await ctx.send(f"🎲 You rolled **{result}** → Nice! +**{profit:,} Pesos**")
        else:
            await self.bank.update_acc(ctx.author, -amount)
            await ctx.send(f"🎲 You rolled **{result}** → You lost **{amount:,} Pesos** 💸")


async def setup(bot):
    await bot.add_gear(Fun(bot))
