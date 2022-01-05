# lrc2osb
Script to convert LRC lyrics to osu! storyboard.
Uses a modified version of [frankhjwx's](https://github.com/frankhjwx/)
[LyricsParser](https://github.com/frankhjwx/osu-storyboard-engine/blob/master/Storyboard%20Engine/tools/LyricsParser.py).

## Set-up
You will need to have installed Python 3.\*. For example: Python 3.10.

Install the dependencies using `py -m pip install -r requirements.txt`.

## Usage

```
usage: lrc2osb.py [-h] [-o OFFSET] [-y] [-Y Y] [-s SCALE] [-fs FONT_SIZE] [-sw STROKE_WIDTH] lrc_path storyboard_path

positional arguments:
  lrc_path              path to LRC file
  storyboard_path       name and path of the storyboard to be made (ending with .osb)

options:
  -h, --help            show this help message and exit
  -o OFFSET, --offset OFFSET
                        offset in seconds (decimal) to line up the LRC with the beatmap audio
  -y                    overwrite existing storyboard and lyrics
  -Y Y                  y-coordinate for placing the lyrics (0.0 is top, 1.0 is bottom) (default: 0.80)
  -s SCALE, --scale SCALE
                        lyrics scale (default: 0.50
  -fs FONT_SIZE, --font-size FONT_SIZE
                        font size (default: 50)
  -sw STROKE_WIDTH, --stroke-width STROKE_WIDTH
                        stroke width (outline width) (default: 5)
```

## LRC format
This script expects LRC with \[MM:SS.ms\] timestamps and optional (Member(/Member2/Member3...)) member-coding.
Every timed line should start with a timestamp, and may contain multiple timestamps for karaoke-sync and line-end time.
Colors for member-coding are defined in [color_coding.json](https://github.com/PlaylistsTrance/lrc2osb/blob/main/color_coding.json).  
To use color-coding, include the group name at the start of the LRC file in `[ar: Group Name]`.  
If people sing who aren't part of the group in `[ar: Group Name]`,
you will have to define your own group in [color_coding.json](https://github.com/PlaylistsTrance/lrc2osb/blob/main/color_coding.json)
and use this group name in `[ar: Group Name]` instead.

Example:
```
[ar: Red Velvet]
[ti: FUTURE]
[al: Start-Up OST Part.1]
[by: RevolutionVoid]
[length: 3:39]
[re: RhythmiKaRuTTE_Spectro]
[ve: 2021-10-24]
[00:10.58](Wendy) 어[00:10.90]딘[00:11.13]지 [00:11.43]모[00:12.03]를[00:12.73] [00:12.98]꿈[00:13.29]결 [00:13.44]속[00:13.89]에[00:14.23]서[00:15.14]
[00:15.64](Wendy) 행[00:16.00]복[00:16.26]한 [00:16.35]날[00:16.79] [00:17.17]또[00:17.44] [00:17.78]본 [00:18.10]것 [00:18.28]같[00:18.40]았[00:18.65]어[00:19.09]
```
