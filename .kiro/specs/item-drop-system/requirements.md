# Requirements Document

## Introduction

The Item Drop System adds dynamic mid-battle pickups to DormFight. During a fight, items fall from the sky at random intervals and land on the stage floor or platforms. Only player-controlled fighters (not minions or AI-controlled minions) can pick up items by walking over them. Items include consumables (coins, mana, health) and weapons with limited uses. All characters start with no weapon; weapons are acquired exclusively through item drops.

## Glossary

- **Item_Drop_System**: The subsystem responsible for spawning, rendering, and managing all in-battle item drops.
- **Item**: A collectible object that falls from the sky and lands on the stage. Has a type, position, and optional use count.
- **Consumable**: An Item that is immediately consumed on pickup (coin bag, mana bag, health bag).
- **Weapon_Item**: An Item that equips a weapon to the collecting Player. Has exactly 3 uses before it is discarded.
- **Player**: A human-controlled Fighter instance (Player class). Minions and AI fighters are excluded from pickup eligibility.
- **Fighter**: The base class for all combat entities in the game.
- **Minion**: A non-player combat entity managed by MinionManager. Cannot pick up items.
- **Stage**: The current battle arena, including ground and platforms.
- **Spawn_Zone**: The horizontal range across the screen from which items may fall.
- **Weapon_Use**: A single activation of an equipped Weapon_Item's attack. Each Weapon_Item has exactly 3 uses.
- **Nuke_Launcher**: A Weapon_Item that fires 3 projectiles at random horizontal positions across the screen, each creating a large explosion on impact.
- **Gatling_Gun**: A Weapon_Item that rapidly fires a burst of bullets in the Player's facing direction.
- **Staff_Red**: A Weapon_Item (fire staff) that spawns random fire effects across the screen.
- **Staff_Blue**: A Weapon_Item (tsunami staff) that spawns random wave effects across the screen.
- **Staff_Green**: A Weapon_Item (bomb staff) that spawns random bomb effects across the screen.
- **HUD**: The heads-up display showing player stats during battle.

---

## Requirements

### Requirement 1: Remove Starting Weapons

**User Story:** As a game designer, I want all characters to start each round with no weapon, so that weapons are earned through item drops rather than being a fixed character trait.

#### Acceptance Criteria

1. WHEN a new round starts, THE Fighter SHALL initialize with no equipped weapon regardless of the character's `weapon_type` stat.
2. THE Fighter SHALL use unarmed (fist) attacks as the default when no Weapon_Item is equipped.

---

### Requirement 2: Item Spawning

**User Story:** As a player, I want items to drop from the sky during battle, so that the fight has dynamic power-up opportunities.

#### Acceptance Criteria

1. WHILE a round is in the FIGHT state, THE Item_Drop_System SHALL spawn a new Item at a random horizontal position within the Spawn_Zone at a random interval between 5 and 15 seconds.
2. WHEN an Item spawns, THE Item_Drop_System SHALL place the Item above the top of the screen and apply a downward velocity so it falls onto the stage.
3. WHEN a falling Item reaches the ground level or a platform surface, THE Item_Drop_System SHALL stop the Item's vertical movement and mark it as landed.
4. THE Item_Drop_System SHALL select the Item type randomly from the full set of available item types (coin bag, mana bag, health bag, nuke launcher, gatling gun, staff red, staff blue, staff green).
5. THE Item_Drop_System SHALL render each Item using its corresponding 32×32 PNG image from `assets/items/`.
6. WHEN a landed Item has not been picked up within 10 seconds, THE Item_Drop_System SHALL remove it from the stage.
7. THE Item_Drop_System SHALL support at most 3 simultaneously active Items on the stage at any time.

---

### Requirement 3: Item Pickup

**User Story:** As a player, I want to pick up items by walking over them, so that I can gain advantages during the fight.

#### Acceptance Criteria

1. WHEN a Player's collision rectangle overlaps a landed Item's rectangle, THE Item_Drop_System SHALL trigger a pickup event for that Player and that Item.
2. WHEN a pickup event is triggered, THE Item_Drop_System SHALL remove the Item from the stage.
3. THE Item_Drop_System SHALL restrict pickup eligibility to Player instances only; Minion entities SHALL NOT trigger pickup events.
4. IF two Players overlap the same Item simultaneously, THEN THE Item_Drop_System SHALL award the Item to the Player whose center is closest to the Item's center.

---

### Requirement 4: Consumable Items

**User Story:** As a player, I want consumable items to immediately grant their benefit on pickup, so that I can recover resources mid-fight.

#### Acceptance Criteria

1. WHEN a Player picks up a coin bag, THE Fighter SHALL receive 50 coins added to the Player's MinionManager coin balance.
2. WHEN a Player picks up a mana bag, THE Fighter SHALL set the Player's `special_energy` to `max_special`.
3. WHEN a Player picks up a health bag, THE Fighter SHALL set the Player's `health` to `max_health`.
4. WHEN a consumable is picked up, THE Item_Drop_System SHALL display a floating text effect above the Player indicating the benefit received (e.g., "+50G", "MANA FULL", "HP FULL").

---

### Requirement 5: Weapon Item Pickup and Equipping

**User Story:** As a player, I want to pick up weapon items and use them in battle, so that I have access to powerful attacks with limited ammunition.

#### Acceptance Criteria

1. WHEN a Player picks up a Weapon_Item, THE Fighter SHALL equip that weapon and set its use count to 3.
2. WHEN a Player already holds a Weapon_Item and picks up a new Weapon_Item, THE Fighter SHALL replace the current weapon with the new one, discarding any remaining uses.
3. WHEN a Player holds a Weapon_Item, THE HUD SHALL display the weapon icon and remaining use count for that Player.
4. WHEN a Player activates a Weapon_Item attack and the use count is greater than 0, THE Fighter SHALL execute the weapon's attack and decrement the use count by 1.
5. WHEN a Weapon_Item's use count reaches 0, THE Fighter SHALL unequip the weapon and return to unarmed attacks.
6. IF a Player attempts to activate a Weapon_Item attack while the use count is 0, THEN THE Fighter SHALL perform no weapon attack.

---

### Requirement 6: Nuke Launcher Weapon

**User Story:** As a player, I want the nuke launcher to fire multiple projectiles across the screen, so that I can deal area damage to opponents anywhere on the stage.

#### Acceptance Criteria

1. WHEN a Player activates the Nuke_Launcher, THE Fighter SHALL fire exactly 3 nuke projectiles, each at a distinct random horizontal position within the stage bounds.
2. WHEN a nuke projectile reaches the ground or a platform, THE Nuke_Launcher SHALL create an explosion with a hitbox radius of at least 100 pixels.
3. WHEN an explosion hitbox overlaps an opponent Fighter's hurtbox, THE Nuke_Launcher SHALL apply damage and knockback to that Fighter.
4. WHEN an explosion hitbox overlaps an enemy Minion's hurtbox, THE Nuke_Launcher SHALL apply damage to that Minion.

---

### Requirement 7: Gatling Gun Weapon

**User Story:** As a player, I want the gatling gun to fire a rapid burst of bullets forward, so that I can deal sustained damage to opponents in front of me.

#### Acceptance Criteria

1. WHEN a Player activates the Gatling_Gun, THE Fighter SHALL fire a burst of at least 8 bullets in the Player's current facing direction.
2. WHEN a Gatling_Gun bullet overlaps an opponent Fighter's hurtbox, THE Gatling_Gun SHALL apply damage to that Fighter.
3. WHEN a Gatling_Gun bullet travels beyond the stage horizontal bounds, THE Gatling_Gun SHALL remove that bullet.

---

### Requirement 8: Staff Weapons (Red, Blue, Green)

**User Story:** As a player, I want the staff weapons to create random screen-wide effects, so that I can deal unpredictable area damage across the entire stage.

#### Acceptance Criteria

1. WHEN a Player activates Staff_Red, THE Fighter SHALL spawn at least 5 fire effect instances at random horizontal positions across the stage.
2. WHEN a Player activates Staff_Blue, THE Fighter SHALL spawn at least 5 wave effect instances at random horizontal positions across the stage.
3. WHEN a Player activates Staff_Green, THE Fighter SHALL spawn at least 5 bomb effect instances at random horizontal positions across the stage.
4. WHEN any staff effect instance overlaps an opponent Fighter's hurtbox, THE Fighter SHALL apply damage to that Fighter.
5. WHEN any staff effect instance overlaps an enemy Minion's hurtbox, THE Fighter SHALL apply damage to that Minion.

---

### Requirement 9: Weapon HUD Display

**User Story:** As a player, I want to see my currently equipped weapon and remaining uses on the HUD, so that I can make informed decisions about when to use my weapon.

#### Acceptance Criteria

1. WHILE a Player holds a Weapon_Item, THE HUD SHALL display the weapon's icon image near that Player's health bar.
2. WHILE a Player holds a Weapon_Item, THE HUD SHALL display the remaining use count as a number alongside the weapon icon.
3. WHEN a Player has no Weapon_Item equipped, THE HUD SHALL not display any weapon icon or use count for that Player.

---

### Requirement 10: Item Visual Feedback

**User Story:** As a player, I want clear visual feedback when items spawn, fall, and are picked up, so that I can react to item drops during the fight.

#### Acceptance Criteria

1. WHEN an Item is falling, THE Item_Drop_System SHALL render the Item's sprite at its current position each frame.
2. WHEN an Item has landed and is awaiting pickup, THE Item_Drop_System SHALL render the Item's sprite with a subtle idle animation or visual indicator (e.g., gentle bob or glow outline).
3. WHEN a Player picks up an Item, THE Item_Drop_System SHALL play a pickup particle effect at the Item's position.
