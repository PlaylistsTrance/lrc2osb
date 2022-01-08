import argparse
import os
import typing

from send2trash import send2trash

from parser.lrc_parser import CharacterRenderer, LyricParser


# defaults
FADE_TIME = 400
FONT_SIZE = 60
SCALE = 480/1080
STROKE_WIDTH = 5
Y_POS = 0.8


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("lrc_path", type=str, help="path to LRC file")
    parser.add_argument("storyboard_path", type=str,
                        help="name and path of the storyboard to be made (ending with .osb)")
    parser.add_argument("-o", "--offset", type=float, default=0.0,
                        help="offset in seconds (decimal) to line up the LRC with the beatmap audio")
    parser.add_argument("-y", action="store_true", help="overwrite existing storyboard and lyrics")
    parser.add_argument("-Y", type=float, default=Y_POS,
                        help=f"y-coordinate for placing the lyrics (0.0 is top, 1.0 is bottom) (default: {Y_POS:.2f})")
    parser.add_argument("-s", "--scale", type=float, default=SCALE, help=f"lyrics scale (default: {SCALE:.2f}")
    parser.add_argument("-fs", "--font-size", type=int, default=FONT_SIZE, help=f"font size (default: {FONT_SIZE})")
    parser.add_argument("-sw", "--stroke-width", type=int, default=STROKE_WIDTH,
                        help=f"stroke width (outline width) (default: {STROKE_WIDTH})")
    return parser.parse_args()


class OSBCommand:
    __slots__ = ["name", "time_start", "val_start", "time_end", "val_end", "easing"]

    def __init__(self, name: str, time_start: float, val_start, val_end_repr: typing.Callable, time_end: float = "",
                 val_end: object = "", easing=0):
        if name not in "CFS":
            raise ValueError(f"Command '{name}' not recognized in list '{', '.join('CFS')}'")
        if not -1 < easing < 35:
            raise ValueError("Easing has to be between 0 and 34 (inclusive)")
        if time_end == "" or time_end == time_start:
            self.time_end = ""
        elif time_start > time_end:
            raise ValueError("End time precedes start time")
        else:
            self.time_end = int(time_end)
        self.name = name
        self.time_start = time_start
        self.val_start = val_start
        if val_end in ["", val_start]:
            self.val_end = ""
        else:
            self.val_end = val_end_repr(val_end)
        self.easing = easing

    def __repr__(self):
        items = [" " + self.name, self.easing, self.time_start, self.time_end, self.val_start]
        if self.val_end != "":
            items.append(self.val_end)
        return ",".join(map(str, items))


class OSBColor(OSBCommand):
    def __init__(self, time_start: float, color_start: tuple, time_end: float = "", color_end: tuple = "",
                 easing=0):
        super().__init__("C", time_start, ",".join(map(str, color_start)), lambda x: x, time_end,
                         ",".join(map(str, color_end)), easing)


class OSBFade(OSBCommand):
    def __init__(self, time_start: float, fade_start: float, time_end: float = "", fade_end: float = "", easing=0):
        if not 0 <= fade_start <= 1:
            raise ValueError(f"Fade start is not between 0 and 1 ({fade_start})")
        if fade_end and not 0 <= fade_end <= 1:
            raise ValueError(f"Fade end is not between 0 and 1 ({fade_end})")
        super().__init__("F", time_start, fade_start, lambda x: str(x), time_end, fade_end, easing)


class OSBScale(OSBCommand):
    def __init__(self, time_start: float, scale_start: float, time_end: float = "", scale_end: float = "", easing=0):
        super().__init__("S", time_start, scale_start, lambda x: str(x), time_end, scale_end, easing)


class OSBSprite:
    __slots__ = ["image_path", "x", "y", "layer", "commands", "origin"]

    def __init__(self, image_path: str, x: float, y: float, layer="Foreground", origin="TopLeft"):
        self.image_path = image_path
        self.x = x
        self.y = y
        self.layer = layer
        self.origin = origin
        self.commands = []

    def __repr__(self):
        return (f"Sprite,{self.layer},{self.origin},\"{self.image_path}\",{self.x:.4f},{self.y:.4f}\n"
                + "\n".join(map(str, self.commands)))

    def append(self, command: OSBCommand):
        self.commands.append(command)


def write_osb(storyboard_path: str, lrc_path: str, file_path: str, offset=0.0, scale=1.0, y=0.0, fade_t_max=400,
              font_size=FONT_SIZE, stroke_width=STROKE_WIDTH, skip_warning=False):
    character_renderer = CharacterRenderer(file_path=os.path.dirname(storyboard_path), font_size=font_size,
                                           stroke_width=stroke_width, skip_warning=skip_warning)
    lyric_parser = LyricParser(lrc_path, character_renderer)

    commands = []

    for i, sentence in enumerate(lyric_parser.sentences):
        for j in range(i-1, -1, -1):
            if sentence.start_t < lyric_parser.sentences[j].end_t:
                sentence.offset_y += sentence.height*scale
                sentence.n_stacked += 1
            else:
                break

    for i, sentence in enumerate(lyric_parser.sentences):
        commands.append(f"//{sentence.content}")

        s_start_t = int((sentence.start_t + offset)*1000)
        s_end_t = int((sentence.end_t + offset)*1000)

        if i == 0:
            fade_in_duration = int(min(fade_t_max, s_start_t))
        else:
            fade_in_duration = int(fade_t_max)
            for j in range(i-1, -1, -1):
                if lyric_parser.sentences[j].n_stacked == sentence.n_stacked:
                    fade_t = (sentence.start_t - lyric_parser.sentences[j].end_t)/2*1000
                    if sentence.n_stacked:
                        fade_in_duration = int(min(fade_t_max, fade_t))
                    else:
                        fade_in_duration = int(fade_t)
                    break

        fade_out_duration = int(fade_t_max)
        for j in range(i+1, len(lyric_parser.sentences)):
            if sentence.n_stacked == lyric_parser.sentences[j].n_stacked:
                fade_out_duration = int(min(fade_t_max,
                                            (lyric_parser.sentences[j].start_t-sentence.end_t)/2*1000))
                break

        use_pre = sentence.letters[-1].start_t != sentence.start_t
        # Pre-sync
        for letter in sentence.letters:
            if letter.character == " ":
                continue
            x = 320 - sentence.width/2*scale + (letter.offset_sentence+letter.offset_x)*scale

            # Outline
            fill_path, outline_path = character_renderer.get_sprites(letter)
            outline_sprite = OSBSprite(outline_path, x, y - sentence.offset_y)

            # Outline color
            outline_sprite.append(OSBColor(s_start_t-fade_in_duration, letter.color))
            # Outline fade in
            outline_sprite.append(OSBFade(s_start_t-fade_in_duration, 0, s_start_t, 1))
            # Outline scale
            if scale != 1:
                outline_sprite.append(OSBScale(s_start_t, scale))
            # Outline fade out
            outline_sprite.append(OSBFade(s_end_t, 1, s_end_t+fade_out_duration, 0))

            commands.append(outline_sprite)

            # Fill
            fill_sprite = OSBSprite(fill_path, x, y - sentence.offset_y)

            l_start_t = int((letter.start_t+offset)*1000)
            l_end_t = int((letter.end_t+offset)*1000)

            # Fill pre-color
            color_pre = character_renderer.get_fill_color(letter.color, pre_sync=use_pre)
            fill_sprite.append(OSBColor(s_start_t-fade_in_duration, color_pre))

            # Fill fade in
            fill_sprite.append(OSBFade(s_start_t-fade_in_duration, 0, s_start_t, 1))

            # Fill scale
            if scale != 1:
                fill_sprite.append(OSBScale(s_start_t, scale))

            # Fill highlight color
            if use_pre:
                color_post = character_renderer.get_fill_color(letter.color)
                color_pre = tuple([int(color_pre[i] + (color_post[i]-color_pre[i])*0.3) for i in range(3)])
                fill_sprite.append(OSBColor(l_start_t, color_pre, l_end_t, color_post))

            # Fill fade out
            fill_sprite.append(OSBFade(s_end_t, 1, s_end_t+fade_out_duration, 0))

            commands.append(fill_sprite)

    if os.path.exists(file_path):
        send2trash(file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("[Events]\n"
                "//Background and Video events\n"
                "//Storyboard Layer 0 (Background)\n"
                "//Storyboard Layer 1 (Fail)\n"
                "//Storyboard Layer 2 (Pass)\n"
                "//Storyboard Layer 3 (Foreground)\n")

        f.write("\n".join(map(str, commands)) + "\n")

        f.write("//Storyboard Layer 4 (Overlay)\n"
                "//Storyboard Sound Samples\n")


if __name__ == '__main__':
    args = get_args()
    write_osb(storyboard_path=args.storyboard_path, lrc_path=args.lrc_path, file_path=args.storyboard_path,
              offset=args.offset, scale=args.scale, y=int(args.Y*480), font_size=args.font_size,
              stroke_width=args.stroke_width, skip_warning=args.y)
