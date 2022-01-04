# coding: utf-8
import json
import os
import re
import typing

from PIL import Image, ImageFont, ImageDraw
from send2trash import send2trash

from util.util import rgb2hex


class Letter:
    __slots__ = ["character", "id", "start_t", "end_t", "offset_sentence", "offset_x", "offset_y", "width", "height",
                 "color"]

    def __init__(self, character, start_t: float, end_t: float, offset_sentence=0, offset_x=0, offset_y=0, width=0,
                 height=0, color=None):
        self.character = character
        self.start_t = start_t
        self.end_t = end_t
        self.offset_sentence = offset_sentence
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.width = width
        self.height = height
        self.color = color

    def get_file_name(self, pre_sync=False):
        return f"{ord(self.character):04x}_{rgb2hex(*self.color)}_{'pre' if pre_sync else 'post'}.png"


# fontPath e.g.: os.path.join("C:/Windows/Fonts", "A-OTF-GothicBBBPr5-Medium.otf")
# fontSize e.g.: 60
# filePath e.g.: SB/lyrics
class CharacterRenderer:
    re_korean = re.compile(r"[가-힣]")

    def __init__(self, file_path, font="malgunbd.ttf", font_size=35, rel_path="SB\\lyrics"):
        self.width = []
        self.height = []
        self.font_size = font_size
        self.file_path = file_path
        self.rel_path = rel_path
        if os.path.exists(os.path.join(self.file_path, self.rel_path)):
            send2trash(os.path.join(self.file_path, self.rel_path))

        self.font = ImageFont.truetype(font=font, size=35)
        self.font_aa = ImageFont.truetype(font=font, size=70)
        self.padding = 0
        self.stroke_width = 5

    def get_ch(self, character: str, start_t: float, end_t: float, color: typing.Optional[typing.List[int]]):
        if len(character) != 1:
            raise ValueError("This method only accepts single characters")
        offset = self.font.getoffset(character)
        width, height = self.font.getsize(character, stroke_width=self.stroke_width)
        return Letter(character, start_t=start_t, end_t=end_t, offset_x=offset[0], offset_y=offset[1], width=width,
                      height=height, color=color)

    @staticmethod
    def get_fill_color(color: typing.List[int], pre_sync=False):
        r, g, b = color
        if pre_sync:
            return int(0.6*r), int(0.6*g), int(0.6*b)
        else:
            return int(r+0.7*(255-r)), int(g+0.7*(255-g)), int(b+0.7*(255-b))

    def get_image(self, letter: Letter, pre_sync=False):
        render_path = os.path.join(self.file_path, self.rel_path)
        file_name = letter.get_file_name(pre_sync=pre_sync)
        image_path = os.path.join(render_path, file_name)
        if not os.path.exists(image_path):
            if not os.path.exists(render_path):
                os.makedirs(render_path)

            width, height = self.font_aa.getsize(letter.character, stroke_width=self.stroke_width)
            im = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            drawer = ImageDraw.Draw(im)
            fill_color = self.get_fill_color(letter.color, pre_sync=pre_sync)
            offset = self.font_aa.getoffset(letter.character)[0]

            drawer.text((-offset + self.stroke_width, 0), letter.character, font=self.font_aa, fill=fill_color,
                        stroke_width=self.stroke_width, stroke_fill=tuple(letter.color))
            im_resized = im.resize((letter.width, letter.height), resample=Image.ANTIALIAS)
            im_resized.save(image_path)

        return f"{self.rel_path}\\{file_name}"


class Sentence:
    def __init__(self, content="", start_t=0.0, end_t=0.0, tag="", artist=""):
        self.letters = []
        self.content = content
        self.tag = tag
        self.artist = artist
        self.start_t = start_t
        self.end_t = end_t
        self.width = 0
        self.height = 0

    def set_time(self, start_t: float, end_t: float):
        self.start_t = start_t
        self.end_t = end_t

    def append(self, letter: Letter):
        self.content += letter.character
        letter.offset_sentence = self.width
        self.letters.append(letter)
        self.width += letter.width + letter.offset_x
        self.height = max(self.height, letter.height)


class LyricParser:
    ts_regex = re.compile(r"\[(?P<minutes>\d\d):(?P<seconds>\d\d\.\d{2,3})](?P<lyric>[^\[]*)")
    ln_regex = re.compile(r"\[length: (?P<minutes>\d\d?):(?P<seconds>\d\d)]\s*")
    ar_regex = re.compile(r"\[ar: (?P<artist>.+)]\s*")

    def __init__(self, lrc_path: str, character_renderer: CharacterRenderer):
        self.CR = character_renderer
        self.artist = None
        self.colors = None
        self.length = None
        self.me_regex = None
        self.sentences = self.parse(lrc_path)

    @staticmethod
    def match2seconds(match: re.Match) -> float:
        return int(match['minutes'])*60 + float(match['seconds'])

    def parse(self, filename: str, color_coding=True):
        """Parser for LRC files. Returns list of timed Sentence objects."""
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
        sentences = []
        for i, line in enumerate(lines):
            if color_coding and self.artist is None:
                match = self.ar_regex.fullmatch(line)
                if match:
                    self.artist = match['artist'].lower()
                    with open(os.path.join(__file__, "..", "..", "color_coding.json"), "r", encoding="utf-8") as f:
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
                col = [200, 200, 200]
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
                            match = self.me_regex.match(timed_string['lyric'].strip("\r\n").lower()[k:])
                            if match:
                                members = match['members'].split("/")
                                if len(members) == 1:
                                    col = self.colors['members'][members[0].lower()]
                                else:
                                    col = self.colors['group']
                                n_skip = len(match['members']) + 2
                                continue
                            else:
                                col = self.colors['group']
                        elif c == ")":
                            col = self.colors['group']
                    letter = self.CR.get_ch(c, time_start, time_end, color=col)
                    sentence.append(letter)

            sentences.append(sentence)
        return sentences

    def parse_test(self):
        for i, sentence in enumerate(self.sentences):
            print(i, sentence.content, sentence.start_t, sentence.end_t)
            for letter in sentence.letters:
                print(" ", letter.character, letter.start_t, letter.end_t, letter.id, letter.width)
