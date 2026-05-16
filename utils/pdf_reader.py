import PyPDF2

def extract_text_from_pdf(pdf_file):
    """
    Takes uploaded PDF file and extracts all text from it
    """

    reader = PyPDF2.PdfReader(pdf_file)

    text = ""

    # loop through all pages
    for page in reader.pages:
        text += page.extract_text()

    return text