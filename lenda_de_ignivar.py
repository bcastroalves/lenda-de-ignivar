#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A LENDA DE IGNIVAR - um pequeno CRPG medieval em pixel art
===========================================================
Requisitos : Python 3.8+  e  pygame 2   ->   pip install pygame
Executar   : python lenda_de_ignivar.py

Controles
  Setas / WASD ..... mover no mapa e navegar nos menus
  ENTER / ESPAÇO ... confirmar
  ESC .............. voltar / ficha do personagem (no mapa)
  H / M ............ beber poção de vida / poção de mana (no mapa)

Todos os gráficos são gerados pelo próprio código (pixel art em texto
e desenho procedural), então não há arquivos externos.
"""
import copy
import math
import random
import sys
from collections import deque

import pygame

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
W, H = 960, 640
TILE = 32
MW, MH = 30, 18
HUD_Y = MH * TILE
FPS = 60
D4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

CONFIRMA = (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)
VOLTA = (pygame.K_ESCAPE, pygame.K_BACKSPACE)
CIMA = (pygame.K_UP, pygame.K_w)
BAIXO = (pygame.K_DOWN, pygame.K_s)
ESQ = (pygame.K_LEFT, pygame.K_a)
DIR = (pygame.K_RIGHT, pygame.K_d)

OURO = (235, 195, 80)
BRANCO = (238, 238, 238)
CINZA = (130, 130, 130)
VERDE = (120, 240, 130)
VERMELHO = (240, 90, 90)
AZUL = (110, 170, 255)


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(v, a, b):
    return max(a, min(b, v))


def lerp_cor(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def tom(c, f):
    """Escurece (f<1) ou clareia (f>1) uma cor."""
    return tuple(clamp(int(x * f), 0, 255) for x in c)


# ---------------------------------------------------------------------------
# Pixel art (16x16).  Cada letra é uma cor da paleta; '.' é transparente.
# ---------------------------------------------------------------------------
PAL = {
    'k': (22, 20, 30), 's': (236, 192, 150), 'h': (110, 70, 40), 'm': (180, 185, 200),
    'M': (95, 100, 118), 'r': (190, 45, 45), 'b': (55, 85, 200), 'B': (30, 45, 120),
    'g': (80, 170, 70), 'G': (45, 100, 50), 'y': (240, 200, 60), 'w': (240, 240, 235),
    'n': (135, 90, 50), 'N': (80, 55, 35), 'p': (140, 70, 170), 'o': (245, 140, 40),
    'e': (255, 60, 60), 'c': (120, 220, 255),
}

SPRITES = {
    'guerreiro': [
        ".....kkkkk......",
        "....kmmmmmk.....",
        "....kmmmmmk.....",
        "....kkMMMkk.....",
        "....kskskk...k..",
        "....ksssskk.kmk.",
        "...kkrrrrrk.kmk.",
        "..kmmrrrrrmkkmk.",
        "..kmmryyyrmmkk..",
        "..kmmrrrrrkssk..",
        "..kmmkyyykkkkk..",
        "...kkMMMMMk.....",
        "....kbbkbbk.....",
        "....kbbkbbk.....",
        "...kNNk.kNNk....",
        "...kkkk.kkkk....",
    ],
    'mago': [
        ".......kk.......",
        "......kbbk....kk",
        ".....kbbbk...kck",
        ".....kbybbk..kck",
        "....kbbbbbbk.kk.",
        "...kkkkkkkkkkn..",
        "....kskssk...n..",
        "....kwwwwk...n..",
        "...kbwwwwbk..n..",
        "..kbbbwwbbbkkn..",
        "..kbbbbbbbbskn..",
        "..kbbbybbbbk.n..",
        "..kbbbybbbbk.n..",
        "..kBBBBBBBBk.n..",
        "...kNNkkNNk..n..",
        "...kkkk.kkk.....",
    ],
    'arqueiro': [
        ".....kkkkk......",
        "....kgggggk.....",
        "...kgggggggk....",
        "...kggsssggk.k..",
        "...kgskskgk.knk.",
        "....kssssk..k.nk",
        "...kGGGGGGk.k.nk",
        "..kGGggggGGkk.nk",
        "..ksGgnngGskk.nk",
        "...kGggggGk.k.nk",
        "...kGnnnnGk.k.nk",
        "....kGGGGk..knk.",
        "....kNNkNNk..k..",
        "....kNNkNNk.....",
        "...kNNk.kNNk....",
        "...kkkk.kkkk....",
    ],
    'anao': [
        "................",
        "................",
        "....kk.kkk.kk...",
        "....kwkmmmkwk...",
        "....kkmmmmmkk...",
        "....kmmmmmmmk...",
        "....kskskskk....",
        "...kooooooook...",
        "..kmoooooooomk..",
        "..kmkoooooookmk.",
        "..kskoooooooksk.",
        "...knnnyynnnk...",
        "...kMMMMMMMMk...",
        "...kMMk..kMMk...",
        "..kNNNk..kNNNk..",
        "..kkkkk..kkkkk..",
    ],
    'goblin': [
        "................",
        "................",
        "................",
        ".kk..kkkkk..kk..",
        ".kgkkgggggkkgk..",
        "..kggyggyggk....",
        "...kgggggggk....",
        "...kgkwwkgk.....",
        "....kkkkkk...k..",
        "...knnnnnnk.kmk.",
        "..kgknnnnkgkmk..",
        "..kgknnnnkgkk...",
        "...kknnnnkk.....",
        "....kgk.kgk.....",
        "...kggk.kggk....",
        "...kkkk.kkkk....",
    ],
    'lobo': [
        "................",
        "................",
        "................",
        "................",
        "..kk............",
        ".kmmk.......kk..",
        ".kmmmk.....kmmk.",
        "kemmmmkkkkkmmk..",
        "kmmmmmmmmmmmmk..",
        ".kkkmmmmmmmmmk..",
        "...kmmmmmmmmmk..",
        "...kmmkkkkkmmk..",
        "...kmk....kmk...",
        "...kmk....kmk...",
        "..kkk....kkk....",
        "................",
    ],
    'orc': [
        "................",
        "....kkkkkk......",
        "...kGGGGGGk.....",
        "...kGeGGeGk..kk.",
        "...kGGGGGGk.kmmk",
        "...kGwGGwGk.kmmk",
        "..kkkGGGGkkk.kn.",
        ".kGGNNNNNNGGkkn.",
        ".kGGNmNNmNGGkn..",
        ".kGGNNNNNNkGGn..",
        ".kGkNNNNNNk.kn..",
        "..kkMMMMMMk..n..",
        "...kNNNNNNk.....",
        "...kGGkkGGk.....",
        "..kNNNk.kNNNk...",
        "..kkkkk.kkkkk...",
    ],
    'esqueleto': [
        "................",
        ".....kkkkk......",
        "....kwwwwwk.....",
        "....kwkwkwk.....",
        "....kwwwwwk.....",
        ".....kwkwk......",
        "...kk.kwk.kk....",
        "..kwkkwwwkkwk...",
        "..kwk.kwk.kwk.m.",
        "..kwk.kwk.kwkm..",
        "...k.kwwwk.km...",
        ".....kwkwk......",
        ".....kwkwk......",
        ".....kwkwk......",
        "....kwk.kwk.....",
        "....kkk.kkk.....",
    ],
    'dragao': [
        "......k.....k...",
        ".....krk...krk..",
        "....krrrk.krrrk.",
        "....krrrrkrrrrk.",
        ".kk..krrrrrrrk..",
        "kyrk..krrrrrk...",
        "krrrk.krrrrk....",
        "kwkrrkkrooorkk..",
        ".kkkrrrooooorrk.",
        "....krroooorrrk.",
        "....krrrrrrrrrk.",
        "....krrkkkrrk.kk",
        "....krk...krkkrk",
        "...kyyk..kyyk.kk",
        "....kk....kk....",
        "................",
    ],
}

_cache = {}


def sprite(nome, esc, over=None, flip=False, branco=False):
    chave = (nome, esc, tuple(sorted(over.items())) if over else None, flip, branco)
    s = _cache.get(chave)
    if s is None:
        pal = dict(PAL)
        if over:
            pal.update(over)
        s = pygame.Surface((16 * esc, 16 * esc), pygame.SRCALPHA)
        for y, lin in enumerate(SPRITES[nome][:16]):
            lin = lin.ljust(16, '.')[:16]
            for x, ch in enumerate(lin):
                if ch in pal:
                    s.fill((255, 255, 255) if branco else pal[ch], (x * esc, y * esc, esc, esc))
        if flip:
            s = pygame.transform.flip(s, True, False)
        _cache[chave] = s
    return s


# ---------------------------------------------------------------------------
# Dados do jogo
# ---------------------------------------------------------------------------
THEMES = {
    'floresta': dict(piso=(70, 120, 55), piso2=(84, 138, 62), parede='arvore', pc=(35, 90, 40), bg=((120, 180, 230), (70, 120, 55))),
    'estrada': dict(piso=(150, 130, 90), piso2=(136, 118, 80), parede='arvore', pc=(45, 100, 45), bg=((150, 190, 230), (130, 115, 75))),
    'colinas': dict(piso=(110, 140, 70), piso2=(98, 126, 62), parede='rocha', pc=(115, 110, 100), bg=((220, 160, 120), (95, 120, 60))),
    'caverna': dict(piso=(72, 64, 60), piso2=(60, 54, 50), parede='rocha', pc=(52, 46, 48), bg=((25, 22, 30), (70, 62, 56))),
    'profundo': dict(piso=(56, 50, 64), piso2=(46, 42, 54), parede='cristal', pc=(46, 40, 62), bg=((14, 12, 26), (58, 50, 72))),
    'pantano': dict(piso=(72, 82, 50), piso2=(60, 70, 44), parede='agua', pc=(35, 62, 58), bg=((85, 100, 85), (58, 68, 42))),
    'fortaleza': dict(piso=(96, 86, 80), piso2=(84, 75, 70), parede='tijolo', pc=(92, 62, 52), bg=((70, 30, 30), (88, 78, 72))),
    'neve': dict(piso=(220, 228, 240), piso2=(200, 212, 230), parede='gelo', pc=(120, 140, 175), bg=((160, 185, 220), (215, 225, 238))),
    'ninho': dict(piso=(84, 58, 46), piso2=(72, 50, 40), parede='lava', pc=(44, 32, 32), bg=((70, 25, 15), (95, 55, 38))),
    'covil': dict(piso=(62, 36, 36), piso2=(52, 30, 30), parede='lava', pc=(34, 22, 24), bg=((32, 6, 12), (75, 32, 28))),
}

SKILLS = {
    'golpe': dict(nome='Golpe Poderoso', custo=5, nv=1, tipo='fis', alvo='um', mult=1.8, cor=(255, 220, 120),
                  desc='Um golpe brutal que causa 180% de dano.'),
    'grito': dict(nome='Grito de Guerra', custo=6, nv=2, tipo='buff', buff='atk', turnos=3, cor=(255, 100, 60),
                  desc='Aumenta o ataque em 50% por 3 turnos.'),
    'redemoinho': dict(nome='Redemoinho', custo=9, nv=4, tipo='fis', alvo='todos', mult=1.15, cor=(230, 230, 255),
                       desc='Gira a espada e atinge todos os inimigos.'),
    'baluarte': dict(nome='Baluarte', custo=8, nv=6, tipo='buff', buff='def', turnos=3, cura=0.2, cor=(120, 180, 255),
                     desc='Defesa +60% por 3 turnos e recupera 20% da vida.'),
    'fogo': dict(nome='Bola de Fogo', custo=5, nv=1, tipo='mag', alvo='um', mult=2.0, cor=(255, 120, 30),
                 desc='Lança uma bola de fogo: 200% de dano mágico.'),
    'cura': dict(nome='Cura', custo=7, nv=2, tipo='cura', cura=0.45, cor=(120, 255, 140),
                 desc='Recupera 45% da vida máxima.'),
    'nevasca': dict(nome='Nevasca', custo=10, nv=4, tipo='mag', alvo='todos', mult=1.35, cor=(150, 220, 255),
                    desc='Uma tempestade de gelo atinge todos os inimigos.'),
    'meteoro': dict(nome='Meteoro', custo=16, nv=6, tipo='mag', alvo='um', mult=3.6, ceu=True, cor=(255, 70, 40),
                    desc='Invoca um meteoro devastador: 360% de dano.'),
    'certeiro': dict(nome='Tiro Certeiro', custo=6, nv=1, tipo='fis', alvo='um', mult=1.3, crit=True, cor=(255, 240, 150),
                     desc='Mira no ponto fraco: sempre é um acerto crítico.'),
    'veneno': dict(nome='Flecha Envenenada', custo=5, nv=2, tipo='fis', alvo='um', mult=0.9, veneno=True, cor=(120, 230, 80),
                   desc='Envenena o alvo, que perde vida por 3 turnos.'),
    'chuva': dict(nome='Chuva de Flechas', custo=9, nv=4, tipo='fis', alvo='todos', mult=1.15, cor=(230, 200, 120),
                  desc='Uma saraivada de flechas atinge todos os inimigos.'),
    'falcao': dict(nome='Olho de Falcão', custo=7, nv=6, tipo='buff', buff='falcao', turnos=3, cor=(255, 230, 90),
                   desc='+35% de esquiva e +30% de crítico por 3 turnos.'),
}
BUFF_NOMES = {'atk': 'ATAQUE+', 'def': 'DEFESA+', 'falcao': 'FOCO+'}

CLASSES = {
    'Guerreiro': dict(spr='guerreiro', hp=60, mp=16, atk=12, df=8, mag=3, crit=0.08, eva=0.05, regen=1,
                      cres=dict(hp=12, mp=2, atk=3, df=2, mag=0.5), skills=['golpe', 'grito', 'redemoinho', 'baluarte'],
                      arma='Espada', armadura='Armadura', nome='Aldric',
                      desc="Resistente e forte no corpo a corpo. Aguenta os golpes mais pesados."),
    'Mago': dict(spr='mago', hp=38, mp=40, atk=5, df=3, mag=14, crit=0.05, eva=0.06, regen=3,
                 cres=dict(hp=7, mp=6, atk=1, df=1, mag=3.5), skills=['fogo', 'cura', 'nevasca', 'meteoro'],
                 arma='Cajado', armadura='Manto', nome='Elara',
                 desc="Frágil, mas domina fogo e gelo. Ataca com magia e pode se curar."),
    'Arqueiro': dict(spr='arqueiro', hp=46, mp=22, atk=11, df=5, mag=5, crit=0.20, eva=0.12, regen=1,
                     cres=dict(hp=9, mp=3, atk=3, df=1.5, mag=1), skills=['certeiro', 'veneno', 'chuva', 'falcao'],
                     arma='Arco', armadura='Couro', nome='Kael',
                     desc="Ágil e preciso. Muitos acertos críticos, esquivas e venenos."),
}
ORDEM_CLASSES = ['Guerreiro', 'Mago', 'Arqueiro']

INIMIGOS = {
    'goblin': dict(nome='Goblin', spr='goblin', hp=18, atk=7, df=2, mag=2, xp=6, ouro=4, ia=[]),
    'goblin_xama': dict(nome='Xamã Goblin', spr='goblin', over={'n': (110, 50, 140), 'N': (70, 30, 90), 'g': (130, 175, 95)},
                        hp=16, atk=5, df=1, mag=8, xp=9, ouro=6, ia=[('dardo', 0.45), ('curar', 0.25)]),
    'lobo': dict(nome='Lobo Cinzento', spr='lobo', hp=20, atk=8, df=2, mag=0, xp=7, ouro=3, ia=[('mordida', 0.3)]),
    'orc': dict(nome='Orc', spr='orc', hp=40, atk=12, df=5, mag=0, xp=14, ouro=9, ia=[('esmagar', 0.2)]),
    'berserker': dict(nome='Orc Berserker', spr='orc', over={'G': (125, 70, 55), 'N': (150, 30, 30)},
                      hp=48, atk=15, df=4, mag=0, xp=20, ouro=12, ia=[('furia', 0.25), ('esmagar', 0.25)]),
    'esqueleto': dict(nome='Esqueleto', spr='esqueleto', hp=26, atk=10, df=6, mag=0, xp=11, ouro=7, ia=[('esmagar', 0.15)]),
    'drake': dict(nome='Dragão Jovem', spr='dragao', over={'r': (210, 110, 40), 'o': (250, 210, 90)},
                  hp=60, atk=16, df=7, mag=14, xp=28, ouro=18, ia=[('dardo', 0.35)]),
    'chefe_goblin': dict(nome='Gnarl, o Rei Goblin', spr='goblin', over={'n': (200, 160, 40), 'N': (150, 110, 20), 'g': (60, 130, 50)},
                         hp=130, atk=13, df=5, mag=4, xp=70, ouro=60, ia=[('furia', 0.2), ('esmagar', 0.3)], boss=True, esc=1.4),
    'troll': dict(nome='Troll das Cavernas', spr='orc', over={'G': (95, 115, 125), 'N': (70, 60, 50), 'M': (80, 80, 80)},
                  hp=270, atk=19, df=8, mag=0, xp=130, ouro=90, ia=[('esmagar', 0.35)], regen=0.05, boss=True, esc=1.6),
    'senhor_guerra': dict(nome='Grukk, Senhor da Guerra', spr='orc', over={'G': (40, 95, 40), 'N': (35, 35, 45), 'M': (200, 170, 60)},
                          hp=360, atk=25, df=11, mag=0, xp=180, ouro=120, ia=[('furia', 0.2), ('esmagar', 0.35)], boss=True, esc=1.6),
    'dragao': dict(nome='Ignivar, o Dragão Negro', spr='dragao', over={'r': (62, 46, 78), 'o': (170, 70, 210), 'y': (255, 220, 60)},
                   hp=950, atk=34, df=14, mag=32, xp=0, ouro=0, ia=[('esmagar', 0.3)], sopro=3, boss=True, esc=2.2),
}

MISSOES = [
    dict(nome="A Floresta de Valverde", tema='floresta', obj='todos', grupos=4, pool=['goblin', 'goblin', 'lobo'], tam=(1, 2),
         texto="Saudações, forasteiro! Sou Borin Martelo-de-Pedra, guardião de Pedraforte, o último reino dos anões. "
               "Ignivar, o Dragão Negro, despertou e reuniu goblins e orcs sob suas asas. Primeiro, livre a Floresta de "
               "Valverde dos goblins saqueadores. Quando todos caírem, o portal rúnico se abrirá."),
    dict(nome="A Estrada dos Mercadores", tema='estrada', obj='resgate', n=3, grupos=4, pool=['goblin', 'lobo', 'goblin_xama'], tam=(1, 2),
         texto="Uma caravana de mercadores anões foi emboscada na estrada. Três sobreviventes estão escondidos entre as árvores. "
               "Encontre-os antes que os lobos sintam o cheiro deles!"),
    dict(nome="As Colinas Uivantes", tema='colinas', obj='chefe', chefe='chefe_goblin', escolta=['goblin', 'goblin_xama'], grupos=4,
         pool=['goblin', 'goblin_xama', 'lobo'], tam=(1, 3),
         texto="Os goblins obedecem a Gnarl, o autoproclamado Rei Goblin, escondido nas colinas. Derrote-o e o bando se dispersará. "
               "Cuidado com os xamãs: eles lançam fogo e curam os aliados."),
    dict(nome="As Minas de Khazrund", tema='caverna', obj='resgate', n=4, grupos=5, pool=['goblin', 'orc', 'esqueleto'], tam=(1, 2),
         texto="Orcs invadiram Khazrund, nossas minas ancestrais! Quatro mineiros ficaram presos nos túneis. "
               "Traga meus irmãos de volta, e a forja de Pedraforte trabalhará para você."),
    dict(nome="Os Salões Profundos", tema='profundo', obj='chefe', chefe='troll', escolta=['esqueleto'], grupos=4,
         pool=['orc', 'esqueleto', 'goblin_xama'], tam=(1, 2),
         texto="Nas profundezas, algo enorme bloqueia a passagem para o leste: um Troll das Cavernas. "
               "Ele se regenera a cada turno, então golpeie forte e sem descanso."),
    dict(nome="O Pântano dos Mortos", tema='pantano', obj='todos', grupos=5, pool=['esqueleto', 'lobo', 'goblin_xama'], tam=(1, 3),
         texto="Os xamãs do dragão ergueram os mortos no Pântano dos Mortos. Esqueletos vagam pelas águas escuras. "
               "Destrua todos para abrir o caminho até a fortaleza orc."),
    dict(nome="A Fortaleza de Grukk", tema='fortaleza', obj='chefe', chefe='senhor_guerra', escolta=['berserker', 'goblin_xama'], grupos=4,
         pool=['orc', 'berserker', 'goblin_xama'], tam=(1, 3),
         texto="Grukk, o Senhor da Guerra, comanda o exército orc em nome de Ignivar. Invada a fortaleza e derrube-o. "
               "Sem Grukk, os orcs não marcharão sobre Pedraforte."),
    dict(nome="Os Picos Gélidos", tema='neve', obj='resgate', n=3, grupos=4, pool=['drake', 'lobo', 'berserker'], tam=(1, 2),
         texto="Nossos batedores foram capturados nos Picos Gélidos, onde dragões jovens caçam. "
               "Resgate os três: só eles conhecem a trilha secreta até o covil."),
    dict(nome="O Ninho dos Dragões", tema='ninho', obj='todos', grupos=5, pool=['drake', 'berserker', 'esqueleto'], tam=(1, 3),
         texto="A trilha leva ao ninho onde a ninhada de Ignivar é criada. Derrote todos os dragões jovens "
               "e seus guardiões. Sem os filhotes, o Dragão Negro estará sozinho."),
    dict(nome="O Covil de Ignivar", tema='covil', obj='chefe', chefe='dragao', escolta=[], grupos=3, pool=['drake', 'berserker'], tam=(1, 2),
         texto="Chegou a hora. Ignivar aguarda sobre montanhas de ouro roubado. A cada três turnos ele solta seu Sopro de Fogo Negro: "
               "esteja com a vida alta quando ele vier. Por Pedraforte!"),
]


# ---------------------------------------------------------------------------
# Personagens
# ---------------------------------------------------------------------------
class Heroi:
    def __init__(self, classe):
        c = CLASSES[classe]
        self.classe = classe
        self.nome = c['nome']
        self.spr = c['spr']
        self.nivel = 1
        self.xp = 0
        self.b = {k: float(c[k]) for k in ('hp', 'mp', 'atk', 'df', 'mag')}
        self.arma = 0
        self.armadura = 0
        self.hp = self.maxhp
        self.mp = self.maxmp
        self.pocoes = 3
        self.eteres = 2
        self.ouro = 25
        self.buffs = {}
        self.veneno = 0
        self.veneno_dano = 0

    @property
    def c(self):
        return CLASSES[self.classe]

    @property
    def maxhp(self):
        return int(self.b['hp'] + self.armadura * 10)

    @property
    def maxmp(self):
        return int(self.b['mp'])

    @property
    def atk(self):
        return self.b['atk'] + (self.arma * 1 if self.classe == 'Mago' else self.arma * 3)

    @property
    def mag(self):
        return self.b['mag'] + (self.arma * 3 if self.classe == 'Mago' else 0)

    @property
    def df(self):
        return self.b['df'] + self.armadura * 2

    def atk_ef(self):
        return self.atk * (1.5 if 'atk' in self.buffs else 1.0)

    def df_ef(self):
        return self.df * (1.6 if 'def' in self.buffs else 1.0)

    def crit_ef(self):
        return self.c['crit'] + (0.3 if 'falcao' in self.buffs else 0)

    def eva_ef(self):
        return self.c['eva'] + (0.35 if 'falcao' in self.buffs else 0)

    def prox_xp(self):
        return 20 * self.nivel + 10

    def ganhar_xp(self, n):
        msgs = []
        self.xp += n
        while self.xp >= self.prox_xp():
            self.xp -= self.prox_xp()
            self.nivel += 1
            for k, v in self.c['cres'].items():
                self.b[k] += v
            self.hp, self.mp = self.maxhp, self.maxmp
            msgs.append(f"Subiu para o nível {self.nivel}! Vida e mana restauradas.")
            for key in self.c['skills']:
                if SKILLS[key]['nv'] == self.nivel:
                    msgs.append(f"Nova habilidade: {SKILLS[key]['nome']}!")
        return msgs


class Inimigo:
    def __init__(self, tipo, mi):
        d = INIMIGOS[tipo]
        self.d, self.tipo, self.nome = d, tipo, d['nome']
        self.boss = d.get('boss', False)
        fh = 1 if self.boss else 1 + 0.14 * mi
        fa = 1 if self.boss else 1 + 0.09 * mi
        fd = 1 if self.boss else 1 + 0.08 * mi
        self.maxhp = int(d['hp'] * fh)
        self.hp = self.maxhp
        self.atk = d['atk'] * fa
        self.mag = d['mag'] * fa
        self.df = d['df'] * fd
        self.xp = int(d['xp'] * fh)
        self.ouro = int(d['ouro'] * fh)
        self.buffs = {}
        self.veneno = 0
        self.veneno_dano = 0
        self.turno = 0
        self.flash = 0
        self.lunge = 0
        self.morto_t = 0
        self.pos = (0, 0)
        self.esc = 5

    def atk_ef(self):
        return self.atk * (1.5 if 'furia' in self.buffs else 1.0)


# ---------------------------------------------------------------------------
# Combate por turnos
# ---------------------------------------------------------------------------
HERO_POS = (220, 320)


class Combate:
    def __init__(self, jogo, tipos, tema, boss):
        self.j = jogo
        self.h = jogo.heroi
        self.boss = boss
        self.tema = THEMES[tema]
        self.inims = [Inimigo(t, jogo.missao) for t in tipos][:3]
        n = len(self.inims)
        if n == 1 and self.inims[0].boss:
            pts = [(710, 270)]
        else:
            pts = {1: [(700, 300)], 2: [(640, 240), (815, 330)], 3: [(630, 205), (825, 255), (720, 370)]}[n]
        for e, p in zip(self.inims, pts):
            e.pos = p
            e.esc = int(5 * e.d.get('esc', 1)) if e.boss else 5
        self.fundo = self.criar_fundo()
        self.log, self.fx, self.txts = [], [], []
        self.queue, self.qt, self._novos = [], 0.0, None
        self.fase, self.menu, self.sel = 'jogador', 'main', 0
        self.alvo_i, self.pendente, self.menu_ant = 0, None, 'main'
        self.h_lunge = self.h_flash = self.shake = self.t = 0.0
        self.resultado, self.fim_t, self.recompensa = None, 0.0, []
        self.h.buffs = {}
        self.h.veneno = 0
        nomes = ", ".join(e.nome for e in self.inims)
        self.add_log(("Surge: " if n == 1 else "Surgem: ") + nomes + "!")

    # ---------------- utilidades
    def criar_fundo(self):
        s = pygame.Surface((W, 440))
        c1, c2 = self.tema['bg']
        hor = 250
        ceu_b = lerp_cor(c1, (255, 255, 255), 0.25)
        for y in range(hor):
            s.fill(lerp_cor(c1, ceu_b, y / hor), (0, y, W, 1))
        pts = [(0, hor)]
        for x in range(0, W + 40, 40):
            pts.append((x, hor - 40 - int(30 * math.sin(x * 0.013) + 20 * math.sin(x * 0.037 + 1))))
        pts.append((W, hor))
        pygame.draw.polygon(s, tom(lerp_cor(c1, c2, 0.5), 0.7), pts)
        for y in range(hor, 440):
            s.fill(lerp_cor(c2, tom(c2, 0.55), (y - hor) / (440 - hor)), (0, y, W, 1))
        rng = random.Random(7)
        for _ in range(140):
            s.fill(tom(c2, rng.choice([0.8, 1.2])), (rng.randrange(W), rng.randrange(hor + 5, 440), 3, 2))
        return s

    def add_log(self, s):
        self.log.append(s)
        self.log = self.log[-6:]

    def flutuar(self, pos, s, cor, grande=False):
        self.txts.append(dict(x=pos[0], y=pos[1], s=s, cor=cor, t=0.0, g=grande))

    def burst(self, pos, cor, dur=0.4):
        self.fx.append(dict(tipo='burst', x=pos[0], y=pos[1], cor=cor, t=0.0, dur=dur))

    def push(self, d, fn):
        (self._novos if self._novos is not None else self.queue).append((d, fn))

    def vivos(self):
        return [e for e in self.inims if e.hp > 0]

    def opcoes_main(self):
        ops = ['Atacar', 'Habilidades', 'Itens']
        if not self.boss:
            ops.append('Fugir')
        return ops

    # ---------------- entrada
    def tecla(self, k):
        if self.resultado:
            if self.resultado != 'fuga' and self.fim_t > 0.7 and k in CONFIRMA:
                self.j.fim_combate(self)
            return
        if self.fase != 'jogador' or self.queue:
            return
        h = self.h
        if self.menu == 'main':
            ops = self.opcoes_main()
            if k in CIMA:
                self.sel = (self.sel - 1) % len(ops)
            elif k in BAIXO:
                self.sel = (self.sel + 1) % len(ops)
            elif k in CONFIRMA:
                op = ops[self.sel]
                if op == 'Atacar':
                    self.escolher_alvo(('atacar',))
                elif op == 'Habilidades':
                    self.menu, self.sel = 'skills', 0
                elif op == 'Itens':
                    self.menu, self.sel = 'itens', 0
                elif op == 'Fugir':
                    self.acao(('fugir',), None)
        elif self.menu == 'skills':
            lst = h.c['skills']
            if k in CIMA:
                self.sel = (self.sel - 1) % len(lst)
            elif k in BAIXO:
                self.sel = (self.sel + 1) % len(lst)
            elif k in VOLTA:
                self.menu, self.sel = 'main', 1
            elif k in CONFIRMA:
                key = lst[self.sel]
                sk = SKILLS[key]
                if h.nivel < sk['nv']:
                    self.add_log(f"{sk['nome']} requer nível {sk['nv']}.")
                elif h.mp < sk['custo']:
                    self.add_log("Mana insuficiente!")
                elif sk.get('alvo') == 'um':
                    self.escolher_alvo(('skill', key))
                else:
                    self.acao(('skill', key), None)
        elif self.menu == 'itens':
            if k in CIMA or k in BAIXO:
                self.sel = 1 - self.sel
            elif k in VOLTA:
                self.menu, self.sel = 'main', 2
            elif k in CONFIRMA:
                item = ('pocao', 'eter')[self.sel]
                qtd = h.pocoes if item == 'pocao' else h.eteres
                if qtd <= 0:
                    self.add_log("Você não tem mais desse item.")
                else:
                    self.acao(('item', item), None)
        elif self.menu == 'alvo':
            vivos = self.vivos()
            if k in CIMA or k in ESQ:
                self.alvo_i = (self.alvo_i - 1) % len(vivos)
            elif k in BAIXO or k in DIR:
                self.alvo_i = (self.alvo_i + 1) % len(vivos)
            elif k in VOLTA:
                self.menu = self.menu_ant
            elif k in CONFIRMA:
                self.acao(self.pendente, vivos[self.alvo_i % len(vivos)])

    def escolher_alvo(self, acao):
        vivos = self.vivos()
        if len(vivos) == 1:
            self.acao(acao, vivos[0])
        else:
            self.menu_ant, self.menu, self.pendente, self.alvo_i = self.menu, 'alvo', acao, 0

    # ---------------- ações do herói
    def acao(self, acao, alvo):
        self.fase, self.menu, self.sel = 'acao', 'main', 0
        h = self.h
        tipo = acao[0]
        if tipo == 'atacar':
            verbo = {'Guerreiro': 'golpeia', 'Mago': 'dispara um raio arcano em', 'Arqueiro': 'atira em'}[h.classe]
            self.add_log(f"{h.nome} {verbo} {alvo.nome}.")
            if h.classe == 'Mago':
                self.ataque_anim([alvo], 0.75, True, (190, 120, 255))
            else:
                self.ataque_anim([alvo], 1.0, False, (255, 255, 255))
        elif tipo == 'skill':
            self.usar_skill(acao[1], alvo)
        elif tipo == 'item':
            if acao[1] == 'pocao':
                h.pocoes -= 1
                self.add_log(f"{h.nome} bebe uma Poção de Vida.")
                self.curar_heroi(0.45, VERDE)
            else:
                h.eteres -= 1
                v = min(int(h.maxmp * 0.5), h.maxmp - h.mp)
                h.mp += v
                self.add_log(f"{h.nome} bebe uma Poção de Mana.")
                self.flutuar(HERO_POS, f"+{v} MP", AZUL)
                self.burst(HERO_POS, AZUL)
        elif tipo == 'fugir':
            if random.random() < 0.65:
                self.add_log("Você fugiu do combate!")
                self.resultado, self.fim_t = 'fuga', 0.0
                return
            self.add_log("Não conseguiu fugir!")
        self.push(0.45, self.turno_inimigos)

    def ataque_anim(self, alvos, mult, magico, cor, crit=False, veneno=False, ceu=False):
        h = self.h
        distancia = magico or h.classe == 'Arqueiro'
        if distancia:
            for a in alvos:
                x0, y0 = (a.pos[0] - 140, -30) if ceu else (HERO_POS[0] + 40, HERO_POS[1] - 10)
                self.fx.append(dict(tipo='proj', x0=x0, y0=y0, x1=a.pos[0], y1=a.pos[1], cor=cor, t=0.0,
                                    dur=0.45 if ceu else 0.32, r=(14 if ceu else 7) if magico else 4, arco=not ceu))
            atraso = 0.46 if ceu else 0.33
        else:
            self.h_lunge = 0.3
            atraso = 0.17

        def acertar():
            for a in alvos:
                if a.hp > 0:
                    if not distancia:
                        self.fx.append(dict(tipo='corte', x=a.pos[0], y=a.pos[1], cor=cor, t=0.0, dur=0.25))
                    self.dano_inimigo(a, mult, magico, crit, veneno)
        self.push(atraso, acertar)

    def usar_skill(self, key, alvo):
        sk = SKILLS[key]
        h = self.h
        h.mp -= sk['custo']
        self.add_log(f"{h.nome} usa {sk['nome']}!")
        alvos = [alvo] if sk.get('alvo') == 'um' else self.vivos()
        t = sk['tipo']
        if t == 'fis':
            self.ataque_anim(alvos, sk['mult'], False, sk['cor'], sk.get('crit', False), sk.get('veneno', False))
        elif t == 'mag':
            self.ataque_anim(alvos, sk['mult'], True, sk['cor'], ceu=sk.get('ceu', False))
        elif t == 'cura':
            self.curar_heroi(sk['cura'], sk['cor'])
        elif t == 'buff':
            h.buffs[sk['buff']] = sk['turnos']
            self.burst(HERO_POS, sk['cor'], 0.6)
            self.flutuar((HERO_POS[0], HERO_POS[1] - 20), BUFF_NOMES[sk['buff']], sk['cor'])
            if sk.get('cura'):
                self.curar_heroi(sk['cura'], VERDE)

    def curar_heroi(self, frac, cor):
        h = self.h
        v = min(max(1, int(h.maxhp * frac)), h.maxhp - h.hp)
        h.hp += v
        self.flutuar(HERO_POS, f"+{v}", VERDE)
        self.burst(HERO_POS, cor, 0.5)

    def dano_inimigo(self, a, mult, magico, crit=False, veneno=False):
        h = self.h
        base = (h.mag if magico else h.atk_ef()) * mult * random.uniform(0.9, 1.1)
        dd = base - a.df * (0.25 if magico else 0.5)
        dd = max(1, int(max(dd, base * 0.2)))
        c = crit or (random.random() < (0.05 if magico else h.crit_ef()))
        if c:
            dd = int(dd * 1.75)
            self.shake = max(self.shake, 0.15)
        a.hp = max(0, a.hp - dd)
        a.flash = 0.2
        self.flutuar(a.pos, f"{dd}!" if c else str(dd), (255, 230, 80) if c else BRANCO, grande=c)
        if veneno and a.hp > 0:
            a.veneno, a.veneno_dano = 3, max(2, int(h.atk_ef() * 0.4))
            self.add_log(f"{a.nome} foi envenenado!")
        if a.hp <= 0:
            self.add_log(f"{a.nome} foi derrotado!")

    # ---------------- turno dos inimigos
    def turno_inimigos(self):
        if self.checar_fim():
            return
        for e in self.vivos():
            self.push(0.5, lambda e=e: self.acao_inimigo(e))
        self.push(0.35, self.fim_rodada)

    def acao_inimigo(self, e):
        if e.hp <= 0 or self.h.hp <= 0 or self.resultado:
            return
        e.turno += 1
        d = e.d
        if d.get('sopro') and e.turno % d['sopro'] == 0:
            self.add_log(f"{e.nome} solta o SOPRO DE FOGO NEGRO!")
            self.fx.append(dict(tipo='proj', x0=e.pos[0] - 60, y0=e.pos[1] - 20, x1=HERO_POS[0], y1=HERO_POS[1],
                                cor=(190, 80, 255), t=0.0, dur=0.4, r=18, arco=False))
            self.push(0.42, lambda: self.dano_heroi(e, 2.2, True))
            return
        esc = None
        r, acum = random.random(), 0.0
        for nome, p in d['ia']:
            acum += p
            if r < acum:
                esc = nome
                break
        if esc == 'curar':
            feridos = [a for a in self.vivos() if a.hp < a.maxhp * 0.7]
            if feridos:
                alvo = min(feridos, key=lambda a: a.hp / a.maxhp)
                v = int(alvo.maxhp * 0.35)
                alvo.hp = min(alvo.maxhp, alvo.hp + v)
                self.add_log(f"{e.nome} cura {alvo.nome}.")
                self.flutuar(alvo.pos, f"+{v}", VERDE)
                self.burst(alvo.pos, VERDE)
                return
            esc = None
        if esc == 'furia':
            if 'furia' not in e.buffs:
                e.buffs['furia'] = 3
                self.add_log(f"{e.nome} entra em fúria!")
                self.flutuar(e.pos, "FÚRIA", VERMELHO)
                self.burst(e.pos, VERMELHO)
                return
            esc = None
        if esc == 'dardo':
            self.add_log(f"{e.nome} lança um Dardo de Fogo!")
            self.fx.append(dict(tipo='proj', x0=e.pos[0] - 30, y0=e.pos[1], x1=HERO_POS[0], y1=HERO_POS[1],
                                cor=(255, 130, 30), t=0.0, dur=0.32, r=7, arco=True))
            self.push(0.33, lambda: self.dano_heroi(e, 1.5, True))
            return
        e.lunge = 0.3
        if esc == 'esmagar':
            self.add_log(f"{e.nome} usa Esmagar!")
            mult = 1.6
        elif esc == 'mordida':
            self.add_log(f"{e.nome} morde com presas venenosas!")
            mult = 1.0
        else:
            self.add_log(f"{e.nome} ataca.")
            mult = 1.0
        veneno = esc == 'mordida'
        self.push(0.17, lambda: self.dano_heroi(e, mult, False, veneno))

    def dano_heroi(self, e, mult, magico, veneno=False):
        h = self.h
        if h.hp <= 0:
            return
        if not magico and random.random() < h.eva_ef():
            self.flutuar(HERO_POS, "Esquiva!", (200, 220, 255))
            self.add_log(f"{h.nome} se esquiva!")
            return
        base = (e.mag if magico else e.atk_ef()) * mult * random.uniform(0.9, 1.1)
        dd = base - h.df_ef() * (0.25 if magico else 0.5)
        dd = max(1, int(max(dd, base * 0.2)))
        h.hp = max(0, h.hp - dd)
        self.h_flash = 0.25
        if mult >= 1.5:
            self.shake = 0.3
        if not magico:
            self.fx.append(dict(tipo='corte', x=HERO_POS[0], y=HERO_POS[1], cor=VERMELHO, t=0.0, dur=0.25))
        self.flutuar(HERO_POS, f"-{dd}", VERMELHO, grande=mult >= 1.5)
        if veneno and h.hp > 0:
            h.veneno, h.veneno_dano = 3, max(2, int(e.atk * 0.3))
            self.add_log(f"{h.nome} foi envenenado!")

    def fim_rodada(self):
        h = self.h
        if h.hp > 0 and h.veneno > 0:
            h.hp = max(1, h.hp - h.veneno_dano)
            h.veneno -= 1
            self.flutuar(HERO_POS, f"-{h.veneno_dano}", (150, 230, 90))
        for e in self.vivos():
            if e.veneno > 0:
                e.hp = max(0, e.hp - e.veneno_dano)
                e.veneno -= 1
                e.flash = 0.15
                self.flutuar(e.pos, str(e.veneno_dano), (150, 230, 90))
                if e.hp <= 0:
                    self.add_log(f"{e.nome} sucumbiu ao veneno!")
                    continue
            if e.d.get('regen') and e.hp < e.maxhp:
                v = int(e.maxhp * e.d['regen'])
                e.hp = min(e.maxhp, e.hp + v)
                self.flutuar((e.pos[0], e.pos[1] + 30), f"+{v}", VERDE)
            for k in list(e.buffs):
                e.buffs[k] -= 1
                if e.buffs[k] <= 0:
                    del e.buffs[k]
        for k in list(h.buffs):
            h.buffs[k] -= 1
            if h.buffs[k] <= 0:
                del h.buffs[k]
        h.mp = min(h.maxmp, h.mp + h.c['regen'])
        if not self.checar_fim():
            self.fase, self.menu, self.sel = 'jogador', 'main', 0

    def checar_fim(self):
        if self.resultado:
            return True
        h = self.h
        if h.hp <= 0:
            self.resultado, self.fim_t = 'derrota', 0.0
            self.add_log(f"{h.nome} caiu em combate...")
            self.queue = []
            return True
        if not self.vivos():
            self.resultado, self.fim_t = 'vitoria', 0.0
            self.queue = []
            xp = sum(e.xp for e in self.inims)
            ouro = sum(e.ouro for e in self.inims)
            h.ouro += ouro
            self.recompensa = [f"+{xp} XP", f"+{ouro} de ouro"]
            if random.random() < 0.25:
                h.pocoes += 1
                self.recompensa.append("Encontrou uma Poção de Vida!")
            self.recompensa += h.ganhar_xp(xp)
            h.hp = min(h.maxhp, h.hp + int(h.maxhp * 0.25))
            h.mp = min(h.maxmp, h.mp + int(h.maxmp * 0.35))
            h.veneno, h.buffs = 0, {}
            return True
        return False

    # ---------------- atualização
    def update(self, dt):
        self.t += dt
        self.h_lunge = max(0, self.h_lunge - dt)
        self.h_flash = max(0, self.h_flash - dt)
        self.shake = max(0, self.shake - dt)
        for e in self.inims:
            e.flash = max(0, e.flash - dt)
            e.lunge = max(0, e.lunge - dt)
            if e.hp <= 0:
                e.morto_t += dt
        novos = []
        for f in self.fx:
            f['t'] += dt
            if f['t'] < f['dur']:
                novos.append(f)
            elif f['tipo'] == 'proj':
                novos.append(dict(tipo='burst', x=f['x1'], y=f['y1'], cor=f['cor'], t=0.0, dur=0.4))
        self.fx = novos
        for tx in self.txts:
            tx['t'] += dt
        self.txts = [tx for tx in self.txts if tx['t'] < 1.1]
        if self.queue:
            self.qt += dt
            if self.qt >= self.queue[0][0]:
                _, fn = self.queue.pop(0)
                self.qt = 0.0
                self._novos = []
                fn()
                self.queue[0:0] = self._novos
                self._novos = None
        if self.resultado:
            self.fim_t += dt
            if self.resultado == 'fuga' and self.fim_t > 0.6:
                self.j.fim_combate(self)

    # ---------------- desenho
    def desenhar(self):
        j = self.j
        tela = j.tela
        ox = random.randint(-5, 5) if self.shake > 0 else 0
        oy = random.randint(-4, 4) if self.shake > 0 else 0
        tela.fill((0, 0, 0))
        tela.blit(self.fundo, (ox, oy))
        # herói
        hx, hy = HERO_POS
        off = math.sin(math.pi * (1 - self.h_lunge / 0.3)) * 60 if self.h_lunge > 0 else 0
        bob = math.sin(self.t * 3) * 2
        sombra(tela, hx + off + ox, hy + 46 + oy, 80)
        pisca = self.h_flash > 0 and int(self.t * 25) % 2 == 0
        if self.h.hp > 0 or not self.resultado:
            tela.blit(sprite(self.h.spr, 6, branco=pisca), (hx - 48 + off + ox, hy - 48 + bob + oy))
        # inimigos
        vivos = self.vivos()
        for i, e in enumerate(self.inims):
            if e.hp <= 0 and e.morto_t > 0.6:
                continue
            tam = 16 * e.esc
            x, y = e.pos
            off = -math.sin(math.pi * (1 - e.lunge / 0.3)) * 50 if e.lunge > 0 else 0
            bob = math.sin(self.t * 2.5 + i * 1.7) * 3
            sombra(tela, x + off + ox, y + tam // 2 + oy, int(tam * 0.8))
            spr = sprite(e.d['spr'], e.esc, e.d.get('over'), branco=e.flash > 0)
            if e.hp <= 0:
                spr = spr.copy()
                spr.set_alpha(int(255 * clamp(1 - e.morto_t / 0.6, 0, 1)))
            tela.blit(spr, (x - tam // 2 + off + ox, y - tam // 2 + bob + oy))
            if e.hp > 0:
                topo = y - tam // 2 - 30
                bw = max(90, int(tam * 0.7))
                j.txt(e.nome, (x, topo - 20), BRANCO, centro=True)
                j.barra(x - bw // 2, topo, bw, 10, e.hp, e.maxhp, (200, 60, 60), texto=False)
                st = []
                if e.veneno:
                    st.append("VENENO")
                if 'furia' in e.buffs:
                    st.append("FÚRIA")
                if st:
                    j.txt(" ".join(st), (x, topo + 12), (255, 170, 90), centro=True)
                if self.menu == 'alvo' and vivos and vivos[self.alvo_i % len(vivos)] is e:
                    ay = topo - 34 + math.sin(self.t * 8) * 4
                    pygame.draw.polygon(tela, OURO, [(x - 10, ay), (x + 10, ay), (x, ay + 12)])
        # efeitos
        for f in self.fx:
            p = f['t'] / f['dur']
            if f['tipo'] == 'proj':
                x = lerp(f['x0'], f['x1'], p)
                y = lerp(f['y0'], f['y1'], p) - (math.sin(math.pi * p) * 30 if f['arco'] else 0)
                for k in range(3, 0, -1):
                    px = lerp(f['x0'], f['x1'], max(0, p - k * 0.05))
                    py = lerp(f['y0'], f['y1'], max(0, p - k * 0.05)) - (math.sin(math.pi * max(0, p - k * 0.05)) * 30 if f['arco'] else 0)
                    pygame.draw.circle(tela, tom(f['cor'], 0.6), (int(px), int(py)), max(1, f['r'] - k * 2))
                pygame.draw.circle(tela, f['cor'], (int(x), int(y)), f['r'])
                pygame.draw.circle(tela, (255, 255, 230), (int(x), int(y)), max(1, f['r'] // 2))
            elif f['tipo'] == 'burst':
                rad = 6 + p * 40
                pygame.draw.circle(tela, f['cor'], (int(f['x']), int(f['y'])), int(rad), max(1, int(5 * (1 - p))))
                for k in range(8):
                    ang = k * math.pi / 4 + p
                    sx = f['x'] + math.cos(ang) * rad * 1.2
                    sy = f['y'] + math.sin(ang) * rad * 1.2
                    tela.fill(f['cor'], (int(sx), int(sy), 4, 4))
            elif f['tipo'] == 'corte':
                for k in range(3):
                    a = (f['x'] - 30 + k * 12, f['y'] - 35)
                    b = (lerp(a[0], a[0] + 40, min(1, p * 2)), lerp(a[1], a[1] + 60, min(1, p * 2)))
                    pygame.draw.line(tela, f['cor'], a, b, 3)
        for tx in self.txts:
            fonte = 'g' if tx['g'] else 'm'
            j.txt(tx['s'], (tx['x'], tx['y'] - 70 - tx['t'] * 45), tx['cor'], f=fonte, centro=True)
        # status do herói
        h = self.h
        box = pygame.Rect(12, 12, 300, 96)
        j.painel(box)
        j.txt(f"{h.nome} - {h.classe}  Nv {h.nivel}", (24, 20), OURO)
        j.barra(24, 44, 276, 18, h.hp, h.maxhp, (200, 60, 60))
        j.barra(24, 66, 276, 18, h.mp, h.maxmp, (60, 100, 210))
        st = [f"{BUFF_NOMES[k]}({v})" for k, v in h.buffs.items()]
        if h.veneno:
            st.append(f"VENENO({h.veneno})")
        if st:
            j.txt("  ".join(st), (24, 88), (255, 220, 120))
        if self.boss:
            b = next((e for e in self.inims if e.boss), None)
            if b:
                j.txt("CHEFE: " + b.nome, (W // 2 + 120, 20), (255, 120, 90), f='m', centro=True)
        self.desenhar_menu()
        if self.resultado in ('vitoria', 'derrota'):
            self.desenhar_resultado()

    def desenhar_menu(self):
        j, h = self.j, self.h
        tela = j.tela
        box = pygame.Rect(12, 452, 280, 176)
        j.painel(box)
        x, y = box.x + 16, box.y + 12
        ativo = self.fase == 'jogador' and not self.queue and not self.resultado
        si = self.sel
        if self.menu == 'skills' and ativo:
            titulo = 'Habilidades'
            itens = []
            for key in h.c['skills']:
                sk = SKILLS[key]
                ok = h.nivel >= sk['nv'] and h.mp >= sk['custo']
                extra = f"Nv {sk['nv']}" if h.nivel < sk['nv'] else f"{sk['custo']} MP"
                itens.append((sk['nome'], ok, extra))
        elif self.menu == 'itens' and ativo:
            titulo = 'Itens'
            itens = [("Poção de Vida", h.pocoes > 0, f"x{h.pocoes}"), ("Poção de Mana", h.eteres > 0, f"x{h.eteres}")]
        elif self.menu == 'alvo' and ativo:
            titulo = 'Escolha o alvo'
            itens = [(e.nome, True, f"{e.hp}") for e in self.vivos()]
            si = self.alvo_i
        else:
            titulo = 'Ações' if ativo else 'Aguarde...'
            itens = [(o, True, '') for o in self.opcoes_main()]
        j.txt(titulo, (x, y), OURO, f='m')
        y += 34
        for i, (nome, ok, extra) in enumerate(itens):
            cor = BRANCO if ok else CINZA
            if not ativo:
                cor = (100, 100, 100)
            if i == si and ativo:
                pygame.draw.rect(tela, (70, 55, 95), (box.x + 8, y - 4, box.w - 16, 26))
                j.txt('>', (x - 4, y), OURO)
            j.txt(nome, (x + 14, y), cor)
            if extra:
                j.txt(extra, (box.right - 14, y), AZUL if ok else CINZA, dir=True)
            y += 28
        lb = pygame.Rect(304, 452, 644, 176)
        j.painel(lb)
        if self.menu == 'skills' and ativo:
            sk = SKILLS[h.c['skills'][self.sel]]
            j.txt(sk['nome'], (lb.x + 16, lb.y + 12), sk['cor'], f='m')
            yy = lb.y + 46
            for linha in j.quebrar(sk['desc'], 'm', lb.w - 32):
                j.txt(linha, (lb.x + 16, yy), BRANCO, f='m')
                yy += 28
            j.txt(f"Custo: {sk['custo']} MP    Requer nível {sk['nv']}", (lb.x + 16, lb.bottom - 34), AZUL)
        else:
            yy = lb.y + 12
            for i, linha in enumerate(self.log):
                cor = BRANCO if i == len(self.log) - 1 else (170, 170, 185)
                j.txt(linha, (lb.x + 16, yy), cor)
                yy += 26

    def desenhar_resultado(self):
        j = self.j
        r = pygame.Rect(0, 0, 460, 110 + 28 * len(self.recompensa))
        r.center = (W // 2, 210)
        j.painel(r, borda=OURO if self.resultado == 'vitoria' else VERMELHO)
        if self.resultado == 'vitoria':
            j.txt("VITÓRIA!", (W // 2, r.y + 14), OURO, f='g', centro=True)
            y = r.y + 62
            for linha in self.recompensa:
                j.txt(linha, (W // 2, y), VERDE if 'nível' in linha or 'Nova' in linha else BRANCO, centro=True)
                y += 28
        else:
            j.txt("DERROTA", (W // 2, r.y + 14), VERMELHO, f='g', centro=True)
            j.txt("Suas forças se esgotaram...", (W // 2, r.y + 64), BRANCO, centro=True)
        if self.fim_t > 0.7:
            j.txt("ENTER para continuar", (W // 2, r.bottom - 30), CINZA, centro=True)


def sombra(tela, x, y, w):
    s = pygame.Surface((max(4, w), max(2, w // 4)), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, 90), s.get_rect())
    tela.blit(s, (x - w // 2, y - w // 8))


# ---------------------------------------------------------------------------
# Mapa de exploração (gerado proceduralmente)
# ---------------------------------------------------------------------------
def desenhar_tile(surf, tx, ty, parede, tema, rng):
    x, y = tx * TILE, ty * TILE
    r = pygame.Rect(x, y, TILE, TILE)
    fc, fc2 = tema['piso'], tema['piso2']
    k, wc = tema['parede'], tema['pc']
    if not parede or k == 'arvore':
        surf.fill(fc, r)
        for _ in range(6):
            surf.fill(fc2 if rng.random() < 0.6 else tom(fc, 1.15), (x + rng.randrange(TILE - 2), y + rng.randrange(TILE - 2), 2, 2))
        if not parede:
            return
    if k == 'arvore':
        pygame.draw.rect(surf, (90, 60, 35), (x + 13, y + 18, 6, 12))
        pygame.draw.circle(surf, tom(wc, 0.75), (x + 16, y + 14), 13)
        pygame.draw.circle(surf, wc, (x + 14, y + 12), 10)
        pygame.draw.circle(surf, tom(wc, 1.4), (x + 11, y + 9), 4)
    elif k in ('rocha', 'cristal', 'gelo'):
        surf.fill(tom(wc, 0.7), r)
        pygame.draw.polygon(surf, wc, [(x + 2, y + 28), (x + 6, y + 6), (x + 18, y + 2), (x + 30, y + 10), (x + 29, y + 29)])
        pygame.draw.polygon(surf, tom(wc, 1.3), [(x + 6, y + 8), (x + 18, y + 4), (x + 22, y + 10), (x + 10, y + 14)])
        if k == 'cristal' and rng.random() < 0.35:
            c = rng.choice([(150, 90, 230), (90, 200, 230)])
            pygame.draw.polygon(surf, c, [(x + 14, y + 26), (x + 18, y + 8), (x + 23, y + 26)])
            pygame.draw.line(surf, (230, 230, 255), (x + 18, y + 10), (x + 17, y + 22))
        if k == 'gelo':
            pygame.draw.polygon(surf, (245, 250, 255), [(x + 6, y + 8), (x + 18, y + 3), (x + 29, y + 11), (x + 18, y + 12)])
    elif k == 'agua':
        surf.fill(wc, r)
        for _ in range(2):
            px, py = x + rng.randrange(4, 20), y + rng.randrange(6, 26)
            pygame.draw.line(surf, tom(wc, 1.5), (px, py), (px + 8, py))
        if rng.random() < 0.25:
            pygame.draw.line(surf, (90, 110, 50), (x + 24, y + 28), (x + 24, y + 14), 2)
    elif k == 'tijolo':
        surf.fill(tom(wc, 0.55), r)
        for row in range(4):
            off = 0 if row % 2 == 0 else 8
            for col in range(-1, 3):
                rr = pygame.Rect(x + col * 16 + off + 1, y + row * 8 + 1, 14, 6).clip(r)
                if rr.w > 0:
                    surf.fill(wc, rr)
    elif k == 'lava':
        surf.fill(wc, r)
        pygame.draw.polygon(surf, tom(wc, 1.6), [(x + 3, y + 26), (x + 8, y + 6), (x + 26, y + 5), (x + 29, y + 27)])
        if rng.random() < 0.5:
            pts = [(x + rng.randrange(4, 28), y + rng.randrange(4, 28)) for _ in range(3)]
            pygame.draw.lines(surf, (255, 110, 20), False, pts, 2)


class Mapa:
    def __init__(self, idx, seed):
        self.idx = idx
        self.m = MISSOES[idx]
        self.tema = THEMES[self.m['tema']]
        rng = random.Random(seed)
        g = [[1] * MW for _ in range(MH)]

        def cav(x, y):
            if 1 <= x < MW - 1 and 1 <= y < MH - 1:
                g[y][x] = 0

        def pisos():
            return [(x, y) for y in range(MH) for x in range(MW) if g[y][x] == 0]

        sx, sy = 2, MH // 2
        x, y = sx, sy
        while x < MW - 3:                      # caminho principal até o leste
            cav(x, y)
            r = rng.random()
            if r < 0.5:
                x += 1
            elif r < 0.75:
                y = max(2, y - 1)
            else:
                y = min(MH - 3, y + 1)
        cav(x, y)
        for _ in range(rng.randint(4, 6)):     # clareiras / salas
            px, py = rng.choice(pisos())
            w, h = rng.randint(3, 6), rng.randint(3, 5)
            x0, y0 = px - rng.randrange(w), py - rng.randrange(h)
            for yy in range(y0, y0 + h):
                for xx in range(x0, x0 + w):
                    cav(xx, yy)
        cnt, alvo = len(pisos()), int(MW * MH * 0.46)
        while cnt < alvo:                       # túneis aleatórios
            x, y = rng.choice(pisos())
            for _ in range(rng.randint(15, 40)):
                dx, dy = rng.choice(D4)
                x, y = clamp(x + dx, 1, MW - 2), clamp(y + dy, 1, MH - 2)
                if g[y][x] == 1:
                    g[y][x] = 0
                    cnt += 1
        self.g = g
        dist, pai, fila = {(sx, sy): 0}, {}, deque([(sx, sy)])
        while fila:
            p = fila.popleft()
            for dx, dy in D4:
                q = (p[0] + dx, p[1] + dy)
                if g[q[1]][q[0]] == 0 and q not in dist:
                    dist[q] = dist[p] + 1
                    pai[q] = p
                    fila.append(q)
        self.px, self.py = sx, sy
        maxd = max(dist.values())
        cands = [p for p in dist if p[0] > MW * 0.6] or list(dist)
        self.saida = max(cands, key=lambda p: dist[p])
        ocupado = {(sx, sy), self.saida}

        def longe(p, lista, d):
            return all(max(abs(p[0] - q[0]), abs(p[1] - q[1])) >= d for q in lista)

        self.inimigos = []
        if self.m.get('chefe'):
            p = self.saida
            for _ in range(2):
                p = pai.get(p, p)
            self.inimigos.append(dict(x=p[0], y=p[1], tipos=[self.m['chefe']] + self.m.get('escolta', []), boss=True, parado=0))
            ocupado.add(p)
        livres = [p for p in dist if dist[p] >= 6 and p not in ocupado]
        rng.shuffle(livres)
        meta = self.m['grupos'] + len(self.inimigos)
        for espaco in (4, 2):
            for p in livres:
                if len(self.inimigos) >= meta:
                    break
                ps = [(e['x'], e['y']) for e in self.inimigos]
                if p not in ocupado and longe(p, ps, espaco) and longe(p, [self.saida], 2):
                    tipos = [rng.choice(self.m['pool']) for _ in range(rng.randint(*self.m['tam']))]
                    self.inimigos.append(dict(x=p[0], y=p[1], tipos=tipos, boss=False, parado=0))
                    ocupado.add(p)
        self.anoes = []
        if self.m['obj'] == 'resgate':
            cands = [p for p in dist if dist[p] >= maxd * 0.35 and p not in ocupado]
            rng.shuffle(cands)
            for espaco in (5, 2):
                for p in cands:
                    if len(self.anoes) >= self.m['n']:
                        break
                    if p not in ocupado and longe(p, self.anoes, espaco):
                        self.anoes.append(p)
                        ocupado.add(p)
        self.total_anoes = len(self.anoes)
        becos = [p for p in dist if p not in ocupado and dist[p] >= 4 and
                 sum(g[p[1] + dy][p[0] + dx] == 0 for dx, dy in D4) <= 1]
        outros = [p for p in dist if p not in ocupado and dist[p] >= 4]
        rng.shuffle(becos)
        rng.shuffle(outros)
        self.baus = []
        for p in becos + outros:
            if len(self.baus) >= 2 + idx % 2:
                break
            if p not in ocupado and longe(p, self.baus, 4):
                self.baus.append(p)
                ocupado.add(p)
        self.avisado = False
        self.surf = pygame.Surface((MW * TILE, MH * TILE))
        trng = random.Random(seed + 1)
        for ty in range(MH):
            for tx in range(MW):
                desenhar_tile(self.surf, tx, ty, g[ty][tx] == 1, self.tema, trng)

    def inimigo_em(self, x, y):
        for e in self.inimigos:
            if e['x'] == x and e['y'] == y:
                return e
        return None

    def objetivo_ok(self):
        o = self.m['obj']
        if o == 'todos':
            return not self.inimigos
        if o == 'chefe':
            return not any(e['boss'] for e in self.inimigos)
        return not self.anoes

    def objetivo_txt(self):
        if self.objetivo_ok():
            return "Portal aberto! Vá até o círculo rúnico."
        o = self.m['obj']
        if o == 'todos':
            return f"Derrote todos os inimigos (restam {len(self.inimigos)} grupos)"
        if o == 'chefe':
            return f"Derrote {INIMIGOS[self.m['chefe']]['nome']}"
        return f"Resgate os anões ({self.total_anoes - len(self.anoes)}/{self.total_anoes})"

    def mover_inimigos(self):
        """Inimigos próximos perseguem o herói. Retorna o inimigo que o alcançou."""
        for e in self.inimigos:
            if e['boss']:
                continue
            if e['parado'] > 0:
                e['parado'] -= 1
                continue
            dx, dy = self.px - e['x'], self.py - e['y']
            if abs(dx) + abs(dy) > 6 or random.random() > 0.5:
                continue
            passos = []
            if dx:
                passos.append((1 if dx > 0 else -1, 0))
            if dy:
                passos.append((0, 1 if dy > 0 else -1))
            if abs(dy) > abs(dx):
                passos.reverse()
            for mx, my in passos:
                nx, ny = e['x'] + mx, e['y'] + my
                if (nx, ny) == (self.px, self.py):
                    return e
                if (self.g[ny][nx] == 0 and not self.inimigo_em(nx, ny) and (nx, ny) not in self.baus
                        and (nx, ny) not in self.anoes and (nx, ny) != self.saida):
                    e['x'], e['y'] = nx, ny
                    break
        return None

    def desenhar(self, tela, t, heroi):
        tela.blit(self.surf, (0, 0))
        sx, sy = self.saida
        cx, cy = sx * TILE + 16, sy * TILE + 16
        if self.objetivo_ok():
            for i in range(3):
                rr = 14 - i * 4 + int(2 * math.sin(t * 5 + i))
                pygame.draw.circle(tela, [(120, 50, 200), (170, 90, 255), (230, 200, 255)][i], (cx, cy), max(2, rr))
            for i in range(4):
                a = t * 3 + i * math.pi / 2
                tela.fill((255, 240, 255), (int(cx + math.cos(a) * 15), int(cy + math.sin(a) * 15), 3, 3))
        else:
            pygame.draw.circle(tela, (95, 95, 110), (cx, cy), 14)
            pygame.draw.circle(tela, (60, 60, 72), (cx, cy), 10)
            for i in range(4):
                a = i * math.pi / 2 + 0.4
                pygame.draw.line(tela, (130, 120, 160), (cx, cy), (cx + math.cos(a) * 9, cy + math.sin(a) * 9), 1)
        for bx, by in self.baus:
            x, y = bx * TILE, by * TILE
            pygame.draw.rect(tela, (22, 20, 30), (x + 5, y + 8, 22, 19))
            pygame.draw.rect(tela, (140, 90, 45), (x + 6, y + 13, 20, 13))
            pygame.draw.rect(tela, (105, 65, 35), (x + 6, y + 9, 20, 5))
            pygame.draw.rect(tela, OURO, (x + 14, y + 13, 4, 5))
        for ax, ay in self.anoes:
            b = math.sin(t * 4 + ax) * 2
            tela.blit(sprite('anao', 2), (ax * TILE, ay * TILE + b))
            pygame.draw.rect(tela, OURO, (ax * TILE + 14, ay * TILE - 12 + b * 2, 4, 8))
            pygame.draw.rect(tela, OURO, (ax * TILE + 14, ay * TILE - 2 + b * 2, 4, 3))
        for i, e in enumerate(self.inimigos):
            d = INIMIGOS[e['tipos'][0]]
            x, y = e['x'] * TILE, e['y'] * TILE
            b = math.sin(t * 3 + i) * 1.5
            if e['boss']:
                pygame.draw.circle(tela, (200, 40, 40), (x + 16, y + 18), int(17 + 2 * math.sin(t * 4)), 2)
            tela.blit(sprite(d['spr'], 2, d.get('over')), (x, y + b))
        tela.blit(sprite(heroi.spr, 2), (self.px * TILE, self.py * TILE))


# ---------------------------------------------------------------------------
# Jogo (estados, telas e laço principal)
# ---------------------------------------------------------------------------
class Jogo:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("A Lenda de Ignivar")
        self.tela = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.f = {'p': pygame.font.Font(None, 24), 'm': pygame.font.Font(None, 30),
                  'g': pygame.font.Font(None, 50), 't': pygame.font.Font(None, 86)}
        pygame.key.set_repeat(190, 95)
        self.estado, self.sel = 'titulo', 0
        self.heroi = self.mapa = self.combate = self.snap = self.enc = None
        self.missao = 0
        self.tempo = self.t = self.trans = 0.0
        self.toasts = []
        self.semente = 0
        self.bonus = 0
        self.rodando = True
        rng = random.Random(3)
        self.estrelas = [(rng.randrange(W), rng.randrange(380), rng.random()) for _ in range(110)]

    # ---------------- helpers de desenho
    def txt(self, s, pos, cor=BRANCO, f='p', centro=False, dir=False, sombra=True):
        fonte = self.f[f]
        img = fonte.render(s, True, cor)
        x, y = pos
        if centro:
            x -= img.get_width() // 2
        if dir:
            x -= img.get_width()
        if sombra:
            self.tela.blit(fonte.render(s, True, (0, 0, 0)), (x + 2, y + 2))
        self.tela.blit(img, (x, y))
        return img.get_width()

    def painel(self, rect, cor=(24, 20, 34), borda=(190, 150, 70)):
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        s.fill((*cor, 235))
        self.tela.blit(s, rect.topleft)
        pygame.draw.rect(self.tela, borda, rect, 2)

    def barra(self, x, y, w, h, val, maxv, cor, texto=True):
        pygame.draw.rect(self.tela, (25, 22, 30), (x, y, w, h))
        frac = clamp(val / maxv if maxv else 0, 0, 1)
        pygame.draw.rect(self.tela, cor, (x, y, int(w * frac), h))
        pygame.draw.rect(self.tela, tom(cor, 1.4), (x, y, int(w * frac), max(1, h // 4)))
        pygame.draw.rect(self.tela, (0, 0, 0), (x, y, w, h), 1)
        if texto:
            self.txt(f"{int(val)}/{int(maxv)}", (x + w // 2, y + (h - 16) // 2), BRANCO, centro=True)

    def quebrar(self, s, f, larg):
        linhas, atual = [], ''
        for p in s.split():
            tst = (atual + ' ' + p).strip()
            if self.f[f].size(tst)[0] <= larg:
                atual = tst
            else:
                linhas.append(atual)
                atual = p
        if atual:
            linhas.append(atual)
        return linhas

    def toast(self, s):
        self.toasts.append([s, 0.0])
        self.toasts = self.toasts[-3:]

    def ceu_noturno(self, c1=(18, 10, 32), c2=(90, 30, 35)):
        for y in range(0, H, 4):
            self.tela.fill(lerp_cor(c1, c2, y / H), (0, y, W, 4))
        for x, y, b in self.estrelas:
            v = int(150 + 100 * math.sin(self.t * 2 + b * 10))
            self.tela.fill((v, v, v), (x, y, 2, 2))

    def montanhas(self, base, cor):
        pts = [(0, H)]
        for x in range(0, W + 30, 30):
            pts.append((x, base - int(60 * math.sin(x * 0.008) + 35 * math.sin(x * 0.023 + 2))))
        pts.append((W, H))
        pygame.draw.polygon(self.tela, cor, pts)

    # ---------------- fluxo
    def novo_jogo(self, classe):
        self.heroi = Heroi(classe)
        self.missao = 0
        self.tempo = 0.0
        self.semente = random.randrange(100000)
        self.iniciar_briefing()

    def iniciar_briefing(self):
        self.estado = 'briefing'
        self.snap = copy.deepcopy(self.heroi)

    def iniciar_missao(self):
        self.mapa = Mapa(self.missao, self.semente + self.missao * 101)
        self.estado = 'mapa'
        self.toasts = []

    def iniciar_combate(self, en):
        self.enc = en
        self.combate = Combate(self, en['tipos'], self.mapa.m['tema'], en['boss'])
        self.estado = 'combate'
        self.trans = 0.35

    def fim_combate(self, c):
        res = c.resultado
        self.combate = None
        if res == 'vitoria':
            if self.enc in self.mapa.inimigos:
                self.mapa.inimigos.remove(self.enc)
            self.estado = 'mapa'
            self.checar_portal()
        elif res == 'fuga':
            self.enc['parado'] = 4
            self.estado = 'mapa'
        else:
            self.estado, self.sel = 'gameover', 0

    def checar_portal(self):
        if self.mapa.objetivo_ok() and not self.mapa.avisado:
            self.mapa.avisado = True
            self.toast("O portal rúnico se abriu!")

    def entrar_acampamento(self):
        h = self.heroi
        h.hp, h.mp, h.veneno, h.buffs = h.maxhp, h.maxmp, 0, {}
        self.estado, self.sel = 'acampamento', 0
        self.toasts = []

    def mover(self, dx, dy):
        m, h = self.mapa, self.heroi
        nx, ny = m.px + dx, m.py + dy
        if m.g[ny][nx] == 1:
            return
        en = m.inimigo_em(nx, ny)
        if en:
            self.iniciar_combate(en)
            return
        m.px, m.py = nx, ny
        if (nx, ny) in m.baus:
            m.baus.remove((nx, ny))
            r = random.random()
            if r < 0.5:
                v = int(random.randint(10, 20) * (1 + 0.25 * self.missao))
                h.ouro += v
                self.toast(f"Baú: {v} moedas de ouro!")
            elif r < 0.8:
                h.pocoes += 1
                self.toast("Baú: uma Poção de Vida!")
            else:
                h.eteres += 1
                self.toast("Baú: uma Poção de Mana!")
        if (nx, ny) in m.anoes:
            m.anoes.remove((nx, ny))
            h.pocoes += 1
            self.toast("Anão resgatado! Ele lhe dá uma Poção de Vida.")
            self.checar_portal()
        if (nx, ny) == m.saida:
            if m.objetivo_ok():
                self.bonus = 30 + 12 * self.missao
                h.ouro += self.bonus
                self.estado = 'concluida'
                return
            self.toast("O portal está selado. " + m.objetivo_txt())
        en = m.mover_inimigos()
        if en:
            self.iniciar_combate(en)

    def beber(self, tipo):
        h = self.heroi
        if tipo == 'pocao':
            if h.pocoes <= 0 or h.hp >= h.maxhp:
                self.toast("Sem poções de vida." if h.pocoes <= 0 else "Sua vida já está cheia.")
                return
            h.pocoes -= 1
            v = min(int(h.maxhp * 0.45), h.maxhp - h.hp)
            h.hp += v
            self.toast(f"Você bebe uma Poção de Vida (+{v}).")
        else:
            if h.eteres <= 0 or h.mp >= h.maxmp:
                self.toast("Sem poções de mana." if h.eteres <= 0 else "Sua mana já está cheia.")
                return
            h.eteres -= 1
            v = min(int(h.maxmp * 0.5), h.maxmp - h.mp)
            h.mp += v
            self.toast(f"Você bebe uma Poção de Mana (+{v}).")

    def opcoes_acamp(self):
        h = self.heroi
        c = h.c
        bonus = '+3 Magia' if h.classe == 'Mago' else '+3 Ataque'
        return [
            ("Poção de Vida", 15),
            ("Poção de Mana", 15),
            (f"Melhorar {c['arma']} ({bonus})", 40 + 35 * h.arma),
            (f"Melhorar {c['armadura']} (+2 Def, +10 Vida)", 40 + 35 * h.armadura),
            ("Partir para a próxima missão", 0),
        ]

    def comprar(self, i):
        h = self.heroi
        nome, preco = self.opcoes_acamp()[i]
        if i == 4:
            self.iniciar_briefing()
            return
        if h.ouro < preco:
            self.toast("Ouro insuficiente!")
            return
        h.ouro -= preco
        if i == 0:
            h.pocoes += 1
        elif i == 1:
            h.eteres += 1
        elif i == 2:
            h.arma += 1
        elif i == 3:
            h.armadura += 1
            h.hp = h.maxhp
        self.toast(f"Comprado: {nome.split(' (')[0]}")

    # ---------------- eventos
    def evento(self, k):
        e = self.estado
        if e == 'titulo':
            if k in CIMA or k in BAIXO:
                self.sel = 1 - self.sel
            elif k in CONFIRMA:
                if self.sel == 0:
                    self.estado, self.sel = 'classe', 0
                else:
                    self.rodando = False
        elif e == 'classe':
            if k in ESQ:
                self.sel = (self.sel - 1) % 3
            elif k in DIR:
                self.sel = (self.sel + 1) % 3
            elif k in VOLTA:
                self.estado, self.sel = 'titulo', 0
            elif k in CONFIRMA:
                self.novo_jogo(ORDEM_CLASSES[self.sel])
        elif e == 'briefing':
            if k in CONFIRMA:
                self.iniciar_missao()
        elif e == 'mapa':
            mov = {pygame.K_UP: (0, -1), pygame.K_w: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
                   pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0)}
            if k in mov:
                self.mover(*mov[k])
            elif k == pygame.K_h:
                self.beber('pocao')
            elif k == pygame.K_m:
                self.beber('eter')
            elif k in VOLTA or k == pygame.K_c:
                self.estado, self.sel = 'pausa', 0
        elif e == 'pausa':
            if k in CIMA or k in BAIXO:
                self.sel = 1 - self.sel
            elif k in VOLTA:
                self.estado = 'mapa'
            elif k in CONFIRMA:
                self.estado = 'mapa' if self.sel == 0 else 'titulo'
                self.sel = 0
        elif e == 'combate':
            self.combate.tecla(k)
        elif e == 'concluida':
            if k in CONFIRMA:
                if self.missao >= len(MISSOES) - 1:
                    self.estado = 'final'
                else:
                    self.missao += 1
                    self.entrar_acampamento()
        elif e == 'acampamento':
            n = len(self.opcoes_acamp())
            if k in CIMA:
                self.sel = (self.sel - 1) % n
            elif k in BAIXO:
                self.sel = (self.sel + 1) % n
            elif k in CONFIRMA:
                self.comprar(self.sel)
        elif e == 'gameover':
            if k in CIMA or k in BAIXO:
                self.sel = 1 - self.sel
            elif k in CONFIRMA:
                if self.sel == 0:
                    self.heroi = copy.deepcopy(self.snap)
                    self.iniciar_missao()
                else:
                    self.estado, self.sel = 'titulo', 0
        elif e == 'final':
            if k in CONFIRMA:
                self.estado, self.sel = 'titulo', 0

    def update(self, dt):
        self.t += dt
        self.trans = max(0, self.trans - dt)
        if self.estado in ('mapa', 'combate'):
            self.tempo += dt
        if self.estado == 'combate' and self.combate:
            self.combate.update(dt)
        for tst in self.toasts:
            tst[1] += dt
        self.toasts = [tst for tst in self.toasts if tst[1] < 3.0]

    # ---------------- telas
    def desenhar(self):
        e = self.estado
        if e == 'titulo':
            self.tela_titulo()
        elif e == 'classe':
            self.tela_classe()
        elif e == 'briefing':
            self.tela_briefing()
        elif e in ('mapa', 'pausa', 'concluida'):
            self.tela_mapa()
            if e == 'pausa':
                self.tela_pausa()
            elif e == 'concluida':
                self.tela_concluida()
        elif e == 'combate':
            self.combate.desenhar()
            if self.trans > 0:
                s = pygame.Surface((W, H), pygame.SRCALPHA)
                s.fill((255, 255, 255, int(255 * self.trans / 0.35)))
                self.tela.blit(s, (0, 0))
        elif e == 'acampamento':
            self.tela_acampamento()
        elif e == 'gameover':
            self.tela_gameover()
        elif e == 'final':
            self.tela_final()
        y = 12
        for s, tt in self.toasts:
            w = self.f['m'].size(s)[0] + 30
            r = pygame.Rect(W // 2 - w // 2, y, w, 34)
            self.painel(r)
            self.txt(s, (W // 2, y + 8), (255, 235, 170), f='m', centro=True)
            y += 40

    def tela_titulo(self):
        self.ceu_noturno()
        self.montanhas(470, (40, 20, 35))
        bob = math.sin(self.t * 1.5) * 8
        self.tela.blit(sprite('dragao', 14, INIMIGOS['dragao']['over']), (600, 90 + bob))
        self.montanhas(560, (22, 12, 22))
        self.txt("A LENDA DE IGNIVAR", (W // 2 - 150, 70), OURO, f='t', centro=True)
        self.txt("Um pequeno CRPG de dragões, anões, orcs e goblins", (W // 2 - 150, 140), (220, 200, 200), f='m', centro=True)
        for i, op in enumerate(["Novo Jogo", "Sair"]):
            sel = i == self.sel
            y = 300 + i * 50
            if sel:
                self.txt(">", (170, y), OURO, f='g')
            self.txt(op, (205, y), OURO if sel else BRANCO, f='g')
        self.txt("Setas/WASD: mover   ENTER: confirmar   ESC: voltar / ficha   H/M: poções", (W // 2, H - 34), CINZA, centro=True)

    def tela_classe(self):
        self.ceu_noturno((15, 15, 35), (40, 30, 50))
        self.txt("Escolha sua classe", (W // 2, 24), OURO, f='g', centro=True)
        for i, nome in enumerate(ORDEM_CLASSES):
            c = CLASSES[nome]
            r = pygame.Rect(25 + i * 312, 80, 290, 520)
            sel = i == self.sel
            self.painel(r, borda=OURO if sel else (90, 90, 110))
            b = math.sin(self.t * 3) * 4 if sel else 0
            self.tela.blit(sprite(c['spr'], 8), (r.centerx - 64, r.y + 20 + b))
            self.txt(nome, (r.centerx, r.y + 160), OURO if sel else BRANCO, f='g', centro=True)
            y = r.y + 205
            for linha in self.quebrar(c['desc'], 'p', r.w - 30):
                self.txt(linha, (r.x + 15, y), (210, 210, 220))
                y += 22
            y += 8
            for rot, k in (("Vida", 'hp'), ("Mana", 'mp'), ("Ataque", 'atk'), ("Defesa", 'df'), ("Magia", 'mag')):
                self.txt(rot, (r.x + 15, y), CINZA)
                pygame.draw.rect(self.tela, (40, 40, 50), (r.x + 95, y + 3, 170, 12))
                pygame.draw.rect(self.tela, (200, 150, 60), (r.x + 95, y + 3, int(170 * min(1, c[k] / 60)), 12))
                self.txt(str(c[k]), (r.right - 15, y), BRANCO, dir=True)
                y += 22
            y += 8
            self.txt("Habilidades:", (r.x + 15, y), OURO)
            y += 22
            for key in c['skills']:
                sk = SKILLS[key]
                self.txt(f"{sk['nome']}", (r.x + 22, y), sk['cor'])
                self.txt(f"Nv {sk['nv']}", (r.right - 15, y), CINZA, dir=True)
                y += 21
        self.txt("<  >  para escolher      ENTER para começar", (W // 2, H - 30), CINZA, centro=True)

    def tela_briefing(self):
        m = MISSOES[self.missao]
        tema = THEMES[m['tema']]
        self.ceu_noturno(tema['bg'][0], tom(tema['bg'][1], 0.5))
        self.montanhas(560, tom(tema['pc'], 0.6))
        self.txt(f"Missão {self.missao + 1} de {len(MISSOES)}", (W // 2, 30), CINZA, f='m', centro=True)
        self.txt(m['nome'], (W // 2, 60), OURO, f='g', centro=True)
        self.tela.blit(sprite('anao', 9), (40, 170 + math.sin(self.t * 2) * 3))
        r = pygame.Rect(210, 140, 720, 330)
        self.painel(r)
        self.txt("Borin Martelo-de-Pedra:", (r.x + 20, r.y + 16), (255, 170, 80), f='m')
        y = r.y + 54
        for linha in self.quebrar(m['texto'], 'm', r.w - 40):
            self.txt(linha, (r.x + 20, y), BRANCO, f='m')
            y += 30
        obj = {'todos': "Objetivo: derrotar todos os inimigos.",
               'resgate': f"Objetivo: resgatar {m.get('n', 0)} anões.",
               'chefe': f"Objetivo: derrotar {INIMIGOS[m.get('chefe', 'goblin')]['nome']}."}[m['obj']]
        self.txt(obj, (r.x + 20, r.bottom - 40), VERDE, f='m')
        if self.missao == 0:
            self.txt("Toque em um inimigo no mapa para lutar. Baús têm ouro e poções.", (W // 2, 500), (220, 220, 220), centro=True)
            self.txt("ESC abre a ficha do personagem. H e M bebem poções fora do combate.", (W // 2, 526), (220, 220, 220), centro=True)
        if int(self.t * 2) % 2 == 0:
            self.txt("ENTER para começar", (W // 2, H - 50), OURO, f='m', centro=True)

    def tela_mapa(self):
        m, h = self.mapa, self.heroi
        m.desenhar(self.tela, self.t, h)
        r = pygame.Rect(0, HUD_Y, W, H - HUD_Y)
        self.tela.fill((20, 17, 28), r)
        pygame.draw.line(self.tela, (190, 150, 70), (0, HUD_Y), (W, HUD_Y), 2)
        self.tela.blit(sprite(h.spr, 3), (6, HUD_Y + 8))
        self.txt(f"{h.nome}, {h.classe} Nv {h.nivel}", (62, HUD_Y + 8), OURO)
        self.txt(f"Ouro {h.ouro}   Vida[H] {h.pocoes}   Mana[M] {h.eteres}", (62, HUD_Y + 34), (220, 210, 170))
        self.barra(330, HUD_Y + 6, 200, 16, h.hp, h.maxhp, (200, 60, 60))
        self.barra(330, HUD_Y + 26, 200, 16, h.mp, h.maxmp, (60, 100, 210))
        pygame.draw.rect(self.tela, (40, 40, 50), (330, HUD_Y + 48, 200, 6))
        pygame.draw.rect(self.tela, (220, 200, 80), (330, HUD_Y + 48, int(200 * h.xp / h.prox_xp()), 6))
        self.txt(f"Missão {self.missao + 1}/10: {m.m['nome']}", (548, HUD_Y + 8), BRANCO)
        mins, segs = divmod(int(self.tempo), 60)
        self.txt(f"{mins:02d}:{segs:02d}", (W - 12, HUD_Y + 8), CINZA, dir=True)
        self.txt(m.objetivo_txt(), (548, HUD_Y + 34), VERDE if m.objetivo_ok() else (255, 210, 140))

    def tela_pausa(self):
        h = self.heroi
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        self.tela.blit(s, (0, 0))
        r = pygame.Rect(170, 70, 620, 470)
        self.painel(r)
        self.tela.blit(sprite(h.spr, 6), (r.x + 20, r.y + 20))
        self.txt(f"{h.nome} - {h.classe}", (r.x + 140, r.y + 24), OURO, f='g')
        self.txt(f"Nível {h.nivel}    XP {h.xp}/{h.prox_xp()}", (r.x + 140, r.y + 72), BRANCO, f='m')
        linhas = [("Vida", f"{h.hp}/{h.maxhp}"), ("Mana", f"{h.mp}/{h.maxmp}"), ("Ataque", f"{int(h.atk)}"),
                  ("Defesa", f"{int(h.df)}"), ("Magia", f"{int(h.mag)}"), ("Crítico", f"{int(h.c['crit'] * 100)}%"),
                  ("Esquiva", f"{int(h.c['eva'] * 100)}%"), (h.c['arma'], f"+{h.arma}"), (h.c['armadura'], f"+{h.armadura}")]
        y = r.y + 130
        for rot, v in linhas:
            self.txt(rot, (r.x + 30, y), CINZA)
            self.txt(v, (r.x + 250, y), BRANCO, dir=True)
            y += 26
        y = r.y + 130
        self.txt("Habilidades", (r.x + 300, y), OURO)
        y += 28
        for key in h.c['skills']:
            sk = SKILLS[key]
            ok = h.nivel >= sk['nv']
            self.txt(sk['nome'], (r.x + 300, y), sk['cor'] if ok else CINZA)
            self.txt(f"{sk['custo']} MP" if ok else f"Nv {sk['nv']}", (r.right - 25, y), AZUL if ok else CINZA, dir=True)
            y += 24
            for linha in self.quebrar(sk['desc'], 'p', 280):
                self.txt(linha, (r.x + 310, y), (170, 170, 180))
                y += 20
            y += 4
        for i, op in enumerate(["Continuar", "Voltar ao menu principal"]):
            yy = r.bottom - 70 + i * 30
            self.txt(("> " if i == self.sel else "  ") + op, (r.x + 30, yy), OURO if i == self.sel else BRANCO, f='m')

    def tela_concluida(self):
        r = pygame.Rect(0, 0, 520, 190)
        r.center = (W // 2, H // 2 - 40)
        self.painel(r, borda=OURO)
        self.txt("MISSÃO CONCLUÍDA!", (W // 2, r.y + 22), OURO, f='g', centro=True)
        self.txt(MISSOES[self.missao]['nome'], (W // 2, r.y + 76), BRANCO, f='m', centro=True)
        self.txt(f"Recompensa de Borin: {self.bonus} de ouro", (W // 2, r.y + 108), VERDE, centro=True)
        self.txt("ENTER para continuar", (W // 2, r.bottom - 34), CINZA, centro=True)

    def tela_acampamento(self):
        h = self.heroi
        self.ceu_noturno((8, 10, 30), (30, 25, 45))
        self.montanhas(420, (25, 22, 40))
        self.tela.fill((38, 34, 30), (0, 470, W, H - 470))
        fx, fy = 250, 470
        for i in range(7):
            a = self.t * 9 + i * 2.1
            hgt = 40 + 18 * math.sin(a)
            cx = fx - 24 + i * 8
            cor = [(255, 90, 20), (255, 160, 40), (255, 230, 120)][i % 3]
            pygame.draw.polygon(self.tela, cor, [(cx - 10, fy), (cx + 10, fy), (cx + math.sin(a) * 4, fy - hgt)])
        pygame.draw.rect(self.tela, (90, 60, 35), (fx - 40, fy - 4, 80, 10))
        luz = pygame.Surface((400, 400), pygame.SRCALPHA)
        for rad in range(200, 0, -20):
            pygame.draw.circle(luz, (255, 150, 60, 5 + int(1.5 * math.sin(self.t * 7))), (200, 200), rad)
        self.tela.blit(luz, (fx - 200, fy - 220))
        self.tela.blit(sprite('anao', 6), (fx - 180, fy - 94))
        self.tela.blit(sprite(h.spr, 6), (fx + 70, fy - 94))
        self.txt("Acampamento dos Anões", (250, 40), OURO, f='g', centro=True)
        self.txt("Vida e mana restauradas junto à fogueira.", (250, 92), VERDE, centro=True)
        self.txt(f"Próxima: Missão {self.missao + 1} - {MISSOES[self.missao]['nome']}", (250, 120), BRANCO, centro=True)
        r = pygame.Rect(500, 40, 440, 400)
        self.painel(r)
        self.txt("Forja e mercado de Borin", (r.x + 20, r.y + 16), OURO, f='m')
        self.txt(f"Ouro: {h.ouro}", (r.right - 20, r.y + 18), (255, 220, 100), f='m', dir=True)
        y = r.y + 64
        for i, (nome, preco) in enumerate(self.opcoes_acamp()):
            sel = i == self.sel
            if sel:
                pygame.draw.rect(self.tela, (70, 55, 95), (r.x + 10, y - 5, r.w - 20, 30))
            pode = preco == 0 or h.ouro >= preco
            self.txt(nome, (r.x + 24, y), (OURO if sel else BRANCO) if pode else CINZA)
            if preco:
                self.txt(f"{preco} ouro", (r.right - 20, y), (255, 220, 100) if pode else CINZA, dir=True)
            y += 38
        y += 10
        self.txt(f"Poções de Vida: {h.pocoes}    Poções de Mana: {h.eteres}", (r.x + 20, y), (200, 200, 210))
        y += 26
        self.txt(f"Nv {h.nivel}   Ataque {int(h.atk)}   Defesa {int(h.df)}   Magia {int(h.mag)}", (r.x + 20, y), (200, 200, 210))
        y += 26
        self.txt(f"Vida {h.maxhp}   Mana {h.maxmp}   XP {h.xp}/{h.prox_xp()}", (r.x + 20, y), (200, 200, 210))

    def tela_gameover(self):
        self.ceu_noturno((20, 0, 0), (60, 10, 10))
        self.txt("VOCÊ CAIU EM COMBATE", (W // 2, 170), VERMELHO, f='g', centro=True)
        self.txt("Mas as runas de Borin podem trazê-lo de volta ao início da missão.", (W // 2, 230), BRANCO, f='m', centro=True)
        for i, op in enumerate(["Tentar a missão novamente", "Voltar ao menu principal"]):
            sel = i == self.sel
            self.txt(("> " if sel else "") + op, (W // 2, 320 + i * 44), OURO if sel else BRANCO, f='m', centro=True)

    def tela_final(self):
        h = self.heroi
        self.ceu_noturno((40, 25, 10), (120, 70, 20))
        self.montanhas(520, (50, 30, 20))
        self.txt("VITÓRIA!", (W // 2, 60), OURO, f='t', centro=True)
        self.txt("Ignivar, o Dragão Negro, foi derrotado!", (W // 2, 150), BRANCO, f='m', centro=True)
        self.txt("Pedraforte está salva e seu nome será cantado nos salões dos anões.", (W // 2, 185), BRANCO, f='m', centro=True)
        self.tela.blit(sprite(h.spr, 8), (W // 2 - 150, 250 + math.sin(self.t * 3) * 4))
        self.tela.blit(sprite('anao', 8), (W // 2 + 22, 250))
        mins, segs = divmod(int(self.tempo), 60)
        self.txt(f"{h.nome}, {h.classe} de nível {h.nivel}   -   Tempo de jogo: {mins:02d}:{segs:02d}", (W // 2, 420), OURO, f='m', centro=True)
        self.txt("Obrigado por jogar!   ENTER para voltar ao menu", (W // 2, 480), CINZA, f='m', centro=True)

    # ---------------- laço principal
    def rodar(self):
        while self.rodando:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.rodando = False
                elif ev.type == pygame.KEYDOWN:
                    self.evento(ev.key)
            self.update(dt)
            self.desenhar()
            pygame.display.flip()
        pygame.quit()


if __name__ == '__main__':
    Jogo().rodar()
    sys.exit()
