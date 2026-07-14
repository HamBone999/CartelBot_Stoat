import random
import time
import stoat
from stoat.ext import commands
from base import Auth
from modules.bank_funcs import RANK_NAMES
from modules.ui import embed

CONFIRM, CANCEL = "🔫", "❌"


class Gangs(commands.Gear):
    GUNS = {
        "pistol": {"cost": 4500, "damage": 35, "name": "🔫 Pistol"},
        "uzi": {"cost": 12500, "damage": 55, "name": "🔫 Uzi"},
        "ak": {"cost": 28000, "damage": 75, "name": "🔫 AK-47"},
        "rocket": {"cost": 65000, "damage": 95, "name": "🚀 Rocket Launcher"},
    }

    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank
        self.inv = bot.db.inv
        self._shoot_cd: dict = {}
        self.pending: dict = {}  # message_id -> pending shoot

    @commands.command(name="buygun", aliases=["buy_gun"])
    async def buy_gun(self, ctx, gun: str = ""):
        """Buy a weapon for street fights"""
        gun = gun.lower().strip()
        if gun not in self.GUNS:
            opts = " • ".join(f"`{k}` ({v['cost']:,})" for k, v in self.GUNS.items())
            return await ctx.send(f"Choose a weapon: {opts}")
        cost = self.GUNS[gun]["cost"]
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        if users[1] < cost:
            return await ctx.send("❌ Not enough cash!")
        await self.bank.update_acc(ctx.author, -cost)
        await self.bank.update_acc(ctx.author, gun, mode="gun")
        await ctx.send(f"🔫 You armed up with a **{self.GUNS[gun]['name']}**!")

    @commands.command(name="shoot")
    async def shoot(self, ctx, member: stoat.User):
        """Shoot another player and try to steal their Pesos (1 min cooldown)"""
        if getattr(member, "bot", None) or member.id == ctx.author.id:
            return await ctx.send("You can't shoot that!")
        uid, now, cd = ctx.author.id, time.time(), 60
        remaining = cd - (now - self._shoot_cd.get(uid, 0))
        if remaining > 0:
            return await ctx.send(f"⏳ Gun's hot — wait **{int(remaining)}s**")
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        gun = users[5] if len(users) > 5 else "none"
        if gun == "none":
            return await ctx.send(f"You don't have a gun! Buy one with `{Auth.COMMAND_PREFIX}buygun`")

        msg = await ctx.send(embeds=[embed(
            title="🔫 Confirm Shoot", color=0xff0000,
            description=f"{ctx.author.mention}, react {CONFIRM} to shoot {member.mention}, or {CANCEL} to cancel.")])
        self.pending[msg.id] = {"shooter": ctx.author, "target": member, "gun": gun, "msg": msg}
        for e in (CONFIRM, CANCEL):
            try:
                await msg.react(e)
            except Exception:
                pass

    @commands.Gear.listener()
    async def on_reaction(self, event: stoat.MessageReactEvent):
        p = self.pending.get(event.message_id)
        if not p or event.user_id != p["shooter"].id:
            return
        emoji = str(getattr(event, "emoji", ""))
        self.pending.pop(event.message_id, None)
        try:
            await p["msg"].clear_reactions()
        except Exception:
            pass
        if emoji == CANCEL:
            return await p["msg"].edit(embeds=[embed(title="🔫 Cancelled", description="Shoot cancelled.", color=0x95a5a6)])
        if emoji != CONFIRM:
            return
        await self._resolve_shot(p)

    async def _resolve_shot(self, p):
        shooter, member, gun, msg = p["shooter"], p["target"], p["gun"], p["msg"]
        self._shoot_cd[shooter.id] = time.time()
        damage = {"pistol": 35, "uzi": 55, "ak": 75, "rocket": 95}.get(gun, 30)

        if random.randint(1, 100) > damage:
            await self.bank.update_acc(shooter, 15, mode="heat")
            return await msg.edit(embeds=[embed(title="😣 Missed!",
                description=f"You missed {member.mention}! Heat +15", color=0xe67e22)])

        # Bulletproof vest deflects 50% of hits
        if await self.inv.has_item(member, "bulletproof_vest") and random.random() < 0.5:
            await self.inv.consume(member, "bulletproof_vest", 1)
            await self.bank.update_acc(shooter, 5, mode="heat")
            return await msg.edit(embeds=[embed(title="🦺 DEFLECTED!",
                description=f"{member.mention}'s bulletproof vest soaked the round — vest destroyed, no money lost.",
                color=0x3498db)])

        target_data = await self.bank.get_acc(member)
        target_wallet = target_data[1] if target_data else 0
        if target_wallet <= 0:
            return await msg.edit(embeds=[embed(title="💸 Broke",
                description=f"{member.mention} is broke — nothing to steal!", color=0x95a5a6)])

        stolen = min(random.randint(5000, 20000), target_wallet)
        await self.bank.update_acc(member, -stolen)
        added, lost = await self.bank.add_to_wallet(shooter, stolen)
        await self.bank.update_acc(shooter, 10, mode="heat")
        _, new_rank, leveled = await self.bank.award_xp(shooter, 15)
        desc = f"You hit {member.mention} and stole **{added:,} Pesos**! (+15 XP)"
        if lost > 0:
            desc += f"\n❗ Wallet cap — {lost:,} Pesos lost."
        if leveled:
            desc += f"\n🎉 **RANKED UP** to {RANK_NAMES[new_rank]}!"
        await msg.edit(embeds=[embed(title="🔫 BOOM!", description=desc, color=0x2ecc71)])

    @commands.command(name="claimterritory")
    async def claimterritory(self, ctx, *, territory_name: str = ""):
        """Claim a territory for passive income (costs 75,000 Pesos)"""
        territory_name = territory_name.strip()
        if not (3 <= len(territory_name) <= 25):
            return await ctx.send("Territory name must be 3–25 characters.")
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        if users[7] is not None:
            return await ctx.send("You already own a territory!")
        if users[1] < 75000:
            return await ctx.send("❌ You need **75,000 Pesos** to claim a territory!")
        await self.bank.update_acc(ctx.author, -75000)
        await self.bank.update_acc(ctx.author, territory_name, mode="territory")
        await ctx.send(f"🌆 **{territory_name}** is now your territory!\nPassive income every 10 minutes.")

    @commands.command(name="abandonterritory")
    async def abandonterritory(self, ctx):
        """Give up your territory"""
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        if users[7] is None:
            return await ctx.send("You don't own any territory.")
        await self.bank.update_acc(ctx.author, None, mode="territory")
        await ctx.send("🏠 You abandoned your territory.")

    @commands.command(name="territory")
    async def territory(self, ctx):
        """Check which territory you own"""
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        terr = users[7]
        if terr is None:
            return await ctx.send(f"You don't own any territory.\nUse `{Auth.COMMAND_PREFIX}claimterritory`")
        await ctx.send(f"🌆 You own **{terr}** territory.")


async def setup(bot):
    await bot.add_gear(Gangs(bot))
