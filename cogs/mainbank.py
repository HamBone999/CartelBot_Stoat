import stoat
from stoat.ext import commands
from base import Auth
from modules.ui import embed


class MainBank(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank

    def _resolve_name(self, uid, server=None):
        """Best-effort display name for a stored user id."""
        u = None
        if server is not None:
            u = server.get_member(uid)
        if u is None:
            getter = getattr(self.bot, "get_user", None)
            u = getter(uid) if getter else None
        if u is not None:
            return getattr(u, "display_name", None) or getattr(u, "name", None) or str(uid)
        return f"user:{str(uid)[:6]}"

    def _lb_embed(self, title, rows, footer, server=None, color=0xffd700):
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        picked = []
        for uid, amt in rows:
            if len(picked) >= 15:
                break
            picked.append((self._resolve_name(uid, server), amt))
        if not picked:
            desc = "*No one has money yet...*"
        else:
            lines = [f"{medals.get(i, f'`#{i:>2}`')}  **{name}** — `{amt:,}₱`"
                     for i, (name, amt) in enumerate(picked, start=1)]
            desc = "\n".join(lines)
        desc += f"\n\n_{footer}_"
        return embed(title=title, description=desc, color=color)

    @commands.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard(self, ctx):
        """Show the global richest cartel members"""
        rows = await self.bank.get_networth_lb()
        em = self._lb_embed("🌍  Global Richest Cartel Members", rows, "Global • All servers")
        await ctx.send(embeds=[em])

    @commands.command(name="serverlb")
    async def server_leaderboard(self, ctx):
        """Show the richest members in this server"""
        if ctx.server is None:
            return await ctx.send("This command can only be used in a server.")
        rows = await self.bank.get_networth_lb()
        # keep only members present in this server
        rows = [(uid, amt) for (uid, amt) in rows if ctx.server.get_member(uid) is not None]
        em = self._lb_embed(f"🏆  {ctx.server.name} Richest", rows,
                            f"Server-only • {ctx.server.name}", server=ctx.server)
        await ctx.send(embeds=[em])

    @commands.command(name="balance", aliases=["bal"])
    async def balance(self, ctx, member: stoat.User = None):
        """Check your (or someone else's) balance"""
        user = member or ctx.author
        if getattr(user, "bot", None):
            return await ctx.send("Bots don't have an account")
        await self.bank.open_acc(user)
        users = await self.bank.get_acc(user)
        wallet_amt, bank_amt = users[1], users[2]
        net_amt = wallet_amt + bank_amt
        cap = await self.bank.get_wallet_cap(user)
        pct = int((wallet_amt / cap) * 10) if cap > 0 else 0
        bar = "▰" * pct + "▱" * (10 - pct)
        name = getattr(user, "display_name", None) or user.name
        fields = [
            ("💵  Wallet", f"**{wallet_amt:,}** / {cap:,}₱\n`{bar}`"),
            ("🏦  Bank", f"**{bank_amt:,}₱**"),
            ("📊  Net", f"**{net_amt:,}₱**"),
        ]
        em = embed(title=f"💼  {name}'s Balance", color=0x2ecc71, fields=fields)
        em.description += f"\n\n_More trap houses → bigger wallet cap • `{Auth.COMMAND_PREFIX}deposit` to safe-store cash_"
        await ctx.send(embeds=[em])

    @commands.command(name="deposit", aliases=["dep"])
    async def deposit(self, ctx, amount: str):
        """Move money from your wallet to your bank (amount or 'all')"""
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        wallet = users[1]
        if amount.lower() == "all":
            amt = wallet
        elif amount.isdigit() and int(amount) > 0:
            amt = int(amount)
        else:
            return await ctx.send("❌ Enter a positive amount or 'all'.")
        if wallet <= 0:
            return await ctx.send("❌ Your wallet is empty.")
        moved = await self.bank.deposit(ctx.author, amt)
        await ctx.send(f"🏦 Deposited **{moved:,} Pesos** into your bank.")

    @commands.command(name="withdraw", aliases=["wd"])
    async def withdraw(self, ctx, amount: str):
        """Move money from your bank to your wallet (amount or 'all')"""
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        bank_amt = users[2]
        if amount.lower() == "all":
            amt = bank_amt
        elif amount.isdigit() and int(amount) > 0:
            amt = int(amount)
        else:
            return await ctx.send("❌ Enter a positive amount or 'all'.")
        if bank_amt <= 0:
            return await ctx.send("❌ Your bank is empty.")
        moved, _, cap_short = await self.bank.withdraw(ctx.author, amt)
        msg = f"💵 Withdrew **{moved:,} Pesos** to your wallet."
        if cap_short > 0:
            msg += f"\n❗ Wallet was capped — **{cap_short:,}** couldn't fit. Buy more trap houses."
        await ctx.send(msg)


async def setup(bot):
    await bot.add_gear(MainBank(bot))
