import os
import time
import asyncio
import sqlite3
import psutil
import stoat
from dotenv import load_dotenv
from stoat.ext import commands

from modules import Database

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


class Auth:
    TOKEN = os.getenv("TOKEN")
    COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "$")
    FILENAME = os.getenv("FILENAME", "stoat_economy.db")
    OWNER_ID = os.getenv("OWNER_ID", "")  # Stoat user ID for [Owner] commands


COGS_DIR = os.path.join(os.path.dirname(__file__), "cogs")


class EconomyBot(commands.Bot):
    """Stoat port of CartelBot. Same DB/economy engine, Stoat-native command layer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = Database(Auth.FILENAME)
        self.start_time = time.time()
        self.commands_used = 0
        self._ready_once = False
        self._ready_servers = []  # captured from ReadyEvent (client.servers is unreliable)
        self._proc = psutil.Process()
        self._proc.cpu_percent(interval=None)  # prime the cpu sampler

    async def setup_hook(self):
        # Build the economy schema (idempotent) — same tables as the Discord bot.
        try:
            await self.db.bank.create_table()
            await self.db.inv.create_table()
            print("✅ Database tables ready")
        except Exception as e:
            print(f"❌ Database setup failed: {e}")

        # Load every gear (cog) under cogs/.
        for f in sorted(os.listdir(COGS_DIR)):
            if f.endswith(".py") and not f.startswith("__"):
                ext = f"cogs.{f[:-3]}"
                try:
                    await self.load_extension(ext)
                    print(f"- {f[:-3]} ✅")
                except Exception as e:
                    print(f"- {f[:-3]} ❌ ({e})")

    # ──────────────────────────── rotating status ────────────────────────────
    STATUS_ROTATE_SECONDS = 45

    def _status_messages(self):
        p = Auth.COMMAND_PREFIX
        return [
            f"{p}help for commands",
            "🌿 Planting on Block 7",
            "🔥 Running from the feds",
            "🧪 Cooking in the trap",
            "💰 Counting the books",
            "🚨 Heat rising...",
            f"🔫 {p}shoot em with your blicky",
            f"🎰 {p}blackjack in the back room",
            f"🏦 {p}heist the bank",
            f"🎲 {p}roll the dice",
            f"🃏 {p}slots • {p}coinflip • {p}rob",
            "💎 Kingpin Mode",
        ]

    async def status_rotate_task(self):
        """Cycle the bot's status text on a timer (also keeps presence online)."""
        messages = self._status_messages()
        i, first = 0, True
        while True:
            text = messages[i % len(messages)]
            try:
                await self.me.edit(status=stoat.UserStatusEdit(
                    text=text, presence=stoat.Presence.online))
                if first:
                    print("   Presence set: online 🟢 (rotating status)", flush=True)
                    first = False
            except Exception as e:
                print(f"status rotate error: {e}", flush=True)
            i += 1
            await asyncio.sleep(self.STATUS_ROTATE_SECONDS)

    async def console_stats_task(self):
        """Print live CPU/RAM/server stats to the console every 3 minutes."""
        while True:
            try:
                cpu = self._proc.cpu_percent(interval=None)
                mem_mb = self._proc.memory_info().rss / 1024 / 1024
                total_mb = psutil.virtual_memory().total / 1024 / 1024
                total_str = f"{total_mb/1024:.1f}GB" if total_mb >= 1024 else f"{total_mb:.0f}MB"

                uptime_s = int(time.time() - self.start_time)
                h, rem = divmod(uptime_s, 3600)
                m, s = divmod(rem, 60)
                uptime = f"{h:02d}:{m:02d}:{s:02d}"

                servers = list(getattr(self, "servers", []) or [])
                ts = time.strftime("%H:%M:%S")
                print(
                    f"[{ts}] STATS  CPU {cpu:5.1f}%  •  RAM {mem_mb:.1f}MB/{total_str}  •  "
                    f"servers {len(servers)}  •  cmds {self.commands_used}  •  up {uptime}",
                    flush=True,
                )
            except Exception as e:
                print(f"console stats task error: {e}", flush=True)
            await asyncio.sleep(180)

    # ──────────────────────────── server breakdown ────────────────────────────
    @staticmethod
    def _registered_users():
        """Count distinct humans who have actually used the bot (economy DB)."""
        for path in (Auth.FILENAME, "stoat_economy.db"):
            if not path:
                continue
            try:
                con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
                try:
                    n = con.execute("SELECT COUNT(DISTINCT user_id) FROM economy").fetchone()[0]
                finally:
                    con.close()
                return n
            except Exception:
                continue
        return None

    @staticmethod
    def _cell(value, width, align="l"):
        s = str(value)
        if len(s) > width:
            s = s[: width - 1] + "…"
        return s.rjust(width) if align == "r" else s.ljust(width)

    def _active_servers(self):
        """Servers the bot is in. The ReadyEvent snapshot holds fully-hydrated
        server objects (name + working fetch_members); client.servers returns
        stubs, so only fall back to it if the snapshot is empty."""
        ready = list(self._ready_servers or [])
        return ready if ready else list(getattr(self, "servers", []) or [])

    @staticmethod
    def _member_info(m):
        """(name, is_bot, user_id) for a fetched Member."""
        u = getattr(m, "user", None)
        name = getattr(m, "display_name", None)
        if not name and u is not None:
            name = getattr(u, "display_name", None) or getattr(u, "name", None)
        is_bot = bool(getattr(u, "bot", None)) if u is not None else bool(getattr(m, "bot", None))
        uid = getattr(u, "id", None) if u is not None else getattr(m, "id", None)
        return (name or "?"), is_bot, uid

    async def _server_stats(self, s):
        """Fetch live member roster + owner for one server."""
        members = []
        try:
            members = list(await s.fetch_members())
        except Exception:
            members = list(getattr(s, "members", []) or [])
        infos = [self._member_info(m) for m in members]
        humans = sum(1 for _, b, _ in infos if not b)
        bots = sum(1 for _, b, _ in infos if b)
        owner_id = getattr(s, "owner_id", None)
        owner = next((n for n, _, uid in infos if uid == owner_id), None) or f"id:{str(owner_id or '')[:10]}"
        chans = list(getattr(s, "channels", []) or []) or list(getattr(s, "channel_ids", []) or [])
        txt = sum(1 for c in chans if "Text" in type(c).__name__)
        vc = sum(1 for c in chans if "Voice" in type(c).__name__)
        roles = len(list(getattr(s, "roles", []) or []))
        created = "?"
        try:
            created = s.created_at.strftime("%Y-%m-%d")
        except Exception:
            pass
        return {
            "name": getattr(s, "name", None) or "?", "id": getattr(s, "id", "?"),
            "total": len(infos), "humans": humans, "bots": bots, "owner": owner,
            "txt": txt, "vc": vc, "chans": len(chans), "roles": roles, "created": created,
        }

    async def server_breakdown_lines(self):
        """Detailed per-server breakdown (owner, members, channels, roles, …)."""
        stats = []
        for s in self._active_servers():
            try:
                stats.append(await self._server_stats(s))
            except Exception as e:
                print(f"server stats error: {e}", flush=True)
        stats.sort(key=lambda d: d["total"], reverse=True)
        total_members = sum(d["total"] for d in stats)
        registered = self._registered_users()
        reg_str = f"{registered:,}" if registered is not None else "n/a"

        cols = [
            ("#", 2, "r"), ("SERVER", 24, "l"), ("MEMBERS", 8, "r"),
            ("HUMANS/BOTS", 13, "l"), ("CH", 4, "r"), ("ROLES", 6, "r"),
            ("CREATED", 10, "l"), ("OWNER", 20, "l"), ("SERVER ID", 28, "l"),
        ]
        width = sum(w for _, w, _ in cols) + (len(cols) - 1)

        def row(cells):
            return " ".join(self._cell(c, w, a) for c, (_, w, a) in zip(cells, cols))

        bar = "═" * width
        lines = [bar, f"  CARTELBOT (STOAT) SERVER BREAKDOWN  —  {time.strftime('%Y-%m-%d %H:%M:%S')}"]
        lines.append(f"  Servers: {len(stats)}   •   Total members: {total_members:,}   •   "
                     f"Registered users (real): {reg_str}")
        if stats:
            lines.append(f"  Largest: {stats[0]['name'][:26]} ({stats[0]['total']:,} members)")
        lines.append(bar)
        lines.append(row([c for c, _, _ in cols]))
        lines.append("─" * width)
        for i, d in enumerate(stats, 1):
            lines.append(row([
                i, d["name"], f"{d['total']:,}", f"{d['humans']:,}h/{d['bots']:,}b",
                d["chans"], d["roles"], d["created"], d["owner"], d["id"],
            ]))
        lines.append(bar)
        return lines

    async def server_breakdown_task(self):
        """Print the full server breakdown to the console periodically."""
        await asyncio.sleep(6)  # let the ReadyEvent snapshot land
        while True:
            try:
                for line in await self.server_breakdown_lines():
                    print(line, flush=True)
            except Exception as e:
                print(f"server breakdown task error: {e}", flush=True)
            await asyncio.sleep(180)
