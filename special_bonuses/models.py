from typing import Self

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.manager import Manager


class SpecialBonus(models.Model):
    special = models.OneToOneField(
        "bd_models.Special",
        on_delete=models.CASCADE,
        related_name="bonus",
        help_text="The special this configuration belongs to.",
    )

    # ── Attack bonuses ──────────────────────────────────────────────────────

    attack_percent_enabled = models.BooleanField(
        default=False,
        help_text="Add a percentage of the ball's base attack to its attack_bonus.",
    )
    attack_percent = models.FloatField(
        default=0.0,
        help_text="Percentage of base attack added to attack_bonus (e.g. 10 = +10%). Range 0-200.",
    )
    flat_attack_enabled = models.BooleanField(
        default=False,
        help_text="Add a flat value to attack_bonus on every caught instance of this special.",
    )
    flat_attack = models.IntegerField(
        default=0,
        help_text="Flat points added to attack_bonus. Range 0-500.",
    )

    # ── HP bonuses ──────────────────────────────────────────────────────────

    hp_percent_enabled = models.BooleanField(
        default=False,
        help_text="Add a percentage of the ball's base health to its health_bonus.",
    )
    hp_percent = models.FloatField(
        default=0.0,
        help_text="Percentage of base health added to health_bonus (e.g. 10 = +10%). Range 0-200.",
    )
    flat_hp_enabled = models.BooleanField(
        default=False,
        help_text="Add a flat value to health_bonus on every caught instance of this special.",
    )
    flat_hp = models.IntegerField(
        default=0,
        help_text="Flat points added to health_bonus. Range 0-500.",
    )

    # ── Pity system ─────────────────────────────────────────────────────────

    pity_enabled = models.BooleanField(
        default=False,
        help_text=(
            "After a player catches pity_threshold balls without catching this special, "
            "their next catch is guaranteed to be this special. "
            "The counter resets to 0 each time they catch this special."
        ),
    )
    pity_threshold = models.IntegerField(
        default=200,
        help_text="Number of catches without this special before pity triggers. Range 1-10000.",
    )

    # ── Catch streak bonus ──────────────────────────────────────────────────

    streak_bonus_enabled = models.BooleanField(
        default=False,
        help_text=(
            "After catching this special streak_threshold times consecutively, "
            "the next catch of this special gets extra flat bonuses on top of everything else. "
            "Catching any other ball or special resets the streak to 0."
        ),
    )
    streak_threshold = models.IntegerField(
        default=3,
        help_text="Consecutive catches of this special needed to trigger the streak bonus. Range 2-100.",
    )
    streak_bonus_attack = models.IntegerField(
        default=0,
        help_text="Extra flat attack_bonus added when a streak triggers. Range 0-200.",
    )
    streak_bonus_hp = models.IntegerField(
        default=0,
        help_text="Extra flat health_bonus added when a streak triggers. Range 0-200.",
    )

    # ── Duplicate cap ───────────────────────────────────────────────────────

    duplicate_cap_enabled = models.BooleanField(
        default=False,
        help_text=(
            "Prevent a player from owning more than duplicate_cap copies of the same "
            "ball + special combination. Catches that would exceed the cap are blocked."
        ),
    )
    duplicate_cap = models.IntegerField(
        default=1,
        help_text="Maximum copies of a given ball + special a player may own. Range 1-999.",
    )

    objects: Manager[Self] = Manager()

    class Meta:
        managed = True
        db_table = "specialbonus"

    def __str__(self) -> str:
        return self.special.name

    def clean(self) -> None:
        if self.attack_percent_enabled and not (0.0 <= self.attack_percent <= 200.0):
            raise ValidationError("attack_percent must be between 0 and 200")
        if self.flat_attack_enabled and not (0 <= self.flat_attack <= 500):
            raise ValidationError("flat_attack must be between 0 and 500")
        if self.hp_percent_enabled and not (0.0 <= self.hp_percent <= 200.0):
            raise ValidationError("hp_percent must be between 0 and 200")
        if self.flat_hp_enabled and not (0 <= self.flat_hp <= 500):
            raise ValidationError("flat_hp must be between 0 and 500")
        if self.pity_enabled and not (1 <= self.pity_threshold <= 10000):
            raise ValidationError("pity_threshold must be between 1 and 10000")
        if self.streak_bonus_enabled:
            if not (2 <= self.streak_threshold <= 100):
                raise ValidationError("streak_threshold must be between 2 and 100")
            if not (0 <= self.streak_bonus_attack <= 200):
                raise ValidationError("streak_bonus_attack must be between 0 and 200")
            if not (0 <= self.streak_bonus_hp <= 200):
                raise ValidationError("streak_bonus_hp must be between 0 and 200")
        if self.duplicate_cap_enabled and not (1 <= self.duplicate_cap <= 999):
            raise ValidationError("duplicate_cap must be between 1 and 999")

    def compute_attack_bonus(self, base_attack: int) -> int:
        """Return the total attack_bonus delta from percent + flat bonuses (streak excluded)."""
        total = 0
        if self.attack_percent_enabled and self.attack_percent:
            total += round(base_attack * self.attack_percent / 100)
        if self.flat_attack_enabled:
            total += self.flat_attack
        return total

    def compute_hp_bonus(self, base_hp: int) -> int:
        """Return the total health_bonus delta from percent + flat bonuses (streak excluded)."""
        total = 0
        if self.hp_percent_enabled and self.hp_percent:
            total += round(base_hp * self.hp_percent / 100)
        if self.flat_hp_enabled:
            total += self.flat_hp
        return total

    def active_bonus_lines(self) -> list[str]:
        """Human-readable lines describing every enabled bonus, for Discord display."""
        lines: list[str] = []
        if self.attack_percent_enabled and self.attack_percent:
            lines.append(f"+{self.attack_percent:g}% attack")
        if self.flat_attack_enabled and self.flat_attack:
            lines.append(f"+{self.flat_attack} flat attack")
        if self.hp_percent_enabled and self.hp_percent:
            lines.append(f"+{self.hp_percent:g}% HP")
        if self.flat_hp_enabled and self.flat_hp:
            lines.append(f"+{self.flat_hp} flat HP")
        if self.pity_enabled:
            lines.append(f"Pity guarantee at {self.pity_threshold} catches")
        if self.streak_bonus_enabled:
            lines.append(
                f"Streak bonus (x{self.streak_threshold}): "
                f"+{self.streak_bonus_attack} ATK / +{self.streak_bonus_hp} HP"
            )
        if self.duplicate_cap_enabled:
            lines.append(f"Max {self.duplicate_cap} duplicate(s) per ball")
        return lines


class PlayerPity(models.Model):
    player = models.ForeignKey(
        "bd_models.Player",
        on_delete=models.CASCADE,
        related_name="pity_counters",
    )
    special = models.ForeignKey(
        "bd_models.Special",
        on_delete=models.CASCADE,
        related_name="pity_counters",
    )
    counter = models.IntegerField(
        default=0,
        help_text="Catches without this special since last catching it. Resets to 0 on catch.",
    )

    objects: Manager[Self] = Manager()

    class Meta:
        managed = True
        db_table = "specialbonus_playerpity"
        unique_together = (("player", "special"),)

    def __str__(self) -> str:
        return f"{self.player} — {self.special.name} pity ({self.counter})"


class PlayerStreak(models.Model):
    player = models.ForeignKey(
        "bd_models.Player",
        on_delete=models.CASCADE,
        related_name="streak_counters",
    )
    special = models.ForeignKey(
        "bd_models.Special",
        on_delete=models.CASCADE,
        related_name="streak_counters",
    )
    counter = models.IntegerField(
        default=0,
        help_text="Consecutive catches of this special. Resets to 0 when any other ball is caught.",
    )

    objects: Manager[Self] = Manager()

    class Meta:
        managed = True
        db_table = "specialbonus_playerstreak"
        unique_together = (("player", "special"),)

    def __str__(self) -> str:
        return f"{self.player} — {self.special.name} streak ({self.counter})"
