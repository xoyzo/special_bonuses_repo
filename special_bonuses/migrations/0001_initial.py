import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("bd_models", "0014_alter_ball_options_alter_ballinstance_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SpecialBonus",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "special",
                    models.OneToOneField(
                        help_text="The special this configuration belongs to.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bonus",
                        to="bd_models.special",
                    ),
                ),
                ("attack_percent_enabled", models.BooleanField(default=False, help_text="Add a percentage of the ball's base attack to its attack_bonus.")),
                ("attack_percent", models.FloatField(default=0.0, help_text="Percentage of base attack added to attack_bonus (e.g. 10 = +10%). Range 0-200.")),
                ("flat_attack_enabled", models.BooleanField(default=False, help_text="Add a flat value to attack_bonus on every caught instance of this special.")),
                ("flat_attack", models.IntegerField(default=0, help_text="Flat points added to attack_bonus. Range 0-500.")),
                ("hp_percent_enabled", models.BooleanField(default=False, help_text="Add a percentage of the ball's base health to its health_bonus.")),
                ("hp_percent", models.FloatField(default=0.0, help_text="Percentage of base health added to health_bonus (e.g. 10 = +10%). Range 0-200.")),
                ("flat_hp_enabled", models.BooleanField(default=False, help_text="Add a flat value to health_bonus on every caught instance of this special.")),
                ("flat_hp", models.IntegerField(default=0, help_text="Flat points added to health_bonus. Range 0-500.")),
                ("pity_enabled", models.BooleanField(default=False, help_text="After a player catches pity_threshold balls without catching this special, their next catch is guaranteed to be this special.")),
                ("pity_threshold", models.IntegerField(default=200, help_text="Number of catches without this special before pity triggers. Range 1-10000.")),
                ("streak_bonus_enabled", models.BooleanField(default=False, help_text="After catching this special streak_threshold times consecutively, the next catch gets extra flat bonuses.")),
                ("streak_threshold", models.IntegerField(default=3, help_text="Consecutive catches of this special needed to trigger the streak bonus. Range 2-100.")),
                ("streak_bonus_attack", models.IntegerField(default=0, help_text="Extra flat attack_bonus added when a streak triggers. Range 0-200.")),
                ("streak_bonus_hp", models.IntegerField(default=0, help_text="Extra flat health_bonus added when a streak triggers. Range 0-200.")),
                ("duplicate_cap_enabled", models.BooleanField(default=False, help_text="Prevent a player from owning more than duplicate_cap copies of the same ball + special combination.")),
                ("duplicate_cap", models.IntegerField(default=1, help_text="Maximum copies of a given ball + special a player may own. Range 1-999.")),
            ],
            options={
                "db_table": "specialbonus",
                "managed": True,
            },
        ),
        migrations.CreateModel(
            name="PlayerPity",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pity_counters",
                        to="bd_models.player",
                    ),
                ),
                (
                    "special",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pity_counters",
                        to="bd_models.special",
                    ),
                ),
                ("counter", models.IntegerField(default=0, help_text="Catches without this special since last catching it. Resets to 0 on catch.")),
            ],
            options={
                "db_table": "specialbonus_playerpity",
                "managed": True,
            },
        ),
        migrations.AlterUniqueTogether(
            name="playerpity",
            unique_together={("player", "special")},
        ),
        migrations.CreateModel(
            name="PlayerStreak",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="streak_counters",
                        to="bd_models.player",
                    ),
                ),
                (
                    "special",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="streak_counters",
                        to="bd_models.special",
                    ),
                ),
                ("counter", models.IntegerField(default=0, help_text="Consecutive catches of this special. Resets to 0 when any other ball is caught.")),
            ],
            options={
                "db_table": "specialbonus_playerstreak",
                "managed": True,
            },
        ),
        migrations.AlterUniqueTogether(
            name="playerstreak",
            unique_together={("player", "special")},
        ),
    ]
