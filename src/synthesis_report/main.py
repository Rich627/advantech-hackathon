import os
import json
from datetime import datetime
from typing import List, Dict, Any
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Paths setup
current_dir = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(current_dir, '..', 'Noto_Sans_TC', 'NotoSansTC-VariableFont_wght.ttf')
image_dir = os.path.join(current_dir, 'image')
metadata_dir = os.path.join(current_dir, 'metadata')
report_dir = os.path.join(current_dir, 'report')

# Register font
pdfmetrics.registerFont(TTFont('NotoTC', font_path))

def generate_report(report: Dict[str, Any], image_path: str = None, output_path: str = None):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Title
    c.setFont('NotoTC', 18)
    c.drawCentredString(width / 2, height - 50, '隧道裂縫維修報告')

    # Start Y
    y = height - 100

    # Insert image
    if image_path and os.path.exists(image_path):
        try:
            img = ImageReader(image_path)
            img_w, img_h = img.getSize()
            scale = min(400 / img_w, 1.0)
            scaled_w, scaled_h = img_w * scale, img_h * scale
            x = (width - scaled_w) / 2
            c.drawImage(img, x, y - scaled_h, width=scaled_w, height=scaled_h, preserveAspectRatio=True)
            y -= scaled_h + 50
        except Exception as e:
            print(f'Warning: Could not load image {image_path}: {e}')
            y -= 50
    else:
        print(f'Warning: No image for report {report.get("id")}, continuing without image.')
        y -= 50

    # Write fields
    c.setFont('NotoTC', 12)
    line_spacing = 20
    fields = [
        ('報告編號', report.get('id', '')),
        ('時間戳記', report.get('timestamp', '')),
        ('裂縫長度', f"{report.get('length', '')} 公分"),
        ('裂縫寬度', f"{report.get('width', '')} 公分"),
        ('位置', report.get('position', '')),
        ('材料', report.get('material', '')),
        ('裂縫位置', report.get('crack_location', '')),
        ('檢修人員', report.get('engineer', '')),
        ('風險等級', report.get('risk_level', '')),
        ('處理方案', report.get('action', ''))
    ]

    for label, value in fields:
        if label == '處理方案':
            y -= line_spacing
            c.drawString(80, y, f"{label}：")
            y -= line_spacing
            c.setFont('NotoTC', 10)
            text = value
            max_chars = 40
            while text:
                line = text[:max_chars]
                text = text[max_chars:]
                c.drawString(80, y, line)
                y -= line_spacing * 0.8
        else:
            c.setFont('NotoTC', 12)
            c.drawString(80, y, f"{label}：{value}")
            y -= line_spacing

    c.save()


def process_all_reports():
    # Load generated metadata list
    metadata_file = 'generated_metadata.json'
    metadata_path = os.path.join(metadata_dir, metadata_file)

    if not os.path.exists(metadata_path):
        print(f"Error: Metadata file not found: {metadata_path}")
        return

    with open(metadata_path, 'r', encoding='utf-8') as f:
        reports = json.load(f)

    # Ensure report directory exists
    os.makedirs(report_dir, exist_ok=True)

    for report in reports:
        image_url = report.get('image_url', '')
        filename = os.path.basename(image_url)
        local_image = os.path.join(image_dir, filename)

        if not os.path.exists(local_image):
            print(f"Warning: Image file not found for {report['id']}: {local_image}")
            image_path = None
        else:
            image_path = local_image

        output_pdf = os.path.join(report_dir, f"{report['id']}.pdf")
        generate_report(report, image_path, output_pdf)
        print(f"Generated PDF for {report['id']}: {output_pdf}")


if __name__ == '__main__':
    process_all_reports()
