import gradio as gr
import time
import os
import zipfile
import shutil
from utils import authorize_google_sheets, analyze_and_replace, get_resource_usage
import json

# 將預設的 Google Sheet 名稱設為變數
DEFAULT_GSHEET_NAME = "dictionary"

def process_text(file_obj):
    if not file_obj:
         return "請上傳檔案", "", ""
    try:
        start_time = time.time()
        filename = os.path.basename(file_obj.name)
        with open(file_obj.name, 'r', encoding='utf-8') as f:
           text = f.read()

        # 從 credentials.json 讀取 Google Sheets 金鑰 JSON
        try:
            with open("credentials.json", "r") as f:
                json_content = json.load(f)
        except FileNotFoundError:
            return "找不到 credentials.json 檔案", "", ""
        except json.JSONDecodeError:
            return "credentials.json 檔案格式錯誤", "", ""

        dictionary = authorize_google_sheets(json_content, DEFAULT_GSHEET_NAME) #傳遞 JSON 物件

        # 確保字典中數據為字串類型
        dictionary['original'] = dictionary['original'].astype(str).fillna('')
        dictionary['modified'] = dictionary['modified'].astype(str).fillna('')
        dictionary['usecase'] = dictionary['usecase'].astype(str).fillna('')
        dictionary['no'] = dictionary['no'].astype(str).fillna('')
        
        report_lines = [f"處理完成: {filename}"] # 初始化報告清單
        updated_text = analyze_and_replace(text, dictionary, report_lines)
        end_time = time.time()
        resource_usage = get_resource_usage()
        report_lines.append(f"資源用量: {resource_usage}")
        report_lines.append(f"耗時: {end_time - start_time:.4f} 秒")
        report_text = "\n".join(report_lines)

        output_dir = "output_files"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{filename.rsplit('.', 1)[0]}_edited.{filename.rsplit('.', 1)[1]}")
        report_path = os.path.join(output_dir, "report.txt")

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(updated_text)

        with open(report_path, "w", encoding="utf-8") as report_file:
            for line in report_lines:
                report_file.write(line + "\n")

        zip_filename = f"{filename.rsplit('.', 1)[0]}.zip" # 根據原始檔案命名 zip 檔案
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
             zipf.write(output_path, os.path.relpath(output_path, output_dir))
             zipf.write(report_path, os.path.relpath(report_path, output_dir))
        shutil.rmtree(output_dir)


        return updated_text, report_text, zip_filename
    except Exception as e:
        return f"處理失敗: {e}", "", ""

if __name__ == "__main__":
    iface = gr.Interface(
        fn=process_text,
        inputs=[
            gr.File(label="上傳文本檔案"),
        ],
        outputs=[
            gr.Textbox(label="處理後的文本"),
            gr.Textbox(label="報告"),
            gr.File(label="下載壓縮檔")
        ],
        title="TextReplacer",
        description="請上傳文本檔案來處理文本。"
    )
    iface.launch()