# -*- coding: utf-8 -*-
from app.services.speech_script_rag import RAGSpeechScriptGenerator
from app.models.schemas import Node, Edge, Position, NodeData

generator = RAGSpeechScriptGenerator()

nodes = [
    Node(id="api", type="api", position=Position(x=100, y=100), data=NodeData(label="API")),
    Node(id="db", type="database", position=Position(x=200, y=100), data=NodeData(label="DB")),
]
edges = [Edge(id="e1", source="api", target="db")]

print("=== Testing word counting ===")
raw_script = generator._generate_mock_script(nodes, edges, "2min")
processed = generator.post_process_script(raw_script, "2min")

print(f"Raw script char length: {len(raw_script)}")
print(f"Processed script char length: {len(processed)}")

word_count = generator._count_words(processed)
print(f"\n>>> Word count (new method): {word_count}")

duration = generator.estimate_duration(processed)
print(f">>> Estimated duration: {duration}s")

print(f"\nShould be ~280-320 words for 2min script")
