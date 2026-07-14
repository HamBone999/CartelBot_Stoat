import random
import time
from stoat.ext import commands
from base import Auth
from modules.bank_funcs import RANK_NAMES, RANK_THRESHOLDS
from modules.ui import send_embed, embed

P = Auth.COMMAND_PREFIX


def progress_bar(value, max_value, length=10):
    if max_value <= 0:
        return "▱" * length
    filled = int(length * min(value, max_value) / max_value)
    return "▰" * filled + "▱" * (length - filled)


class Cartel(commands.Gear):
    ITEM_EMOTES = {
        "weed_seeds": "🌱", "coke_kit": "🧊", "meth": "💎", "battery": "🔋",
        "pseudo": "💊", "acetone": "🧪", "sulfuric": "🧪", "red_phos": "🔥",
        "coffee_filters": "☕", "scale": "📏", "ziplock": "📦", "lighter": "🔥",
        "gloves": "🧤", "muriatic": "🧪", "iodine": "🧪",
    }
    GUNS = {
        "pistol": {"name": "🔫 Pistol"}, "uzi": {"name": "🔫 Uzi"},
        "ak": {"name": "🔫 AK-47"}, "rocket": {"name": "🚀 Rocket Launcher"},
    }

    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank
        self.inv = bot.db.inv
        self._search_cd: dict = {}

    async def random_encounter(self, ctx):
        heat = await self.bank.get_heat(ctx.author)
        roll = random.random()
        heat_bonus = (heat / 100) * 0.20
        if roll < 0.06 + heat_bonus:
            await self.bank.open_acc(ctx.author)
            users = await self.bank.get_acc(ctx.author)
            robbed = int(users[1] * 0.075)
            await self.bank.update_acc(ctx.author, -robbed)
            await self.inv.reset_all_items(ctx.author)
            await send_embed(ctx, title="🧟 CRACKHEAD ATTACK!", color=0xff0000,
                description="A wild crackhead sprints out yelling **'GIMME THAT SHIT BRO!'**",
                fields=[("💸 Stolen", f"**{robbed:,} Pesos** (7.5%)"), ("📦 Looted", "**ALL your items**")])
            return True
        if roll < 0.09 + heat_bonus:
            await self.bank.open_acc(ctx.author)
            users = await self.bank.get_acc(ctx.author)
            loss = int(users[1] * 0.35)
            await self.bank.update_acc(ctx.author, -loss)
            await self.bank.update_acc(ctx.author, 20, mode="heat")
            await send_embed(ctx, title="🚨 POLICE RAID!", color=0x0000ff,
                description="Cops kicked in the door! They took 35% of your cash and raised your heat!")
            return True
        if roll < 0.105 + heat_bonus:
            await self.bank.open_acc(ctx.author)
            users = await self.bank.get_acc(ctx.author)
            wallet = users[1]
            if wallet > 0:
                phrases = [
                    "A **Super Rock Head** tackles you, steals your wallet, and screams 'THIS IS MY HOUSE NOW BITCH!'",
                    "The Super Rock Head rips your cash out and yells 'I'M THE KING OF THE STREETS!' doing the worm",
                    "He looks you dead in the eyes: 'Gimme that bag' and takes everything",
                    "Super Rock Head steals all your wallet money while twerking and screaming 'YEEEEEET!'",
                ]
                await self.bank.update_acc(ctx.author, -wallet)
                await send_embed(ctx, title="🪨 SUPER ROCK HEAD ATTACK!", color=0x800080,
                    description=random.choice(phrases), fields=[("💸 Stolen", f"**ALL {wallet:,} Pesos**")])
            return True
        return False

    @commands.command(name="sellall", aliases=["sell_all"])
    async def sellall(self, ctx):
        """Sell every cooking item in your inventory"""
        await self.bank.open_acc(ctx.author)
        await self.inv.open_acc(ctx.author)
        prices = {
            "weed_seeds": 320, "coke_kit": 1250, "meth": 2800, "battery": 125, "pseudo": 650,
            "acetone": 220, "sulfuric": 330, "red_phos": 950, "coffee_filters": 60, "scale": 450,
            "ziplock": 45, "lighter": 30, "gloves": 95, "muriatic": 280, "iodine": 540,
        }
        mult = await self.bank.get_rank_multiplier(ctx.author)
        total = 0
        for item in self.ITEM_EMOTES:
            qty = await self.inv.get_qty(ctx.author, item)
            if qty > 0:
                total += int(prices.get(item, 100) * qty * mult)
                await self.inv.update_acc(ctx.author, -qty, item)
        if total > 0:
            added, lost = await self.bank.add_to_wallet(ctx.author, total)
            msg = f"💰 **Sold everything!** You received **{added:,} Pesos** (rank x{mult:.2f})."
            if lost > 0:
                msg += f"\n❗ Wallet was capped — **{lost:,}** Pesos lost."
            await ctx.send(msg)
        else:
            await ctx.send("You have no items to sell.")

    @commands.command(name="profile")
    async def profile(self, ctx):
        """View your cartel empire stats"""
        await self.bank.open_acc(ctx.author)
        await self.inv.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        balance, heat, rank, gun = users[1], users[3], users[4], users[5]
        xp = await self.bank.get_xp(ctx.author)
        rank_name = RANK_NAMES[min(rank, 5)]
        if rank < 5:
            cur, nxt = RANK_THRESHOLDS[rank], RANK_THRESHOLDS[rank + 1]
            rank_progress = f"**{xp:,} XP** • Next: {nxt:,} ({xp-cur}/{nxt-cur})\n{progress_bar(xp-cur, nxt-cur)}"
        else:
            rank_progress = f"**{xp:,} XP** • MAX RANK 👑"
        inv_list = [f"{self.ITEM_EMOTES[i]} **{await self.inv.get_qty(ctx.author, i)}x {i.replace('_',' ')}**"
                    for i in self.ITEM_EMOTES if await self.inv.get_qty(ctx.author, i) > 0]
        name = getattr(ctx.author, "display_name", None) or ctx.author.name
        fields = [
            (f"🏠 Rank — {rank_name}", rank_progress),
            ("🔫 Equipped", self.GUNS.get(gun, {"name": "None"})["name"] if gun != "none" else "None"),
            ("💵 Balance", f"{balance:,} Pesos"),
            ("🥵 Heat", f"{heat}/100\n{progress_bar(min(heat,100),100)}"),
            ("📦 Cooking Inventory", "\n".join(inv_list) if inv_list else "Empty"),
        ]
        await send_embed(ctx, title=f"💼 {name}'s Cartel Empire", color=0x00ff88, fields=fields)

    @commands.command(name="hoodrank")
    async def hoodrank(self, ctx):
        """Check your current rank in the cartel"""
        rank = await self.bank.get_rank(ctx.author)
        xp = await self.bank.get_xp(ctx.author)
        name = getattr(ctx.author, "display_name", None) or ctx.author.name
        await ctx.send(f"🏠 **{name}** — **{RANK_NAMES[min(rank,5)]}** • {xp:,} XP")

    @commands.command(name="cartelmenu")
    async def cartelmenu(self, ctx):
        """Open the cartel action hub"""
        name = getattr(ctx.author, "display_name", None) or ctx.author.name
        desc = (f"Hey **{name}** — what's the move?\n\n"
                f"💼  `{P}profile` — rank, XP, heat & gear\n"
                f"💰  `{P}sellall` — dump every cooking item\n"
                f"🥵  `{P}heat` — quick heat check\n"
                f"🏴  `{P}howtorob` — tips on robbing & padlocks")
        await send_embed(ctx, title="🧭  Cartel Command Hub", description=desc, color=0x00ff88)

    @commands.command(name="howtorob")
    async def howtorob(self, ctx):
        """Tips on robbing and padlocks"""
        await send_embed(ctx, title="🏴 How to Rob", color=0xe74c3c, description=(
            f"Use `{P}rob @user` to try and rob another player.\n"
            "**45%** base success. Steal up to **8,000 Pesos** on success.\n\n"
            "**Boost your odds:** 🎭 Ski Mask +10% • 🔓 Lockpick +10% • 🔧 Crowbar +5%\n"
            f"**Defend:** 🔒 buy a padlock from `{P}shop gear` — blocks one rob"))

    @commands.command(name="heat")
    async def heat_cmd(self, ctx):
        """Check your current heat level"""
        heat = await self.bank.get_heat(ctx.author)
        status = ("🟢 Cool" if heat < 30 else "🟡 Watch your back" if heat < 60
                  else "🟠 They're sniffing around" if heat < 80 else "🔴 RUN — feds are close")
        await send_embed(ctx, title="🥵 Heat Status",
            color=0xff5500 if heat >= 60 else 0xffd700 if heat >= 30 else 0x00ff88,
            description=f"**{heat}/100**\n{progress_bar(min(heat,100),100)}\n\n{status}\n\n"
                        f"_Use `{P}laylow` or `{P}use bleach/burner_barrel/fake_passport` to reduce heat_")

    @commands.command(name="laylow")
    async def laylow(self, ctx):
        """Lay low to reduce your heat (1 hour cooldown)"""
        last = await self.bank.get_laylow_at(ctx.author)
        now = int(time.time())
        if now - last < 3600:
            r = 3600 - (now - last)
            return await ctx.send(f"⏳ You can lay low again in **{r//60}m {r%60}s**.")
        reduced = await self.bank.reduce_heat(ctx.author, 25)
        await self.bank.set_laylow_at(ctx.author, now)
        await ctx.send(f"😴 You laid low for an hour. **Heat -{reduced}**." if reduced > 0
                       else "😴 You laid low. Your heat was already at 0.")

    @commands.command(name="search")
    async def search(self, ctx):
        """Search the streets for items (5 min cooldown)"""
        uid, now, cd = ctx.author.id, time.time(), 300
        remaining = cd - (now - self._search_cd.get(uid, 0))
        if remaining > 0:
            return await ctx.send(f"⏳ Lay low for **{int(remaining)}s** before searching again.")
        self._search_cd[uid] = now

        heat = await self.bank.get_heat(ctx.author)
        if heat >= 70 and random.random() < 0.25:
            await self.bank.open_acc(ctx.author)
            users = await self.bank.get_acc(ctx.author)
            loss = int(users[1] * 0.20)
            await self.bank.update_acc(ctx.author, -loss)
            await self.bank.update_acc(ctx.author, 10, mode="heat")
            return await send_embed(ctx, title="🚔 HEAT IS TOO HIGH — POLICE RAID!", color=0xff0000,
                description=f"Your heat ({heat}/100) brought the feds. You lost **{loss:,} Pesos** and gained more heat.")

        if await self.random_encounter(ctx):
            return
        await self.bank.open_acc(ctx.author)

        has_gas = await self.inv.has_item(ctx.author, "gas_mask")
        has_nv = await self.inv.has_item(ctx.author, "night_vision")
        has_scan = await self.inv.has_item(ctx.author, "police_scanner")
        yield_mult = 1.0 + (0.25 if has_gas else 0) + (0.15 if has_nv else 0)
        heat_mult = (0.5 if has_gas else 1.0) * (0.75 if has_scan else 1.0)
        heat_gain = max(1, int(random.randint(3, 8) * heat_mult))
        await self.bank.update_acc(ctx.author, heat_gain, mode="heat")

        common = ["battery", "acetone", "sulfuric", "coffee_filters", "ziplock", "lighter", "gloves", "muriatic"]
        rare = ["pseudo", "red_phos", "scale", "iodine", "meth"]
        ultra = ["coke_kit"]
        tier = random.choices(["common", "rare", "ultra"], weights=[75, 10, 15], k=1)[0]
        found = {}
        for _ in range(random.randint(1, 3)):
            pool = common if tier == "common" else (rare if tier == "rare" else ultra)
            base = random.randint(2, 5) if tier == "common" else (random.randint(1, 3) if tier == "rare" else random.randint(1, 2))
            qty = max(1, int(base * yield_mult))
            item = random.choice(pool)
            found[item] = found.get(item, 0) + qty
        for item, qty in found.items():
            await self.inv.update_acc(ctx.author, qty, item)

        _, new_rank, leveled = await self.bank.award_xp(ctx.author, 5)
        items_list = "\n".join(f"{self.ITEM_EMOTES.get(i,'📦')} **{q}x {i.replace('_',' ')}**" for i, q in found.items())
        bonus = []
        if has_gas:
            bonus.append("🧪 Gas Mask: +25% yield, -50% heat")
        if has_nv:
            bonus.append("👀 Night Vision: +15% yield")
        if has_scan:
            bonus.append("📡 Scanner: -25% heat")
        msg = f"🔎 You found:\n{items_list}\n\n**Heat +{heat_gain}** • **+5 XP**"
        if bonus:
            msg += "\n" + "\n".join(bonus)
        if leveled:
            msg += f"\n\n🎉 **RANKED UP!** You're now a **{RANK_NAMES[new_rank]}**!"
        await ctx.send(msg)

    @commands.command(name="plant")
    async def plant(self, ctx, amount: int = 0):
        """Plant weed seeds — 10 per trap house, 1 hour to grow"""
        if amount < 1:
            return await ctx.send(f"Usage: `{P}plant <amount>`")
        existing = await self.bank.get_plant(ctx.author)
        if existing:
            remaining = int((existing[1] + 3600) - time.time())
            if remaining > 0:
                return await ctx.send(f"🌱 You already have **{existing[0]}** seeds growing! Ready in **{remaining//60}m {remaining%60}s**.")
            return await ctx.send(f"🌿 Your plants are ready! Use `{P}harvest` to collect them.")
        houses = (await self.bank.get_tycoon(ctx.author))[0]
        max_plants = houses * 10
        if amount > max_plants:
            return await ctx.send(f"🏠 You can only plant **{max_plants} seeds** ({houses} × 10). Buy more with `{P}buyspot`.")
        await self.inv.open_acc(ctx.author)
        owned = await self.inv.get_qty(ctx.author, "weed_seeds")
        if owned < amount:
            return await ctx.send(f"❌ You only have **{owned}x weed seeds**. Buy more from `{P}shop cooking`.")
        await self.inv.update_acc(ctx.author, -amount, "weed_seeds")
        await self.bank.set_plant(ctx.author, amount, int(time.time()))
        await send_embed(ctx, title="🌱 Seeds Planted!", color=0x2ecc71,
                         fields=[("Seeds in ground", f"**{amount}x weed seeds**"), ("Ready in", "**1 hour**")])

    @commands.command(name="harvest")
    async def harvest(self, ctx):
        """Harvest your grown weed for Pesos"""
        plant = await self.bank.get_plant(ctx.author)
        if not plant:
            return await ctx.send("🌱 You have nothing planted.")
        quantity, planted_at = plant
        remaining = int((planted_at + 3600) - time.time())
        if remaining > 0:
            return await ctx.send(f"⏳ Not ready yet — **{remaining//60}m {remaining%60}s** left.")
        mult = await self.bank.get_rank_multiplier(ctx.author)
        total = int(random.randint(500, 900) * mult) * quantity
        added, lost = await self.bank.add_to_wallet(ctx.author, total)
        await self.bank.clear_plant(ctx.author)
        _, new_rank, leveled = await self.bank.award_xp(ctx.author, 10)
        fields = [("🌱 Seeds harvested", f"**{quantity}x**"),
                  ("💰 Payout", f"**{added:,} Pesos** (rank x{mult:.2f})"), ("🎓 XP", "**+10 XP**")]
        if lost > 0:
            fields.append(("❗ Wallet capped", f"{lost:,} Pesos lost"))
        if leveled:
            fields.append(("🎉 RANKED UP!", f"You're now a **{RANK_NAMES[new_rank]}**!"))
        await send_embed(ctx, title="🌿 Harvest Complete!", color=0x27ae60, fields=fields)


async def setup(bot):
    await bot.add_gear(Cartel(bot))
