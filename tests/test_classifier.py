from app.ingestion.classifier import classify_memory
from app.models.schemas import MemoryInput


def test_procedural_classification():
    memory_type, classifier = classify_memory(
        MemoryInput(text="First run the migration, then restart the API service.")
    )
    assert memory_type == "procedural"
    assert classifier["importance"] >= 0.45
