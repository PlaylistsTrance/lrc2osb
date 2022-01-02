# coding: utf-8
import os
import re
import typing

import pygame

from util.util import padding


class Letter:
    def __init__(self, ch, i, t1, t2):
        self.character = ch
        self.id = i
        self.start_t = t1
        self.end_t = t2
        self.offset_x = 0
        self.width = 0
        self.height = 0
        self.filename_dark = ""
        self.filename_light = ""


# fontPath e.g.: os.path.join("C:/Windows/Fonts", "A-OTF-GothicBBBPr5-Medium.otf")
# fontSize e.g.: 60
# filePath e.g.: SB/lyrics
class CharacterRenderer:
    re_korean = re.compile(r"[가-힣]")

    def __init__(self, font="arial", font_size=35, file_path=os.path.join("SB", "lyrics"), korean_font="malgungothic",
                 color_dark=(108, 0, 54), color_light=(255, 0, 128)):
        self.characters = []  # type: typing.List[chr]
        self.width = []
        self.height = []
        self.font_size = font_size
        self.file_path = file_path
        self.color_dark = color_dark
        self.color_light = color_light
        pygame.init()
        self.font = pygame.font.SysFont(font, self.font_size, bold=True)
        self.korean_font = pygame.font.SysFont(korean_font, self.font_size, bold=True)
        self.padding = 0

    def set_ch(self, letter):
        if letter.character not in self.characters:
            self.characters.append(letter.character)
            # self.ch_render(len(self.characters)-1)
            if self.re_korean.match(letter.character):
                width, height = self.korean_font.size(letter.character)
            else:
                width, height = self.font.size(letter.character)
            self.width.append(width)
            self.height.append(height)
            letter.index = len(self.characters)-1
            letter.width = width
            letter.height = height
        else:
            letter.id = self.characters.index(letter.character)
            letter.width = self.width[letter.id]
            letter.height = self.height[letter.id]
        return

    def render(self):
        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)
        # print(self.file_path)
        for i in range(len(self.characters)):
            self.ch_render(i)

    def ch_render(self, index):
        character = self.characters[index]
        if self.re_korean.match(character):
            dark = self.korean_font.render(character, True, self.color_dark)
            light = self.korean_font.render(character, True, self.color_light)
        else:
            dark = self.font.render(character, True, self.color_dark)
            light = self.font.render(character, True, self.color_light)

        name = f"{index:0{padding(len(self.characters))}}a.png"
        pygame.image.save(dark, os.path.join(self.file_path, name))
        name = f"{index:0{padding(len(self.characters))}}b.png"
        pygame.image.save(light, os.path.join(self.file_path, name))


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

    def __init__(self, lrc_path, character_renderer):
        self.CR = character_renderer
        self.length = None
        self.sentences = self.parse(lrc_path)

    @staticmethod
    def match2seconds(match: re.Match) -> float:
        return int(match['minutes'])*60 + float(match['seconds'])

    def parse(self, filename):
        """Parser for LRC files. Returns list of timed Sentence objects."""
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
        sentences = []
        for i, line in enumerate(lines):
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
            for j, timed_string in enumerate(matches):
                if j == 0 and timed_string['lyric'] == "​":
                    continue
                elif j == (len(matches)-1):
                    if timed_string['lyric'].strip() == "":
                        break
                    else:
                        time_end = sentence.end_t
                else:
                    time_end = self.match2seconds(matches[j+1])
                time_start = self.match2seconds(timed_string)
                for c in timed_string['lyric'].strip("\r\n"):
                    letter = Letter(c, 0, time_start, time_end)
                    self.CR.set_ch(letter)
                    sentence.append(letter)
                    sentence.content += letter.character
            sentences.append(sentence)
        pad = padding(len(self.CR.characters))
        for sentence in sentences:
            for letter in sentence.letters:
                id_ = self.CR.characters.index(letter.character)
                letter.filename_dark = '"' + os.path.join(self.CR.file_path, f"{id_:0{pad}}a.png") + '"'
                letter.filename_light = '"' + os.path.join(self.CR.file_path, f"{id_:0{pad}}b.png") + '"'
        return sentences

    def parse_test(self):
        for i, sentence in enumerate(self.sentences):
            print(i, sentence.content, sentence.start_t, sentence.end_t)
            for letter in sentence.letters:
                print(" ", letter.character, letter.start_t, letter.end_t, letter.id, letter.width)
