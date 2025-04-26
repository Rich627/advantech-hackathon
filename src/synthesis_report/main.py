from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import json

# Get the absolute paths
current_dir = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(current_dir, "..", "Noto_Sans_TC", "NotoSansTC-VariableFont_wght.ttf")
image_dir = os.path.join(current_dir, "image")
metadata_dir = os.path.join(current_dir, "metadata")
report_dir = os.path.join(current_dir, "report")


# Register font
pdfmetrics.registerFont(TTFont('NotoTC', font_path))

def generate_report(report, image_path=None, output_path=None):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # 標題
    c.setFont("NotoTC", 18)
    c.drawCentredString(width / 2, height - 50, "隧道裂縫維修報告")

    # 設定初始 y 位置（從頂部開始）
    y = height - 100  # 標題下方留空間

    # 插入圖片（如果有的話）
    if image_path:
        try:
            img = ImageReader(image_path)
            # 獲取圖片尺寸
            img_width, img_height = img.getSize()
            # 計算縮放比例，保持寬度在 400 以內
            scale = min(400 / img_width, 1.0)
            # 計算縮放後的尺寸
            scaled_width = img_width * scale
            scaled_height = img_height * scale
            # 計算圖片位置（置中）
            x = (width - scaled_width) / 2
            # 在標題下方繪製圖片
            c.drawImage(img, x, y - scaled_height, width=scaled_width, height=scaled_height, preserveAspectRatio=True)
            # 更新 y 位置（圖片下方）
            y = y - scaled_height - 50  # 圖片下方留 50 點空間
            print(f"Image successfully inserted: {image_path}")
        except Exception as e:
            print(f"Warning: Could not load image: {e}")
    else:
        print("Warning: No image provided")
        y = y - 50  # 如果沒有圖片，也留些空間

    # 寫入資料
    c.setFont("NotoTC", 12)
    line_spacing = 20

    # 嚴格按照提供的 schema 順序
    fields = [
        ("報告編號", report["id"]),
        ("時間戳記", report["timestamp"]),
        ("裂縫長度", f"{report['length']} 公分"),
        ("裂縫寬度", f"{report['width']} 公分"),
        ("位置", report["position"]),
        ("材料", report["material"]),
        ("裂縫位置", report["crack_location"]),
        ("檢修人員", report["engineer"]),
        ("風險等級", report["risk_level"]),
        ("處理方案", report["action"])
    ]

    # 繪製欄位
    for label, value in fields:
        if label == "處理方案":
            # 處理方案可能較長，需要特殊處理
            y -= line_spacing  # 額外空間
            c.drawString(80, y, f"{label}：")
            y -= line_spacing
            
            # 處理長文字換行
            text_width = width - 160  # 左右各留 80 點空間
            c.setFont("NotoTC", 10)  # 使用較小的字型來顯示詳細內容
            
            # 每 40 個字元換行
            text = value
            while text:
                if len(text) > 40:
                    line = text[:40]
                    text = text[40:]
                else:
                    line = text
                    text = ""
                c.drawString(80, y, line)
                y -= line_spacing * 0.8  # 稍微縮小行距
        else:
            c.setFont("NotoTC", 12)
            c.drawString(80, y, f"{label}：{value}")
            y -= line_spacing

    c.save()

def process_all_reports():
    # 讀取指定的 metadata 檔案
    metadata_file = "sample_metadata.json"
    metadata_path = os.path.join(metadata_dir, metadata_file)
    
    if not os.path.exists(metadata_path):
        print(f"Error: Metadata file not found: {metadata_path}")
        return

    # 讀取 metadata
    with open(metadata_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    # 設定圖片路徑
    image_path = None
    for ext in ['.jpg', '.jpeg', '.png']:
        temp_path = os.path.join(image_dir, "sample_image" + ext)
        if os.path.exists(temp_path):
            image_path = temp_path
            break
    
    if not image_path:
        print("Warning: No image found with name 'sample_image'")
    
    # 設定輸出 PDF 路徑
    output_path = os.path.join(report_dir, "sample_report.pdf")
    
    # 生成報告
    generate_report(report_data, image_path, output_path)
    print(f"Generated report: {output_path}")

if __name__ == "__main__":
    process_all_reports()