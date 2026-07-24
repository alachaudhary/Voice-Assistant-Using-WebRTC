from loaders import DocumentLoader
from embeddings import EmbeddingService
from vectorstore import VectorStore


def main():

    print("Loading documents...")

    loader = DocumentLoader("documents")
    documents = loader.load()

    print(f"Loaded {len(documents)} document(s)")

    print("Loading embedding model...")

    embedding_model = EmbeddingService().get_model()

    print("Connecting to Chroma...")

    vectorstore = VectorStore(embedding_model)

    print("Indexing documents...")

    vectorstore.add_documents(documents)

    print("Done!")


if __name__ == "__main__":
    main()