from langchain_chroma import Chroma


class VectorStore:
    def __init__(self, embedding_model):
        self.vectorstore = Chroma(
            collection_name="company_policies",
            embedding_function=embedding_model,
            persist_directory="chroma_db",
        )

    def add_documents(self, documents):
        return self.vectorstore.add_documents(documents)

    def get_vectorstore(self):
        return self.vectorstore