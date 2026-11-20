#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF抽出テキストの商品名区切り検査（Python標準ライブラリのみ）。"""
import bisect
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

SEPARATORS = {' ', '\u3000', '\n', '\r'}
ENCODINGS = ('utf-8-sig', 'cp932', 'utf-16')


def read_text(path):
    for encoding in ENCODINGS:
        try:
            return Path(path).read_text(encoding=encoding), encoding
        except UnicodeError:
            continue
    raise ValueError('文字コードを判定できません（UTF-8 / CP932 / UTF-16に対応）。')


def analyze(text, rule_lines):
    # スペース・改行を除いた文字列と、元テキストの位置の対応表を作る。
    chars, positions = [], []
    for i, char in enumerate(text):
        if char not in SEPARATORS:
            chars.append(char)
            positions.append(i)
    compact = ''.join(chars)
    line_starts = [0] + [m.end() for m in re.finditer(r'\n', text)]
    seen, rules = set(), []
    for raw in rule_lines:
        rule = raw.strip()
        if not rule or rule in seen:
            continue
        seen.add(rule)
        parts = rule.split('■')
        if len(parts) < 2 or any(not p for p in parts):
            continue  # ■のない行や空の区間は検査対象外
        rules.append((rule, parts))

    results = []
    for rule, parts in rules:
        needle = ''.join(parts)
        start = 0
        while True:
            at = compact.find(needle, start)
            if at == -1:
                break
            start = at + 1  # 重なる出現も検査
            missing = []
            offset = 0
            for idx, part in enumerate(parts[:-1], 1):
                offset += len(part)
                left = positions[at + offset - 1]
                right = positions[at + offset]
                between = text[left + 1:right]
                if not between or any(c not in SEPARATORS for c in between):
                    missing.append(str(idx))
            original_start = positions[at]
            original_end = positions[at + len(needle) - 1] + 1
            line_no = bisect.bisect_right(line_starts, original_start)
            results.append({
                'line': line_no,
                'status': 'NG' if missing else 'OK',
                'rule': rule,
                'missing': ','.join(missing) if missing else '-',
                'actual': text[original_start:original_end],
                'position': original_start,
            })
    results.sort(key=lambda x: (x['position'], x['rule']))
    return results, len(rules)


def save_report(path, source_path, rules_path, results, rule_count):
    ok = sum(r['status'] == 'OK' for r in results)
    ng = len(results) - ok
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        f.write('PDF抽出テキスト・区切り検査結果\n')
        f.write(f'抽出テキスト: {source_path}\n入力規則: {rules_path}\n')
        f.write(f'有効規則数: {rule_count}件 / 検出: {len(results)}件 / OK: {ok}件 / NG: {ng}件\n')
        f.write('※「■」の番号は左から1, 2, ... と数えます。\n')
        f.write('※照合できなかった規則は検出件数に含まれません。\n\n')
        f.write('【NG一覧】\n')
        if not ng:
            f.write('該当なし\n')
        for r in results:
            if r['status'] == 'NG':
                f.write(f"行{r['line']} / 区切り不足: {r['missing']}番目\n")
                f.write(f"  規則: {r['rule']}\n")
                f.write(f"  実際: {r['actual'].replace(chr(13), '〈CR〉').replace(chr(10), '〈改行〉')}\n\n")
        f.write('\n【全検出結果】\n')
        for r in results:
            actual = r['actual'].replace('\r', '〈CR〉').replace('\n', '〈改行〉')
            f.write(f"{r['status']} / 行{r['line']} / 区切り不足: {r['missing']} / {r['rule']} / {actual}\n")


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('PDF抽出テキスト 入力規則チェック')
        self.geometry('780x350')
        self.minsize(680, 320)
        self.source = tk.StringVar()
        self.rules = tk.StringVar()
        self.output = tk.StringVar()
        self.status = tk.StringVar(value='テキストと入力規則一覧を選択してください。')
        frame = ttk.Frame(self, padding=18)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='商品名の「■」区切りを検査', font=('', 15, 'bold')).pack(anchor='w', pady=(0, 15))
        self.file_row(frame, 'PDF抽出テキスト（.txt）', self.source, self.choose_source)
        self.file_row(frame, '入力規則一覧（.txt）', self.rules, self.choose_rules)
        self.file_row(frame, '結果の保存先（.txt）', self.output, self.choose_output)
        ttk.Label(frame, text='「■」には半角スペース・全角スペース・改行を許可します。規則一覧内の重複は自動で除外します。', wraplength=730).pack(anchor='w', pady=(7, 12))
        ttk.Button(frame, text='検査を実行して結果を保存', command=self.run).pack(anchor='center', ipady=7)
        ttk.Label(frame, textvariable=self.status, wraplength=730).pack(anchor='w', pady=(18, 0))

    def file_row(self, parent, title, variable, callback):
        group = ttk.Frame(parent)
        group.pack(fill='x', pady=6)
        ttk.Label(group, text=title, width=25).pack(side='left')
        ttk.Entry(group, textvariable=variable).pack(side='left', fill='x', expand=True, padx=6)
        ttk.Button(group, text='参照...', command=callback).pack(side='left')

    def choose_source(self):
        p = filedialog.askopenfilename(title='PDFから抽出したテキストを選択', filetypes=[('テキストファイル', '*.txt'), ('すべて', '*.*')])
        if p:
            self.source.set(p)
            if not self.output.get():
                self.output.set(str(Path(p).with_name(Path(p).stem + '_check_result.txt')))

    def choose_rules(self):
        p = filedialog.askopenfilename(title='入力規則一覧を選択', filetypes=[('テキストファイル', '*.txt'), ('すべて', '*.*')])
        if p:
            self.rules.set(p)

    def choose_output(self):
        p = filedialog.asksaveasfilename(title='結果の保存先とファイル名を指定', defaultextension='.txt', filetypes=[('テキストファイル', '*.txt')], initialfile=Path(self.output.get()).name if self.output.get() else 'check_result.txt')
        if p:
            self.output.set(p)

    def run(self):
        source, rules, output = (v.get().strip() for v in (self.source, self.rules, self.output))
        if not all((source, rules, output)):
            messagebox.showwarning('入力不足', '3つのファイルパスを指定してください。')
            return
        try:
            paths = [Path(x).resolve() for x in (source, rules, output)]
            if paths[2] in paths[:2]:
                raise ValueError('出力先に入力ファイルを指定できません。')
            text, _ = read_text(source)
            rule_text, _ = read_text(rules)
            results, count = analyze(text, rule_text.splitlines())
            if not count:
                raise ValueError('有効な「■」付き入力規則がありません。')
            if Path(output).exists() and not messagebox.askyesno('上書き確認', '出力ファイルが存在します。上書きしますか？'):
                return
            save_report(output, source, rules, results, count)
            ok = sum(r['status'] == 'OK' for r in results)
            ng = len(results) - ok
            msg = f'有効規則: {count}件 / 検出: {len(results)}件 / OK: {ok}件 / NG: {ng}件\n保存先: {output}'
            self.status.set(msg)
            messagebox.showinfo('検査完了', msg)
        except (OSError, ValueError) as e:
            messagebox.showerror('エラー', str(e))


if __name__ == '__main__':
    Application().mainloop()
