"""Debug script to test Excalidraw generation"""
import asyncio
from app.services.excalidraw_generator import create_excalidraw_service

async def test_generation():
    service = create_excalidraw_service()

    try:
        # Test prompt building
        prompt = service._build_prompt(
            prompt="用户登录流程",
            style="balanced",
            width=1200,
            height=800
        )
        print("[OK] Prompt built successfully")
        print(f"Prompt length: {len(prompt)} characters")
        print("-" * 80)
        print("First 500 chars of prompt:")
        print(prompt[:500])
        print("-" * 80)

        # Test mock scene generation
        mock_scene = service._mock_scene()
        print(f"[OK] Mock scene generated: {len(mock_scene.elements)} elements")

        # Test full generation with siliconflow (will fail without API key but should handle gracefully)
        print("\n" + "=" * 80)
        print("Testing with siliconflow provider (expecting graceful fallback)...")
        print("=" * 80)
        scene = await service.generate_scene(
            prompt="user login workflow with 3 steps",
            style="balanced",
            width=1200,
            height=800,
            provider="siliconflow",
            api_key=None  # Will trigger fallback
        )
        print(f"[OK] Scene generated: {len(scene.elements)} elements")
        print(f"  Message: {scene.appState.get('message', 'N/A')[:100]}")

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_generation())
