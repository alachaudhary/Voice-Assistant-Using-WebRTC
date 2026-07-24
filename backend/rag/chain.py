from langchain_core.prompts import ChatPromptTemplate


class RAGChain:

    def __init__(
        self,
        retriever,
        llm,
        conversation_history,
    ):
        self.retriever = retriever
        self.llm = llm
        self.conversation_history = conversation_history

        self.prompt = ChatPromptTemplate.from_template(
            """
You are MetaCorp's HR assistant.

Answer ONLY from the provided context.

If the answer is not present, reply:

"I couldn't find that information in the company policies."

Context:
{context}

Question:
{question}
"""
        )

    def invoke(self, question: str):

        documents = self.retriever.retrieve(question)

        context = "\n\n".join(
            doc.page_content
            for doc in documents
        )

        prompt = self.prompt.invoke(
            {
                "context": context,
                "question": question,
            }
        )

        response = self.llm.create_chat_completion(
            history=self.conversation_history.messages,
            user_message=question,
            retrieved_context=context,
        )

        return response

     