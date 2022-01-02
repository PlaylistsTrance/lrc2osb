import argparse

from parser.lrc_parser import CharacterRenderer, LyricParser


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("lrc_path", type=str, help="Path to LRC file")
    parser.add_argument("storyboard_path", type=str, nargs="?", help="Name and path of the storyboard (ending on .osb)",
                        default="storyboard.osb")
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    CR = CharacterRenderer()
    LP = LyricParser(args.lrc_path, CR)
    # LP.parse_test()
    CR.render()

    with open(args.beatmap_path, "w", encoding="utf-8") as f:
        f.write("[Events]\n"
                "//Background and Video events\n"
                "//Storyboard Layer 0 (Background)\n"
                "//Storyboard Layer 1 (Fail)\n"
                "//Storyboard Layer 2 (Pass)\n"
                "//Storyboard Layer 3 (Foreground)\n")
        for sentence in LP.sentences:
            for letter in sentence.letters:
                if letter.start_t > sentence.start_t:
                    f.write(f"Sprite,Foreground,BottomLeft,{letter.filename_dark},"
                            f"{320 - sentence.width/2 + letter.offset_x:.4f},400\n")
                    f.write(f" F,0,{int(sentence.start_t*1000)-1},{int(sentence.start_t*1000)},0,1\n")
                    f.write(f" F,0,{int(letter.start_t*1000)-1},{int(letter.start_t*1000)},1,0\n")
            for letter in sentence.letters:
                f.write(f"Sprite,Foreground,BottomLeft,{letter.filename_light},"
                        f"{320 - sentence.width/2 + letter.offset_x:.4f},400\n")
                f.write(f" F,19,{int(letter.start_t*1000)},{int(letter.end_t*1000)-1},1\n")
                f.write(f" F,0,{int(sentence.end_t*1000)-1},{int(sentence.end_t*1000)},1,0\n")
        f.write(
                "//Storyboard Layer 4 (Overlay)\n"
                "//Storyboard Sound Samples\n")
