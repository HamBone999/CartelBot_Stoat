import random
import stoat
from stoat.ext import commands
from modules.ui import embed

ACCEPT, DECLINE = "✅", "❌"


class Coinflip(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank
        self.pending = {}  # message_id -> challenge state

    @commands.command(name="coinflip", aliases=["cf"])
    async def coinflip(self, ctx, member: stoat.User, amount: int):
        """Challenge a player to a 50/50 coinflip"""
        if amount < 100 or amount > 50_000:
            return await ctx.send("❌ Wager must be between **100** and **50,000** Pesos.")
        if getattr(member, "bot", None) or member.id == ctx.author.id:
            return await ctx.send("You can't challenge that!")

        await self.bank.open_acc(ctx.author)
        await self.bank.open_acc(member)
        ch = await self.bank.get_acc(ctx.author)
        op = await self.bank.get_acc(member)
        if ch[1] < amount:
            return await ctx.send("❌ You don't have enough Pesos.")
        if op[1] < amount:
            return await ctx.send(f"❌ {member.mention} doesn't have **{amount:,} Pesos** to match.")

        desc = (f"{ctx.author.mention} challenges {member.mention} to a coinflip for "
                f"**{amount:,} Pesos**!\n\n{member.mention}, react {ACCEPT} to accept or {DECLINE} to decline.")
        msg = await ctx.send(embeds=[embed(title="🪙 Coinflip Challenge", description=desc, color=0xf1c40f)])
        self.pending[msg.id] = {"challenger": ctx.author, "opponent": member, "amount": amount, "msg": msg}
        for e in (ACCEPT, DECLINE):
            try:
                await msg.react(e)
            except Exception:
                pass

    @commands.Gear.listener()
    async def on_reaction(self, event: stoat.MessageReactEvent):
        p = self.pending.get(event.message_id)
        if not p or event.user_id != p["opponent"].id:
            return
        emoji = str(getattr(event, "emoji", ""))
        self.pending.pop(event.message_id, None)
        try:
            await p["msg"].clear_reactions()
        except Exception:
            pass

        if emoji == DECLINE:
            return await p["msg"].edit(embeds=[embed(
                title="🪙 Coinflip Declined",
                description=f"{p['opponent'].mention} declined the coinflip.", color=0xe74c3c)])
        if emoji != ACCEPT:
            return

        challenger, opponent, amount = p["challenger"], p["opponent"], p["amount"]
        ch = await self.bank.get_acc(challenger)
        op = await self.bank.get_acc(opponent)
        if ch[1] < amount or op[1] < amount:
            return await p["msg"].edit(embeds=[embed(
                title="🪙 Coinflip Cancelled",
                description="❌ One of you doesn't have enough Pesos anymore.", color=0xe74c3c)])

        winner, loser = random.choice([(challenger, opponent), (opponent, challenger)])
        await self.bank.update_acc(loser, -amount)
        added, lost = await self.bank.add_to_wallet(winner, amount * 2)
        coin = "🟡 Heads" if random.random() < 0.5 else "⚪ Tails"

        desc = (f"Coin landed on **{coin}**\n\n"
                f"🏆 Winner: {winner.mention} — **+{added:,} Pesos**\n"
                f"💸 Loser: {loser.mention} — **-{amount:,} Pesos**")
        if lost > 0:
            desc += f"\n❗ Wallet cap — {lost:,} Pesos lost (winner's wallet was capped)"
        await p["msg"].edit(embeds=[embed(title="🪙 Coinflip Result", description=desc, color=0xffd700)])


async def setup(bot):
    await bot.add_gear(Coinflip(bot))
