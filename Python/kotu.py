import cv2
import numpy as np
import os

def process_to_white_bg(image_path, output_path):
    # 1. 读取图像
    img = cv2.imread(image_path)
    if img is None:
        return False

    # 2. 提取红色区域 (HSV 空间)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 红色范围涵盖
    lower1 = np.array([0, 50, 50])
    upper1 = np.array([10, 255, 255])
    lower2 = np.array([170, 50, 50])
    upper2 = np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(mask1, mask2)

    # 3. 创建纯白背景
    white_bg = np.full(img.shape, 255, dtype=np.uint8)

    # 4. 提取印章部分并覆盖到白色背景上
    # 只有 mask 为 255 的地方保留原图红色，其余地方保持白色
    res = cv2.bitwise_and(img, img, mask=mask)
    final_img = cv2.add(res, cv2.bitwise_and(white_bg, white_bg, mask=cv2.bitwise_not(mask)))

    # 5. 保存结果
    cv2.imwrite(output_path, final_img)
    return True

# --- 主循环逻辑 ---
input_folder = 'Python'  # 根据你之前的目录结构
output_folder = 'white_bg_seals'

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

for i in range(1, 11):
    filename = f"{i}.png"
    # 尝试多个可能的路径
    possible_paths = [filename, os.path.join(input_folder, filename)]
    
    success = False
    for path in possible_paths:
        if os.path.exists(path):
            out_path = os.path.join(output_folder, f"white_{i}.png")
            if process_to_white_bg(path, out_path):
                print(f"成功处理: {path} -> {out_path}")
                success = True
                break
    
    if not success:
        print(f"跳过: 未找到文件 {filename}")

print("\n所有操作已完成！请查看 'white_bg_seals' 文件夹。")