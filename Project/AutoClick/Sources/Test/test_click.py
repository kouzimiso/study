import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageFont
import pytesseract
from pytesseract import Output
import cv2
import numpy as np

# 画像にOKの文字を描画して保存
def create_ok_image():
    image_width = 200
    image_height = 100
    image = Image.new("RGB", (image_width, image_height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 36)
    text = "OK"
    text_width, text_height = draw.textsize(text, font)
    x = (image_width - text_width) / 2
    y = (image_height - text_height) / 2
    draw.text((x, y), text, fill="black", font=font)
    image.save("ok_image.png")

# Page2の画面を作成
def create_page2():
    page2 = tk.Toplevel(root)
    page2.title("Page2")
    label = tk.Label(page2, text="Page2")
    label.pack()

# OKの画像を検出してOCRを実行
def detect_ok_and_ocr():
    ok_image = cv2.imread("ok_image.png")
    screen = np.array(ImageGrab.grab(bbox=(0, 0, 800, 600)))

    # 画像からOKの文字を検出
    result = cv2.matchTemplate(screen, ok_image, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(result)

    if max_loc:
        # OKの文字を検出したらPage2を開く
        create_page2()
        # 画面をOCRで読み取り
        cropped_screen = screen[max_loc[1]:max_loc[1] + ok_image.shape[0], max_loc[0]:max_loc[0] + ok_image.shape[1]]
        ocr_text = pytesseract.image_to_string(cropped_screen, config='--psm 6', output_type=Output.STRING)

        # テキストに"Page2"が含まれていればOK、それ以外はNGと判定
        if "Page2" in ocr_text:
            messagebox.showinfo("OK", "OKのポップアップを表示します")
        else:
            messagebox.showerror("NG", "NGのポップアップを表示します")

# メインウィンドウの作成
root = tk.Tk()
root.title("OCRアプリ")

# OKの画像を作成
create_ok_image()

# ボタンの作成
button = tk.Button(root, text="検出とOCR実行", command=detect_ok_and_ocr)
button.pack()

# ラベルの作成
label = tk.Label(root, text="Page1")
label.pack()

root.mainloop()
