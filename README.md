# lrc2osb
Script to convert LRC lyrics to osu! storyboard

## Set-up
You will need to have installed Python 3.\*. For example: Python 3.10.

Install the depencies using `py -m pip install -r requirements.txt`.

## Usage

`py .\lrc2osb.py "/path/to/lyrics.lrc" "/path/to/storyboard.osb"`
Where the path to storyboard does not yet exist.

## LRC format
This script expects LRC with only \[MM:SS.ms\] timestamps. Every timed line should start with one, and may contain multiple timestamps for karaoke-sync and line-end time.

Example:
```
[ar: PURPLE KISS]
[ti: Cast pearls before swine]
[al: HIDE & SEEK]
[by: RevolutionVoid]
[re: RhythmiKaRuTTE]
[length: 03:08]
[00:06.31]뭐[00:06.48]라[00:06.68]는 [00:06.96]거[00:07.09]니[00:07.37] [00:07.91]솔[00:08.11]직[00:08.36]해 [00:08.57]봐 [00:08.97]봐
[00:09.51]뭐 [00:09.73]하[00:09.93]는 [00:10.15]거[00:10.29]니[00:10.53] [00:11.05]내 [00:11.33]눈 [00:11.51]쳐[00:11.74]다[00:12.15]봐
[00:12.73]나 [00:12.93]혼[00:13.12]자 [00:13.34]벌[00:14.35]받[00:14.52]는 [00:14.74]거 [00:14.99]같[00:15.30]아
[00:16.39]사[00:16.67]랑[00:16.95]이[00:17.14]란 [00:17.36]불[00:17.52]에 [00:17.75]데[00:17.90]었[00:18.11]잖[00:18.53]아
[00:19.31]새[00:20.13]빨[00:20.26]간 [00:20.89]거[00:21.02]짓[00:21.70]말[00:21.96]은 [00:22.11]그[00:22.51]만
[00:23.33]그[00:23.46]럴 [00:24.12]시[00:24.25]간[00:24.75]에 [00:24.92]잠[00:25.11]이[00:25.37]나 [00:25.75]자[00:26.12]```
