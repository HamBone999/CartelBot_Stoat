import asyncio
import random
import stoat
from stoat.ext import commands
from base import Auth
from modules.bank_funcs import RANK_NAMES
from modules.ui import embed

JOIN, START = "🤝", "🚀"

TARGETS = {
    "gas_station": {"emoji": "⛽", "name": "Gas Station",  "stake": 1_000, "min_p": 2, "base_success": 0.70, "payout_low": 2_000, "payout_high": 5_000, "xp": 20, "min_rank": 0},
    "liquor_store": {"emoji": "🥃", "name": "Liquor Store", "stake": 3_000, "min_p": 2, "base_success": 0.60, "payout_low": 6_000, "payout_high": 14_000, "xp": 40, "min_rank": 1},
    "bank": {"emoji": "🏦", "name": "Bank", "stake": 10_000, "min_p": 3, "base_success": 0.45, "payout_low": 22_000, "payout_high": 50_000, "xp": 80, "min_rank": 2},
    "casino": {"emoji": "🎰", "name": "Casino", "stake": 25_000, "min_p": 4, "base_success": 0.35, "payout_low": 60_000, "payout_high": 150_000, "xp": 150, "min_rank": 3},
}


class Heist(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank
        self.inv = bot.db.inv
        self.lobbies = {}  # message_id -> lobby state

    def _embed(self, lobby):
        t = lobby["target"]
        parts = list(lobby["participants"].values())
        desc = (
            f"**{lobby['host'].mention}** is planning a heist!\n\n"
            f"Stake: **{t['stake']:,} Pesos** per player\n"
            f"Min players: **{t['min_p']}** • Min rank: **{RANK_NAMES[t['min_rank']]}**\n"
            f"Payout pool: **{t['payout_low']:,}–{t['payout_high']:,}**\n"
            f"Base success: **{int(t['base_success']*100)}%** (+5% per extra player, +item bonuses)\n\n"
            f"React {JOIN} to join • host reacts {START} to start (auto-starts in 60s)\n\n"
            f"**Crew ({len(parts)}):** " + ", ".join(p.mention for p in parts)
        )
        return embed(title=f"{t['emoji']} HEIST: {t['name']}", description=desc, color=0xe74c3c)

    @commands.command(name="heist")
    async def heist(self, ctx, target: str = ""):
        """Plan a multiplayer heist: $heist <gas_station|liquor_store|bank|casino>"""
        target = target.lower().strip()
        if target not in TARGETS:
            opts = " • ".join(f"`{k}`" for k in TARGETS)
            return await ctx.send(f"Pick a target: {opts}")
        t = TARGETS[target]
        rank = await self.bank.get_rank(ctx.author)
        if rank < t["min_rank"]:
            return await ctx.send(f"❌ You need to be **{RANK_NAMES[t['min_rank']]}** to host this heist.")
        heat = await self.bank.get_heat(ctx.author)
        if heat >= 50:
            return await ctx.send(f"🥵 Too hot to host ({heat}/100). Lay low first.")
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        if users[1] < t["stake"]:
            return await ctx.send(f"❌ You need **{t['stake']:,} Pesos** in your wallet to host.")

        lobby = {
            "host": ctx.author, "target_key": target, "target": t,
            "participants": {ctx.author.id: ctx.author},
            "server": ctx.server, "msg": None, "started": False, "task": None,
        }
        msg = await ctx.send(embeds=[self._embed(lobby)])
        lobby["msg"] = msg
        self.lobbies[msg.id] = lobby
        for e in (JOIN, START):
            try:
                await msg.react(e)
            except Exception:
                pass
        lobby["task"] = asyncio.create_task(self._auto_start(msg.id))

    async def _auto_start(self, message_id):
        await asyncio.sleep(60)
        lobby = self.lobbies.get(message_id)
        if lobby and not lobby["started"]:
            if len(lobby["participants"]) >= lobby["target"]["min_p"]:
                await self._run(lobby)
            else:
                lobby["started"] = True
                self.lobbies.pop(message_id, None)
                try:
                    await lobby["msg"].edit(embeds=[embed(
                        title="🚔 Heist cancelled", color=0x95a5a6,
                        description="Not enough crew showed up. Stakes returned.")])
                except Exception:
                    pass

    async def _fetch_member(self, lobby, uid):
        srv = lobby["server"]
        if srv is not None:
            try:
                return await srv.fetch_member(uid)
            except Exception:
                pass
        try:
            return await self.bot.fetch_user(uid)
        except Exception:
            return None

    @commands.Gear.listener()
    async def on_reaction(self, event: stoat.MessageReactEvent):
        lobby = self.lobbies.get(event.message_id)
        if not lobby or lobby["started"]:
            return
        me = getattr(self.bot, "me", None)
        if me is not None and event.user_id == me.id:
            return
        emoji = str(getattr(event, "emoji", ""))

        if emoji == START:
            if event.user_id != lobby["host"].id:
                return
            if len(lobby["participants"]) < lobby["target"]["min_p"]:
                return
            if lobby["task"]:
                lobby["task"].cancel()
            await self._run(lobby)
            return

        if emoji != JOIN or event.user_id in lobby["participants"]:
            return

        t = lobby["target"]
        member = await self._fetch_member(lobby, event.user_id)
        if member is None or getattr(member, "bot", None):
            return
        if await self.bank.get_rank(member) < t["min_rank"]:
            return
        if await self.bank.get_heat(member) >= 50:
            return
        await self.bank.open_acc(member)
        acc = await self.bank.get_acc(member)
        if acc[1] < t["stake"]:
            return
        lobby["participants"][event.user_id] = member
        try:
            await lobby["msg"].edit(embeds=[self._embed(lobby)])
        except Exception:
            pass

    async def _run(self, lobby):
        if lobby["started"]:
            return
        lobby["started"] = True
        self.lobbies.pop(lobby["msg"].id, None)
        t = lobby["target"]
        parts = list(lobby["participants"].values())
        for p in parts:
            await self.bank.update_acc(p, -t["stake"])

        item_bonus, crew_bonuses = 0.0, []
        checks = [("getaway_van", 0.05, "🚐", "Getaway Van"), ("armored_suv", 0.10, "🚙", "Armored SUV"),
                  ("walkie_talkie", 0.03, "📻", "Walkie Talkie"), ("police_scanner", 0.05, "📡", "Police Scanner")]
        for p in parts:
            for item, bonus, icon, label in checks:
                if await self.inv.has_item(p, item):
                    item_bonus += bonus
                    name = getattr(p, "display_name", None) or getattr(p, "name", "?")
                    crew_bonuses.append(f"{icon} {name} has {label} (+{int(bonus*100)}%)")

        chance = min(0.95, t["base_success"] + 0.05 * (len(parts) - t["min_p"]) + item_bonus)
        success = random.random() < chance

        desc = (f"**Crew:** " + ", ".join(p.mention for p in parts) +
                f"\n**Success roll:** {int(chance*100)}% chance\n\n")
        if success:
            pot = random.randint(t["payout_low"], t["payout_high"])
            share = pot // len(parts)
            lines = []
            for p in parts:
                added, lost = await self.bank.add_to_wallet(p, share)
                await self.bank.award_xp(p, t["xp"])
                line = f"{p.mention} → **+{added:,}**" + (f" (lost {lost:,} to cap)" if lost > 0 else "")
                lines.append(line)
            desc += (f"💰 **Pot: {pot:,} Pesos** split {len(parts)} ways → **{share:,} each • +{t['xp']} XP**\n"
                     + "\n".join(lines))
            color = 0x2ecc71
        else:
            for p in parts:
                await self.bank.update_acc(p, 25, mode="heat")
            desc += f"💀 The heist **FAILED**. Stakes ({t['stake']:,} each) lost. Crew **+25 heat**."
            color = 0xff0000
        if crew_bonuses:
            desc += "\n\n🎒 " + " • ".join(crew_bonuses[:10])

        try:
            await lobby["msg"].edit(embeds=[embed(title=f"{t['emoji']} {t['name']} Heist — RESULT",
                                                  description=desc, color=color)])
            await lobby["msg"].clear_reactions()
        except Exception:
            pass


async def setup(bot):
    await bot.add_gear(Heist(bot))
