# coding: utf-8
import json
from enum import Enum
import os
import re
import typing

import pygame

from util.util import padding


class Mode(Enum):
    DARK = 1
    LIGHT = 2


class Letter:
    def __init__(self, ch, i, t1, t2, color=None):
        self.character = ch
        self.id = i
        self.start_t = t1
        self.end_t = t2
        self.offset_x = 0
        self.width = 0
        self.height = 0
        self.color = color


# fontPath e.g.: os.path.join("C:/Windows/Fonts", "A-OTF-GothicBBBPr5-Medium.otf")
# fontSize e.g.: 60
# filePath e.g.: SB/lyrics
class CharacterRenderer:
    re_korean = re.compile(r"[가-힣]")

    def __init__(self, file_path, font="arial", font_size=35, rel_path="SB\\lyrics",
                 korean_font="malgungothic"):
        self.characters = []  # type: typing.List[chr]
        self.width = []
        self.height = []
        self.font_size = font_size
        self.file_path = file_path
        self.rel_path = rel_path
        pygame.init()
        self.font = pygame.font.SysFont(font, self.font_size, bold=True)
        self.korean_font = pygame.font.SysFont(korean_font, self.font_size, bold=True)
        self.padding = 0

    def set_ch(self, letter):
        if letter.character not in self.characters:
            self.characters.append(letter.character)
            if self.re_korean.match(letter.character):
                width, height = self.korean_font.size(letter.character)
            else:
                width, height = self.font.size(letter.character)
            self.width.append(width)
            self.height.append(height)
            letter.index = len(self.characters)-1
            letter.width = width
            letter.height = height
            self.padding = max(self.padding, padding(len(self.characters)))
        else:
            letter.id = self.characters.index(letter.character)
            letter.width = self.width[letter.id]
            letter.height = self.height[letter.id]
        return

    def get_filepath(self, character):
        render_path = os.path.join(self.file_path, self.rel_path)
        if not os.path.exists(render_path):
            os.makedirs(render_path)
        name = f"{self.characters.index(character):0{self.padding}}{'x'}.png"
        file_path = os.path.join(render_path, name)
        if not os.path.exists(file_path):
            if self.re_korean.match(character):
                render = self.korean_font.render(character, True, (255, 255, 255))
            else:
                render = self.font.render(character, True, (255, 255, 255))
            pygame.image.save(render, file_path)
        return f"{self.rel_path}\\{name}"

    def render(self):
        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)
        # print(self.file_path)
        for i in range(len(self.characters)):
            self.ch_render(i)

    def ch_render(self, index):
        character = self.characters[index]
        if character == " ":
            return
        if self.re_korean.match(character):
            render = self.korean_font.render(character, True, (255, 255, 255))
        else:
            render = self.font.render(character, True, (255, 255, 255))

        name = f"{index:0{padding(len(self.characters))}}x.png"
        pygame.image.save(render, os.path.join(self.file_path, self.rel_path, name))


class Sentence:
    def __init__(self, content="", start_t=0.0, end_t=0.0,
                 character_renderer=None, tag="", artist=""):
        self.letters = []
        self.content = content
        self.tag = tag
        self.artist = artist
        self.start_t = start_t
        self.end_t = end_t
        self.width = 0
        self.height = 0
        if content != "":
            for ch in content:
                letter = Letter(ch, 0, start_t, end_t)
                character_renderer.set_ch(letter)
                letter.start_t = self.start_t
                letter.end_t = self.end_t
                self.letters.append(letter)
                self.width += letter.width
                self.height = max(self.height, letter.height)

    def set_time(self, start_t, end_t):
        self.start_t = start_t
        self.end_t = end_t

    def append(self, letter):
        letter.offset_x = self.width
        self.letters.append(letter)
        self.width += letter.width
        self.height = max(self.height, letter.height)


class LyricParser:
    ts_regex = re.compile(r"\[(?P<minutes>\d\d):(?P<seconds>\d\d\.\d{2,3})](?P<lyric>[^\[]*)")
    ln_regex = re.compile(r"\[length: (?P<minutes>\d\d?):(?P<seconds>\d\d)]\s*")
    ar_regex = re.compile(r"\[ar: (?P<artist>.+)]\s*")

    def __init__(self, lrc_path, character_renderer):
        self.CR = character_renderer
        self.artist = None
        self.colors = None
        self.length = None
        self.me_regex = None
        self.sentences = self.parse(lrc_path)

    @staticmethod
    def match2seconds(match: re.Match) -> float:
        return int(match['minutes'])*60 + float(match['seconds'])

    def parse(self, filename, color_coding=True):
        """Parser for LRC files. Returns list of timed Sentence objects."""
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
        sentences = []
        for i, line in enumerate(lines):
            if color_coding and self.artist is None:
                match = self.ar_regex.fullmatch(line)
                if match:
                    self.artist = match['artist']
                    with open(r"D:\Documents\Git projects\lrc2osb\color_coding.json", "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if self.artist in data:
                        self.colors = data[self.artist]
                        members = "|".join(self.colors['members'].keys()) + "|All"
                        self.me_regex = re.compile(f"^\\((?P<members>(?:{members})(?:/(?:{members}))*)\\)")
                    continue
            if self.length is None:
                match = self.ln_regex.fullmatch(line)
                if match:
                    self.length = int(self.match2seconds(match))
                    continue

            matches = list(self.ts_regex.finditer(line))
            if not matches:
                continue

            time_start = self.match2seconds(matches[0])
            if len(matches) > 1 and matches[-1]['lyric'].strip() == "":
                time_end = self.match2seconds(matches[-1])
            elif i < (len(lines)-1):
                time_end = self.match2seconds(self.ts_regex.match(lines[i+1]))
            elif self.length:
                time_end = self.length
            else:
                print("Warning: Last timed text has unknown end time. Used default of 3 seconds.")
                time_end = time_start + 3

            sentence = Sentence(start_t=time_start, end_t=time_end)
            if self.colors:
                col = self.colors['group']
            else:
                col = None
            for j, timed_string in enumerate(matches):
                if timed_string['lyric'] == "​":
                    continue
                elif j == (len(matches)-1):
                    if timed_string['lyric'].strip():
                        time_end = sentence.end_t
                    else:
                        break
                else:
                    time_end = self.match2seconds(matches[j+1])
                time_start = self.match2seconds(timed_string)
                n_skip = 0
                for k, c in enumerate(timed_string['lyric'].strip("\r\n")):
                    if self.colors:
                        if n_skip > 0:
                            n_skip -= 1
                            continue
                        if c == "(":
                            match = self.me_regex.match(timed_string['lyric'].strip("\r\n")[k:])
                            if match:
                                members = match['members'].split("/")
                                if len(members) == 1:
                                    col = self.colors['members'][members[0]]
                                else:
                                    col = self.colors['group']
                                n_skip = len(match['members']) + 2
                                continue
                            else:
                                col = self.colors['group']
                        elif c == ")":
                            col = self.colors['group']
                    letter = Letter(c, 0, time_start, time_end, color=col)
                    self.CR.set_ch(letter)
                    sentence.append(letter)
                    sentence.content += letter.character

            sentences.append(sentence)
        return sentences

    def parse_test(self):
        for i, sentence in enumerate(self.sentences):
            print(i, sentence.content, sentence.start_t, sentence.end_t)
            for letter in sentence.letters:
                print(" ", letter.character, letter.start_t, letter.end_t, letter.id, letter.width)
