# -*- coding: utf-8 -*-
from app.services.speech_script_rag import RAGSpeechScriptGenerator
from app.models.schemas import Node, Edge, Position, NodeData

generator = RAGSpeechScriptGenerator()

nodes = [
    Node(id="api", type="api", position=Position(x=100, y=100), data=NodeData(label="API")),
    Node(id="db", type="database", position=Position(x=200, y=100), data=NodeData(label="DB")),
]
edges = [Edge(id="e1", source="api", target="db")]

print("=== Testing _generate_mock_script ===")
raw_script = generator._generate_mock_script(nodes, edges, "2min")

print(f"Raw script length: {len(raw_script)}")
print(f"Raw script word count: {len(raw_script.split())}")
print(f"\nRaw script content (first 300 chars):")
print(repr(raw_script[:300]))

print("\n=== Testing post_process_script ===")
processed = generator.post_process_script(raw_script, "2min")

print(f"Processed script length: {len(processed)}")
print(f"Processed script word count: {len(processed.split())}")
print(f"\nProcessed script content (first 300 chars):")
print(repr(processed[:300]))
