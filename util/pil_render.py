from PIL import Image, ImageFont, ImageDraw


def render(text: str, stroke_width=5):
    font = ImageFont.truetype(font="malgunbd.ttf", size=70)
    offset = font.getoffset(text)
    print(offset)
    width, height = font.getsize(text, stroke_width=stroke_width)
    im = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    drawer = ImageDraw.Draw(im)

    r, g, b = [6, 193, 193]
    fill_color = (int(r+0.7*(255-r)), int(g+0.7*(255-g)), int(b+0.7*(255-b)))
    stroke_color = (6, 193, 193)

    drawer.text((-offset[0]+stroke_width, 0), text, font=font, fill=fill_color, stroke_width=stroke_width,
                stroke_fill=stroke_color)

    im.show("text-image")
    im.save("OH MY GIRL - STEP BY STEP (Line 1 - Jiho - pre).png")

    im = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    drawer = ImageDraw.Draw(im)

    fill_color = (int(0.6*r), int(0.6*g), int(0.6*b))

    drawer.text((-offset[0]+stroke_width, 0), text, font=font, fill=fill_color, stroke_width=stroke_width,
                stroke_fill=stroke_color)

    im.show("text-image")
    im.save("OH MY GIRL - STEP BY STEP (Line 1 - Jiho - post).png")


if __name__ == "__main__":
    # render("한")
    render("그댄 어디쯤 걷고 있나요", stroke_width=5)
    # render("j")
