from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from ballsdex.core.utils.transformers import SpecialTransformer
from bd_models.models import BallInstance, Player, Special

from ..models import PlayerPity, PlayerStreak, SpecialBonus

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

log = logging.getLogger(__name__)

SpecialTransform = app_commands.Transform[Special, SpecialTransformer]


class SpecialBonuses(commands.Cog):
    """
    Applies stat bonuses, pity, streak and duplicate-cap rules to ball catches.

    Listens for the `ballsdex_ball_caught` event dispatched by the core after a
    successful catch.  The event provides the interaction and the BallInstance
    before it is saved, allowing us to mutate attack_bonus / health_bonus.

    Event signature expected:
        bot.dispatch("ballsdex_ball_caught", interaction, ball_instance)
    """

    def __init__(self, bot: "BallsDexBot") -> None:
        self.bot = bot

    # ── Internal helpers ────────────────────────────────────────────────────

    async def _get_bonus(self, special_id: int) -> SpecialBonus | None:
        try:
            return await SpecialBonus.objects.select_related("special").aget(special_id=special_id)
        except SpecialBonus.DoesNotExist:
            return None

    async def _get_or_create_pity(self, player: Player, special: Special) -> PlayerPity:
        pity, _ = await PlayerPity.objects.aget_or_create(
            player=player, special=special, defaults={"counter": 0}
        )
        return pity

    async def _get_or_create_streak(self, player: Player, special: Special) -> PlayerStreak:
        streak, _ = await PlayerStreak.objects.aget_or_create(
            player=player, special=special, defaults={"counter": 0}
        )
        return streak

    # ── Catch hook ──────────────────────────────────────────────────────────

    @commands.Cog.listener("on_ballsdex_ball_caught")
    async def on_ball_caught(
        self,
        interaction: discord.Interaction["BallsDexBot"],
        ball_instance: BallInstance,
    ) -> None:
        try:
            player = await Player.objects.aget(discord_id=interaction.user.id)
        except Player.DoesNotExist:
            return

        caught_special = ball_instance.special

        # ── 1. Duplicate cap ────────────────────────────────────────────────
        if caught_special is not None:
            bonus = await self._get_bonus(caught_special.pk)
            if bonus and bonus.duplicate_cap_enabled:
                existing = await BallInstance.objects.filter(
                    player=player,
                    ball=ball_instance.ball,
                    special=caught_special,
                    deleted=False,
                ).acount()
                if existing >= bonus.duplicate_cap:
                    ball_instance.extra_data["sb_blocked_duplicate"] = True
                    log.info(
                        "Duplicate cap hit for player %s, ball %s, special %s",
                        player.discord_id,
                        ball_instance.ball.country,
                        caught_special.name,
                    )
                    return

        # ── 2. Pity counters ────────────────────────────────────────────────
        pity_triggered_special: Special | None = None
        async for sb in SpecialBonus.objects.filter(pity_enabled=True).select_related("special"):
            pity = await self._get_or_create_pity(player, sb.special)
            if caught_special is not None and caught_special.pk == sb.special.pk:
                pity.counter = 0
                await pity.asave(update_fields=["counter"])
            else:
                pity.counter += 1
                await pity.asave(update_fields=["counter"])
                if pity.counter >= sb.pity_threshold and pity_triggered_special is None:
                    pity_triggered_special = sb.special
                    log.info(
                        "Pity triggered for player %s -> special %s",
                        player.discord_id,
                        sb.special.name,
                    )

        if pity_triggered_special is not None and caught_special != pity_triggered_special:
            ball_instance.special = pity_triggered_special
            caught_special = pity_triggered_special
            pity = await self._get_or_create_pity(player, pity_triggered_special)
            pity.counter = 0
            await pity.asave(update_fields=["counter"])
            ball_instance.extra_data["sb_pity_triggered"] = True

        # ── 3. Stat bonuses + streak ────────────────────────────────────────
        if caught_special is None:
            await PlayerStreak.objects.filter(player=player).aupdate(counter=0)
            return

        bonus = await self._get_bonus(caught_special.pk)
        if bonus is None:
            await PlayerStreak.objects.filter(player=player).exclude(
                special=caught_special
            ).aupdate(counter=0)
            return

        atk_delta = bonus.compute_attack_bonus(ball_instance.ball.attack)
        hp_delta = bonus.compute_hp_bonus(ball_instance.ball.health)

        if bonus.streak_bonus_enabled:
            streak = await self._get_or_create_streak(player, caught_special)
            streak.counter += 1
            if streak.counter >= bonus.streak_threshold:
                atk_delta += bonus.streak_bonus_attack
                hp_delta += bonus.streak_bonus_hp
                streak.counter = 0
                ball_instance.extra_data["sb_streak_triggered"] = True
                log.info(
                    "Streak bonus triggered for player %s, special %s",
                    player.discord_id,
                    caught_special.name,
                )
            await streak.asave(update_fields=["counter"])

        await PlayerStreak.objects.filter(player=player).exclude(
            special=caught_special
        ).aupdate(counter=0)

        ball_instance.attack_bonus += atk_delta
        ball_instance.health_bonus += hp_delta

    # ── Player commands ─────────────────────────────────────────────────────

    special_bonuses_group = app_commands.Group(
        name="special_bonuses",
        description="View information about special bonus systems.",
    )

    @special_bonuses_group.command(name="info")
    @app_commands.describe(special="The special you want to inspect.")
    async def bonuses_info(
        self,
        interaction: discord.Interaction["BallsDexBot"],
        special: SpecialTransform,
    ) -> None:
        """Show the active bonuses configured for a special."""
        try:
            bonus = await SpecialBonus.objects.aget(special=special)
        except SpecialBonus.DoesNotExist:
            await interaction.response.send_message(
                f"**{special.name}** has no bonus configuration.", ephemeral=True
            )
            return

        lines = bonus.active_bonus_lines()
        if not lines:
            await interaction.response.send_message(
                f"**{special.name}** has a bonus record but no features are currently enabled.",
                ephemeral=True,
            )
            return

        text = f"## {special.name} — Active Bonuses\n" + "\n".join(f"- {l}" for l in lines)
        await interaction.response.send_message(text, ephemeral=True)

    @special_bonuses_group.command(name="pity")
    @app_commands.describe(special="The special to check your pity counter for.")
    async def bonuses_pity(
        self,
        interaction: discord.Interaction["BallsDexBot"],
        special: SpecialTransform,
    ) -> None:
        """Show your current pity counter for a special."""
        try:
            bonus = await SpecialBonus.objects.aget(special=special)
        except SpecialBonus.DoesNotExist:
            await interaction.response.send_message(
                f"**{special.name}** has no bonus configuration.", ephemeral=True
            )
            return

        if not bonus.pity_enabled:
            await interaction.response.send_message(
                f"**{special.name}** does not have the pity system enabled.", ephemeral=True
            )
            return

        try:
            player = await Player.objects.aget(discord_id=interaction.user.id)
        except Player.DoesNotExist:
            await interaction.response.send_message(
                "You don't have a player profile yet. Catch some balls first!", ephemeral=True
            )
            return

        try:
            pity = await PlayerPity.objects.aget(player=player, special=special)
            counter = pity.counter
        except PlayerPity.DoesNotExist:
            counter = 0

        remaining = max(0, bonus.pity_threshold - counter)
        await interaction.response.send_message(
            f"## {special.name} — Your Pity Counter\n"
            f"Catches without this special: **{counter}** / **{bonus.pity_threshold}**\n"
            f"Guaranteed in at most: **{remaining}** more catch(es).",
            ephemeral=True,
        )

    @special_bonuses_group.command(name="streak")
    @app_commands.describe(special="The special to check your streak counter for.")
    async def bonuses_streak(
        self,
        interaction: discord.Interaction["BallsDexBot"],
        special: SpecialTransform,
    ) -> None:
        """Show your current catch streak counter for a special."""
        try:
            bonus = await SpecialBonus.objects.aget(special=special)
        except SpecialBonus.DoesNotExist:
            await interaction.response.send_message(
                f"**{special.name}** has no bonus configuration.", ephemeral=True
            )
            return

        if not bonus.streak_bonus_enabled:
            await interaction.response.send_message(
                f"**{special.name}** does not have the streak bonus system enabled.", ephemeral=True
            )
            return

        try:
            player = await Player.objects.aget(discord_id=interaction.user.id)
        except Player.DoesNotExist:
            await interaction.response.send_message(
                "You don't have a player profile yet. Catch some balls first!", ephemeral=True
            )
            return

        try:
            streak = await PlayerStreak.objects.aget(player=player, special=special)
            counter = streak.counter
        except PlayerStreak.DoesNotExist:
            counter = 0

        remaining = max(0, bonus.streak_threshold - counter)
        await interaction.response.send_message(
            f"## {special.name} — Your Catch Streak\n"
            f"Consecutive catches: **{counter}** / **{bonus.streak_threshold}**\n"
            f"Streak bonus triggers in: **{remaining}** more consecutive catch(es).\n"
            f"-# Catching any other ball or special resets your streak to 0.",
            ephemeral=True,
        )
