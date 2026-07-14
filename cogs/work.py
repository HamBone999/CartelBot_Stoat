import random
import time
from stoat.ext import commands
from modules.bank_funcs import RANK_NAMES
from modules.ui import send_embed

JOBS = [
    ("ran a corner for the day",          400, 1200, 1.0),
    ("moved a brick across town",        1200, 2800, 0.9),
    ("drove a getaway for some guys",    1000, 2200, 0.9),
    ("intimidated a snitch into silence", 500, 1400, 1.0),
    ("robbed a bodega",                   800, 2000, 0.8),
    ("delivered to a Kingpin personally",2500, 4500, 0.3),
    ("scored a side hustle on craigslist",200,  900, 1.0),
    ("collected protection money",       1500, 3000, 0.7),
    ("babysat a stash house overnight",   900, 1900, 0.9),
    ("did a tattoo in the back of a bar", 400, 1100, 1.0),
]
BAD_OUTCOMES = [
    ("got pulled over and had to pay a bribe", 500, 1500),
    ("dropped your wallet running from the feds", 300, 1000),
    ("paid a guy who turned out to be a cop", 800, 1800),
]


class Work(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank
        self.inv = bot.db.inv
        self._cd: dict = {}

    @commands.command(name="work")
    async def work(self, ctx):
        """Hustle for cash (1 hour cooldown)"""
        uid, now, cd = ctx.author.id, time.time(), 3600
        remaining = cd - (now - self._cd.get(uid, 0))
        if remaining > 0:
            m, s = int(remaining) // 60, int(remaining) % 60
            return await ctx.send(f"⏳ You're burned out. Come back in **{m}m {s}s**.")
        self._cd[uid] = now

        await self.bank.open_acc(ctx.author)

        # 10% chance something goes wrong
        if random.random() < 0.10:
            desc, lo, hi = random.choice(BAD_OUTCOMES)
            loss = random.randint(lo, hi)
            users = await self.bank.get_acc(ctx.author)
            loss = min(loss, users[1])
            if loss > 0:
                await self.bank.update_acc(ctx.author, -loss)
            return await send_embed(
                ctx, title="😬 Bad day at work", description=f"You {desc}.",
                color=0xff0000, fields=[("Lost", f"**{loss:,} Pesos**")],
            )

        weights = [j[3] for j in JOBS]
        job = random.choices(JOBS, weights=weights, k=1)[0]
        desc, lo, hi, _ = job
        payout = random.randint(lo, hi)

        # Item + rank bonuses
        cookbook_mult = 1.20 if await self.inv.has_item(ctx.author, "cartel_cookbook") else 1.0
        rank_mult = await self.bank.get_rank_multiplier(ctx.author)
        final_payout = int(payout * cookbook_mult * rank_mult)

        added, lost = await self.bank.add_to_wallet(ctx.author, final_payout)
        new_xp, new_rank, leveled = await self.bank.award_xp(ctx.author, 10)

        fields = [
            ("Earned", f"**{added:,} Pesos**"),
            ("XP", "**+10**"),
            ("Multipliers", f"Rank x{rank_mult:.2f}" + (" • 📖 Cookbook x1.20" if cookbook_mult > 1 else "")),
        ]
        if lost > 0:
            fields.append(("❗ Wallet capped", f"Lost **{lost:,}** Pesos."))
        if leveled:
            fields.append(("🎉 RANKED UP", f"You're now a **{RANK_NAMES[new_rank]}**!"))
        await send_embed(ctx, title="💼 Day's work", description=f"You {desc}.", color=0x00ff88, fields=fields)


async def setup(bot):
    await bot.add_gear(Work(bot))
