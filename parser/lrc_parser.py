"""
Parser for LRC files for use in OSB generation.
Based on https://github.com/frankhjwx/osu-storyboard-engine/blob/master/Storyboard%20Engine/tools/LyricsParser.py
"""

import json
import os
import re
import typing

from PIL import Image, ImageFont, ImageDraw
from send2trash import send2trash


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

    def get_file_name(self, outline=False):
        return f"{ord(self.character):04x}{'_ol'*int(outline)}.png"


# TODO: Language support other than Korean
class CharacterRenderer:
    def __init__(self, file_path, font="malgunbd.ttf", rel_path="SB\\lyrics", font_size=35, stroke_width=5,
                 skip_warning=False):
        self.file_path = file_path
        self.rel_path = rel_path
        self.render_path = os.path.join(self.file_path, self.rel_path)
        if os.path.exists(os.path.join(self.file_path, self.rel_path)):
            if not skip_warning:
                if input("Delete existing lyrics images and continue? (y/N)\n").lower() != "y":
                    print("Aborting.")
                    quit()
            send2trash(os.path.join(self.file_path, self.rel_path))

        self.font_size = font_size
        self.font = ImageFont.truetype(font=font, size=self.font_size)
        self.font_aa = ImageFont.truetype(font=font, size=self.font_size*2)
        self.stroke_width = stroke_width

    def get_ch(self, character: str, start_t: float, end_t: float, color: typing.Optional[typing.List[int]]):
        """Creates and returns Letter object."""
        if len(character) != 1:
            raise ValueError("This method only accepts single characters")
        offset = self.font.getoffset(character)
        width, height = self.font.getsize(character, stroke_width=self.stroke_width)
        return Letter(character, start_t=start_t, end_t=end_t, offset_x=offset[0], offset_y=offset[1], width=width,
                      height=height, color=color)

    @staticmethod
    def get_fill_color(color: typing.List[int], pre_sync=False):
        """Calculate fill color. Pre-sync is RGB values times 0.6,
        on-sync is RGB values plus 0.7 times the difference to 255."""
        r, g, b = color
        if pre_sync:
            return int(0.6*r), int(0.6*g), int(0.6*b)
        else:
            return int(r+0.7*(255-r)), int(g+0.7*(255-g)), int(b+0.7*(255-b))

    def render(self, letter: Letter, outline=False):
        """Render and save character outline to PNG file if it doesn't exist yet and return its path."""
        file_name = letter.get_file_name(outline=outline)
        image_path = os.path.join(self.render_path, file_name)
        if not os.path.exists(image_path):
            if not os.path.exists(self.render_path):
                os.makedirs(self.render_path)
            width, height = self.font_aa.getsize(letter.character, stroke_width=self.stroke_width)
            im = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            drawer = ImageDraw.Draw(im)
            offset = self.font_aa.getoffset(letter.character)[0]

            drawer.text((-offset + self.stroke_width, 0), letter.character, font=self.font_aa,
                        fill=(255, 255, 255, 255),
                        stroke_width=self.stroke_width, stroke_fill=(255, 255, 255, 255*int(outline)))
            # 2x Super-sampling
            im_resized = im.resize((letter.width, letter.height), resample=Image.ANTIALIAS)

            # Save to file
            im_resized.save(image_path)
        return f"{self.rel_path}\\{file_name}"

    def get_sprites(self, letter: Letter) -> typing.Tuple[str, str]:
        """Returns character fill and outline image paths."""
        return self.render(letter), self.render(letter, outline=True)


class Sentence:
    def __init__(self, start_t=0.0, end_t=0.0):
        self.letters = []
        self.content = ""
        self.start_t = start_t
        self.end_t = end_t
        self.width = 0
        self.height = 0
        self.n_stacked = 0
        self.offset_y = 0.0

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

            # Check if line equals [ar: ...]
            if color_coding and self.artist is None:
                match = self.ar_regex.fullmatch(line)
                if match:
                    self.artist = match['artist'].lower()
                    with open(os.path.join(__file__, "..", "..", "color_coding.json"), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if self.artist in data:
                        self.colors = data[self.artist]
                        # Generate regex for member names in brackets for member-coding
                        members = "|".join(self.colors['members'].keys()) + "|All"
                        self.me_regex = re.compile(f"^\\((?P<members>(?:{members})(?:/(?:{members}))*)\\)")
                    continue

            # Check if line equals [length: MM:SS]
            if self.length is None:
                match = self.ln_regex.fullmatch(line)
                if match:
                    self.length = int(self.match2seconds(match))
                    continue

            # Get list of timed text within the line
            matches = list(self.ts_regex.finditer(line))
            if not matches:
                continue

            if matches[0]['lyric'] == "​":
                time_start = self.match2seconds(matches[1])
            else:
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

            # Go through all timed text in the line
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
                                    if sentence.letters and sentence.letters[-1].character == "(":
                                        sentence.letters[-1].color = col
                                else:
                                    col = self.colors['group']
                                n_skip = len(match['members']) + 2
                                continue
                            else:
                                col = self.colors['group']
                    letter = self.CR.get_ch(c, time_start, time_end, color=col)
                    if self.colors and c == ")":
                        col = self.colors['group']
                    sentence.append(letter)

            sentences.append(sentence)
        return sentences

    def parse_test(self):
        for i, sentence in enumerate(self.sentences):
            print(i, sentence.content, sentence.start_t, sentence.end_t)
            for letter in sentence.letters:
                print(" ", letter.character, letter.start_t, letter.end_t, letter.id, letter.width)
