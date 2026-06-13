from django.contrib import admin

from .models import PlayerPity, PlayerStreak, SpecialBonus


@admin.register(SpecialBonus)
class SpecialBonusAdmin(admin.ModelAdmin):
    list_display = (
        "special",
        "attack_percent_enabled",
        "attack_percent",
        "flat_attack_enabled",
        "flat_attack",
        "hp_percent_enabled",
        "hp_percent",
        "flat_hp_enabled",
        "flat_hp",
        "pity_enabled",
        "pity_threshold",
        "streak_bonus_enabled",
        "streak_threshold",
        "duplicate_cap_enabled",
        "duplicate_cap",
    )
    list_filter = (
        "attack_percent_enabled",
        "flat_attack_enabled",
        "hp_percent_enabled",
        "flat_hp_enabled",
        "pity_enabled",
        "streak_bonus_enabled",
        "duplicate_cap_enabled",
    )
    search_fields = ("special__name",)
    autocomplete_fields = ("special",)
    fieldsets = (
        (
            "Special",
            {
                "fields": ("special",),
            },
        ),
        (
            "Attack Bonuses",
            {
                "description": "Applied to attack_bonus on the BallInstance at catch time.",
                "fields": (
                    "attack_percent_enabled",
                    "attack_percent",
                    "flat_attack_enabled",
                    "flat_attack",
                ),
            },
        ),
        (
            "HP Bonuses",
            {
                "description": "Applied to health_bonus on the BallInstance at catch time.",
                "fields": (
                    "hp_percent_enabled",
                    "hp_percent",
                    "flat_hp_enabled",
                    "flat_hp",
                ),
            },
        ),
        (
            "Pity System",
            {
                "description": (
                    "After a player catches pity_threshold balls without catching this special, "
                    "their next catch is forced to be this special. Counter resets on catch."
                ),
                "fields": (
                    "pity_enabled",
                    "pity_threshold",
                ),
            },
        ),
        (
            "Catch Streak Bonus",
            {
                "description": (
                    "Catching this special streak_threshold times in a row triggers an extra "
                    "flat bonus on the next catch. Catching anything else resets the streak."
                ),
                "fields": (
                    "streak_bonus_enabled",
                    "streak_threshold",
                    "streak_bonus_attack",
                    "streak_bonus_hp",
                ),
            },
        ),
        (
            "Duplicate Cap",
            {
                "description": (
                    "Blocks a player from owning more than duplicate_cap copies of the "
                    "same ball + special combination."
                ),
                "fields": (
                    "duplicate_cap_enabled",
                    "duplicate_cap",
                ),
            },
        ),
    )


@admin.register(PlayerPity)
class PlayerPityAdmin(admin.ModelAdmin):
    list_display = ("player", "special", "counter")
    list_filter = ("special",)
    search_fields = ("player__discord_id",)
    readonly_fields = ("player", "special", "counter")


@admin.register(PlayerStreak)
class PlayerStreakAdmin(admin.ModelAdmin):
    list_display = ("player", "special", "counter")
    list_filter = ("special",)
    search_fields = ("player__discord_id",)
    readonly_fields = ("player", "special", "counter")
