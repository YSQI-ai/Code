import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.scrolledtext as scrolledtext
import subprocess
import os
import re
import threading
import sys

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

def log_msg(msg):
    log_box.config(state=tk.NORMAL)
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)
    log_box.config(state=tk.DISABLED)

def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    local_ffmpeg = os.path.join(application_path, "ffmpeg.exe")
    return f'"{local_ffmpeg}"' if os.path.exists(local_ffmpeg) else "ffmpeg"

def select_file():
    filepath = filedialog.askopenfilename(title="选择视频", filetypes=(("视频", "*.mp4 *.avi *.mkv *.mov *.flv"), ("所有", "*.*")))
    if filepath:
        file_path_var.set(filepath)
        if not out_path_var.get(): out_path_var.set(os.path.dirname(filepath))
        log_msg(f"📁 已选择视频: {filepath}")

def select_out_dir():
    folder = filedialog.askdirectory(title="选择输出位置")
    if folder: out_path_var.set(folder)

def toggle_mode():
    main_mode = mode_var.get()
    ppt_mode = ppt_submode_var.get()
    
    if main_mode == 1:
        parts_entry.config(state=tk.NORMAL)
        sense_entry.config(state=tk.DISABLED)
        interval_entry.config(state=tk.DISABLED)
        radio_smart.config(state=tk.DISABLED)
        radio_timer.config(state=tk.DISABLED)
    else:
        parts_entry.config(state=tk.DISABLED)
        radio_smart.config(state=tk.NORMAL)
        radio_timer.config(state=tk.NORMAL)
        
        if ppt_mode == 1:
            sense_entry.config(state=tk.NORMAL)
            interval_entry.config(state=tk.DISABLED)
        else:
            sense_entry.config(state=tk.DISABLED)
            interval_entry.config(state=tk.NORMAL)

def get_duration(input_file, ffmpeg_cmd):
    cmd = f'{ffmpeg_cmd} -i "{input_file}"'
    try:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
        match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)", result.stderr)
        if match: return float(match.group(1))*3600 + float(match.group(2))*60 + float(match.group(3))
        return -1
    except: return -1

def process_task(input_file, main_mode, ppt_mode, num_parts, interval, sensitivity, base_out_dir, use_subfolder):
    ffmpeg_cmd = get_ffmpeg_path()
    file_dir, file_name = os.path.split(input_file)
    base_name, ext = os.path.splitext(file_name)
    
    final_dir = base_out_dir if base_out_dir else file_dir
    if use_subfolder:
        suffix = "_切片" if main_mode == 1 else ("_智能笔记" if ppt_mode == 1 else "_定时笔记")
        final_dir = os.path.join(final_dir, base_name + suffix)
    if not os.path.exists(final_dir): os.makedirs(final_dir, exist_ok=True)

    if main_mode == 1:
        duration = get_duration(input_file, ffmpeg_cmd)
        if duration < 0:
            log_msg("❌ 失败：获取时长出错。")
            run_btn.config(state=tk.NORMAL)
            return
        segment_duration = duration / num_parts
        for i in range(num_parts):
            start_time = i * segment_duration
            out_file = os.path.join(final_dir, f"{base_name}_part{i+1}{ext}")
            cmd = f'{ffmpeg_cmd} -ss {start_time} -i "{input_file}" ' + (f'-t {segment_duration} ' if i < num_parts - 1 else '') + f'-c copy -y "{out_file}"'
            log_msg(f"✂️ 生成第 {i+1}/{num_parts} 部分...")
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
    elif main_mode == 2:
        if ppt_mode == 2:
            log_msg(f"📝 [模式: 定时抽帧] 开始提取，每 {interval} 秒截取...")
            output_pattern = os.path.join(final_dir, f"slide_%04d.jpg")
            cmd = f'{ffmpeg_cmd} -i "{input_file}" -vf "fps=1/{interval}" -q:v 2 "{output_pattern}" -y'
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        elif ppt_mode == 1:
            if not HAS_CV2:
                log_msg("❌ 错误：未检测到 OpenCV！")
                run_btn.config(state=tk.NORMAL)
                return
            
            log_msg(f"🧠 [抗干扰模式] 启动！忽略老师走动，专注板书更新...")
            cap = cv2.VideoCapture(input_file)
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0: fps = 25
            
            # 每秒抽查2次画面，加快速度
            frame_skip = int(fps / 2) 
            if frame_skip < 1: frame_skip = 1
            
            success, prev_frame = cap.read()
            if not success:
                log_msg("❌ 无法读取视频！")
                run_btn.config(state=tk.NORMAL)
                return
                
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            last_saved_gray = prev_gray # 记录上一张保存的笔记模样
            
            # 保存第一张
            out_path = os.path.join(final_dir, "slide_0001.jpg")
            cv2.imencode('.jpg', prev_frame)[1].tofile(out_path)
            log_msg(" ✔️ 保存初始板书: slide_0001.jpg")
            
            saved_count = 1
            stable_threshold = 0.3 # 动态防抖阈值（0.3%）：相邻画面变化小于这个值，才算“老师没在动”
            
            while True:
                for _ in range(frame_skip):
                    success = cap.grab()
                    if not success: break
                if not success: break
                
                success, frame = cap.retrieve()
                curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # 1. 测谎仪：判断画面是否稳定（过滤老师走动）
                diff_motion = cv2.absdiff(prev_gray, curr_gray)
                _, thresh_motion = cv2.threshold(diff_motion, 25, 255, cv2.THRESH_BINARY)
                motion_ratio = (np.sum(thresh_motion) / 255.0) / (curr_gray.shape[0] * curr_gray.shape[1]) * 100
                
                # 如果画面非常稳定（没人在大幅度走动）
                if motion_ratio < stable_threshold:
                    # 2. 对比仪：和上一张保存的笔记做对比，看看有没有多出新字
                    diff_update = cv2.absdiff(last_saved_gray, curr_gray)
                    _, thresh_update = cv2.threshold(diff_update, 25, 255, cv2.THRESH_BINARY)
                    update_ratio = (np.sum(thresh_update) / 255.0) / (curr_gray.shape[0] * curr_gray.shape[1]) * 100
                    
                    # 如果多出的新字超过了设定的灵敏度
                    if update_ratio > sensitivity:
                        saved_count += 1
                        out_path = os.path.join(final_dir, f"slide_{saved_count:04d}.jpg")
                        cv2.imencode('.jpg', frame)[1].tofile(out_path)
                        log_msg(f" ✔️ 板书更新已捕捉 (新增 {update_ratio:.2f}% 内容)，保存第 {saved_count} 张")
                        # 更新“上一张保存的笔记”的记忆
                        last_saved_gray = curr_gray
                        
                # 更新循环
                prev_gray = curr_gray
                
            cap.release()

    log_msg("-" * 30)
    log_msg(f"🎉 任务完成！存放于:\n{final_dir}")
    run_btn.config(state=tk.NORMAL)

def start_processing():
    input_file = file_path_var.get()
    if not os.path.exists(input_file): return messagebox.showerror("错误", "请选择视频！")
    
    main_mode = mode_var.get()
    ppt_mode = ppt_submode_var.get()
    num_parts, interval, sensitivity = 2, 10, 0.5
    
    if main_mode == 1:
        try:
            num_parts = int(parts_var.get())
            if num_parts < 2: raise ValueError
        except: return messagebox.showerror("错误", "分段数需大于1！")
    else:
        if ppt_mode == 1:
            try:
                sensitivity = float(sense_var.get())
                if sensitivity <= 0: raise ValueError
            except: return messagebox.showerror("错误", "更新阈值必须大于0！")
        else:
            try:
                interval = float(interval_var.get())
                if interval <= 0: raise ValueError
            except: return messagebox.showerror("错误", "间隔秒数必须大于0！")

    run_btn.config(state=tk.DISABLED)
    log_msg("\n" + "=" * 30)
    threading.Thread(target=process_task, args=(input_file, main_mode, ppt_mode, num_parts, interval, sensitivity, out_path_var.get(), subfolder_bool.get()), daemon=True).start()

# ==================== GUI 布局 ====================
root = tk.Tk()
root.title("全能课堂神器 (抗走动智能笔记版)")
root.geometry("700x680")
root.configure(padx=20, pady=10)

f1 = tk.Frame(root); f1.pack(fill=tk.X, pady=5)
tk.Label(f1, text="视频文件:", width=10, anchor=tk.W, font=("微软雅黑", 10)).pack(side=tk.LEFT)
file_path_var = tk.StringVar()
tk.Entry(f1, textvariable=file_path_var, state="readonly", font=("微软雅黑", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
tk.Button(f1, text="浏览视频", command=select_file, font=("微软雅黑", 9)).pack(side=tk.LEFT)

mode_frame = tk.LabelFrame(root, text=" 处理模式设置 ", font=("微软雅黑", 10, "bold"), padx=10, pady=10)
mode_frame.pack(fill=tk.X, pady=10)

mode_var = tk.IntVar(value=1)
ppt_submode_var = tk.IntVar(value=1)

m1_frame = tk.Frame(mode_frame); m1_frame.pack(fill=tk.X, pady=5)
tk.Radiobutton(m1_frame, text="【模式 1】 极速视频切片", variable=mode_var, value=1, command=toggle_mode, font=("微软雅黑", 10, "bold"), fg="#D35400").pack(side=tk.LEFT)
tk.Label(m1_frame, text="分几段:", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=(10, 5))
parts_var = tk.StringVar(value="2")
parts_entry = tk.Entry(m1_frame, textvariable=parts_var, width=6, font=("微软雅黑", 9))
parts_entry.pack(side=tk.LEFT)

tk.Frame(mode_frame, height=1, bg="#E0E0E0").pack(fill=tk.X, pady=5)

tk.Radiobutton(mode_frame, text="【模式 2】 提取 PPT/黑板笔记", variable=mode_var, value=2, command=toggle_mode, font=("微软雅黑", 10, "bold"), fg="#2980B9").pack(anchor=tk.W)

sub1_frame = tk.Frame(mode_frame); sub1_frame.pack(fill=tk.X, padx=20, pady=3)
radio_smart = tk.Radiobutton(sub1_frame, text="A. 抗干扰智能提取", variable=ppt_submode_var, value=1, command=toggle_mode, font=("微软雅黑", 9), state=tk.DISABLED)
radio_smart.pack(side=tk.LEFT)
tk.Label(sub1_frame, text="新内容识别阈值(%):", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=(5, 5))
sense_var = tk.StringVar(value="0.8") # 默认改成0.8，避免太灵敏
sense_entry = tk.Entry(sub1_frame, textvariable=sense_var, width=6, font=("微软雅黑", 9), state=tk.DISABLED)
sense_entry.pack(side=tk.LEFT)
tk.Label(sub1_frame, text="(等老师走开后，发现新板书才截图)", font=("微软雅黑", 8, "italic"), fg="gray").pack(side=tk.LEFT, padx=5)

sub2_frame = tk.Frame(mode_frame); sub2_frame.pack(fill=tk.X, padx=20, pady=3)
radio_timer = tk.Radiobutton(sub2_frame, text="B. 传统定时抽帧", variable=ppt_submode_var, value=2, command=toggle_mode, font=("微软雅黑", 9), state=tk.DISABLED)
radio_timer.pack(side=tk.LEFT)
tk.Label(sub2_frame, text="截取间隔(秒):", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=(5, 5))
interval_var = tk.StringVar(value="10")
interval_entry = tk.Entry(sub2_frame, textvariable=interval_var, width=6, font=("微软雅黑", 9), state=tk.DISABLED)
interval_entry.pack(side=tk.LEFT)

f3 = tk.Frame(root); f3.pack(fill=tk.X, pady=5)
tk.Label(f3, text="输出路径:", width=10, anchor=tk.W, font=("微软雅黑", 10)).pack(side=tk.LEFT)
out_path_var = tk.StringVar()
tk.Entry(f3, textvariable=out_path_var, font=("微软雅黑", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
tk.Button(f3, text="选择路径", command=select_out_dir, font=("微软雅黑", 9)).pack(side=tk.LEFT)

f4 = tk.Frame(root); f4.pack(fill=tk.X, pady=2)
subfolder_bool = tk.BooleanVar(value=True)
tk.Checkbutton(f4, text="自动创建同名文件夹进行收纳", variable=subfolder_bool, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=10)

run_btn = tk.Button(root, text="🚀 执 行 任 务", command=start_processing, bg="#0078D7", fg="white", font=("微软雅黑", 12, "bold"), pady=10)
run_btn.pack(fill=tk.X, pady=10)

tk.Label(root, text="运行进度日志:", font=("微软雅黑", 10)).pack(anchor=tk.W)
log_box = scrolledtext.ScrolledText(root, height=10, state=tk.DISABLED, bg="#F5F5F5", font=("Consolas", 9), fg="#333333")
log_box.pack(fill=tk.BOTH, expand=True)

root.after(500, get_ffmpeg_path)
root.mainloop()