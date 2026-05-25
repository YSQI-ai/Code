import matplotlib.pyplot as plt
import numpy as np

# 1. 题目参数设置
# 载波频率 fc = 10^4*pi / (2*pi) = 5000 Hz
fc = 5000 
# 调制信号频率 f1 = 2000*pi / (2*pi) = 1000 Hz, f2 = 2000 Hz
f_mod = [1000, 2000] 

# 计算 USB 和 LSB 的频率位置
usb_freqs = [fc + f for f in f_mod]  # [6000, 7000] Hz
lsb_freqs = [fc - f for f in f_mod]  # [4000, 3000] Hz
amplitude = 0.5  # 时域 cos(A)cos(B) 展开后的系数

# 2. 开始绘图
plt.figure(figsize=(12, 6))

# 绘制 LSB (下边带) - 橙色
markerline1, stemlines1, _ = plt.stem(lsb_freqs, [amplitude, amplitude], label='LSB (Lower Sideband)')
plt.setp(stemlines1, 'color', 'orange', 'linewidth', 2)
plt.setp(markerline1, 'markerfacecolor', 'orange', 'markeredgecolor', 'orange')

# 绘制 USB (上边带) - 蓝色
markerline2, stemlines2, _ = plt.stem(usb_freqs, [amplitude, amplitude], label='USB (Upper Sideband)')
plt.setp(stemlines2, 'color', 'blue', 'linewidth', 2)
plt.setp(markerline2, 'markerfacecolor', 'blue', 'markeredgecolor', 'blue')

# 绘制载波位置 (参考虚线)
plt.axvline(x=fc, color='red', linestyle='--', alpha=0.5, label='Carrier (Suppressed)')

# 3. 标注具体数值 (防止乱码，使用纯英文字符)
for f in lsb_freqs:
    plt.text(f, amplitude + 0.02, f'{f}Hz', ha='center', fontweight='bold', color='orange')
for f in usb_freqs:
    plt.text(f, amplitude + 0.02, f'{f}Hz', ha='center', fontweight='bold', color='blue')
plt.text(fc, 0.05, f'Carrier:{fc}Hz', ha='center', color='red', fontsize=10)

# 4. 图表装饰
plt.title('SSB Modulation Spectrum (USB vs LSB)', fontsize=14)
plt.xlabel('Frequency (Hz)', fontsize=12)
plt.ylabel('Amplitude', fontsize=12)
plt.ylim(0, 0.7)
plt.xlim(0, 9000)
plt.grid(True, axis='y', linestyle=':', alpha=0.7)
plt.legend()

plt.tight_layout()
plt.show()