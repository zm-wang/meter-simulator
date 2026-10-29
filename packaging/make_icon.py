#!/usr/bin/env python3
"""生成程序图标 icon.png / icon.ico（需要 Pillow）。图标已提交，改样式时才需要重跑。"""

import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1024


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def main():
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 表壳
    d.rounded_rectangle((90, 70, 934, 954), radius=150, fill=(38, 50, 66))
    d.rounded_rectangle((90, 70, 934, 954), radius=150, outline=(90, 110, 135), width=14)
    # 液晶屏
    d.rounded_rectangle((180, 180, 844, 470), radius=40, fill=(176, 214, 140))
    d.text((512, 300), '0123.4', font=font(190), fill=(30, 52, 24), anchor='mm')
    d.text((800, 425), 'kWh', font=font(70), fill=(30, 52, 24), anchor='rm')
    # 光口 + 脉冲灯
    d.ellipse((330, 580, 530, 780), fill=(20, 26, 34), outline=(120, 140, 165), width=12)
    d.ellipse((395, 645, 465, 715), fill=(200, 60, 50))
    d.ellipse((640, 620, 720, 700), fill=(240, 80, 60))
    d.text((680, 760), 'IEC', font=font(80), fill=(200, 210, 222), anchor='mm')
    d.text((512, 880), '62056-21', font=font(72), fill=(150, 165, 185), anchor='mm')

    img.save(os.path.join(HERE, 'icon.png'))
    img.save(os.path.join(HERE, 'icon.ico'),
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print('icon.png / icon.ico 已生成')


if __name__ == '__main__':
    main()
