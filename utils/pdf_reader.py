import fitz


def extract_text(pdf_path):

    text = ""

    document = fitz.open(pdf_path)

    for page in document:

        text += page.get_text()

    document.close()

    return text