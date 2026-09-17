from embedding_service import generate_embedding


if __name__ == "__main__":
    text = "Crop diversification can improve biodiversity and soil health."

    embedding = generate_embedding(text)

    print("Embedding generated successfully")
    print("Dimension:", len(embedding))
    print("First 5 values:", embedding[:5])