import argparse
import os

from send2trash import send2trash

from parser.lrc_parser import CharacterRenderer, LyricParser


# defaults
FADE_TIME = 400
FONT_SIZE = 35
SCALE = 0.5
STROKE_WIDTH = 5
Y_POS = 0.9


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
                        help=f"Stroke width (outline width) (default: {STROKE_WIDTH})")
    return parser.parse_args()


def write_osb(storyboard_path: str, lrc_path: str, file_path: str, offset=0.0, scale=1.0, y=0.0, fade_t_max=400,
              font_size=FONT_SIZE, stroke_width=STROKE_WIDTH, skip_warning=False):
    character_renderer = CharacterRenderer(file_path=os.path.dirname(storyboard_path), font_size=font_size,
                                           stroke_width=stroke_width, skip_warning=skip_warning)
    lyric_parser = LyricParser(lrc_path, character_renderer)

    if os.path.exists(file_path):
        send2trash(file_path)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("[Events]\n"
                "//Background and Video events\n"
                "//Storyboard Layer 0 (Background)\n"
                "//Storyboard Layer 1 (Fail)\n"
                "//Storyboard Layer 2 (Pass)\n"
                "//Storyboard Layer 3 (Foreground)\n")

        for i, sentence in enumerate(lyric_parser.sentences):
            for j in range(i-1, -1, -1):
                if sentence.start_t < lyric_parser.sentences[j].end_t:
                    sentence.offset_y += lyric_parser.sentences[j].height*scale
                    sentence.n_stacked += 1
                else:
                    break

        for i, sentence in enumerate(lyric_parser.sentences):
            f.write(f"//{sentence.content}\n")

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

            # Karaoke (syllables are timed)
            if sentence.letters[-1].start_t != sentence.start_t:
                # Pre-sync
                for letter in sentence.letters:
                    if letter.character == " ":
                        continue
                    x = 320 - sentence.width/2*scale + (letter.offset_sentence+letter.offset_x)*scale
                    f.write(f"Sprite,Foreground,TopLeft,"
                            f"\"{character_renderer.get_image(letter, pre_sync=True)}\","
                            f"{x:.4f},{y - sentence.offset_y:.4f}\n")

                    # Fade in
                    if fade_in_duration:
                        f.write(f" F,0,{s_start_t-fade_in_duration},{s_start_t},0,1\n")
                    else:
                        f.write(f" F,0,{s_start_t},,1\n")
                    if scale != 1:
                        f.write(f" S,0,{s_start_t},,{scale:.4f}\n")

                    # Disappear once highlight character is fully drawn
                    l_end_t = int((letter.end_t+offset)*1000)
                    f.write(f" F,0,{l_end_t},,1,0\n")

                # On sync
                for letter in sentence.letters:
                    if letter.character == " ":
                        continue
                    l_start_t = int((letter.start_t+offset)*1000)
                    l_end_t = int((letter.end_t+offset)*1000)
                    x = 320 - sentence.width/2*scale + (letter.offset_sentence+letter.offset_x)*scale
                    f.write(f"Sprite,Foreground,TopLeft,"
                            f"\"{character_renderer.get_image(letter)}\","
                            f"{x:.4f},{y - sentence.offset_y:.4f}\n")

                    # Fade in
                    f.write(f" F,0,{l_start_t},{l_end_t},0.3,1\n")
                    if scale != 1:
                        f.write(f" S,0,{l_start_t},,{scale:.4f}\n")

                    # Fade out
                    if fade_out_duration:
                        f.write(f" F,0,{s_end_t},{s_end_t+fade_out_duration},1,0\n")
                    else:
                        f.write(f" F,0,{s_end_t},,1,0\n")
            # Line-by-line
            else:
                for letter in sentence.letters:
                    if letter.character == " ":
                        continue
                    x = 320 - sentence.width/2*scale + (letter.offset_sentence+letter.offset_x)*scale
                    f.write(f"Sprite,Foreground,TopLeft,"
                            f"\"{character_renderer.get_image(letter)}\","
                            f"{x:.4f},{y - sentence.offset_y:.4f}\n")
                    # Fade in
                    if fade_in_duration:
                        f.write(f" F,0,{s_start_t-fade_in_duration},{s_start_t},0,1\n")
                    else:
                        f.write(f" F,0,{s_start_t},,1\n")
                    if scale != 1:
                        f.write(f" S,0,{s_start_t},,{scale:.4f}\n")

                    # Fade out
                    if i < (len(lyric_parser.sentences)-1):
                        if sentence.end_t > lyric_parser.sentences[i+1].start_t:
                            if i < (len(lyric_parser.sentences)-2):
                                s_diff = (lyric_parser.sentences[i+2].start_t-sentence.end_t)/2*1000
                            else:
                                s_diff = fade_t_max
                        else:
                            s_diff = (lyric_parser.sentences[i+1].start_t-sentence.end_t)/2*1000
                        fade_out_duration = int(min(fade_t_max, s_diff))
                    else:
                        fade_out_duration = fade_t_max
                    if fade_out_duration:
                        f.write(f" F,0,{s_end_t},{s_end_t+fade_out_duration},1,0\n")
                    else:
                        f.write(f" F,0,{s_end_t},,1,0\n")

        f.write("//Storyboard Layer 4 (Overlay)\n"
                "//Storyboard Sound Samples\n")


if __name__ == '__main__':
    args = get_args()
    write_osb(storyboard_path=args.storyboard_path, lrc_path=args.lrc_path, file_path=args.storyboard_path,
              offset=args.offset, scale=args.scale, y=int(args.Y*480), font_size=args.font_size,
              stroke_width=args.stroke_width, skip_warning=args.y)
