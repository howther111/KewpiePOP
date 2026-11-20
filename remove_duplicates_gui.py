import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path


def read_lines(path):
    # UTF-8 (BOM付き含む) を基本とし、Windowsの日本語テキストも扱う
    for encoding in ('utf-8-sig', 'cp932'):
        try:
            with path.open('r', encoding=encoding) as f:
                return f.read().splitlines(), encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeError('文字コードを判定できませんでした（UTF-8 / Shift_JIS対応）。')


class DuplicateRemover(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('テキスト重複行削除ツール')
        self.geometry('690x290')
        self.minsize(570, 260)
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.result = tk.StringVar(value='入力ファイルと出力ファイルを指定してください。')

        frame = ttk.Frame(self, padding=18)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text='入力ファイル').grid(row=0, column=0, sticky='w', pady=8)
        ttk.Entry(frame, textvariable=self.input_path).grid(row=0, column=1, sticky='ew', padx=10)
        ttk.Button(frame, text='参照...', command=self.select_input).grid(row=0, column=2)

        ttk.Label(frame, text='出力ファイル').grid(row=1, column=0, sticky='w', pady=8)
        ttk.Entry(frame, textvariable=self.output_path).grid(row=1, column=1, sticky='ew', padx=10)
        ttk.Button(frame, text='保存先...', command=self.select_output).grid(row=1, column=2)

        ttk.Label(frame, text='完全一致した行のみ削除し、最初の出現順を維持します。').grid(
            row=2, column=0, columnspan=3, sticky='w', pady=(12, 8))
        ttk.Button(frame, text='重複行を削除して保存', command=self.process).grid(
            row=3, column=0, columnspan=3, pady=12)
        ttk.Label(frame, textvariable=self.result, justify='left').grid(
            row=4, column=0, columnspan=3, sticky='w', pady=5)

    def select_input(self):
        name = filedialog.askopenfilename(
            title='入力テキストファイルを選択',
            filetypes=[('テキストファイル', '*.txt'), ('すべてのファイル', '*.*')])
        if name:
            self.input_path.set(name)
            src = Path(name)
            self.output_path.set(str(src.with_name(src.stem + '_unique.txt')))

    def select_output(self):
        name = filedialog.asksaveasfilename(
            title='出力ファイル名と保存先を指定',
            defaultextension='.txt',
            initialfile=Path(self.output_path.get()).name if self.output_path.get() else 'unique.txt',
            initialdir=str(Path(self.output_path.get()).parent) if self.output_path.get() else None,
            filetypes=[('テキストファイル', '*.txt'), ('すべてのファイル', '*.*')])
        if name:
            self.output_path.set(name)

    def process(self):
        src_text = self.input_path.get().strip()
        dst_text = self.output_path.get().strip()
        if not src_text or not dst_text:
            messagebox.showwarning('入力不足', '入力ファイルと出力ファイルを指定してください。')
            return
        src, dst = Path(src_text), Path(dst_text)
        if not src.is_file():
            messagebox.showerror('エラー', '入力ファイルが見つかりません。')
            return
        if src.resolve() == dst.resolve():
            messagebox.showerror('エラー', '元ファイル保護のため、別の出力ファイル名を指定してください。')
            return
        try:
            lines, encoding = read_lines(src)
            unique = list(dict.fromkeys(lines))
            if dst.exists() and not messagebox.askyesno('上書き確認', f'既存ファイルを上書きしますか？\n{dst}'):
                return
            with dst.open('w', encoding=encoding, newline='') as f:
                if unique:
                    f.write('\n'.join(unique) + '\n')
            summary = (f'処理前：{len(lines)}件　処理後：{len(unique)}件　'
                       f'削除：{len(lines) - len(unique)}件')
            self.result.set(summary + f'\n保存先：{dst}')
            messagebox.showinfo('処理完了', summary + f'\n\n保存先：{dst}')
        except (OSError, UnicodeError) as exc:
            messagebox.showerror('処理エラー', str(exc))


if __name__ == '__main__':
    DuplicateRemover().mainloop()
