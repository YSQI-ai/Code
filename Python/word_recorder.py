import os
import re
import requests
from bs4 import BeautifulSoup
import xlwings as xw
import tkinter as tk
from tkinter import filedialog, messagebox

class WordRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("专属单词本录入工具 (实时同步版)")
        self.root.geometry("520x450")
        
        self.existing_words = set()
        self.setup_ui()

    def setup_ui(self):
        # --- 文件路径区域 ---
        frame_file = tk.Frame(self.root)
        frame_file.pack(pady=10, padx=10, fill='x')
        
        tk.Label(frame_file, text="Excel文件路径:").pack(anchor='w')
        
        self.entry_filepath = tk.Entry(frame_file, width=50)
        self.entry_filepath.pack(side='left', expand=True, fill='x', padx=(0, 5))
        
        btn_browse = tk.Button(frame_file, text="浏览...", command=self.browse_file)
        btn_browse.pack(side='right')

        # --- 单词输入区域 ---
        frame_word = tk.Frame(self.root)
        frame_word.pack(pady=10, padx=10, fill='x')
        
        tk.Label(frame_word, text="输入英文单词:").pack(anchor='w')
        
        self.entry_word = tk.Entry(frame_word, font=('Arial', 14))
        self.entry_word.pack(side='left', expand=True, fill='x', padx=(0, 5))
        self.entry_word.bind('<Return>', lambda event: self.process_word())
        
        btn_add = tk.Button(frame_word, text="查询并添加", command=self.process_word, bg='#4CAF50', fg='white')
        btn_add.pack(side='right')

        # --- 日志显示区域 ---
        frame_log = tk.Frame(self.root)
        frame_log.pack(pady=10, padx=10, fill='both', expand=True)
        
        tk.Label(frame_log, text="运行日志:").pack(anchor='w')
        
        self.text_log = tk.Text(frame_log, state='disabled', font=('Consolas', 10))
        self.text_log.pack(fill='both', expand=True)

    def log(self, message):
        """向界面输出日志信息"""
        self.text_log.config(state='normal')
        self.text_log.insert(tk.END, message + "\n")
        self.text_log.see(tk.END) 
        self.text_log.config(state='disabled')

    def browse_file(self):
        """选择文件路径并加载查重词库"""
        filepath = filedialog.askopenfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filepath:
            self.entry_filepath.delete(0, tk.END)
            self.entry_filepath.insert(0, filepath)
            self.load_existing_words(filepath)

    def load_existing_words(self, file_path):
        """利用 xlwings 读取已存在的单词"""
        self.existing_words.clear()
        if os.path.exists(file_path):
            try:
                # xw.Book 会连接已打开的表格，或者自动打开闭合的表格
                wb = xw.Book(file_path)
                ws = wb.sheets[0]
                
                # 寻找最后一行
                last_row = ws.range('A' + str(ws.cells.last_cell.row)).end('up').row
                if last_row > 1:
                    vals = ws.range(f'A2:A{last_row}').value
                    if isinstance(vals, list):
                        for v in vals:
                            if v: self.existing_words.add(str(v).strip().lower())
                    elif vals:
                        self.existing_words.add(str(vals).strip().lower())
                        
                self.log(f"[*] 已成功连接表格，发现 {len(self.existing_words)} 个已存单词。")
            except Exception as e:
                self.log(f"[!] 读取表格失败: {e}")

    def get_word_info(self, word):
        """网络爬虫：获取音标和精简释义"""
        url = f"http://dict.youdao.com/w/{word}/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')

            phonetic_tags = soup.find_all('span', class_='phonetic')
            phonetic = phonetic_tags[0].text if phonetic_tags else ""

            meaning_str = ""
            trans_container = soup.find('div', class_='trans-container')
            if trans_container:
                ul = trans_container.find('ul')
                if ul:
                    first_li = ul.find('li') 
                    if first_li:
                        raw_text = first_li.text.strip()
                        raw_text = raw_text.split('【')[0]
                        raw_text = re.sub(r'\(.*?\)|\（.*?\）', '', raw_text)
                        parts = [p.strip() for p in raw_text.split('；') if p.strip()]
                        meaning_str = '；'.join(parts[:2])
            
            return phonetic, meaning_str
        except Exception as e:
            self.log(f"[!] 网络查询失败: {e}")
            return "", ""

    def append_to_excel(self, file_path, word, phonetic, meaning):
        """核心：通过 xlwings 实时写入数据并设置字体"""
        try:
            if not os.path.exists(file_path):
                # 如果文件不存在，新建并添加表头
                app = xw.App(visible=True, add_book=False)
                wb = app.books.add()
                ws = wb.sheets[0]
                ws.range('A1').value = ['单词', '音标', '中文释义']
                ws.range('A1:C1').api.Font.Bold = True # 表头加粗
                wb.save(file_path)
            else:
                # 连接或打开现有文件
                wb = xw.Book(file_path)
                ws = wb.sheets[0]

            # 寻找最后一行并在下一行写入
            last_row = ws.range('A' + str(ws.cells.last_cell.row)).end('up').row
            new_row = last_row + 1

            ws.range(f'A{new_row}').value = [word, phonetic, meaning]
            
            # 调用底层 COM 接口设置字体
            ws.range(f'A{new_row}:B{new_row}').api.Font.Name = 'Times New Roman'
            ws.range(f'A{new_row}:B{new_row}').api.Font.Size = 11
            ws.range(f'C{new_row}').api.Font.Name = '宋体'
            ws.range(f'C{new_row}').api.Font.Size = 11

            # 仅保存，不关闭窗口，实现所见即所得
            wb.save()
            return True
            
        except Exception as e:
            self.log(f"[!] 写入异常: {e}")
            return False
 
    def process_word(self):
        """处理查询和写入流程"""
        file_path = self.entry_filepath.get().strip()
        word = self.entry_word.get().strip()

        if not file_path:
            messagebox.showwarning("提示", "请先选择或输入 Excel 文件路径！")
            return
        if not word:
            return

        if word.lower() in self.existing_words:
            self.log(f"[跳过] '{word}' 已存在，请勿重复添加。")
            self.entry_word.delete(0, tk.END)
            return

        self.log(f"正在查询: {word} ...")
        self.root.update()

        phonetic, meaning = self.get_word_info(word)

        if not meaning:
            self.log(f"[失败] 未查到 '{word}' 的释义，请检查拼写。")
        else:
            if self.append_to_excel(file_path, word, phonetic, meaning):
                self.log(f"[成功] {word} {phonetic} -> {meaning}")
                self.existing_words.add(word.lower()) 
                self.entry_word.delete(0, tk.END) 

if __name__ == "__main__":
    root = tk.Tk()
    app = WordRecorderApp(root)
    root.mainloop()