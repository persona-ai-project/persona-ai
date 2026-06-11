"""
Example showing P2  exactly how to call search_hybrid()
and inject RAG results into a prompt.
"""
from services.ai.rag.retriever import search_hybrid
from shared.contracts.retriever import RetrievalResult


def build_prompt_with_rag(user_id: str, user_message: str) -> str:
    """
    Example of how to wire search_hybrid() into PromptBuilder.
    Copy this pattern into your FastAPI route.
    """
    # Step 1: Get relevant memories
    result: RetrievalResult = search_hybrid(user_id, user_message, k=5)

    # Step 2: Format chunks for prompt
    memory_block = "\n".join([
        f"- {chunk.text} (score: {chunk.score:.2f})"
        for chunk in result.chunks
    ])

    # Step 3: Build final prompt
    prompt = f"""You are an AI twin of a real person.

Here are relevant memories about this person:
{memory_block}

Now respond to this message as that person would:
User: {user_message}
"""
    return prompt


# Quick demo
if __name__ == "__main__":
    prompt = build_prompt_with_rag("demo-user", "what food do you like?")
    print(prompt)