
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import fitz  # PyMuPDF


def extract_pdf_text():
    # PDFファイルを選択
    pdf_path = filedialog.askopenfilename(
        title="テキストを抽出するPDFを選択",
        filetypes=[("PDFファイル", "*.pdf")]
    )

    if not pdf_path:
        return

    try:
        # PDFを開いてテキストを抽出
        texts = []

        with fitz.open(pdf_path) as doc:
            for page_number, page in enumerate(doc, start=1):
                text = page.get_text("text", sort=True)

                texts.append(
                    f"===== {page_number}ページ =====\n"
                    f"{text}\n"
                )

        # 保存先を指定
        default_name = Path(pdf_path).stem + ".txt"

        save_path = filedialog.asksaveasfilename(
            title="抽出したテキストの保存先",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("テキストファイル", "*.txt")]
        )

        if not save_path:
            return

        # UTF-8形式で保存
        with open(save_path, "w", encoding="utf-8") as f:
            f.write("\n".join(texts))

        messagebox.showinfo(
            "完了",
            f"テキスト抽出が完了しました。\n\n{save_path}"
        )

    except Exception as e:
        messagebox.showerror(
            "エラー",
            f"処理中にエラーが発生しました。\n{e}"
        )


# GUI画面
root = tk.Tk()
root.title("PDFテキスト抽出ツール")
root.geometry("440x220")
root.resizable(False, False)

title_label = tk.Label(
    root,
    text="PDFテキスト抽出ツール",
    font=("Arial", 17, "bold")
)
title_label.pack(pady=25)

description = tk.Label(
    root,
    text="PDFファイルを選択してテキストを抽出します。",
    font=("Arial", 11)
)
description.pack(pady=5)

extract_button = tk.Button(
    root,
    text="PDFファイルを選択",
    font=("Arial", 12),
    width=24,
    height=2,
    command=extract_pdf_text
)
extract_button.pack(pady=20)

root.mainloop()
