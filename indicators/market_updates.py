from docx import Document
import re

def load_market_update_markdown(path):
    doc = Document(path)
    md_output = []

    section_labels = [
        "summary", "key uka price drivers", "uka price outlook", "market commentary",
        "ets linkage", "trading activity", "auction supply"
    ]

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Detect and split section headers
        lowered = text.lower()
        matched_label = next((label for label in section_labels if lowered.startswith(label)), None)

        if matched_label:
            # Extract the header portion
            header = re.match(rf"^({matched_label}):?", text, re.IGNORECASE)
            if header:
                label_text = header.group(1).title()
                rest = text[len(header.group(0)):].strip()
                md_output.append(f"### {label_text}:")
                if rest:
                    md_output.append(rest)
        elif para.style.name.startswith("List Bullet"):
            md_output.append(f"- {text}")
        else:
            md_output.append(text)

    return "\n\n".join(md_output)
