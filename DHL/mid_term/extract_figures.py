"""从 user_info PDF 中提取关键图片，保存到 figures/ 目录"""
import fitz  # PyMuPDF
import os

FIGURES_DIR = r"z:\321\DHL\Self_Learning\DHL\mid_term\figures"
os.makedirs(FIGURES_DIR, exist_ok=True)

# 定义要提取的 PDF 和对应页码范围
pdfs = {
    "pra_published": {
        "path": r"z:\321\DHL\Self_Learning\DHL\mid_term\user_info\已发表论文\Deep-sub-cycle ultrafast optical pulses.pdf",
        "pages": "all",  # 提取所有页的图片
        "desc": "PRA已发表论文-深亚周期脉冲"
    },
    "apr_nanowire": {
        "path": r"z:\321\DHL\Self_Learning\DHL\mid_term\user_info\准备论文\高功率\proof.pdf",
        "pages": "all",
        "desc": "APR投稿-纳米线高功率导波"
    },
    "hole_quantization": {
        "path": r"z:\321\DHL\Self_Learning\DHL\mid_term\user_info\准备论文\小孔量子化\小孔极端约束光场的量子化.pdf",
        "pages": "all",
        "desc": "小孔量子化论文"
    },
}

def extract_images(pdf_key, pdf_path, pages="all"):
    """提取 PDF 中的图片"""
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"\n=== {pdf_key}: {total_pages} pages ===")

    img_count = 0
    for page_num in range(total_pages):
        page = doc[page_num]
        images = page.get_images(full=True)
        for img_idx, img_info in enumerate(images):
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                if base_image:
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    width = base_image["width"]
                    height = base_image["height"]

                    # 跳过过小的图片（图标、logo等）
                    if width < 100 or height < 100:
                        continue

                    # 跳过纯灰度小图（通常是装饰）
                    if len(image_bytes) < 5000:
                        continue

                    filename = f"{pdf_key}_p{page_num+1}_img{img_idx+1}.{image_ext}"
                    filepath = os.path.join(FIGURES_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(image_bytes)
                    img_count += 1
                    print(f"  Page {page_num+1}: {filename} ({width}x{height}, {len(image_bytes)//1024}KB)")
            except Exception as e:
                pass

    # 如果没有提取到嵌入图片，用页面渲染方式提取整页
    if img_count == 0:
        print(f"  No embedded images found, rendering key pages...")
        for page_num in range(total_pages):
            page = doc[page_num]
            # 渲染为高分辨率 PNG
            mat = fitz.Matrix(2.0, 2.0)  # 2x 缩放
            pix = page.get_pixmap(matrix=mat)
            filename = f"{pdf_key}_p{page_num+1}_render.png"
            filepath = os.path.join(FIGURES_DIR, filename)
            pix.save(filepath)
            img_count += 1
            print(f"  Rendered page {page_num+1}: {filename} ({pix.width}x{pix.height})")

    doc.close()
    return img_count

total = 0
for key, info in pdfs.items():
    if os.path.exists(info["path"]):
        count = extract_images(key, info["path"])
        total += count
        print(f"  → {count} images extracted")
    else:
        print(f"  SKIP: {info['path']} not found")

print(f"\n总计提取 {total} 张图片到 {FIGURES_DIR}")
