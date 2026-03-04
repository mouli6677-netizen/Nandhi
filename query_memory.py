from memory.vector_store import VectorStore
from memory.knowledge_store import KnowledgeStore


def main():

    user_id = "mouli"

    # Conversation memory
    memory = VectorStore(
        persist_directory="nandhi_memory",
        collection_name="nandhi_conversations"
    )

    # Knowledge memory
    knowledge = KnowledgeStore(
        persist_directory="knowledge/vectors"
    )

    question = input("Ask Nandhi (memory test): ").strip()

    print("\n--- Conversation Memory Results ---\n")
    mem_results = memory.search(question, k=3, user_id=user_id)

    if mem_results:
        for r in mem_results:
            print("-", r[:300], "\n")
    else:
        print("No conversation matches found.\n")

    print("\n--- Knowledge Results ---\n")
    know_results = knowledge.search(question, k=3, user_id=user_id)

    if know_results:
        for r in know_results:
            print("-", r[:300], "\n")
    else:
        print("No knowledge matches found.\n")


if __name__ == "__main__":
    main()