from embedding_service import generate_embeddings


if __name__ == "__main__":
    texts = [
        "Crop diversification can improve biodiversity.",
        "Soil organic carbon is an important soil health indicator.",
        "Climate change can affect ecosystem services and species survival.",
    ]

    embeddings = generate_embeddings(texts)

    print("Batch embedding successful")
    print("Input texts:", len(texts))
    print("Embeddings:", len(embeddings))

    for i, embedding in enumerate(embeddings, start=1):
        print(
            f"Embedding {i}: "
            f"dimension={len(embedding)}"
        )