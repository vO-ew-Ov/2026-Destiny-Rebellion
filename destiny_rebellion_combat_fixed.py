# -*- coding: utf-8 -*-
"""
DESTINY REBELLION - 전투 시스템 프로토타입
Python 3.10+ / 외부 라이브러리 불필요

기획서 반영:
- 아군 6명 vs 적군 최대 6명
- 플레이어가 행동 가능한 아군을 직접 선택
- 아군 행동마다 적의 대기 카운트 감소, 0이 된 적은 즉시 행동
- 모든 아군의 행동 횟수 소모 후 아군 턴 종료
- 공격은 HIT마다 코인을 굴림 (앞면 확률 50%)
- 요구 앞면 수를 충족한 HIT만 피해 발생
- 요구량을 넘긴 앞면 1개마다 피해량 +5%
- 다단히트, 스킬 쿨타임, 피격 시 반격
- 적 전멸 후 다음 웨이브, 모든 웨이브 클리어 시 승리 / 아군 전멸 시 패배

실행: python destiny_rebellion_combat.py
"""

from dataclasses import dataclass, field
from typing import Optional
import random


# ----------------------------- 데이터 모델 -----------------------------

@dataclass
class Skill:
    name: str
    power: float
    hits: int = 1
    coins: int = 2
    required_heads: int = 1
    cooldown: int = 0
    description: str = ""
    counter_power: Optional[float] = None
    counter_required_heads: int = 1

    def __post_init__(self):
        self.coins = max(1, self.coins)
        self.hits = max(1, self.hits)
        self.required_heads = min(max(0, self.required_heads), self.coins)
        self.counter_required_heads = min(
            max(0, self.counter_required_heads), self.coins
        )


@dataclass
class Fighter:
    name: str
    max_hp: int
    attack: int
    defense: int
    speed: int
    skills: list[Skill]
    is_player: bool = True
    hp: int = field(init=False)
    action_points: int = 1
    counter_charges: int = 1
    wait: int = 1
    cooldowns: dict[str, int] = field(default_factory=dict)
    alive: bool = field(default=True, init=False)

    def __post_init__(self):
        self.hp = self.max_hp
        for skill in self.skills:
            self.cooldowns[skill.name] = 0

    def refresh(self):
        self.alive = self.hp > 0

    def take_damage(self, amount: int) -> int:
        amount = max(1, amount)
        actual = min(self.hp, amount)
        self.hp -= actual
        self.refresh()
        return actual

    def skill_ready(self, skill: Skill) -> bool:
        return self.cooldowns.get(skill.name, 0) <= 0

    def start_cooldown(self, skill: Skill):
        if skill.cooldown > 0:
            self.cooldowns[skill.name] = skill.cooldown

    def reduce_cooldowns(self):
        for name in self.cooldowns:
            self.cooldowns[name] = max(0, self.cooldowns[name] - 1)


# ----------------------------- 스킬 / 캐릭터 -----------------------------

def make_player_party() -> list[Fighter]:
    # 수치와 캐릭터는 기획서에 상세 정의가 없어 프로토타입용으로 임의 설정.
    return [
        Fighter("검은 칼날", 120, 24, 7, 8, [
            Skill("수직 베기", 1.0, coins=2, required_heads=1, description="안정적인 단일 공격"),
            Skill("처형 연격", 0.72, hits=3, coins=2, required_heads=1, cooldown=2,
                  description="3회 공격하는 다단히트"),
            Skill("되받아치기", 0.85, coins=2, required_heads=1, cooldown=1,
                  description="반격용 기술", counter_power=1.25, counter_required_heads=1),
        ]),
        Fighter("유리 사수", 92, 29, 3, 10, [
            Skill("조준 사격", 1.15, coins=3, required_heads=2, description="높은 명중 조건, 높은 위력"),
            Skill("속사", 0.58, hits=3, coins=2, required_heads=1, cooldown=2,
                  description="빠르게 3회 공격"),
            Skill("반격탄", 0.75, coins=2, required_heads=1, cooldown=1,
                  description="반격용 기술", counter_power=1.1),
        ]),
        Fighter("철벽 수감자", 155, 18, 13, 4, [
            Skill("방패 강타", 0.95, coins=2, required_heads=1, description="방어력이 높은 전열 공격"),
            Skill("진압 타격", 1.55, coins=3, required_heads=2, cooldown=2, description="강력하지만 조건이 까다로움"),
            Skill("방어 반격", 0.7, coins=2, required_heads=1, cooldown=1,
                  description="반격용 기술", counter_power=1.35),
        ]),
        Fighter("붉은 집행자", 105, 27, 5, 7, [
            Skill("낙인", 1.0, coins=2, required_heads=1, description="기본 공격"),
            Skill("난도질", 0.8, hits=2, coins=3, required_heads=1, cooldown=2, description="2회 공격"),
            Skill("피의 반격", 0.8, coins=2, required_heads=1, cooldown=1,
                  description="반격용 기술", counter_power=1.2),
        ]),
        Fighter("회색 의무관", 100, 17, 6, 6, [
            Skill("주사기 투척", 0.9, coins=2, required_heads=1, description="기본 원거리 공격"),
            Skill("응급 처치", 0, coins=1, required_heads=0, cooldown=3, description="아군 한 명 회복"),
            Skill("의무 반격", 0.65, coins=2, required_heads=1, cooldown=1,
                  description="반격용 기술", counter_power=0.9),
        ]),
        Fighter("번개의 죄수", 98, 25, 4, 9, [
            Skill("전류 방출", 1.0, coins=2, required_heads=1, description="기본 공격"),
            Skill("낙뢰 연쇄", 0.62, hits=4, coins=2, required_heads=1, cooldown=3,
                  description="4회 공격하는 다단히트"),
            Skill("전격 반사", 0.8, coins=2, required_heads=1, cooldown=1,
                  description="반격용 기술", counter_power=1.15),
        ]),
    ]


ENEMY_TEMPLATES = [
    ("하급 망자", 78, 17, 3, 1),
    ("쇠사슬 사냥개", 92, 20, 4, 1),
    ("붕괴한 경비병", 115, 19, 7, 2),
    ("핏빛 신도", 88, 23, 2, 2),
    ("무너진 처형인", 145, 27, 8, 3),
    ("심연의 감시자", 132, 24, 6, 2),
]


def make_enemy_wave(wave_number: int) -> list[Fighter]:
    count = min(6, 3 + wave_number)  # 첫 웨이브 4명, 이후 최대 6명
    enemies = []
    for i in range(count):
        name, hp, attack, defense, wait = ENEMY_TEMPLATES[(i + wave_number - 1) % len(ENEMY_TEMPLATES)]
        scale = 1 + (wave_number - 1) * 0.12
        enemy = Fighter(
            f"{name} {i + 1}",
            int(hp * scale),
            int(attack * scale),
            defense + (wave_number - 1) // 2,
            random.randint(5, 10),
            [
                Skill("흉악한 일격", 1.0, coins=2, required_heads=1),
                Skill("맹공", 0.72, hits=2, coins=2, required_heads=1, cooldown=2),
            ],
            is_player=False,
        )
        enemy.wait = wait
        enemy.counter_charges = 0
        enemies.append(enemy)
    return enemies


# ----------------------------- 전투 엔진 -----------------------------

class CombatGame:
    def __init__(self):
        self.party = make_player_party()
        self.wave_number = 1
        self.total_waves = 3
        self.enemies = make_enemy_wave(self.wave_number)
        self.logs: list[str] = []
        self.running = True
        self.won = False

    def log(self, message: str):
        self.logs.append(message)
        print(message)

    def living(self, fighters: list[Fighter]) -> list[Fighter]:
        return [f for f in fighters if f.hp > 0]

    def status(self):
        print("\n" + "=" * 72)
        print(f" DESTINY REBELLION  |  웨이브 {self.wave_number}/{self.total_waves}")
        print("-" * 72)
        print(" [아군]")
        for i, f in enumerate(self.party, 1):
            state = "전투 불능" if f.hp <= 0 else f"HP {f.hp}/{f.max_hp}"
            print(f" {i}. {f.name:<10} {state:<17} ATK {f.attack:<3} DEF {f.defense:<2} 행동 {f.action_points}")
        print(" [적군]")
        if not self.living(self.enemies):
            print("  남은 적 없음")
        for i, f in enumerate(self.enemies, 1):
            state = "전투 불능" if f.hp <= 0 else f"HP {f.hp}/{f.max_hp} | 대기 {f.wait}"
            print(f" {i}. {f.name:<14} {state}")
        print("=" * 72)

    def choose_number(self, prompt: str, low: int, high: int) -> int:
        while True:
            raw = input(prompt).strip()
            if raw.lower() in ("q", "quit", "종료"):
                self.running = False
                return low
            try:
                value = int(raw)
                if low <= value <= high:
                    return value
            except ValueError:
                pass
            print(f"{low}~{high} 사이의 숫자를 입력하세요. (q: 전투 종료)")

    def choose_target(self, targets: list[Fighter], prompt="대상 번호 선택: ") -> Fighter:
        for i, target in enumerate(targets, 1):
            print(f" {i}. {target.name} (HP {target.hp}/{target.max_hp})")
        return targets[self.choose_number(prompt, 1, len(targets)) - 1]

    def coin_roll(self, skill: Skill) -> tuple[int, list[str]]:
        heads = 0
        faces = []
        for _ in range(skill.coins):
            if random.random() < 0.5:
                heads += 1
                faces.append("앞")
            else:
                faces.append("뒤")
        return heads, faces

    def attack(self, attacker: Fighter, target: Fighter, skill: Skill,
               power_override: Optional[float] = None,
               required_override: Optional[int] = None,
               is_counter: bool = False):
        if attacker.hp <= 0 or target.hp <= 0:
            return
        power = skill.power if power_override is None else power_override
        required = skill.required_heads if required_override is None else required_override
        title = "반격" if is_counter else skill.name
        self.log(f"\n▶ {attacker.name} 사용: {title} → {target.name}")
        for hit in range(1, skill.hits + 1):
            if target.hp <= 0:
                break
            heads, faces = self.coin_roll(skill)
            face_text = " ".join("앞면" if x == "앞" else "뒷면" for x in faces)
            self.log(f"  HIT {hit}/{skill.hits} | 코인: [{face_text}] ({heads}/{skill.coins} 앞면)")
            if heads < required:
                self.log(f"  실패: 필요 앞면 {required}개를 충족하지 못했습니다.")
                continue
            extra_heads = max(0, heads - required)
            multiplier = 1 + extra_heads * 0.05
            raw_damage = attacker.attack * power * multiplier
            damage = max(1, round(raw_damage - target.defense))
            dealt = target.take_damage(damage)
            self.log(f"  적중! 피해 {dealt} (추가 앞면 {extra_heads}개, 피해 보정 x{multiplier:.2f})")
            self.log(f"  {target.name} HP: {target.hp}/{target.max_hp}")
            if target.hp <= 0:
                self.log(f"  ☠ {target.name} 전투 불능!")
                break
            if not is_counter:
                self.try_counter(target, attacker)

    def try_counter(self, defender: Fighter, attacker: Fighter):
        if not defender.is_player or defender.counter_charges <= 0 or defender.hp <= 0 or attacker.hp <= 0:
            return
        defender.counter_charges -= 1
        counter_skill = next((s for s in defender.skills
                              if s.counter_power is not None and defender.skill_ready(s)), None)
        if counter_skill:
            self.log(f"  ↳ {defender.name} 반격 발동! (남은 반격 {defender.counter_charges})")
            self.attack(defender, attacker, counter_skill,
                        power_override=counter_skill.counter_power,
                        required_override=counter_skill.counter_required_heads,
                        is_counter=True)
            defender.start_cooldown(counter_skill)
        else:
            # 조건을 충족하는 반격 스킬이 없으면 기본 공격으로 반격
            fallback = defender.skills[0]
            self.log(f"  ↳ 사용 가능한 반격 스킬 없음: {fallback.name}으로 반격")
            self.attack(defender, attacker, fallback, is_counter=True)

    def use_skill(self, actor: Fighter, target: Fighter, skill: Skill):
        if skill.name == "응급 처치":
            heal_target = target
            amount = max(1, round(heal_target.max_hp * 0.25))
            before = heal_target.hp
            heal_target.hp = min(heal_target.max_hp, heal_target.hp + amount)
            self.log(f"\n✚ {actor.name}의 {skill.name}: {heal_target.name} HP {before} → {heal_target.hp}")
        else:
            self.attack(actor, target, skill)
        actor.start_cooldown(skill)

    def choose_actor(self) -> Optional[Fighter]:
        """행동 횟수가 남은 아군 중 플레이어가 직접 행동자를 선택한다."""
        candidates = [f for f in self.living(self.party) if f.action_points > 0]
        if not candidates:
            return None

        print("\\n[행동할 아군 선택]")
        for i, fighter in enumerate(candidates, 1):
            print(
                f" {i}. {fighter.name} | HP {fighter.hp}/{fighter.max_hp} "
                f"| 남은 행동 {fighter.action_points}"
            )
        choice = self.choose_number("행동할 아군 번호: ", 1, len(candidates))
        if not self.running:
            return None
        return candidates[choice - 1]

    def choose_player_action(self, actor: Fighter):
        # 한 번 선택된 캐릭터는 행동 1회를 사용한다.
        if actor.action_points <= 0 or actor.hp <= 0 or not self.running:
            return
        self.status()
        print(f"\n[{actor.name}] 행동 선택 (남은 행동 {actor.action_points})")
        for i, skill in enumerate(actor.skills, 1):
            cd = actor.cooldowns.get(skill.name, 0)
            label = f"{i}. {skill.name} | HIT {skill.hits} | 코인 {skill.coins} | 필요 앞면 {skill.required_heads}"
            label += f" | 쿨타임 {cd}" if cd > 0 else " | 사용 가능"
            label += f"\n    {skill.description}"
            print(label)
        print(" 0. 대기 (행동 1회 소모)")
        choice = self.choose_number("스킬 번호: ", 0, len(actor.skills))
        if not self.running:
            return
        if choice == 0:
            self.log(f"{actor.name} 대기.")
            actor.action_points -= 1
            self.after_ally_action()
            return
        skill = actor.skills[choice - 1]
        if not actor.skill_ready(skill):
            print("아직 쿨타임이 남아 있습니다. 행동은 소모되지 않습니다.")
            return
        if skill.name == "응급 처치":
            targets = self.living(self.party)
            target = self.choose_target(targets, "회복할 아군 번호: ")
        else:
            targets = self.living(self.enemies)
            if not targets:
                return
            target = self.choose_target(targets)
        if not self.running:
            return
        self.use_skill(actor, target, skill)
        actor.action_points -= 1
        self.after_ally_action()

    def choose_available_ally(self) -> Optional[Fighter]:
        available = [f for f in self.living(self.party) if f.action_points > 0]
        if not available:
            return None
        print("\n[행동할 아군 선택]")
        for i, fighter in enumerate(self.party, 1):
            if fighter.hp <= 0:
                state = "전투 불능"
            elif fighter.action_points <= 0:
                state = "행동 완료"
            else:
                state = "행동 가능"
            print(f" {i}. {fighter.name} - {state} (HP {fighter.hp}/{fighter.max_hp})")
        while self.running:
            choice = self.choose_number("아군 번호: ", 1, len(self.party))
            if not self.running:
                return None
            fighter = self.party[choice - 1]
            if fighter.hp > 0 and fighter.action_points > 0:
                return fighter
            print("이 캐릭터는 현재 행동할 수 없습니다. 다른 아군을 선택하세요.")
        return None

    def after_ally_action(self):
        # 아군 행동마다 모든 생존 적의 대기 카운트를 1 감소.
        for enemy in self.living(self.enemies):
            enemy.wait -= 1
        # 대기 카운트가 0 이하인 적은 즉시 행동한 뒤 다음 대기값을 받는다.
        # 대기 카운트가 0이 된 적은 해당 아군 행동 직후 즉시 행동한다.
        ready = [e for e in self.living(self.enemies) if e.wait <= 0]
        for enemy in ready:
            if not self.living(self.party):
                return
            self.enemy_action(enemy)
            if enemy.hp > 0:
                enemy.wait = random.randint(2, 4)
        if not self.living(self.enemies):
            return

    def enemy_action(self, enemy: Fighter):
        targets = self.living(self.party)
        if not targets:
            return
        # 적은 기본 공격과 쿨타임이 없는 스킬 중 하나를 사용한다.
        skill = enemy.skills[0]
        if enemy.cooldowns.get(enemy.skills[1].name, 0) <= 0 and random.random() < 0.25:
            skill = enemy.skills[1]
        target = random.choice(targets)
        self.log(f"\n⚠ {enemy.name}의 차례!")
        self.attack(enemy, target, skill)
        enemy.start_cooldown(skill)

    def end_side_turn(self, fighters: list[Fighter]):
        for fighter in fighters:
            fighter.reduce_cooldowns()

    def start_ally_turn(self):
        for fighter in self.living(self.party):
            fighter.action_points = 1
            fighter.counter_charges = 1
        self.log("\n\n◆ 아군 턴 시작! 각 생존 아군은 행동 1회를 얻습니다.")

    def next_wave(self):
        if self.wave_number >= self.total_waves:
            self.won = True
            self.running = False
            return
        self.wave_number += 1
        self.enemies = make_enemy_wave(self.wave_number)
        self.log(f"\n\n★★ 웨이브 {self.wave_number} 시작! 적 {len(self.enemies)}명 출현.")
        # 웨이브 사이 소량 회복으로 플레이 가능성을 확보.
        for fighter in self.living(self.party):
            fighter.hp = min(fighter.max_hp, fighter.hp + 12)
            fighter.reduce_cooldowns()

    def run(self):
        print("\\nDESTINY REBELLION - 전투 프로토타입")
        print("아군 6명으로 웨이브 3개를 돌파하세요.")
        print("매 행동마다 플레이어가 직접 아군을 선택한 뒤 스킬과 대상을 지정합니다.")
        print("행동 후 적의 대기 카운트가 1 감소하며, 0이 된 적은 즉시 행동합니다.")
        print("기획서에 없는 능력치·스킬·웨이브 수는 테스트용 임시 설정입니다.")
        print("전투 중 q를 입력하면 프로토타입을 종료합니다.")

        while self.running:
            if not self.living(self.party):
                self.running = False
                self.won = False
                break

            if not self.living(self.enemies):
                self.log(f"\\n✓ 웨이브 {self.wave_number} 클리어!")
                self.next_wave()
                if not self.running:
                    break
                continue

            self.start_ally_turn()

            # 플레이어가 행동 가능한 아군을 매번 직접 선택한다.
            while self.running and self.living(self.party) and self.living(self.enemies):
                actor = self.choose_actor()
                if not self.running or actor is None:
                    break

                self.choose_player_action(actor)

                if not self.living(self.enemies) or not self.living(self.party):
                    break

                # 모든 생존 아군이 행동을 소모했다면 아군 턴을 종료한다.
                if not any(f.hp > 0 and f.action_points > 0 for f in self.party):
                    break

            self.end_side_turn(self.party)
            self.end_side_turn(self.enemies)

        print("\\n" + "=" * 50)
        if self.won:
            print(" ★ 승리! 모든 웨이브를 돌파했습니다.")
        elif not self.living(self.party):
            print(" 패배 — 아군이 전멸했습니다.")
        else:
            print(" 전투를 종료했습니다.")
        print("=" * 50)


if __name__ == "__main__":
    random.seed()
    CombatGame().run()
