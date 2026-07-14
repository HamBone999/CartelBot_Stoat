"""Stoat UI helpers.

Stoat's SendableEmbed has only title/description/color/url/icon_url/media —
there is no add_field(). So Discord embed "fields" are folded into the
markdown description here, keeping the cog code close to the originals.
"""
from stoat import SendableEmbed


def hexcolor(c):
    """Accept a Discord-style int (0x00ff88) or a CSS string; return CSS string."""
    if c is None:
        return None
    if isinstance(c, int):
        return f"#{c:06x}"
    return str(c)


def embed(title=None, description="", color=None, fields=None):
    """Build a SendableEmbed. `fields` is a list of (name, value[, inline]) tuples
    appended to the description as `**name:** value` lines (inline flag ignored)."""
    body = description or ""
    if fields:
        rendered = []
        for f in fields:
            name, value = f[0], f[1]
            rendered.append(f"**{name}:** {value}")
        if rendered:
            body = (body + "\n\n" if body else "") + "\n".join(rendered)
    return SendableEmbed(title=title, description=body, color=hexcolor(color))


async def send_embed(ctx, title=None, description="", color=None, fields=None):
    """Convenience: build and send an embed in one call."""
    return await ctx.send(embeds=[embed(title, description, color, fields)])
