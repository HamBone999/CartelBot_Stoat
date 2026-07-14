from stoat.ext import commands
from base import Auth
from modules.ui import send_embed

P = Auth.COMMAND_PREFIX

SECTIONS = [
    ("💰 Economy", [
        "daily / weekly / monthly — timed rewards",
        "work — hustle for cash (1h)",
        "balance ($bal) [@user] — check money",
        "deposit <amt|all> • withdraw <amt|all>",
        "send @user <amt> — transfer Pesos",
        "leaderboard ($lb) • serverlb",
    ]),
    ("🎒 Items & Shop", [
        "shop [category] — browse items",
        "buy <item> [qty] — purchase",
        "inventory ($inv) [@user] — your items",
        "use <item> — consume an item",
        "gift @user <item> [qty] — give an item",
        "sellall — dump all cooking items",
    ]),
    ("🎲 Gambling", [
        "slots <bet> • roll <bet>",
        "coinflip ($cf) @user <bet> — react ✅ to accept",
        "blackjack ($bj) <bet> — react 🃏 hit / ✋ stand / ⚡ double",
    ]),
    ("🔫 Crime", [
        "rob @user — steal Pesos (30m)",
        "buygun <pistol|uzi|ak|rocket>",
        "shoot @user — react 🔫 to confirm",
        "search — scavenge for items (5m)",
        "heist <target> — multiplayer, react 🤝 to join",
    ]),
    ("🌆 Empire", [
        "profile • hoodrank • cartelmenu",
        "heat • laylow — manage heat",
        "tycoon • collect • upgrade • buyspot",
        "plant <amt> • harvest — grow weed",
        "claimterritory <name> • territory • abandonterritory",
    ]),
    ("🏴 Crew", [
        "createcrew <name> • joincrew <name>",
        "crew • leavecrew",
    ]),
]


class Chelp(commands.Gear):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["chelp", "commands"])
    async def chelp(self, ctx):
        """Show all CartelBot commands"""
        blocks = []
        for title, cmds in SECTIONS:
            lines = "\n".join(f"• `{P}`{c}" for c in cmds)
            blocks.append(f"__{title}__\n{lines}")
        desc = (f"Prefix: **`{P}`** — Stoat has no slash commands, so type `{P}command`.\n\n"
                + "\n\n".join(blocks))
        await send_embed(ctx, title="🧭 CartelBot Commands", description=desc, color=0x00ff88)


async def setup(bot):
    await bot.add_gear(Chelp(bot))
