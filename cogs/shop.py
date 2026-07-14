from stoat.ext import commands
from base import Auth
from modules.inventory_funcs import SHOP_CATEGORIES
from modules.ui import embed

CATEGORY_COLORS = {
    "cooking": 0x27ae60, "gear": 0x3498db, "weapons": 0xe74c3c,
    "vehicles": 0x95a5a6, "luxury": 0xf1c40f, "misc": 0x9b59b6,
}
CATEGORY_BLURBS = {
    "cooking": "Raw materials for cooking ops & search drops.",
    "gear": "Wearable items + gadgets with passive bonuses.",
    "weapons": "Melee tools and explosives for the rough work.",
    "vehicles": "Speed, escape, intimidate. Heist success boosts.",
    "luxury": "Status symbols. Sell for big returns when desperate.",
    "misc": "Consumables, edge cases, and chaos in a bag.",
}


class Shop(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank
        self.inv = bot.db.inv

    @commands.command(name="shop")
    async def shop(self, ctx, *, category: str = ""):
        """Browse the Cartel item shop. `!shop <category>` to view items."""
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        cap = await self.bank.get_wallet_cap(ctx.author)
        wallet = users[1]
        p = Auth.COMMAND_PREFIX
        cat = category.lower().strip()

        if not cat:
            rows = [f"{emoji}  **{label}** (`{key}`) — {CATEGORY_BLURBS[key]}"
                    for key, (emoji, label) in SHOP_CATEGORIES.items()]
            desc = (f"**{len(self.inv.shop_items)} items** across **{len(SHOP_CATEGORIES)} categories**.\n"
                    f"💵 Wallet: **{wallet:,}** / {cap:,} Pesos\n\n" + "\n".join(rows) +
                    f"\n\nBrowse: `{p}shop <category>`  •  Buy: `{p}buy <item> [qty]`")
            return await ctx.send(embeds=[embed(title="🛒  Cartel Shop", description=desc, color=0x00ff88)])

        if cat not in SHOP_CATEGORIES:
            return await ctx.send(f"❌ Unknown category. Options: {', '.join(f'`{k}`' for k in SHOP_CATEGORIES)}")

        emoji, label = SHOP_CATEGORIES[cat]
        items = [i for i in self.inv.shop_items if i.get("category") == cat]
        lines = []
        for i in items:
            afford = "✅" if wallet >= i["cost"] else "🔒"
            lines.append(f"{afford} {i['info']} `{i['name']}` — **{i['cost']:,}₱**")
        desc = (f"*{CATEGORY_BLURBS[cat]}*\n💵 Wallet: **{wallet:,}** / {cap:,} Pesos\n\n"
                + "\n".join(lines) + f"\n\nBuy with `{p}buy <item> [qty]` (✅ = affordable)")
        await ctx.send(embeds=[embed(title=f"{emoji}  {label}", description=desc, color=CATEGORY_COLORS[cat])])

    @commands.command(name="buy")
    async def buy(self, ctx, item: str = "", qty: int = 1):
        """Buy an item: `!buy <item> [qty]`"""
        if not item:
            return await ctx.send(f"Usage: `{Auth.COMMAND_PREFIX}buy <item> [qty]`")
        if qty < 1:
            return await ctx.send("Quantity must be at least 1.")
        item_name = item.lower().strip().replace(" ", "_")
        await self.bank.open_acc(ctx.author)
        await self.inv.open_acc(ctx.author)
        it = next((i for i in self.inv.shop_items if i["name"] == item_name), None)
        if not it:
            return await ctx.send(f"❌ Item `{item}` not found. Check `{Auth.COMMAND_PREFIX}shop <category>`.")
        cost = it["cost"] * qty
        users = await self.bank.get_acc(ctx.author)
        if users[1] < cost:
            return await ctx.send(f"❌ You need **{cost:,} Pesos**. Wallet: **{users[1]:,}**")
        await self.bank.update_acc(ctx.author, -cost)
        await self.inv.update_acc(ctx.author, qty, item_name)
        await ctx.send(f"✅ Bought **{qty}x {item_name.replace('_', ' ').title()}** — **-{cost:,} Pesos**")


async def setup(bot):
    await bot.add_gear(Shop(bot))
