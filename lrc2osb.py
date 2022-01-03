import argparse

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
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    CR = CharacterRenderer()
    LP = LyricParser(args.lrc_path, CR)
    # LP.parse_test()
    CR.render()

    with open(args.storyboard_path, "w", encoding="utf-8") as f:
        f.write("[Events]\n"
                "//Background and Video events\n"
                "//Storyboard Layer 0 (Background)\n"
                "//Storyboard Layer 1 (Fail)\n"
                "//Storyboard Layer 2 (Pass)\n"
                "//Storyboard Layer 3 (Foreground)\n")
        for i, sentence in enumerate(LP.sentences):
            if i > 0 and sentence.start_t < LP.sentences[i-1].end_t:
                offset_y = LP.sentences[i-1].height + sentence.height/2
            else:
                offset_y = 0
            for letter in sentence.letters:
                if letter.character != " " and letter.start_t > sentence.start_t:
                    f.write(f"Sprite,Foreground,CentreLeft,{letter.filename_dark},"
                            f"{320 - sentence.width/2 + letter.offset_x:.4f},{args.y - offset_y:.4f}\n")
                    f.write(f" F,0,{int((sentence.start_t+args.offset)*1000)-1},"
                            f"{int((sentence.start_t+args.offset)*1000)},0,1\n")
                    f.write(f" F,0,{int((letter.start_t+args.offset)*1000)-1},"
                            f"{int((letter.start_t+args.offset)*1000)},1,0\n")
            for letter in sentence.letters:
                if letter.character != " ":
                    f.write(f"Sprite,Foreground,CentreLeft,{letter.filename_light},"
                            f"{320 - sentence.width/2 + letter.offset_x:.4f},{args.y - offset_y:.4f}\n")
                    f.write(f" F,19,{int(letter.start_t*1000)},{int(letter.end_t*1000)-1},0,1\n")
                    f.write(f" F,0,{int(sentence.end_t*1000)-1},{int(sentence.end_t*1000)},1,0\n")
        f.write(
                "//Storyboard Layer 4 (Overlay)\n"
                "//Storyboard Sound Samples\n")
