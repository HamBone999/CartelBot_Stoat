import stoat
import random
import time
from stoat.ext import commands
from modules.bank_funcs import RANK_NAMES
from modules.ui import send_embed


class Rob(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank
        self.inv = bot.db.inv
        self._cd: dict = {}

    @commands.command(name="rob")
    async def rob(self, ctx, member: stoat.User):
        """Try to rob another player (30 min cooldown)"""
        if getattr(member, "bot", None) or member.id == ctx.author.id:
            return await ctx.send("You can't rob that!")

        uid, now, cd = ctx.author.id, time.time(), 1800
        remaining = cd - (now - self._cd.get(uid, 0))
        if remaining > 0:
            m, s = int(remaining) // 60, int(remaining) % 60
            return await ctx.send(f"⏳ Heat's still on you. Wait **{m}m {s}s**.")

        await self.bank.open_acc(ctx.author)
        await self.bank.open_acc(member)
        await self.inv.open_acc(member)

        target_data = await self.bank.get_acc(member)
        target_wallet = target_data[1]
        if target_wallet < 500:
            return await ctx.send(f"💸 {member.mention} is broke — not worth the risk.")

        # Padlock blocks the rob, burns one lock
        if await self.inv.has_item(member, "padlock"):
            await self.inv.consume(member, "padlock", 1)
            self._cd[uid] = now
            return await send_embed(
                ctx, title="🔒 PADLOCKED!", color=0xffa500,
                description=f"You tried to rob {member.mention} but their wallet was **padlocked**! Lock broke off.")

        self._cd[uid] = now

        ski_mask = await self.inv.has_item(ctx.author, "ski_mask")
        lockpick = await self.inv.has_item(ctx.author, "lockpick_set")
        crowbar = await self.inv.has_item(ctx.author, "crowbar")
        success_rate = 0.45 + (0.10 if ski_mask else 0) + (0.10 if lockpick else 0) + (0.05 if crowbar else 0)

        bonus_lines = []
        if ski_mask:
            bonus_lines.append("🎭 Ski Mask: +10% success")
        if lockpick:
            bonus_lines.append("🔓 Lockpick: +10% success")
        if crowbar:
            bonus_lines.append("🔧 Crowbar: +5% success")

        if random.random() < success_rate:
            steal_pct = random.uniform(0.10, 0.30)
            stolen = min(int(target_wallet * steal_pct), 8000)
            await self.bank.update_acc(member, -stolen)
            added, lost = await self.bank.add_to_wallet(ctx.author, stolen)
            await self.bank.update_acc(ctx.author, 8, mode="heat")
            new_xp, new_rank, leveled = await self.bank.award_xp(ctx.author, 20)

            fields = [("Heat", "+8"), ("XP", "+20"), ("Success rate", f"{int(success_rate*100)}%")]
            if bonus_lines:
                fields.append(("Item bonuses", "\n".join(bonus_lines)))
            if lost > 0:
                fields.append(("❗ Wallet cap", f"**{lost:,}** Pesos lost"))
            if leveled:
                fields.append(("🎉 RANKED UP!", f"You're now a **{RANK_NAMES[new_rank]}**!"))
            await send_embed(ctx, title="🏴 Rob successful!", color=0x2ecc71,
                             description=f"You jumped {member.mention} and got away with **{added:,} Pesos**!",
                             fields=fields)
        else:
            fine = random.randint(800, 2500)
            users = await self.bank.get_acc(ctx.author)
            fine = min(fine, users[1])
            await self.bank.update_acc(ctx.author, -fine)
            await self.bank.update_acc(ctx.author, 15, mode="heat")
            fields = [("Heat", "+15"), ("Success rate", f"{int(success_rate*100)}%")]
            if bonus_lines:
                fields.append(("Item bonuses (applied)", "\n".join(bonus_lines)))
            await send_embed(ctx, title="🚨 Rob FAILED!", color=0xff0000,
                             description=f"{member.mention} pulled out a piece — you bolted but dropped **{fine:,} Pesos** running.",
                             fields=fields)


async def setup(bot):
    await bot.add_gear(Rob(bot))
