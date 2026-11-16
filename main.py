pip install pygame
python main.py
import pygame
import random
import sys

pygame.init()

WIDTH = 1280
HEIGHT = 720

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Destiny Rebellion Prototype")

clock = pygame.time.Clock()

FONT = pygame.font.SysFont("malgungothic", 24)
BIG_FONT = pygame.font.SysFont("malgungothic", 40)

WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (220,60,60)
GREEN = (70,200,70)
BLUE = (70,120,240)
GRAY = (120,120,120)
DARK = (40,40,40)
YELLOW = (255,220,0)

# --------------------------------
# Skill
# --------------------------------

class Skill:

    def __init__(
        self,
        name,
        multiplier,
        coins,
        need_heads,
        cooldown
    ):

        self.name = name
        self.multiplier = multiplier
        self.coins = coins
        self.need_heads = need_heads
        self.cooldown = cooldown
        self.current_cd = 0

    def ready(self):
        return self.current_cd <= 0


# --------------------------------
# Character
# --------------------------------

class Character:

    def __init__(
        self,
        name,
        hp,
        atk,
        counter
    ):

        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk

        self.counter_max = counter
        self.counter = counter

        self.skills = []

    @property
    def alive(self):
        return self.hp > 0

    def reset_turn(self):

        for s in self.skills:
            if s.current_cd > 0:
                s.current_cd -= 1

        self.counter = self.counter_max


# --------------------------------
# Coin System
# --------------------------------

def coin_result(skill):

    heads = 0

    for _ in range(skill.coins):
        if random.random() < 0.5:
            heads += 1

    success = heads >= skill.need_heads

    return success, heads


def calculate_damage(attacker, skill):

    success, heads = coin_result(skill)

    if not success:
        return False, 0

    bonus = max(0, heads - skill.need_heads)

    damage = int(
        attacker.atk *
        skill.multiplier *
        (1 + bonus * 0.15)
    )

    return True, damage


# --------------------------------
# Create Units
# --------------------------------

def create_player_team():

    team = []

    knight = Character("기사", 420, 45, 2)
    knight.skills = [
        Skill("베기",1.0,2,1,0),
        Skill("십자베기",1.5,3,2,2),
        Skill("처형",2.5,5,3,4)
    ]

    ranger = Character("레인저", 300, 60, 1)
    ranger.skills = [
        Skill("사격",1.0,2,1,0),
        Skill("속사",1.4,3,2,2),
        Skill("저격",2.8,5,3,4)
    ]

    mage = Character("메이지", 260, 70, 1)
    mage.skills = [
        Skill("마력탄",1.1,2,1,0),
        Skill("화염구",1.7,3,2,2),
        Skill("메테오",3.0,5,3,5)
    ]

    team.extend([knight,ranger,mage])

    return team


def create_enemy_team(wave):

    team = []

    for i in range(3):

        enemy = Character(
            f"고블린{i+1}",
            240 + wave*40,
            35 + wave*10,
            1
        )

        enemy.skills = [
            Skill("공격",1.0,2,1,0)
        ]

        team.append(enemy)

    return team


# --------------------------------
# Battle
# --------------------------------

player_team = create_player_team()

wave = 1
MAX_WAVE = 5

enemy_team = create_enemy_team(wave)

selected_ally = 0
selected_skill = None

state = "PLAYER"

message_log = [
    "전투 시작!"
]


def add_log(text):

    message_log.append(text)

    if len(message_log) > 12:
        message_log.pop(0)


def living(team):

    return [x for x in team if x.alive]


def counter_attack(target, attacker):

    if target.counter <= 0:
        return

    target.counter -= 1

    damage = int(target.atk * 0.8)

    attacker.hp -= damage

    add_log(
        f"{target.name} 반격! {damage} 피해"
    )


def player_attack(skill, target):

    global state

    actor = player_team[selected_ally]

    success, dmg = calculate_damage(actor, skill)

    skill.current_cd = skill.cooldown

    if success:

        target.hp -= dmg

        add_log(
            f"{actor.name}의 {skill.name}!"
        )

        add_log(
            f"{target.name}에게 {dmg} 피해"
        )

        if target.alive:
            counter_attack(target, actor)

    else:

        add_log(
            f"{actor.name}의 {skill.name} 실패!"
        )

    state = "ENEMY"


def enemy_turn():

    global wave
    global enemy_team
    global state

    enemies = living(enemy_team)

    for enemy in enemies:

        targets = living(player_team)

        if not targets:
            return

        target = random.choice(targets)

        skill = enemy.skills[0]

        success, dmg = calculate_damage(
            enemy,
            skill
        )

        if success:

            target.hp -= dmg

            add_log(
                f"{enemy.name} 공격!"
            )

            add_log(
                f"{target.name} {dmg} 피해"
            )

            if target.alive:
                counter_attack(target, enemy)

    if not living(enemy_team):

        wave += 1

        if wave > MAX_WAVE:
            state = "WIN"

        else:

            add_log(
                f"웨이브 {wave} 진입!"
            )

            enemy_team = create_enemy_team(wave)

    elif not living(player_team):

        state = "LOSE"

    else:

        for p in player_team:
            p.reset_turn()

        state = "PLAYER"


# --------------------------------
# UI
# --------------------------------

def draw_character(unit, x, y, color):

    pygame.draw.rect(
        screen,
        color,
        (x,y,160,100),
        border_radius=10
    )

    hp_ratio = max(
        0,
        unit.hp / unit.max_hp
    )

    pygame.draw.rect(
        screen,
        RED,
        (x,y+110,160,18)
    )

    pygame.draw.rect(
        screen,
        GREEN,
        (x,y+110,160*hp_ratio,18)
    )

    screen.blit(
        FONT.render(
            unit.name,
            True,
            WHITE
        ),
        (x+10,y+10)
    )

    screen.blit(
        FONT.render(
            f"HP {max(0,int(unit.hp))}/{unit.max_hp}",
            True,
            WHITE
        ),
        (x+10,y+40)
    )


# --------------------------------
# Main Loop
# --------------------------------

while True:

    clock.tick(60)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if state == "PLAYER":

            if event.type == pygame.MOUSEBUTTONDOWN:

                mx,my = pygame.mouse.get_pos()

                # 스킬 선택
                actor = player_team[selected_ally]

                for i,skill in enumerate(actor.skills):

                    rect = pygame.Rect(
                        920,
                        150+i*80,
                        280,
                        60
                    )

                    if rect.collidepoint(mx,my):

                        if skill.ready():

                            selected_skill = skill

                # 적 선택
                if selected_skill:

                    for idx,e in enumerate(enemy_team):

                        rect = pygame.Rect(
                            150+idx*250,
                            80,
                            160,
                            100
                        )

                        if rect.collidepoint(mx,my):
                            if e.alive:

                                player_attack(
                                    selected_skill,
                                    e
                                )

                                selected_skill = None

    screen.fill((25,25,40))

    # 적

    for i,e in enumerate(enemy_team):

        draw_character(
            e,
            150+i*250,
            80,
            RED if e.alive else GRAY
        )

    # 아군

    for i,p in enumerate(player_team):

        draw_character(
            p,
            150+i*250,
            450,
            BLUE if p.alive else GRAY
        )

    # 웨이브

    wave_text = BIG_FONT.render(
        f"Wave {min(wave,MAX_WAVE)}/{MAX_WAVE}",
        True,
        YELLOW
    )

    screen.blit(wave_text,(20,20))

    # 스킬 UI

    actor = player_team[selected_ally]

    title = FONT.render(
        f"선택 캐릭터 : {actor.name}",
        True,
        WHITE
    )

    screen.blit(title,(920,100))

    for i,skill in enumerate(actor.skills):

        rect = pygame.Rect(
            920,
            150+i*80,
            280,
            60
        )

        color = GREEN if skill.ready() else GRAY

        pygame.draw.rect(
            screen,
            color,
            rect,
            border_radius=10
        )

        text = f"{skill.name}"

        if not skill.ready():
            text += f" (CD:{skill.current_cd})"

        screen.blit(
            FONT.render(
                text,
                True,
                BLACK
            ),
            (930,168+i*80)
        )

    # 로그

    pygame.draw.rect(
        screen,
        DARK,
        (20,560,860,140)
    )

    for i,msg in enumerate(message_log):

        t = FONT.render(
            msg,
            True,
            WHITE
        )

        screen.blit(
            t,
            (30,570+i*20)
        )

    # 승패

    if state == "WIN":

        txt = BIG_FONT.render(
            "VICTORY",
            True,
            YELLOW
        )

        screen.blit(txt,(520,320))

    elif state == "LOSE":

        txt = BIG_FONT.render(
            "DEFEAT",
            True,
            RED
        )

        screen.blit(txt,(540,320))

    elif state == "ENEMY":

        enemy_turn()

    pygame.display.flip()