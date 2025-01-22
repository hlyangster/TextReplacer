import pandas as pd
import time
import os
import psutil
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import jieba
import json

# 1. 從 Google Sheets 取得字典
def authorize_google_sheets(json_content, sheet_name):
    # 使用 ServiceAccountCredentials.from_json_keyfile_dict 解析 JSON 物件
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_content, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(credentials)
    spreadsheet = client.open(sheet_name)
    sheet = spreadsheet.sheet1
    data = sheet.get_all_records()
    dictionary = pd.DataFrame(data)
    return dictionary

# 2. 使用 Jieba 進行斷詞
def jieba_segmentation(text):
    seg_list = jieba.cut(text)
    return list(seg_list)

# 3. 核心替換邏輯
def analyze_and_replace(text, dictionary, report_lines):
    updated_text = text  # 初始化為原始文本
    segmented_text = jieba_segmentation(text)  # 取得斷詞結果
    report_lines.append(f"斷詞結果:\n{' '.join(segmented_text)}") # 添加斷詞結果到報告

    replaced_indices = set() # 追蹤已替換的詞彙索引

    for _, row in dictionary.iterrows():
        no = str(row['no'])
        original = str(row['original'])
        replacement = str(row['modified'])
        usecases = str(row['usecase']).split(",")
        usecases = [uc.strip() for uc in usecases]  # 清理空白

        for index, word in enumerate(segmented_text):
            if index in replaced_indices:
                continue # 如果已經替換過，跳過

            for usecase in usecases:
                if word == usecase:
                    if len(usecase) > 1:
                        try:
                            pos = usecase.index(original)
                            if pos >= 0 :
                                updated_text = updated_text.replace(usecase, usecase[:pos] + replacement + usecase[pos+1:])
                                report_lines.append(f"替換成功：'{usecase}' -> '{usecase[:pos] + replacement + usecase[pos+1:]}'")
                        except ValueError:
                            print (f"ValueError: Can't find '{original}' in '{usecase}'")
                            continue
                    else:
                        updated_text = updated_text.replace(word, replacement)
                        report_lines.append(f"替換成功：'{word}' -> '{replacement}'")

                    replaced_indices.add(index)  # 添加到已替換集合
                    break

    return updated_text

# 4. 顯示資源用量
def get_resource_usage():
    process = psutil.Process(os.getpid())
    memory_usage = process.memory_info().rss / 1024 / 1024 # in MB
    cpu_usage = process.cpu_percent()
    return f"Memory Usage: {memory_usage:.2f} MB, CPU Usage: {cpu_usage}%"