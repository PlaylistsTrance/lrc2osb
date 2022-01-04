import argparse
import os

from send2trash import send2trash

from parser.lrc_parser import CharacterRenderer, LyricParser
from parser.lrc_parser_pil import CharacterRenderer as CharacterRendererPIL, LyricParser as LyricParserPIL


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("lrc_path", type=str, help="path to LRC file")
    parser.add_argument("-p", "--storyboard_path", type=str, nargs="?",
                        help="name and path of the storyboard (ending with .osb)", default="storyboard.osb")
    parser.add_argument("-o", "--offset", type=float, nargs="?", default=0.0,
                        help="offset in seconds (decimal) to line up the LRC with the beatmap audio")
    parser.add_argument("-y", type=float, default=400.0,
                        help="y-coordinate for placing the lyrics (0 is highest, 480 is lowest) (default: 400.0)")
    parser.add_argument("-s", "--scale", type=float, default=0.5, help="Font scale")
    return parser.parse_args()


def write_osb(lyric_parser: LyricParser, character_renderer: CharacterRenderer, file_path: str, offset=0.0):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("[Events]\n"
                "//Background and Video events\n"
                "//Storyboard Layer 0 (Background)\n"
                "//Storyboard Layer 1 (Fail)\n"
                "//Storyboard Layer 2 (Pass)\n"
                "//Storyboard Layer 3 (Foreground)\n")
        for i, sentence in enumerate(lyric_parser.sentences):
            f.write(f"//{sentence.content}\n")
            if i > 0 and sentence.start_t < lyric_parser.sentences[i-1].end_t:
                offset_y = sentence.height*args.scale
            else:
                offset_y = 0
            s_start_t = int((sentence.start_t + offset)*1000)
            s_end_t = int((sentence.end_t + offset)*1000)
            for j, letter in enumerate(sentence.letters):
                if letter.character != " ":
                    f.write(f"//{letter.character}\n")

                    # Inner character
                    f.write(f"Sprite,Foreground,CentreLeft,"
                            f"{character_renderer.get_filepath(letter.character)},"
                            f"{320 - sentence.width/2*args.scale + letter.offset_x*args.scale:.4f},"
                            f"{args.y - offset_y:.4f}\n")
                    f.write(f" F,0,{s_start_t},,1\n")
                    if args.scale != 1:
                        f.write(f" S,0,{s_start_t},,{args.scale:.4f}\n")
                    if letter.start_t > sentence.start_t:
                        if letter.color:
                            f.write(f" C,0,{s_start_t},,{','.join([f'{int(x*0.5)}' for x in letter.color])}\n")
                        else:
                            f.write(f" C,0,{s_start_t},,0,0,0\n")

                    l_start_t = int(letter.start_t*1000)
                    l_end_t = int(letter.end_t*1000)
                    if letter.color:
                        f.write(f" C,0,{l_start_t},{l_end_t},{','.join(map(str, letter.color))}\n")
                    else:
                        f.write(f" C,0,{l_start_t},{l_end_t},255,255,255\n")
                    f.write(f" F,0,{s_end_t},,1,0\n")
        f.write("//Storyboard Layer 4 (Overlay)\n"
                "//Storyboard Sound Samples\n")


def write_osb2(storyboard_path: str, lrc_path: str, file_path: str, offset=0.0, scale=1.0, y=0.0, fade_time=400):
    character_renderer = CharacterRendererPIL(file_path=os.path.dirname(storyboard_path))
    lyric_parser = LyricParserPIL(lrc_path, character_renderer)

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
            f.write(f"//{sentence.content}\n")
            if i > 0 and sentence.start_t < lyric_parser.sentences[i-1].end_t:
                offset_y = lyric_parser.sentences[i-1].height*scale
            else:
                offset_y = 0
            s_start_t = int((sentence.start_t + offset)*1000)
            s_end_t = int((sentence.end_t + offset)*1000)

            if sentence.letters[-1].start_t != sentence.start_t:
                if i == 0:
                    fade_in_duration = int(min(fade_time, s_start_t))
                else:
                    s_diff = (lyric_parser.sentences[i-1].end_t - sentence.start_t)/2*1000
                    fade_in_duration = int(min(fade_time, s_diff))

                # Pre-sync
                for letter in sentence.letters:
                    if letter.character == " ":
                        continue
                    x = 320 - sentence.width/2*scale + (letter.offset_sentence+letter.offset_x)*scale
                    f.write(f"Sprite,Foreground,TopLeft,"
                            f"\"{character_renderer.get_image(letter, pre_sync=True)}\","
                            f"{x:.4f},{y - offset_y:.4f}\n")
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
                            f"{x:.4f},{y - offset_y:.4f}\n")

                    # Fade in
                    f.write(f" F,0,{l_start_t},{l_end_t},0,1\n")
                    if scale != 1:
                        f.write(f" S,0,{l_start_t},,{scale:.4f}\n")

                    # Fade out
                    if i < (len(lyric_parser.sentences)-1):
                        s_diff = (lyric_parser.sentences[i+1].start_t-sentence.end_t)/2*1000
                        fade_out_duration = int(min(fade_time, s_diff))
                    else:
                        fade_out_duration = fade_time
                    if fade_out_duration:
                        f.write(f" F,0,{s_end_t},{s_end_t+fade_out_duration},1,0\n")
                    else:
                        f.write(f" F,0,{s_end_t},,1,0\n")
        f.write("//Storyboard Layer 4 (Overlay)\n"
                "//Storyboard Sound Samples\n")


if __name__ == '__main__':
    args = get_args()
    # CR = CharacterRendererPIL(file_path=os.path.dirname(args.storyboard_path))
    # LP = LyricParserPIL(args.lrc_path, CR)
    # LP.parse_test()
    # write_osb(lyric_parser=LP, character_renderer=CR, file_path=args.storyboard_path, offset=args.offset)
    write_osb2(storyboard_path=args.storyboard_path, lrc_path=args.lrc_path, file_path=args.storyboard_path,
               offset=args.offset, scale=args.scale, y=args.y)
