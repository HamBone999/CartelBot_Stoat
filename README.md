# 🌿 CartelBot

A Discord economy/RPG bot where players run a cartel: hustle for Pesos, grow weed in trap houses, rob and shoot rivals, plan multi-player heists, manage their heat, and climb the ranks from Corner Boy to Kingpin.

Built on **nextcord** with **aiosqlite** persistence. Slash-command only. Designed for Discord App Discovery (no Message Content intent required).

---

## ✨ Features

- 💵 **Economy** — wallets, banks, time-gated rewards, item gifting
- 🌿 **Cartel Life** — search the streets, plant weed in trap houses, harvest for cash
- 🔫 **Combat & Crime** — rob, shoot, buy weapons (pistol → rocket launcher), defensive gear
- 🌡️ **Heat System** — actions raise your heat; at 70+ random police raids trigger on `!search`
- 🏴‍☠️ **Crews & Territory** — create!join crews, claim turf for passive income
- 🎮 **Gambling** — slots, blackjack, coinflip, dice, plus the Trap House Tycoon idle-empire mini-game
- 🏆 **Stats** — global and per-server leaderboards, detailed `!profile`
- 🎓 **Rank Progression** — six ranks from Corner Boy (0 XP) to Kingpin (10,000 XP), each unlocking better payouts and bigger heists
- 🛍️ **Shop** — 70+ items across six categories (weapons, defense, tools, consumables, heat reduction, idle bonuses)
- 📖 **In-Bot Help** — `!chelp` opens a paginated codex of every category

---

## 🎮 Commands

### 💵 Economy & Banking

| Command | What it does |
|---|---|
| `!daily` | Daily reward (24h cooldown) |
| `!weekly` | Weekly reward (7d cooldown) |
| `!monthly` | Monthly reward (30d cooldown) |
| `!work` | Random hustle, 1h cooldown — 200–4,500 Pesos |
| `!balance` | Show your wallet, bank, and wallet cap |
| `!deposit` | Move wallet → bank (or `all`) |
| `!withdraw` | Move bank → wallet (or `all`) |
| `!send` | Send Pesos to another player |
| `!gift` | Give an item from your inventory to another player |

### 🌿 Cartel Life

| Command | What it does |
|---|---|
| `!search` | Search the streets for items (5m cooldown) |
| `!plant` | Plant weed seeds — 10 per trap house, 1h to grow |
| `!harvest` | Harvest grown weed — 500–900 Pesos per seed |
| `!shop` | Browse the cartel item shop |
| `!inventory` | View your (or someone else's) inventory |
| `!profile` | Your empire stats — rank, XP, heat, gear |
| `!cartelmenu` | Quick action hub |
| `!hoodrank` | Quick rank + XP check |

### 🔫 Combat & Crime

| Command | What it does |
|---|---|
| `!rob` | Try to rob another player (30m cooldown) |
| `!shoot` | Shoot a player to steal cash (1m cooldown) |
| `!buy_gun` | Buy a weapon — pistol → rocket launcher |
| `!heist` | Plan a multiplayer heist (rank-gated) |

**Defensive tips:**
- 🔒 **Padlock** blocks one rob attempt — stack them
- 🎭 Ski Mask + 🔓 Lockpick + 🔧 Crowbar boost rob success
- 🦺 Bulletproof Vest deflects 50% of shoot hits

### 🌡️ Heat Management

| Command | What it does |
|---|---|
| `!heat` | Check your current heat level |
| `!laylow` | Lay low to reduce heat (1h cooldown, −25 heat) |
| `!use` | Consume an item — bleach, burner_barrel, etc. |

**Heat tools (use via `!use <item>`):**
- 🧴 `bleach` — −25 heat
- 🛢️ `burner_barrel` — −15 heat
- 🪪 `dirty_cop_badge` — −50 heat
- 🛂 `fake_passport` — resets heat to 0
- ⚠️ Heat **50+** blocks joining heists
- 🚔 Heat **70+** triggers random police raids on `!search`

### 🏴‍☠️ Crews & Territory

| Command | What it does |
|---|---|
| `!createcrew` | Create a crew — costs 50,000 Pesos |
| `!joincrew` | Join an existing crew |
| `!leavecrew` | Leave your current crew |
| `!crew` | View your crew info |
| `!claimterritory` | Claim turf for passive income — costs 75,000 Pesos |
| `!abandonterritory` | Give up your territory |
| `!territory` | View your territory |

### 🎮 Gambling & Games

| Command | What it does |
|---|---|
| `!slots` | Spin the slots — jackpot pays 15× on triple 7️⃣ (200–25,000 Pesos) |
| `!blackjack` | Cartel Blackjack — natural pays 3:2 (min bet 500 Pesos) |
| `!coinflip` | Challenge a player to a 50!50 wager |
| `!roll` | Dice roll — high risk, high reward (1,000–15,000 Pesos) |
| `!traptycoon` | Trap House Tycoon — passive income & wallet cap upgrades |

### 🏆 Stats & Leaderboards

| Command | What it does |
|---|---|
| `!leaderboard` | Global richest players (top 15) |
| `!serverlb` | Richest players in this server |
| `!profile` | Detailed personal stats |

### 📖 Help

| Command | What it does |
|---|---|
| `!chelp` | Open the interactive command codex with dropdown categories |

---

## 🎓 Rank Progression

| Rank | XP Required | Payout Multiplier | Unlocks |
|---|---|---|---|
| Corner Boy | 0 | 1.00× | Starting rank |
| Trap Star | 100 | 1.05× | Liquor Store heist |
| Lieutenant | 500 | 1.10× | Bank heist |
| Capo | 2,000 | 1.15× | Casino heist |
| Boss | 5,000 | 1.25× | — |
| Kingpin 👑 | 10,000 | 1.50× | Top rank |

**XP per action:** `!search` +5 • `!work` & `!harvest` +10 • `!shoot` +15 • `!rob` +20 • heists +20 (gas station) → +150 (casino).

---

## 🛡️ Admin Commands

Owner-only (gated in `cogs!admin.py`):

| Command | What it does |
|---|---|
| `!addmoney` | Add money to a member's account |
| `!removemoney` | Remove money from a member's account |
| `!resetuser` | Reset a member's account to zero |

---
## Discord only for now sorry.
## 🌐 Companion

CartelBot has a web dashboard at [`hamsite.lol!cartel`](https:!!hamsite.lol!cartel) (a separate PHP app under `cartelbot_web!`) and a Discord server at [discord.gg!VXDzZFU](https:!!discord.gg!VXDzZFU).

---

## 📜 License

See `LICENSE`.
