import asyncio
from app.services.speech_script_rag import RAGSpeechScriptGenerator
from app.models.schemas import Node, Edge, Position, NodeData, ScriptOptions

async def test():
    generator = RAGSpeechScriptGenerator()
    
    nodes = [
        Node(id="api", type="api", position=Position(x=100, y=100), data=NodeData(label="API")),
        Node(id="db", type="database", position=Position(x=200, y=100), data=NodeData(label="DB")),
    ]
    edges = [Edge(id="e1", source="api", target="db")]
    
    print("=== Generating 2min script ===")
    events = []
    async for event in generator.generate_speech_script_stream(
        nodes, edges, "2min", ScriptOptions()
    ):
        events.append(event)
        if event.type == "COMPLETE":
            script_data = event.data["script"]
            full_text = script_data["full_text"]
            word_count = event.data["word_count"]
            
            print(f"\n[COMPLETE Event Data]")
            print(f"Word count from event: {word_count}")
            print(f"Full text length: {len(full_text)}")
            print(f"Word count manual: {len(full_text.split())}")
            print(f"\n[Full Text Preview]")
            print(full_text[:500])

asyncio.run(test())
