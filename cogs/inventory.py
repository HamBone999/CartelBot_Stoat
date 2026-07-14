import stoat
from stoat.ext import commands
from base import Auth
from modules.inventory_funcs import SHOP_CATEGORIES
from modules.ui import send_embed


class Inventory(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank
        self.inv = bot.db.inv

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx, member: stoat.User = None):
        """View your (or someone else's) inventory"""
        user = member or ctx.author
        if getattr(user, "bot", None):
            return await ctx.send("Bots don't have an account")
        await self.inv.open_acc(user)

        name = getattr(user, "display_name", None) or user.name
        # Stoat SendableEmbed has no fields — build the body as markdown.
        sections = []
        total_value = 0
        total_items = 0
        for cat_key, (cat_emoji, cat_label) in SHOP_CATEGORIES.items():
            cat_items = [i for i in self.inv.shop_items if i.get("category") == cat_key]
            lines = []
            for item in cat_items:
                qty = await self.inv.get_qty(user, item["name"])
                if qty > 0:
                    iname = item["name"].replace("_", " ").title()
                    value = qty * item["cost"]
                    total_value += value
                    total_items += qty
                    icon = item["info"].split()[0] if item.get("info") else "📦"
                    lines.append(f"**{qty}x** {icon} {iname} *({value:,}₱)*")
            if lines:
                sections.append(f"__{cat_emoji}  {cat_label}__\n" + "\n".join(lines))

        if total_items == 0:
            body = f"*Inventory is empty — try `{Auth.COMMAND_PREFIX}search` or `{Auth.COMMAND_PREFIX}shop`*"
        else:
            header = f"**{total_items}** items • Total value: **{total_value:,}₱**"
            body = header + "\n\n" + "\n\n".join(sections)
        body += f"\n\n_Sell cooking items with `{Auth.COMMAND_PREFIX}cartelmenu` → Sell All • Gift with `{Auth.COMMAND_PREFIX}gift`_"

        await send_embed(ctx, title=f"🎒  {name}'s Inventory", description=body, color=0x3498db)


async def setup(bot):
    await bot.add_gear(Inventory(bot))
