# Implementation Plan: Item Drop System

## Overview

Implement the item drop system in `entities/item_drop.py` and wire it into `Fighter`, `Player`, `FightUI`, and `main.py`. Items fall from the sky during fights, can be picked up by players, and grant consumable effects or equip limited-use weapons.

## Tasks

- [x] 1. Create `entities/item_drop.py` with `ItemDrop` and data classes
  - [x] 1.1 Implement `ItemDrop` class with physics, state machine, and image loading
    - Define `ITEM_TYPES`, `WEAPON_TYPES`, and `ITEM_IMAGES` class-level cache
    - Implement `__init__` with `y = -32`, `vel_y = 4.0`, `landed = False`, `lifetime = 0.0`, `active = True`
    - Implement `get_rect()` returning `(x - 16, y - 16, 32, 32)` centered on position
    - Implement `update(dt, stage)`: apply downward velocity until landing on ground/platform, then count lifetime
    - Implement `load_images()` classmethod loading all 8 PNGs from `assets/items/`; fall back to colored 32×32 rect on missing file
    - _Requirements: 2.2, 2.3, 2.5, 10.1_

  - [ ]* 1.2 Write property test for item physics invariants
    - **Property 3: Item physics invariants**
    - **Validates: Requirements 2.2, 2.3**

  - [x] 1.3 Implement `NukeProjectile`, `GatlingBullet`, and `StaffEffect` dataclasses
    - `NukeProjectile`: `x, y, vel_y=6.0, active=True, owner_id, damage=150, knockback=20.0`
    - `GatlingBullet`: `x, y, direction, speed=18.0, active=True, owner_id, damage=25`
    - `StaffEffect`: `x, y, effect_type, timer=0.0, duration=0.8, active=True, owner_id, damage, hit_targets=set()`
    - _Requirements: 6.1, 7.1, 8.1, 8.2, 8.3_

- [x] 2. Implement `ItemDropManager` core (spawning, update, draw)
  - [x] 2.1 Implement `ItemDropManager.__init__`, `start()`, and `stop()`
    - Initialize `items`, `spawn_timer`, `active` flag, and weapon effect lists
    - `start()` sets `active = True`; `stop()` clears all items and weapon effects
    - _Requirements: 2.1, 2.7_

  - [x] 2.2 Implement `ItemDropManager.update()` — spawn logic and item lifecycle
    - Tick `spawn_timer`; when elapsed and `len(items) < MAX_ITEMS`, spawn a new `ItemDrop` at random x in `[STAGE_LEFT, STAGE_RIGHT]`
    - Reset timer to `random.uniform(5.0, 15.0)`
    - Call `item.update(dt, stage)` for each item; remove items where `lifetime >= ITEM_LIFETIME` or `not active`
    - _Requirements: 2.1, 2.4, 2.6, 2.7_

  - [ ]* 2.3 Write property test for spawn interval bounds
    - **Property 2: Spawn interval is within bounds**
    - **Validates: Requirements 2.1**

  - [ ]* 2.4 Write property test for maximum active items
    - **Property 5: Maximum active items**
    - **Validates: Requirements 2.7**

  - [ ]* 2.5 Write property test for item expiry
    - **Property 4: Item expiry**
    - **Validates: Requirements 2.6**

  - [x] 2.6 Implement `ItemDropManager.draw(surface)`
    - Draw each active item's sprite (or fallback rect) at its position
    - For landed items, draw a subtle glow outline (e.g., `pygame.draw.rect` with a bright border)
    - Draw `NukeProjectile`, `GatlingBullet`, and `StaffEffect` visuals
    - _Requirements: 2.5, 10.1, 10.2_

- [x] 3. Implement pickup detection and consumable effects
  - [x] 3.1 Implement `ItemDropManager.check_pickups(players)`
    - Only consider `Player` instances (check `isinstance(p, Player)`)
    - For each landed item, find all overlapping players; award to closest by center x distance
    - Call `apply_item(player, item)` and set `item.active = False`
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 3.2 Write property test for pickup collision and removal
    - **Property 6: Pickup collision and removal**
    - **Validates: Requirements 3.1, 3.2**

  - [ ]* 3.3 Write property test for only Players can pick up items
    - **Property 7: Only Players can pick up items**
    - **Validates: Requirements 3.3**

  - [ ]* 3.4 Write property test for closest player wins tie-break
    - **Property 8: Closest player wins tie-break**
    - **Validates: Requirements 3.4**

  - [x] 3.5 Implement `ItemDropManager.apply_item(player, item)`
    - `coin_bag`: `player.minion_manager.coins += 50`; show "+50G" floating text
    - `mana_bag`: `player.special_energy = player.max_special`; show "MANA FULL"
    - `health_bag`: `player.health = player.max_health`; show "HP FULL"
    - Weapon types: set `player.equipped_weapon = item.item_type`, `player.weapon_uses = 3`; show weapon name
    - Add pickup particle burst via `player.effect_manager`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 10.3_

  - [ ]* 3.6 Write property test for consumable effects are exact
    - **Property 9: Consumable effects are exact**
    - **Validates: Requirements 4.1, 4.2, 4.3**

  - [ ]* 3.7 Write property test for weapon equip sets uses to 3 and replaces existing
    - **Property 10: Weapon equip sets uses to 3 and replaces existing**
    - **Validates: Requirements 5.1, 5.2**

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement weapon attacks in `ItemDropManager`
  - [x] 5.1 Implement `execute_weapon_attack(fighter, stage)`
    - Dispatch to `_fire_nuke`, `_fire_gatling`, or `_fire_staff_*` based on `fighter.equipped_weapon`
    - Decrement `fighter.weapon_uses`; set `fighter.equipped_weapon = None` when uses reach 0
    - No-op if `weapon_uses == 0`
    - _Requirements: 5.4, 5.5, 5.6_

  - [ ]* 5.2 Write property test for weapon use decrements count
    - **Property 11: Weapon use decrements count**
    - **Validates: Requirements 5.4**

  - [ ]* 5.3 Write property test for weapon unequipped at zero uses
    - **Property 12: Weapon unequipped at zero uses**
    - **Validates: Requirements 5.5**

  - [x] 5.4 Implement `_fire_nuke(fighter, stage)`
    - Spawn exactly 3 `NukeProjectile` instances at distinct random x positions within `[STAGE_LEFT, STAGE_RIGHT]`
    - Each starts above screen (`y = -32`) and falls with `vel_y = 6.0`
    - On landing, create explosion: check all fighters and minions within 100px radius, call `take_damage(150)` with knockback
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ]* 5.5 Write property test for nuke fires exactly 3 projectiles at distinct positions
    - **Property 13: Nuke fires exactly 3 projectiles at distinct positions**
    - **Validates: Requirements 6.1**

  - [x] 5.6 Implement `_fire_gatling(fighter)`
    - Spawn 8+ `GatlingBullet` instances in fighter's facing direction with slight y spread
    - Each frame in `update()`: move bullets by `speed * direction`; deactivate when `x < STAGE_LEFT` or `x > STAGE_RIGHT`
    - On overlap with opponent hurtbox, call `take_damage(25)`
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ]* 5.7 Write property test for gatling fires at least 8 bullets
    - **Property 15: Gatling fires at least 8 bullets and applies damage**
    - **Validates: Requirements 7.1**

  - [ ]* 5.8 Write property test for gatling bullets removed when out of bounds
    - **Property 16: Gatling bullets removed when out of bounds**
    - **Validates: Requirements 7.3**

  - [x] 5.9 Implement `_fire_staff_red`, `_fire_staff_blue`, `_fire_staff_green`
    - Each spawns 5+ `StaffEffect` instances at random x positions across the stage
    - `effect_type`: `"fire"` / `"wave"` / `"bomb"` with respective damage values (60 / 60 / 80)
    - Each frame in `update()`: advance `timer`; check overlap with opponent hurtboxes; call `take_damage()` once per target via `hit_targets`; deactivate when `timer >= duration`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 5.10 Write property test for each staff type spawns at least 5 effects
    - **Property 17: Each staff type spawns at least 5 effects**
    - **Validates: Requirements 8.1, 8.2, 8.3**

- [x] 6. Modify `Fighter` and `Player` to support item weapons
  - [x] 6.1 Add `equipped_weapon`, `weapon_uses`, and `weapon_attack_pending` fields to `Fighter.__init__`
    - After the existing weapon system block, add:
      `self.equipped_weapon: Optional[str] = None`
      `self.weapon_uses: int = 0`
      `self.weapon_attack_pending: bool = False`
    - Change `self.weapon_data = get_weapon(WeaponType.FIST)` unconditionally (remove `stats.weapon_type` lookup)
    - _Requirements: 1.1, 1.2_

  - [ ]* 6.2 Write property test for fighter starts unarmed
    - **Property 1: Fighter starts unarmed**
    - **Validates: Requirements 1.1**

  - [x] 6.3 Add `attack_weapon()` method to `Fighter`
    - If `equipped_weapon` and `weapon_uses > 0`, set `self.weapon_attack_pending = True` and return `True`
    - Otherwise return `False`
    - _Requirements: 5.4_

  - [x] 6.4 Modify `Player.handle_input()` to try weapon attack before normal heavy attack
    - In the `heavy_attack` branch: `if not self.attack_weapon(): self.attack_heavy()`
    - _Requirements: 5.4_

- [x] 7. Add weapon HUD to `FightUI`
  - [x] 7.1 Implement `FightUI.draw_weapon_hud(surface, fighter, is_player1)`
    - If `fighter.equipped_weapon` is not None, draw the 32×32 weapon icon below the special bar
    - Draw use count number next to the icon
    - Position: below p1_special (left side, x≈20) or p2_special (right side)
    - If no weapon equipped, draw nothing
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 7.2 Call `draw_weapon_hud` from `FightUI.draw()`
    - Pass `p1_fighter` and `p2_fighter` into `FightUI.draw()` (update signature)
    - Call `self.draw_weapon_hud(surface, p1_fighter, True)` and `self.draw_weapon_hud(surface, p2_fighter, False)`
    - Update the call site in `main.py` to pass fighters
    - _Requirements: 9.1, 9.2, 9.3_

- [x] 8. Wire `ItemDropManager` into `main.py`
  - [x] 8.1 Create `ItemDropManager` in `start_round()` and integrate into `update_fight()` and `render()`
    - In `start_round()`: `self.item_drop_manager = ItemDropManager()`
    - In `update_fight()` when `round_state == FIGHT`: call `item_drop_manager.start()` (idempotent), then `item_drop_manager.update(dt, self.stage, players)`
    - Handle `weapon_attack_pending` for each player: call `item_drop_manager.execute_weapon_attack(p, self.stage)`
    - In `render()`: call `self.item_drop_manager.draw(main_surface)` after drawing fighters, before HUD
    - _Requirements: 2.1, 5.4_

- [x] 9. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Property tests use the `hypothesis` library; each must be tagged `# Feature: item-drop-system, Property N: ...`
- `ItemDropManager` is the single owner of all weapon attack state; `Fighter` only holds `equipped_weapon` and `weapon_uses`
- `check_pickups` must use `isinstance(p, Player)` to exclude `AIFighter` and `Minion` entities
