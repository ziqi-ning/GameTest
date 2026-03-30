# Design Document: Item Drop System

## Overview

The Item Drop System adds dynamic mid-battle pickups to DormFight. Items fall from the sky at random intervals, land on the stage, and can be collected by walking over them. Items are either consumables (instant effect) or weapons (3-use limited attacks). All fighters start each round unarmed; weapons are acquired exclusively through drops.

The system is self-contained in `entities/item_drop.py` and integrates with the existing `Fighter`, `Player`, `FightUI`, and `main.py` with minimal changes to existing code.

---

## Architecture

```mermaid
graph TD
    Main["main.py\nupdate_fight()"] -->|update/draw| IDM["ItemDropManager"]
    IDM -->|spawns| Item["ItemDrop"]
    IDM -->|checks overlap| P1["Player (p1)"]
    IDM -->|checks overlap| P2["Player (p2)"]
    IDM -->|apply_item()| Fighter["Fighter base"]
    Fighter -->|equipped_weapon\nweapon_uses| WeaponState
    Fighter -->|attack_weapon()| WA["WeaponAttack\n(nuke/gatling/staff)"]
    WA -->|projectile_manager| PM["ProjectileManager"]
    WA -->|effect_manager| EM["EffectManager"]
    FightUI -->|draw_weapon_hud()| HUD["Weapon Icon + Uses"]
```

**Key design decisions:**

- `ItemDropManager` owns all active `ItemDrop` instances and all weapon-attack state (nuke projectiles, gatling bullets, staff effects). This keeps `Fighter` clean.
- `Fighter` gains only two new fields: `equipped_weapon: Optional[str]` and `weapon_uses: int`. The actual attack logic lives in `ItemDropManager.execute_weapon_attack()`.
- Weapon activation is triggered by the player's existing heavy-attack key (`K`) when a weapon is equipped, falling back to the normal heavy attack when unarmed. This avoids adding new input bindings.
- Starting weapon removal is a one-line change in `Fighter.__init__`: always initialize `weapon_data` to `WeaponType.FIST` regardless of `stats.weapon_type`. The `stats.weapon_type` field is preserved for future use.

---

## Components and Interfaces

### `entities/item_drop.py`

#### `ItemDrop`

Represents a single item on the stage.

```python
class ItemDrop:
    ITEM_TYPES = [
        "coin_bag", "mana_bag", "health_bag",
        "nuke_launcher", "gatling", "staff_red", "staff_blue", "staff_green"
    ]
    WEAPON_TYPES = {"nuke_launcher", "gatling", "staff_red", "staff_blue", "staff_green"}
    ITEM_IMAGES: dict[str, pygame.Surface] = {}  # class-level cache

    def __init__(self, item_type: str, x: float):
        self.item_type = item_type
        self.x = x
        self.y = -32          # starts above screen
        self.vel_y = 4.0      # pixels/frame downward
        self.landed = False
        self.lifetime = 0.0   # seconds since landing
        self.active = True

    def get_rect(self) -> tuple[float, float, float, float]:
        """Returns (x, y, w, h) centered on self.x/self.y"""

    def update(self, dt: float, stage) -> None:
        """Apply gravity until landed; count lifetime after landing."""

    @classmethod
    def load_images(cls) -> None:
        """Load all item PNGs from assets/items/ into ITEM_IMAGES cache."""
```

#### `ItemDropManager`

Manages spawning, updating, pickup detection, and weapon attacks.

```python
class ItemDropManager:
    MAX_ITEMS = 3
    SPAWN_INTERVAL_MIN = 5.0   # seconds
    SPAWN_INTERVAL_MAX = 15.0  # seconds
    ITEM_LIFETIME = 10.0       # seconds before auto-removal
    STAGE_LEFT = 100
    STAGE_RIGHT = 1180

    def __init__(self):
        self.items: list[ItemDrop] = []
        self.spawn_timer: float = random.uniform(5.0, 15.0)
        self.active: bool = False  # only spawns during FIGHT state

        # Weapon attack state
        self.nuke_projectiles: list[NukeProjectile] = []
        self.gatling_bullets: list[GatlingBullet] = []
        self.staff_effects: list[StaffEffect] = []

    def start(self) -> None:
        """Called when round enters FIGHT state."""

    def stop(self) -> None:
        """Called when round ends; clears all items and weapon effects."""

    def update(self, dt: float, stage, players: list) -> None:
        """
        1. Tick spawn timer; spawn if ready and len(items) < MAX_ITEMS.
        2. Update each ItemDrop (physics + lifetime).
        3. Remove expired items.
        4. Check pickup for each player.
        5. Update weapon attack projectiles/effects.
        """

    def check_pickups(self, players: list) -> None:
        """
        For each landed item, find all overlapping players.
        Award to closest. Apply item effect. Remove item.
        """

    def apply_item(self, player: 'Fighter', item: ItemDrop) -> None:
        """Apply consumable effect or equip weapon."""

    def execute_weapon_attack(self, fighter: 'Fighter', stage) -> None:
        """
        Called by Fighter.attack_weapon() when weapon_uses > 0.
        Dispatches to _fire_nuke / _fire_gatling / _fire_staff_*.
        Decrements fighter.weapon_uses; unequips if reaches 0.
        """

    def draw(self, surface: pygame.Surface) -> None:
        """Draw all active items and weapon attack visuals."""
```

#### Weapon Attack Sub-classes (internal to `item_drop.py`)

```python
@dataclass
class NukeProjectile:
    x: float; y: float; vel_y: float = 6.0; active: bool = True
    owner_id: int = 0; damage: int = 150; knockback: float = 20.0

@dataclass
class GatlingBullet:
    x: float; y: float; direction: int; speed: float = 18.0
    active: bool = True; owner_id: int = 0; damage: int = 25

@dataclass
class StaffEffect:
    x: float; y: float; effect_type: str  # "fire"|"wave"|"bomb"
    timer: float = 0.0; duration: float = 0.8
    active: bool = True; owner_id: int = 0; damage: int = 60
    hit_targets: set = field(default_factory=set)  # prevent multi-hit
```

### Changes to `entities/fighter.py`

Two new fields added in `__init__`, after the existing weapon system block:

```python
# Item drop weapon state (replaces character weapon_type at round start)
self.equipped_weapon: Optional[str] = None   # e.g. "nuke_launcher"
self.weapon_uses: int = 0

# Remove starting weapon: always start as FIST
self.weapon_data: WeaponData = get_weapon(WeaponType.FIST)
```

New method:

```python
def attack_weapon(self) -> bool:
    """
    Called by Player.handle_input() when heavy-attack key pressed.
    Returns True if a weapon attack was dispatched, False if unarmed.
    The actual attack logic is delegated to ItemDropManager.
    """
    if self.equipped_weapon and self.weapon_uses > 0:
        # signal to ItemDropManager via a flag
        self.weapon_attack_pending = True
        return True
    return False
```

### Changes to `entities/player.py`

In `handle_input()`, modify the heavy-attack branch:

```python
elif heavy_attack and self.attack_cooldown <= 0:
    if not self.attack_weapon():   # try weapon first
        self.attack_heavy()        # fall back to normal heavy
```

### Changes to `ui/fight_ui.py`

Add `draw_weapon_hud()` called from `FightUI.draw()`:

```python
def draw_weapon_hud(self, surface, fighter, is_player1: bool) -> None:
    """
    If fighter.equipped_weapon is not None, draw:
    - 32x32 weapon icon below the special bar
    - use count number next to the icon
    Position: below p1_special (left side) or p2_special (right side).
    """
```

### Changes to `main.py`

In `start_round()`: create a single shared `ItemDropManager` instance.

```python
self.item_drop_manager = ItemDropManager()
```

In `update_fight()`, after the round state check:

```python
if self.round_state == RoundState.FIGHT:
    self.item_drop_manager.start()  # idempotent
    players = [p for p in [self.player1, self.player2] if p]
    self.item_drop_manager.update(dt, self.stage, players)
    # Handle pending weapon attacks
    for p in players:
        if getattr(p, 'weapon_attack_pending', False):
            p.weapon_attack_pending = False
            self.item_drop_manager.execute_weapon_attack(p, self.stage)
```

In `render()`, after drawing fighters and before drawing HUD:

```python
self.item_drop_manager.draw(main_surface)
```

In `fight_ui.draw()` call site, pass fighters for weapon HUD:

```python
self.fight_ui.draw(main_surface, p1_name, p2_name,
                   self.player1, self.player2)
```

---

## Data Models

### Item Type → Effect Mapping

| item_type       | Category   | Effect                                              |
|-----------------|------------|-----------------------------------------------------|
| `coin_bag`      | Consumable | `minion_manager.coins += 50`                        |
| `mana_bag`      | Consumable | `special_energy = max_special`                      |
| `health_bag`    | Consumable | `health = max_health`                               |
| `nuke_launcher` | Weapon     | equip; 3 uses; fires 3 nuke projectiles per use     |
| `gatling`       | Weapon     | equip; 3 uses; fires 8+ bullets per use             |
| `staff_red`     | Weapon     | equip; 3 uses; spawns 5+ fire effects per use       |
| `staff_blue`    | Weapon     | equip; 3 uses; spawns 5+ wave effects per use       |
| `staff_green`   | Weapon     | equip; 3 uses; spawns 5+ bomb effects per use       |

### Weapon Attack Parameters

| Weapon          | Projectile count | Damage per hit | Knockback | Notes                              |
|-----------------|-----------------|----------------|-----------|------------------------------------|
| Nuke Launcher   | 3 nukes         | 150            | 20        | Explosion radius 100px on landing  |
| Gatling Gun     | 8 bullets       | 25             | 3         | Fires in facing direction          |
| Staff Red       | 5 fire effects  | 60             | 5         | Random x positions across stage    |
| Staff Blue      | 5 wave effects  | 60             | 8         | Random x positions across stage    |
| Staff Green     | 5 bomb effects  | 80             | 10        | Random x positions across stage    |

### `ItemDrop` State Machine

```
FALLING → (reaches ground/platform) → LANDED → (lifetime > 10s OR picked up) → REMOVED
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Fighter starts unarmed

*For any* Fighter initialized with any `CharacterStats.weapon_type`, the fighter's `weapon_data` SHALL be `WeaponType.FIST` and `equipped_weapon` SHALL be `None` after `__init__` completes.

**Validates: Requirements 1.1**

---

### Property 2: Spawn interval is within bounds

*For any* call to `ItemDropManager._next_spawn_interval()`, the returned value SHALL be in the range `[5.0, 15.0]` seconds.

**Validates: Requirements 2.1**

---

### Property 3: Item physics invariants

*For any* newly spawned `ItemDrop`, `y < 0` and `vel_y > 0` (falling). *For any* `ItemDrop` that has landed, `vel_y == 0` and `landed == True`.

**Validates: Requirements 2.2, 2.3**

---

### Property 4: Item expiry

*For any* `ItemDrop` with `landed == True` and `lifetime >= 10.0`, the item SHALL NOT appear in `ItemDropManager.items` after the next `update()` call.

**Validates: Requirements 2.6**

---

### Property 5: Maximum active items

*For any* state of `ItemDropManager` after `update()`, `len(items) <= 3`.

**Validates: Requirements 2.7**

---

### Property 6: Pickup collision and removal

*For any* `Player` whose `get_rect()` overlaps a landed `ItemDrop`'s `get_rect()`, after `check_pickups()` the item SHALL NOT be in `ItemDropManager.items`.

**Validates: Requirements 3.1, 3.2**

---

### Property 7: Only Players can pick up items

*For any* non-`Player` entity (e.g., `AIFighter`, `Minion`) whose bounding box overlaps a landed item, `check_pickups()` SHALL NOT remove the item or apply any effect to that entity.

**Validates: Requirements 3.3**

---

### Property 8: Closest player wins tie-break

*For any* two `Player` instances both overlapping the same `ItemDrop`, the item SHALL be awarded to the player whose center `x` is closer to the item's center `x`.

**Validates: Requirements 3.4**

---

### Property 9: Consumable effects are exact

*For any* `Player` with coin balance `c`, picking up a `coin_bag` SHALL result in `minion_manager.coins == c + 50`. *For any* `Player` with any `special_energy`, picking up a `mana_bag` SHALL result in `special_energy == max_special`. *For any* `Player` with any `health`, picking up a `health_bag` SHALL result in `health == max_health`.

**Validates: Requirements 4.1, 4.2, 4.3**

---

### Property 10: Weapon equip sets uses to 3 and replaces existing

*For any* `Player` (with or without an existing weapon), picking up any `Weapon_Item` SHALL result in `equipped_weapon == item_type` and `weapon_uses == 3`.

**Validates: Requirements 5.1, 5.2**

---

### Property 11: Weapon use decrements count

*For any* `Player` with `weapon_uses == n > 0`, after one call to `execute_weapon_attack()`, `weapon_uses == n - 1`.

**Validates: Requirements 5.4**

---

### Property 12: Weapon unequipped at zero uses

*For any* `Player` with `weapon_uses == 1`, after one call to `execute_weapon_attack()`, `equipped_weapon == None` and `weapon_uses == 0`.

**Validates: Requirements 5.5**

---

### Property 13: Nuke fires exactly 3 projectiles at distinct positions

*For any* `Player` activating the nuke launcher, `execute_weapon_attack()` SHALL add exactly 3 `NukeProjectile` instances to `nuke_projectiles`, each with a distinct `x` value within `[STAGE_LEFT, STAGE_RIGHT]`.

**Validates: Requirements 6.1**

---

### Property 14: Nuke explosion radius and damage

*For any* `NukeProjectile` that has landed, the explosion hitbox radius SHALL be `>= 100` pixels, and *for any* `Fighter` or `Minion` whose hurtbox overlaps that explosion, `take_damage()` SHALL be called with `damage > 0`.

**Validates: Requirements 6.2, 6.3, 6.4**

---

### Property 15: Gatling fires at least 8 bullets and applies damage

*For any* `Player` activating the gatling gun, `execute_weapon_attack()` SHALL add `>= 8` `GatlingBullet` instances. *For any* `GatlingBullet` whose rect overlaps an opponent's hurtbox, `take_damage()` SHALL be called.

**Validates: Requirements 7.1, 7.2**

---

### Property 16: Gatling bullets removed when out of bounds

*For any* `GatlingBullet` with `x < STAGE_LEFT` or `x > STAGE_RIGHT`, `active` SHALL be `False` after the next `update()` call.

**Validates: Requirements 7.3**

---

### Property 17: Each staff type spawns at least 5 effects

*For any* `Player` activating `staff_red`, `staff_blue`, or `staff_green`, `execute_weapon_attack()` SHALL add `>= 5` `StaffEffect` instances of the corresponding `effect_type`.

**Validates: Requirements 8.1, 8.2, 8.3**

---

### Property 18: Staff effects apply damage on overlap

*For any* active `StaffEffect` whose rect overlaps an opponent `Fighter`'s or `Minion`'s hurtbox, `take_damage()` SHALL be called with `damage > 0`, and the target SHALL be added to `hit_targets` to prevent repeated hits.

**Validates: Requirements 8.4, 8.5**

---

## Error Handling

| Scenario | Handling |
|---|---|
| Item image file missing | `ItemDrop.load_images()` falls back to a colored 32×32 rectangle drawn procedurally; logs a warning |
| `stage` is `None` during item update | Items use `GROUND_Y` from config as fallback landing y |
| `player.minion_manager` missing (edge case) | `apply_item()` skips coin grant and logs a warning |
| Weapon attack called with `weapon_uses == 0` | `execute_weapon_attack()` is a no-op; `equipped_weapon` is cleared |
| Two items spawned at same x | Allowed; no deduplication needed |
| `ItemDropManager.stop()` called mid-flight | All items and weapon effects cleared immediately |

---

## Testing Strategy

### Unit Tests

Focus on specific examples and edge cases:

- `test_item_drop_load_images`: verify all 8 image keys are present after `load_images()`
- `test_item_type_selection`: call `_random_item_type()` 1000 times; verify all 8 types appear
- `test_consumable_coin_exact`: player with 0 coins picks up coin_bag → coins == 50
- `test_consumable_mana_full`: player with 0 mana picks up mana_bag → special_energy == max_special
- `test_consumable_health_full`: player with 1 hp picks up health_bag → health == max_health
- `test_weapon_replaces_existing`: player holding nuke picks up gatling → equipped_weapon == "gatling", uses == 3
- `test_no_pickup_when_not_landed`: item still falling, player overlaps → no pickup triggered
- `test_ai_fighter_no_pickup`: AIFighter overlaps item → item remains active

### Property-Based Tests

Use `hypothesis` library. Each test runs minimum 100 iterations.

```
# Feature: item-drop-system, Property 1: Fighter starts unarmed
@given(weapon_type=st.sampled_from(list(WeaponType)))
def test_fighter_starts_unarmed(weapon_type): ...

# Feature: item-drop-system, Property 2: Spawn interval within bounds
@given(st.nothing())  # stateless, just call _next_spawn_interval many times
def test_spawn_interval_in_bounds(): ...

# Feature: item-drop-system, Property 3: Item physics invariants
@given(x=st.floats(100, 1180))
def test_item_spawns_above_screen(x): ...

# Feature: item-drop-system, Property 4: Item expiry
@given(lifetime=st.floats(min_value=10.0, max_value=60.0))
def test_expired_item_removed(lifetime): ...

# Feature: item-drop-system, Property 5: Max 3 active items
@given(spawn_count=st.integers(4, 20))
def test_max_three_items(spawn_count): ...

# Feature: item-drop-system, Property 6: Pickup collision and removal
@given(player_x=st.floats(100, 1180), item_x=st.floats(100, 1180))
def test_pickup_removes_item(player_x, item_x): ...

# Feature: item-drop-system, Property 8: Closest player wins tie-break
@given(p1_x=st.floats(100, 600), p2_x=st.floats(600, 1180), item_x=st.floats(100, 1180))
def test_closest_player_wins(p1_x, p2_x, item_x): ...

# Feature: item-drop-system, Property 9: Consumable effects are exact
@given(coins=st.integers(0, 9999), item_type=st.sampled_from(["coin_bag","mana_bag","health_bag"]))
def test_consumable_exact_effect(coins, item_type): ...

# Feature: item-drop-system, Property 10: Weapon equip sets uses to 3
@given(weapon=st.sampled_from(list(ItemDrop.WEAPON_TYPES)), existing=st.one_of(st.none(), st.sampled_from(...)))
def test_weapon_equip(weapon, existing): ...

# Feature: item-drop-system, Property 11: Weapon use decrements count
@given(uses=st.integers(1, 3))
def test_weapon_use_decrements(uses): ...

# Feature: item-drop-system, Property 12: Weapon unequipped at zero uses
def test_weapon_unequipped_at_zero(): ...

# Feature: item-drop-system, Property 13: Nuke fires 3 distinct projectiles
@given(player_x=st.floats(200, 1000), facing_right=st.booleans())
def test_nuke_fires_three_distinct(player_x, facing_right): ...

# Feature: item-drop-system, Property 15: Gatling fires >= 8 bullets
@given(player_x=st.floats(200, 1000), facing_right=st.booleans())
def test_gatling_fires_eight(player_x, facing_right): ...

# Feature: item-drop-system, Property 16: Gatling bullets removed out of bounds
@given(x=st.one_of(st.floats(-1000, 59), st.floats(1221, 3000)))
def test_gatling_bullet_oob_removed(x): ...

# Feature: item-drop-system, Property 17: Staff spawns >= 5 effects
@given(staff=st.sampled_from(["staff_red","staff_blue","staff_green"]))
def test_staff_spawns_five(staff): ...
```

Each property test MUST be tagged with a comment in the format:
`# Feature: item-drop-system, Property N: <property_text>`
