import random
from stoat.ext import commands
from modules.ui import send_embed

# item -> short label (shown in the help list since Stoat has no choice menus)
USABLE = {
    "bleach": "🧴 Bleach (-25 heat)",
    "burner_barrel": "🔥 Burner Barrel (-15 heat)",
    "dirty_cop_badge": "🪪 Dirty Cop Badge (-50 heat)",
    "fake_passport": "🛂 Fake Passport (reset heat to 0)",
    "mystery_package": "📫 Mystery Package (random reward)",
    "sus_backpack": "🎒 Sus Backpack (50/50 risk)",
    "narco_prayer_candle": "🙏 Narco Prayer Candle (+5 XP)",
    "blood_money_case": "💼 Blood Money Case (open for cash)",
    "counterfeit_bills": "💵 Counterfeit Bills (try to spend)",
}


class Items(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank
        self.inv = bot.db.inv

    @commands.command(name="use")
    async def use(self, ctx, *, item: str = ""):
        """Use a consumable item from your inventory"""
        item = item.lower().strip().replace(" ", "_")
        if item not in USABLE:
            listing = "\n".join(f"• `{k}` — {v}" for k, v in USABLE.items())
            return await ctx.send(f"Usable items:\n{listing}")
        if not await self.inv.has_item(ctx.author, item):
            return await ctx.send(f"❌ You don't own a `{item}`.")

        title, color, extra = "", 0x00ff88, None

        if item == "bleach":
            await self.inv.consume(ctx.author, item, 1)
            reduced = await self.bank.reduce_heat(ctx.author, 25)
            title, desc = "🧴 Evidence cleaned", f"You bleached the scene. Heat **-{reduced}**."
        elif item == "burner_barrel":
            await self.inv.consume(ctx.author, item, 1)
            reduced = await self.bank.reduce_heat(ctx.author, 15)
            title, desc = "🔥 Burned the evidence", f"Smoke goes up, evidence goes away. Heat **-{reduced}**."
        elif item == "dirty_cop_badge":
            await self.inv.consume(ctx.author, item, 1)
            reduced = await self.bank.reduce_heat(ctx.author, 50)
            title, desc = "🪪 Bribe accepted", f"Officer Friendly looked the other way. Heat **-{reduced}**."
        elif item == "fake_passport":
            await self.inv.consume(ctx.author, item, 1)
            await self.bank.set_heat(ctx.author, 0)
            title, color, desc = "🛂 New identity", 0xffd700, "You crossed the border. Heat reset to **0**."
        elif item == "mystery_package":
            await self.inv.consume(ctx.author, item, 1)
            roll = random.random()
            if roll < 0.5:
                added, lost = await self.bank.add_to_wallet(ctx.author, random.randint(500, 5000))
                title, desc = "📫 Mystery Package — CASH", f"Inside was **{added:,} Pesos**!"
                if lost > 0:
                    extra = [("❗ Wallet capped", f"{lost:,} Pesos lost")]
            elif roll < 0.85:
                drop = random.choice(["meth", "coke_kit", "pseudo", "scale", "stash_box", "padlock"])
                qty = random.randint(1, 3)
                await self.inv.update_acc(ctx.author, qty, drop)
                title, desc = "📫 Mystery Package — ITEMS", f"Inside: **{qty}x {drop.replace('_',' ').title()}**!"
            else:
                title, color, desc = "📫 Mystery Package — EMPTY", 0xff0000, "Just an empty box. You got scammed."
        elif item == "sus_backpack":
            await self.inv.consume(ctx.author, item, 1)
            if random.random() < 0.5:
                added, lost = await self.bank.add_to_wallet(ctx.author, random.randint(2000, 15000))
                title, desc = "🎒 Sus Backpack — JACKPOT", f"It was someone's stash. **+{added:,} Pesos**"
                if lost > 0:
                    extra = [("❗ Wallet capped", f"{lost:,} Pesos lost")]
            else:
                users = await self.bank.get_acc(ctx.author)
                loss = min(users[1], random.randint(1000, 5000))
                await self.bank.update_acc(ctx.author, -loss)
                title, color, desc = "💥 Sus Backpack — IT WAS A BOMB", 0xff0000, f"It exploded. You lost **{loss:,} Pesos** to the chaos."
        elif item == "narco_prayer_candle":
            await self.inv.consume(ctx.author, item, 1)
            await self.bank.award_xp(ctx.author, 5)
            title, desc = "🙏 Prayer answered", "The cartel saints smile. **+5 XP**"
        elif item == "blood_money_case":
            await self.inv.consume(ctx.author, item, 1)
            added, lost = await self.bank.add_to_wallet(ctx.author, random.randint(40_000, 100_000))
            title, color, desc = "💼 Case opened", 0xffd700, f"**+{added:,} Pesos**"
            if lost > 0:
                extra = [("❗ Wallet capped", f"{lost:,} Pesos lost — deposit first next time")]
        elif item == "counterfeit_bills":
            await self.inv.consume(ctx.author, item, 1)
            if random.random() < 0.6:
                added, lost = await self.bank.add_to_wallet(ctx.author, random.randint(8_000, 16_000))
                title, desc = "💵 Spent the fakes", f"Cashier didn't check. **+{added:,} Pesos**"
                if lost > 0:
                    extra = [("❗ Wallet capped", f"{lost:,} lost")]
            else:
                await self.bank.update_acc(ctx.author, 20, mode="heat")
                title, color, desc = "💵 Cashier caught it", 0xff0000, "Cashier flagged the bills. **+20 heat**."

        await send_embed(ctx, title=title, description=desc, color=color, fields=extra)


async def setup(bot):
    await bot.add_gear(Items(bot))
