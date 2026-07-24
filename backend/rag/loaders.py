from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


class DocumentLoader:
    def __init__(self, document_dir: str):
        self.document_dir = Path(document_dir)

    def load(self) -> list[Document]:
        documents = []

        pdf_files = list(self.document_dir.glob("*.pdf"))

        print(f"Found {len(pdf_files)} PDF(s)")

        for pdf_path in pdf_files:
            print(f"Loading: {pdf_path.name}")

            loader = PyPDFLoader(str(pdf_path))
            docs = loader.load()

            print(f"  -> {len(docs)} pages")

            documents.extend(docs)

        print(f"\nTotal pages loaded: {len(documents)}")

        return documents