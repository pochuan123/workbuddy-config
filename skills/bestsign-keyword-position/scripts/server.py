"""
PDF 关键字坐标定位服务
用途：接收 PDF 文件和关键字，返回关键字在 PDF 中的坐标位置

坐标规则：上上签标准
  - 原点：页面左下角（bottom-left）
  - X轴：向右为正，距左边距离 / 页宽 → 比例值 [0,1]
  - Y轴：向上为正，距下边距离 / 页高 → 比例值 [0,1]
  - 锚点：印章图片左下角
  - 输出：关键字右下角坐标（与上上签"多关键字查询"返回格式一致）

坐标格式：支持两种输出模式（通过 unit 参数指定）
  - unit=ratio（默认）：比例值 [0,1]
  - unit=pixel：72dpi 绝对像素值（PyMuPDF 坐标天然就是 72dpi 像素）

印章居中偏移（参考上上签文档）：
  - X基础偏移 -0.1630, Y基础偏移 -0.0925 可使印章中心与关键字中心重合

支持两种 PDF 类型：
1. 文本型 PDF → PyMuPDF 直接提取（快速、精确）
2. 图片型 PDF → Tesseract OCR 识别（需要安装 Tesseract）
"""

import io
import os
import sys
import json
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)

# Tesseract 配置
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = os.path.expanduser("~/.tessdata")

def get_ocr_lang():
    """自动检测可用的 OCR 语言，优先中文"""
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        langs = pytesseract.get_languages()
        if 'chi_sim' in langs:
            return 'chi_sim+eng'
        elif 'chi_tra' in langs:
            return 'chi_tra+eng'
        else:
            return 'eng'  # 回退到英文
    except Exception:
        return 'eng'

OCR_LANG = get_ocr_lang()

# ============================================================
# 工具函数
# ============================================================

def is_text_pdf(pdf_data: bytes) -> bool:
    """判断 PDF 是否为文本型（包含可搜索文本）"""
    import fitz
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    for page in doc:
        text = page.get_text().strip()
        if len(text) > 10:
            return True
    return False


def find_keyword_pymupdf(pdf_data: bytes, keyword: str, page_index: int = None, unit: str = "ratio") -> list:
    """
    使用 PyMuPDF 在文本型 PDF 中查找关键字坐标。
    使用 search_for 精确字符框，返回关键字右下角坐标。

    坐标规则（上上签）：
      - 原点：页面左下角
      - 锚点：印章图片左下角
      - offsetX = keyword_x1 / page_width（关键字右边距左边的比例）
      - offsetY = (page_height - keyword_y1) / page_height（关键字底边距下边的比例）

    unit 参数：
      - "ratio"（默认）：比例值 [0,1]
      - "pixel"：72dpi 绝对像素值
    """
    import fitz
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    results = []
    pages_to_search = [page_index] if page_index is not None else range(len(doc))

    for page_num in pages_to_search:
        page = doc[page_num]
        page_width = page.rect.width
        page_height = page.rect.height

        # search_for 找到精确匹配的字符框
        keyword_rects = page.search_for(keyword)

        if not keyword_rects:
            text_blocks = page.get_text("blocks")
            for block in text_blocks:
                if keyword in block[4]:
                    keyword_rects.append(fitz.Rect(block[:4]))

        for rect in keyword_rects:
            kx0, ky0, kx1, ky1 = rect  # PyMuPDF坐标：左上角原点，Y向下

            if unit == "pixel":
                # 72dpi 绝对像素值
                # X = 关键字右边距左边距离；Y = 关键字底边距下边距离
                results.append({
                    "page": page_num + 1,
                    "keyword": keyword,
                    "offsetX": round(kx1, 1),
                    "offsetY": round(page_height - ky1, 1),
                    "width": round(kx1 - kx0, 1),
                    "height": round(ky1 - ky0, 1),
                    "centerX": round((kx0 + kx1) / 2, 1),
                    "centerY": round(page_height - (ky0 + ky1) / 2, 1),
                    "page_width_px": round(page_width, 1),
                    "page_height_px": round(page_height, 1),
                    "bestSignOffset": {"x": -97.0, "y": -77.9},
                    "unit": "pixel",
                    "method": "pymupdf"
                })
            else:
                # 比例值 [0,1]（默认）
                results.append({
                    "page": page_num + 1,
                    "keyword": keyword,
                    "offsetX": round(kx1 / page_width, 4),
                    "offsetY": round((page_height - ky1) / page_height, 4),
                    "width": round((kx1 - kx0) / page_width, 4),
                    "height": round((ky1 - ky0) / page_height, 4),
                    "centerX": round((kx0 + kx1) / 2 / page_width, 4),
                    "centerY": round((page_height - (ky0 + ky1) / 2) / page_height, 4),
                    "page_width_px": round(page_width, 1),
                    "page_height_px": round(page_height, 1),
                    "bestSignOffset": {"x": -0.1630, "y": -0.0925},
                    "unit": "ratio",
                    "method": "pymupdf"
                })

    doc.close()
    return results


def find_keyword_ocr(page_image, keyword: str, page_num: int, page_width: int, page_height: int, unit: str = "ratio") -> list:
    """
    使用 Tesseract OCR 在图片型 PDF 中查找关键字坐标。
    返回坐标已经转换为上上签标准格式。

    unit 参数：
      - "ratio"（默认）：比例值 [0,1]
      - "pixel"：72dpi 绝对像素值
    """
    try:
        import pytesseract
        from PIL import Image

        # Tesseract 配置（自动选择可用语言）
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        ocr_data = pytesseract.image_to_data(
            page_image,
            lang=OCR_LANG,
            output_type=pytesseract.Output.DICT
        )

        results = []
        img_width, img_height = page_image.size

        # 缩放比例：将图片坐标映射回 PDF 页面坐标
        scale_x = page_width / img_width
        scale_y = page_height / img_height

        # OCR 识别出的文本经常字符间带空格，去掉空格后全文匹配
        n = len(ocr_data['text'])
        full_text = ""
        char_info = []  # (start, end, left, top, width, height)
        for i in range(n):
            t = ocr_data['text'][i].strip()
            if t:
                full_text += t
                char_info.append((len(full_text) - len(t), len(full_text),
                                  ocr_data['left'][i], ocr_data['top'][i],
                                  ocr_data['width'][i], ocr_data['height'][i],
                                  ocr_data['conf'][i]))

        kw_compact = keyword.replace(" ", "")
        idx = 0
        while True:
            idx = full_text.find(kw_compact, idx)
            if idx < 0:
                break
            # 找到对应的 OCR 坐标
            x0 = y0 = x1 = y1 = conf = None
            for ci_start, ci_end, cx, cy, cw, ch, cc in char_info:
                if ci_start <= idx < ci_end:
                    x0, y0, conf = cx, cy, cc
                if ci_start <= idx + len(kw_compact) - 1 < ci_end:
                    x1, y1 = cx + cw, cy + ch

            if x0 is not None and x1 is not None:
                rx, ry = x0 * scale_x, y0 * scale_y
                rw, rh = (x1 - x0) * scale_x, (y1 - y0) * scale_y
                # 上上签坐标：原点左下角，锚点印章左下角
                bestsign_x1 = x1 * scale_x
                bestsign_y1 = page_height - y1 * scale_y
                if unit == "pixel":
                    results.append({
                        "page": page_num,
                        "keyword": keyword,
                        "offsetX": round(bestsign_x1, 1),
                        "offsetY": round(bestsign_y1, 1),
                        "width": round(rw, 1),
                        "height": round(rh, 1),
                        "centerX": round((rx + rw / 2), 1),
                        "centerY": round(page_height - (ry + rh / 2), 1),
                        "page_width_px": round(page_width, 1),
                        "page_height_px": round(page_height, 1),
                        "confidence": conf,
                        "bestSignOffset": {"x": -97.0, "y": -77.9},
                        "unit": "pixel",
                        "method": "ocr"
                    })
                else:
                    results.append({
                        "page": page_num,
                        "keyword": keyword,
                        "offsetX": round(bestsign_x1 / page_width, 4),
                        "offsetY": round(bestsign_y1 / page_height, 4),
                        "width": round(rw / page_width, 4),
                        "height": round(rh / page_height, 4),
                        "centerX": round((rx + rw / 2) / page_width, 4),
                        "centerY": round((page_height - (ry + rh / 2)) / page_height, 4),
                        "page_width_px": round(page_width, 1),
                        "page_height_px": round(page_height, 1),
                        "confidence": conf,
                        "bestSignOffset": {"x": -0.1630, "y": -0.0925},
                        "unit": "ratio",
                        "method": "ocr"
                    })
            idx += 1

        return results
    except ImportError:
        return [{"error": "OCR not available: Tesseract not installed"}]
    except Exception as e:
        return [{"error": f"OCR error: {str(e)}"}]


def ocr_find_keyword(pdf_data: bytes, keyword: str, page_index: int = None, unit: str = "ratio") -> list:
    """
    对图片型 PDF 进行 OCR 并查找关键字。
    """
    import fitz
    from PIL import Image

    doc = fitz.open(stream=pdf_data, filetype="pdf")
    results = []
    pages_to_search = [page_index] if page_index is not None else range(len(doc))

    for page_num in pages_to_search:
        page = doc[page_num]
        page_width = page.rect.width
        page_height = page.rect.height

        # 将 PDF 页面渲染为图片（300 DPI 提高识别精度）
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        page_results = find_keyword_ocr(img, keyword, page_num + 1, page_width, page_height, unit)
        results.extend(page_results)

    doc.close()
    return results


# ============================================================
# API 端点
# ============================================================

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    tesseract_available = False
    tesseract_version = None
    ocr_languages = []
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        tesseract_version = str(pytesseract.get_tesseract_version())
        ocr_languages = pytesseract.get_languages()
        tesseract_available = True
    except Exception:
        pass

    return jsonify({
        "status": "ok",
        "pymupdf": True,
        "ocr_available": tesseract_available,
        "tesseract_version": tesseract_version,
        "ocr_languages": ocr_languages,
        "active_ocr_lang": OCR_LANG
    })


@app.route('/find-keyword', methods=['POST'])
def find_keyword():
    """
    接收 PDF 文件和关键字，返回上上签坐标（原点左下角，锚点印章左下角）。

    请求格式：
    - multipart/form-data
    - file: PDF 文件
    - keyword: 关键字（必填）
    - page: 指定页码（可选，1-based，不填则搜索所有页）
    - unit: "ratio"（默认，比例值）或 "pixel"（72dpi像素值）
    """
    if 'file' not in request.files:
        return jsonify({"error": "Missing PDF file"}), 400

    keyword = request.form.get('keyword', '').strip()
    if not keyword:
        return jsonify({"error": "Missing keyword"}), 400

    page_param = request.form.get('page', '').strip()
    page_index = int(page_param) - 1 if page_param.isdigit() else None

    unit = request.form.get('unit', 'ratio').strip().lower()
    if unit not in ('ratio', 'pixel'):
        return jsonify({"error": "unit must be 'ratio' or 'pixel'"}), 400

    file = request.files['file']
    pdf_data = file.read()

    if len(pdf_data) == 0:
        return jsonify({"error": "Empty file"}), 400

    # 自动判断 PDF 类型
    if is_text_pdf(pdf_data):
        results = find_keyword_pymupdf(pdf_data, keyword, page_index, unit)
    else:
        results = ocr_find_keyword(pdf_data, keyword, page_index, unit)

    return jsonify({
        "keyword": keyword,
        "total_matches": len(results),
        "unit": unit,
        "results": results
    })


@app.route('/find-keyword-json', methods=['POST'])
def find_keyword_json():
    """
    JSON 格式接口（适合明道云 HAP 发送API请求节点）。
    返回上上签坐标系坐标：原点左下角，锚点印章左下角，关键字右下角。

    请求体：
    {
        "file_url": "明道云附件下载链接（可选）",
        "file_base64": "base64编码的PDF文件（可选，与file_url二选一）",
        "keyword": "北京发那科机电有限公司",
        "page": 1,
        "unit": "ratio"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    keyword = data.get('keyword', '').strip()
    if not keyword:
        return jsonify({"error": "Missing keyword"}), 400

    unit = str(data.get('unit', 'ratio')).strip().lower()
    if unit not in ('ratio', 'pixel'):
        return jsonify({"error": "unit must be 'ratio' or 'pixel'"}), 400

    # 获取 PDF 数据
    pdf_data = None

    if data.get('file_base64'):
        import base64
        pdf_data = base64.b64decode(data['file_base64'])
    elif data.get('file_url'):
        import requests as req
        resp = req.get(data['file_url'], timeout=30)
        pdf_data = resp.content
    else:
        return jsonify({"error": "Need file_base64 or file_url"}), 400

    page_param = str(data.get('page', '')).strip()
    page_index = int(page_param) - 1 if page_param.isdigit() else None

    # 自动判断 PDF 类型
    if is_text_pdf(pdf_data):
        results = find_keyword_pymupdf(pdf_data, keyword, page_index, unit)
    else:
        results = ocr_find_keyword(pdf_data, keyword, page_index, unit)

    return jsonify({
        "keyword": keyword,
        "total_matches": len(results),
        "unit": unit,
        "coordinateSystem": "bestSign",
        "results": results
    })


# ============================================================
# 启动服务
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*50}")
    print(f"  PDF 关键字坐标定位服务")
    print(f"  地址: http://0.0.0.0:{port}")
    print(f"  健康检查: http://localhost:{port}/health")
    print(f"{'='*50}\n")

    # 检查 OCR 可用性
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        ver = pytesseract.get_tesseract_version()
        langs = pytesseract.get_languages()
        print(f"  ✓ Tesseract OCR {ver}")
        print(f"  可用语言: {', '.join(langs)}")
        print(f"  当前使用: {OCR_LANG}")
    except Exception as e:
        print(f"  ⚠ OCR 不可用（图片型PDF将无法处理）")
        print(f"    请在 GET /health 中确认状态")

    app.run(host='0.0.0.0', port=port, debug=False)