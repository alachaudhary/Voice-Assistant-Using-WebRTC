from langchain_chroma import Chroma


class DocumentRetriever:

    def __init__(self, vectorstore: Chroma):
        self.retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 1
            },
        )

    def retrieve(self, question: str):
        return self.retriever.invoke(question)