import pdfplumber
import textwrap


def extract_text(pdf_path: str) -> str:
    txt = []
    with pdfplumber.open(pdf_path) as doc:
        for p in doc.pages:
            txt.append(p.extract_text() or "")
    return "\n".join(txt)


def chunk(text: str, max_tokens: int = 800) -> list[str]:
    # 粗估 1 token ≈ 4 chars
    return textwrap.wrap(text, width=max_tokens * 4)
