import tkinter
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import merge_pdf


def ask_folder():
    """　フォルダ指定
    """
    path = filedialog.askdirectory()
    folder_path.set(path)


def app():
    """ 処理実行
    """
    is_reverse = order_comb.get() == "降順"
    input_dir = folder_path.get()
    # 保存するPDFファイルを指定
    output_file = filedialog.asksaveasfilename(
        filetypes=[("PDF files", "*.pdf")], defaultextension=".pdf"
    )
    if not input_dir or not output_file:
        return
    # 結合実行
    merge_pdf.merge_pdf_files(input_dir, output_file, is_reverse)
    # メッセージボックス
    messagebox.showinfo('完了', '完了しました。')


# メインウィンドウ
main_win = tkinter.Tk()
main_win.title("PDFを結合する")
main_win.geometry("500x120")

# メインフレーム
main_frm = ttk.Frame(main_win)
main_frm.grid(column=0, row=0, sticky=tkinter.NSEW, padx=5, pady=10)

# パラメータ
folder_path = tkinter.StringVar()

# ウィジェット（フォルダ名）
folder_label = ttk.Label(main_frm, text="フォルダ指定")
folder_box = ttk.Entry(main_frm, textvariable=folder_path)
folder_btn = ttk.Button(main_frm, text="参照", command=ask_folder)

# ウィジェット（並び順）
order_label = ttk.Label(main_frm, text="並び順")
order_comb = ttk.Combobox(main_frm, values=["昇順", "降順"], width=10)
order_comb.current(0)

# ウィジェット（実行ボタン）
app_btn = ttk.Button(main_frm, text="実行", command=app)

# ウィジェットの配置
folder_label.grid(column=0, row=0, pady=10)
folder_box.grid(column=1, row=0, sticky=tkinter.EW, padx=5)
folder_btn.grid(column=2, row=0)
order_label.grid(column=0, row=1)
order_comb.grid(column=1, row=1, sticky=tkinter.W, padx=5)
app_btn.grid(column=1, row=2)

# 配置設定
main_win.columnconfigure(0, weight=1)
main_win.rowconfigure(0, weight=1)
main_frm.columnconfigure(1, weight=1)

main_win.mainloop()
