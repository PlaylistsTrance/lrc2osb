import argparse
import os.path

from parser.lrc_parser import CharacterRenderer, LyricParser


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

                    # Outline
                    outline_offset_x = (letter.width*(args.scale + 0.1) - letter.width*args.scale)/2
                    outline_offset_y = (letter.height*(args.scale + 0.1) - letter.height*args.scale)/2
                    f.write(f"Sprite,Pass,TopLeft,"
                            f"{character_renderer.get_filepath(letter.character)},"
                            f"{320 - sentence.width/2*args.scale + letter.offset_x*args.scale - outline_offset_x:.4f},"
                            f"{args.y - offset_y - outline_offset_y:.4f}\n")
                    f.write(f" F,0,{s_start_t},,1\n")
                    f.write(f" S,0,{s_start_t},,{args.scale + 0.1}\n")
                    f.write(f" F,0,{s_end_t},,1,0\n")

                    # Inner character
                    f.write(f"Sprite,Foreground,TopLeft,"
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


if __name__ == '__main__':
    args = get_args()
    CR = CharacterRenderer(file_path=os.path.dirname(args.storyboard_path))
    LP = LyricParser(args.lrc_path, CR)
    # LP.parse_test()
    write_osb(lyric_parser=LP, character_renderer=CR, file_path=args.storyboard_path, offset=args.offset)
