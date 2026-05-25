import os
import shutil
import re

def remove_numbers_from_filenames(source_folder, target_folder):
    """
    删除源文件夹中所有文件名的数字，并将新文件保存到目标文件夹。
    """
    # 1. 如果目标文件夹不存在，则自动创建
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    # 2. 遍历源文件夹中的所有文件
    for filename in os.listdir(source_folder):
        source_file_path = os.path.join(source_folder, filename)

        # 确保只处理文件，不处理子文件夹
        if os.path.isfile(source_file_path):
            # 将文件名与扩展名分开 (例如: "file123.txt" 变成 "file123" 和 ".txt")
            name, ext = os.path.splitext(filename)
            
            # 使用正则表达式替换掉 name 中的所有数字
            new_name = re.sub(r'\d+', '', name)
            
            # 去除可能因为删除数字而产生的多余首尾空格
            new_name = new_name.strip()
            
            # 组合成新的文件名
            new_filename = new_name + ext
            
            # 构建目标文件路径
            target_file_path = os.path.join(target_folder, new_filename)
            
            # 3. 复制文件到新文件夹并重命名 (copy2 会保留原文件的创建/修改时间等元数据)
            shutil.copy2(source_file_path, target_file_path)
            
            print(f"成功: '{filename}' -> '{new_filename}'")

# ==========================================
# 使用说明：在这里修改你的文件夹路径
# ==========================================
if __name__ == "__main__":
    # 请将下面两个路径替换为你电脑上的实际路径
    # 注意：Windows 路径前保留字母 'r' 可以防止转义字符报错
    SOURCE_DIR = r"C:\Users\YS_SQI\Documents\Code\Python\music one"
    TARGET_DIR = r"C:\Users\YS_SQI\Documents\Code\Python\music one"
    
    print("开始处理文件...")
    remove_numbers_from_filenames(SOURCE_DIR, TARGET_DIR)
    print("所有文件处理完成！")