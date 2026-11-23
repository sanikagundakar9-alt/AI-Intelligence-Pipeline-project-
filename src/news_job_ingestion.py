def is_ai_job(title, description=""):
    title = (title or "").lower()
    description = (description or "").lower()

    role_keywords = [
        "ai engineer",
        "artificial intelligence engineer",
        "machine learning engineer",
        "ml engineer",
        "deep learning engineer",
        "data scientist",
        "research scientist",
        "ai researcher",
        "machine learning researcher",
        "research engineer",
        "nlp engineer",
        "computer vision engineer",
        "generative ai engineer",
        "llm engineer",
        "robotics engineer",
        "ai developer",
        "machine learning scientist",
        "applied scientist",
        "ai scientist",
        "ml researcher"
    ]

    title_match = any(
        keyword in title
        for keyword in role_keywords
    )

    if title_match:
        return True

    technical_keywords = [
        "machine learning",
        "deep learning",
        "neural network",
        "natural language processing",
        "computer vision",
        "large language model",
        "generative ai",
        "artificial intelligence",
        "reinforcement learning",
        "transformer model"
    ]

    technical_match = any(
        keyword in description
        for keyword in technical_keywords
    )

    technical_roles = [
        "engineer",
        "scientist",
        "researcher",
        "developer",
        "architect",
        "analyst"
    ]

    role_match = any(
        role in title
        for role in technical_roles
    )

    return technical_match and role_match