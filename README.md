# Installation
```toml
[[ballsdex.packages]]
location = "git+https://github.com/yourname/special_bonuses.git@v1.0.0"
path = "special_bonuses"
enabled = true
```

# Special Bonuses Package

Attach optional stat bonuses and luck systems to any Ballsdex special. Every feature is
independently toggled in the admin panel — nothing activates unless its enabled flag is set.

## Features

- **Attack %** — adds a percentage of the ball's base attack to `attack_bonus` at catch time
- **Flat Attack** — adds a flat integer to `attack_bonus` at catch time
- **HP %** — adds a percentage of the ball's base health to `health_bonus` at catch time
- **Flat HP** — adds a flat integer to `health_bonus` at catch time
- **Pity** — after N catches without this special, the next catch is guaranteed to be it
- **Catch Streak Bonus** — catch the same special N times in a row for an extra stat burst
- **Duplicate Cap** — prevent a player from owning more than N copies of the same ball + special

## Commands

- `/special_bonuses info <special>` — view all active bonuses for a special
- `/special_bonuses pity <special>` — check your pity counter for a special
- `/special_bonuses streak <special>` — check your streak counter for a special

## Notes

- Stat bonuses write directly to `attack_bonus` and `health_bonus` on the `BallInstance`.
- The pity and streak systems require the core to dispatch `ballsdex_ball_caught` after a catch.
  Check your Ballsdex version for the exact event name.
- For every new `SpecialBonus` record you do not need to restart; the admin panel changes take
  effect immediately on the next catch.
