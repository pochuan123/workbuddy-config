---
name: bestsign-keyword-position
description: "从 PDF 文件中识别指定关键词的坐标位置，输出上上签电子签章平台兼容的坐标格式。支持文本型 PDF（PyMuPDF 直接提取）和图片型 PDF（Tesseract OCR 识别）。当用户需要在明道云 HAP 中通过上上签 API 进行关键字定位盖章时触发此技能。Bestsign keyword positioning, PDF keyword coordinate extraction."
agent_created: true
---

# 上上签关键词位置识别

## 概述

从 PDF 文件中搜索指定关键词，返回关键词在页面上的精确坐标，坐标格式遵循上上签/开放签电子签章平台规范。

## 坐标规范

> 遵循上上签官方坐标体系（来源：[上上签 API 文档 - 位置坐标的计算方法](https://apidocs.bestsign.cn/docs/apis/2388204816150036481/2389027319206379522)）

| 属性 | 说明 |
|------|------|
| **原点** | 页面**左下角** (bottom-left) |
| **锚点** | 印章图片**左下角** |
| **X 轴** | 向右为正，`X = 距左边距离 ÷ 页宽` |
| **Y 轴** | 向上为正，`Y = 距下边距离 ÷ 页高` |
| **输出基准** | 关键字**右下角**坐标（与上上签"多关键字查询"返回格式一致） |
| **单位** | 比例值 [0, 1]（默认 ratio）或 72dpi 像素（pixel） |
| **印章居中** | 减 `X偏移-0.1630, Y偏移-0.0925` 可使印章中心与关键字中心重合 |

### 本服务输出格式

通过 `unit` 参数控制：

| unit 值 | 输出格式 | 示例 |
|--------|---------|------|
| `ratio`（默认） | 比例值 [0, 1] | `offsetX: 0.3518, offsetY: 0.8811` |
| `pixel` | 72dpi 绝对像素 | `offsetX: 209.4, offsetY: 741.8` |

每个结果额外包含 `bestSignOffset` 字段，提供印章居中的推荐偏移值。

## 环境依赖

运行前确保以下依赖已安装：

| 组件 | 用途 | 安装方式 |
|------|------|---------|
| Python 3.10+ | 运行环境 | 系统自带或官网下载 |
| PyMuPDF | 文本型 PDF 处理 | `pip install pymupdf` |
| Tesseract OCR 5.x | 图片型 PDF 识别 | winget 或 GitHub 安装包 |
| pytesseract | OCR Python 接口 | `pip install pytesseract` |
| Pillow | 图片处理 | `pip install pillow` |
| Flask | HTTP 服务（可选） | `pip install flask` |
| Tesseract 中文语言包 | 中文 OCR | 下载 chi_sim.traineddata |
| PowerShell 7 | 后台服务稳定性 | 官网安装 |

使用清华大学镜像源加速安装：
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pymupdf pytesseract pdf2image flask pillow requests
```

Tesseract 默认安装在 `C:\Program Files\Tesseract-OCR\`。中文语言包 `chi_sim.traineddata` 需放入 tessdata 目录（或通过 `TESSDATA_PREFIX` 环境变量指向自定义目录）。

## 使用方式

### 方式一：HTTP 服务（推荐，与明道云 HAP 集成）

启动服务（建议用 PowerShell 7 独立进程保证稳定性）：

```powershell
Start-Process pwsh -ArgumentList '-NoProfile','-Command','cd /path/to/workdir; python server.py' -WindowStyle Hidden
```

服务默认监听 `http://0.0.0.0:5000`。

**API**: `POST /find-keyword-json`

请求体：
```json
{
  "file_base64": "base64编码的PDF文件",
  "keyword": "北京发那科机电有限公司",
  "page": 1,
  "unit": "ratio"
}
```

响应：
```json
{
  "keyword": "北京发那科机电有限公司",
  "total_matches": 2,
  "unit": "ratio",
  "coordinateSystem": "bestSign",
  "results": [
    {
      "page": 1,
      "offsetX": 0.3518,
      "offsetY": 0.8811,
      "bestSignOffset": {"x": -0.1630, "y": -0.0925},
      "unit": "ratio",
      "method": "pymupdf"
    },
    {
      "page": 2,
      "offsetX": 0.8481,
      "offsetY": 0.5574,
      "bestSignOffset": {"x": -0.1630, "y": -0.0925},
      "unit": "ratio",
      "method": "pymupdf"
    }
  ]
}
```

明道云 HAP 工作流中通过「发送API请求」节点调用此接口，获取坐标后传给上上签盖章 API。

### 方式二：直接调用 Python 函数

在 Python 脚本中导入 `server.py` 中的函数直接调用：

```python
from server import find_keyword_pymupdf, ocr_find_keyword

with open("contract.pdf", "rb") as f:
    pdf_data = f.read()

results = find_keyword_pymupdf(pdf_data, "甲方（盖章）", unit="ratio")
print(results)
```

## PDF 类型自动识别

服务自动判断 PDF 类型并选择处理方式：

| PDF 类型 | 判断方式 | 处理 | 精度 |
|---------|---------|------|------|
| 文本型 | `page.get_text()` 有内容 | PyMuPDF search_for 精确字符框 | 像素级精确 |
| 图片型 | 无文本内容 | 渲染为图片 → Tesseract OCR | 取决于扫描质量 |

## OCR 特殊处理

Tesseract 中文识别输出的字符间常带空格，匹配时需要：
1. 去掉 OCR 输出文本中的所有空格
2. 去掉关键词中的空格（`keyword.replace(" ", "")`）
3. 在去空格后的全文执行 `find()`
4. 通过字符索引反查 OCR 原始坐标

## 已知限制

- 图片型 PDF 的 OCR 精度受扫描质量和 DPI 影响，坐标可能有 ±5px 误差
- 长关键词可能在 OCR 中被分词打断，需去空格全文匹配
- HTTP 服务在 PowerShell 5.1 下后台进程不稳定，建议用 PowerShell 7 独立进程启动
- 输出坐标为关键字右下角（与上上签"多关键字查询"格式一致），如需印章居中请使用 `bestSignOffset` 偏移