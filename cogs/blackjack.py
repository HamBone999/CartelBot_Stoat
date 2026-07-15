import random
import stoat
from stoat.ext import commands
from modules.ui import embed

HIT, STAND, DOUBLE = "🃏", "✋", "⚡"


# Pip symbols render as double-width emoji in Stoat code blocks and break the
# grid — use single-width letter suits so the ASCII boxes stay aligned.
SUIT_LETTER = {"♠": "S", "♥": "H", "♦": "D", "♣": "C"}


def render_card(card, hidden=False):
    if hidden:
        return [".-----.", "|/////|", "|/ ? /|", "|/////|", "'-----'"]
    rank = card[:-1]
    suit = SUIT_LETTER.get(card[-1], card[-1])
    return [
        ".-----.",
        "|" + rank.ljust(5) + "|",
        f"|  {suit}  |",
        "|" + rank.rjust(5) + "|",
        "'-----'",
    ]


def render_hand(hand, hide_index=None):
    cards = [render_card(c, hidden=(i == hide_index)) for i, c in enumerate(hand)]
    return "\n".join("  ".join(c[i] for c in cards) for i in range(5))


def hand_value(hand):
    value, aces = 0, 0
    for card in hand:
        rank = card[:-1]
        if rank in ("J", "Q", "K"):
            value += 10
        elif rank == "A":
            aces += 1
            value += 11
        else:
            value += int(rank)
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value


class Blackjack(commands.Gear):
    def __init__(self, bot):
        self.bot = bot
        self.bank = bot.db.bank
        self.cards = [f"{r}{s}" for s in ("♠", "♥", "♦", "♣")
                      for r in ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")]
        self.games = {}  # message_id -> game state

    def draw(self):
        return random.choice(self.cards)

    def _embed(self, g, reveal, status):
        pv = hand_value(g["player"])
        dealer_head = hand_value(g["dealer"]) if reveal else "?"
        desc = (
            f"🎩 **Dealer — {dealer_head}**\n"
            f"```\n{render_hand(g['dealer'], hide_index=None if reveal else 1)}\n```\n"
            f"🧍 **You — {pv}**\n"
            f"```\n{render_hand(g['player'])}\n```\n"
            f"💰 Bet: **{g['bet']:,} Pesos**" + (" • ⚡ Doubled" if g["doubled"] else "")
        )
        if not reveal:
            desc += f"\n\nReact: {HIT} Hit  •  {STAND} Stand  •  {DOUBLE} Double"
        return embed(title=f"🃏 Cartel Blackjack — {status}", description=desc, color=0x1abc9c)

    @commands.command(name="blackjack", aliases=["bj"])
    async def blackjack(self, ctx, bet: int):
        """Play Cartel Blackjack (min bet 500 Pesos)"""
        if bet < 500:
            return await ctx.send("❌ Minimum bet is **500 Pesos**.")
        await self.bank.open_acc(ctx.author)
        users = await self.bank.get_acc(ctx.author)
        if users[1] < bet:
            return await ctx.send("❌ You don't have enough Pesos!")
        await self.bank.update_acc(ctx.author, -bet)

        g = {"player_id": ctx.author.id, "bet": bet, "doubled": False,
             "player": [self.draw(), self.draw()], "dealer": [self.draw(), self.draw()], "msg": None}

        if hand_value(g["player"]) == 21:
            return await self._natural(ctx, g)

        msg = await ctx.send(embeds=[self._embed(g, reveal=False, status="Your move")])
        g["msg"] = msg
        self.games[msg.id] = g
        for e in (HIT, STAND, DOUBLE):
            try:
                await msg.react(e)
            except Exception:
                pass

    async def _natural(self, ctx, g):
        added, lost = await self.bank.add_to_wallet(ctx.author, int(g["bet"] * 2.5))
        await self.bank.award_xp(ctx.author, 15)
        desc = (f"🧍 You:\n```\n{render_hand(g['player'])}\n```\n🎩 Dealer:\n```\n{render_hand(g['dealer'])}\n```\n"
                f"💰 Payout (3:2): **+{added:,} Pesos** • 🎓 **+15 XP**")
        if lost > 0:
            desc += f"\n❗ Wallet capped — {lost:,} Pesos lost"
        await ctx.send(embeds=[embed(title="🎰 NATURAL BLACKJACK!", description=desc, color=0xffd700)])

    async def _finish(self, g):
        """Remove the game and clean up its reactions."""
        self.games.pop(g["msg"].id, None)
        try:
            await g["msg"].clear_reactions()
        except Exception:
            pass

    async def _user(self, g):
        class _U:
            def __init__(s, uid):
                s.id = uid
        return _U(g["player_id"])

    @commands.Gear.listener()
    async def on_reaction(self, event: stoat.MessageReactEvent):
        g = self.games.get(event.message_id)
        if not g or event.user_id != g["player_id"]:
            return
        emoji = str(getattr(event, "emoji", ""))
        user = await self._user(g)

        if emoji == HIT:
            g["player"].append(self.draw())
            if hand_value(g["player"]) > 21:
                return await self._bust(g)
            await g["msg"].edit(embeds=[self._embed(g, reveal=False, status="Hit")])
        elif emoji == STAND:
            await self._dealer_turn(g, user)
        elif emoji == DOUBLE:
            if len(g["player"]) > 2:
                return
            acc = await self.bank.get_acc(user)
            if acc[1] < g["bet"]:
                return
            await self.bank.update_acc(user, -g["bet"])
            g["bet"] *= 2
            g["doubled"] = True
            g["player"].append(self.draw())
            if hand_value(g["player"]) > 21:
                return await self._bust(g)
            await self._dealer_turn(g, user)

    async def _dealer_turn(self, g, user):
        while hand_value(g["dealer"]) < 17:
            g["dealer"].append(self.draw())
        pv, dv = hand_value(g["player"]), hand_value(g["dealer"])
        if dv > 21 or pv > dv:
            await self._win(g, user)
        elif pv == dv:
            await self._push(g, user)
        else:
            await self._lose(g)

    def _result_desc(self, g):
        return (f"🎩 Dealer — {hand_value(g['dealer'])}\n```\n{render_hand(g['dealer'])}\n```\n"
                f"🧍 You — {hand_value(g['player'])}\n```\n{render_hand(g['player'])}\n```")

    async def _bust(self, g):
        await g["msg"].edit(embeds=[embed(title="💥 BUST!", color=0xff0000,
            description=f"```\n{render_hand(g['player'])}\n```\n💸 Lost **{g['bet']:,} Pesos**")])
        await self._finish(g)

    async def _win(self, g, user):
        added, lost = await self.bank.add_to_wallet(user, g["bet"] * 2)
        await self.bank.award_xp(user, 10)
        d = self._result_desc(g) + f"\n💰 Payout: **+{added:,} Pesos** • 🎓 **+10 XP**"
        if lost > 0:
            d += f"\n❗ Wallet capped — {lost:,} Pesos lost"
        await g["msg"].edit(embeds=[embed(title="🎉 YOU WIN!", description=d, color=0x2ecc71)])
        await self._finish(g)

    async def _push(self, g, user):
        await self.bank.update_acc(user, g["bet"])
        d = self._result_desc(g) + f"\n💵 Bet returned: **{g['bet']:,} Pesos**"
        await g["msg"].edit(embeds=[embed(title="🤝 PUSH", description=d, color=0xf1c40f)])
        await self._finish(g)

    async def _lose(self, g):
        d = self._result_desc(g) + f"\n💸 Lost **{g['bet']:,} Pesos**"
        await g["msg"].edit(embeds=[embed(title="😔 DEALER WINS", description=d, color=0xe74c3c)])
        await self._finish(g)


async def setup(bot):
    await bot.add_gear(Blackjack(bot))
