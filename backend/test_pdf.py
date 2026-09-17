from pypdf import PdfReader


PDF_PATH = "../data/sources/fao_biodiversity.pdf"


if __name__ == "__main__":
    reader = PdfReader(PDF_PATH)

    print("PDF loaded successfully")
    print("Number of pages:", len(reader.pages))

    first_page_text = reader.pages[0].extract_text()

    print("\n--- FIRST PAGE TEXT ---\n")
    print(first_page_text[:2000])