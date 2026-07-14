import stoat
from stoat.ext import commands
from base import Auth
from modules.ui import send_embed


class Gift(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank
        self.inv = bot.db.inv

    @commands.command(name="send")
    async def send_cash(self, ctx, member: stoat.User, amount: int):
        """Send Pesos from your wallet to another player"""
        if amount < 1:
            return await ctx.send("Amount must be at least 1.")
        if getattr(member, "bot", None) or member.id == ctx.author.id:
            return await ctx.send("You can't send to that.")

        await self.bank.open_acc(ctx.author)
        await self.bank.open_acc(member)
        users = await self.bank.get_acc(ctx.author)
        if users[1] < amount:
            return await ctx.send(f"❌ You only have **{users[1]:,} Pesos** in your wallet.")

        await self.bank.update_acc(ctx.author, -amount)
        added, lost = await self.bank.add_to_wallet(member, amount)

        desc = f"{ctx.author.mention} sent **{added:,} Pesos** to {member.mention}"
        fields = None
        if lost > 0:
            # refund the over-cap portion to the sender's wallet
            await self.bank.add_to_wallet(ctx.author, lost)
            fields = [("❗ Recipient wallet was capped", f"**{lost:,} Pesos** refunded to you.")]
        await send_embed(ctx, title="💸 Cash Sent", description=desc, color=0x00ff88, fields=fields)

    @commands.command(name="gift")
    async def gift(self, ctx, member: stoat.User, item: str, amount: int = 1):
        """Give an item from your inventory to another player"""
        if amount < 1:
            return await ctx.send("Amount must be at least 1.")
        if getattr(member, "bot", None) or member.id == ctx.author.id:
            return await ctx.send("You can't gift that.")

        item_name = item.lower().strip().replace(" ", "_")
        valid = {i["name"] for i in self.inv.shop_items}
        if item_name not in valid:
            return await ctx.send(f"❌ Unknown item `{item}`. Check `{Auth.COMMAND_PREFIX}inventory` for exact names.")

        await self.inv.open_acc(ctx.author)
        await self.inv.open_acc(member)
        qty_data = await self.inv.update_acc(ctx.author, 0, item_name)
        owned = qty_data[0] if qty_data else 0
        if owned < amount:
            return await ctx.send(f"❌ You only have **{owned}x {item_name}**.")

        await self.inv.update_acc(ctx.author, -amount, item_name)
        await self.inv.update_acc(member, amount, item_name)

        pretty = item_name.replace("_", " ").title()
        await send_embed(ctx, title="🎁 Item Gifted",
                         description=f"{ctx.author.mention} gave **{amount}x {pretty}** to {member.mention}",
                         color=0x00ff88)


async def setup(bot):
    await bot.add_gear(Gift(bot))
