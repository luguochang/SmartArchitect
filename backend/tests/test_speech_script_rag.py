"""
Speech Script RAG Service Tests

Tests for professional speech script generation with CO-STAR framework
Tests actual API calls to custom Claude endpoint
"""

import pytest
import asyncio
from typing import List
from app.services.speech_script_rag import (
    ProfessionalPromptBuilder,
    RAGSpeechScriptGenerator,
    get_rag_speech_script_generator
)
from app.models.schemas import (
    Node,
    Edge,
    Position,
    NodeData,
    ScriptOptions,
    StreamEvent,
)


# ============================================================
# Test Data - Sample Architecture
# ============================================================

@pytest.fixture
def sample_nodes():
    """Sample architecture nodes for testing"""
    return [
        Node(
            id="api-gateway",
            type="api",
            position=Position(x=100, y=100),
            data=NodeData(label="API Gateway")
        ),
        Node(
            id="user-service",
            type="service",
            position=Position(x=300, y=100),
            data=NodeData(label="User Service")
        ),
        Node(
            id="auth-service",
            type="service",
            position=Position(x=300, y=300),
            data=NodeData(label="Auth Service")
        ),
        Node(
            id="postgres",
            type="database",
            position=Position(x=500, y=200),
            data=NodeData(label="PostgreSQL")
        ),
        Node(
            id="redis",
            type="cache",
            position=Position(x=500, y=400),
            data=NodeData(label="Redis Cache")
        ),
    ]


@pytest.fixture
def sample_edges():
    """Sample architecture edges for testing"""
    return [
        Edge(id="e1", source="api-gateway", target="user-service", label="REST"),
        Edge(id="e2", source="api-gateway", target="auth-service", label="gRPC"),
        Edge(id="e3", source="user-service", target="postgres", label="SQL"),
        Edge(id="e4", source="auth-service", target="redis", label="Session"),
    ]


@pytest.fixture
def default_options():
    """Default script options"""
    return ScriptOptions(
        tone="professional",
        audience="mixed",
        focus_areas=["scalability", "performance"]
    )


# ============================================================
# Test 1: ProfessionalPromptBuilder
# ============================================================

def test_prompt_builder_initialization():
    """Test prompt builder initializes correctly with duration specs"""
    builder = ProfessionalPromptBuilder()

    assert hasattr(builder, 'duration_specs')
    assert "30s" in builder.duration_specs
    assert "2min" in builder.duration_specs
    assert "5min" in builder.duration_specs

    # Check duration spec structure
    spec_30s = builder.duration_specs["30s"]
    assert "words" in spec_30s
    assert "structure" in spec_30s
    assert "required_elements" in spec_30s
    assert "tone" in spec_30s

    print("[OK] ProfessionalPromptBuilder initialized correctly")


def test_prompt_builder_30s_script(sample_nodes, sample_edges, default_options):
    """Test building prompt for 30-second script"""
    builder = ProfessionalPromptBuilder()

    # Mock RAG context
    mock_rag_context = {
        "chunks": [],
        "suggested_patterns": ["microservices", "cache-aside"],
    }

    prompt = builder.build_script_prompt(
        nodes=sample_nodes,
        edges=sample_edges,
        duration="30s",
        rag_context=mock_rag_context,
        options=default_options
    )

    # Verify prompt contains key sections
    assert "CONTEXT" in prompt
    assert "OBJECTIVE" in prompt
    assert "STYLE" in prompt
    assert "TONE" in prompt
    assert "AUDIENCE" in prompt
    assert "RESPONSE FORMAT" in prompt

    # Verify architecture information is included
    assert "API Gateway" in prompt
    assert "User Service" in prompt

    # Verify duration-specific information
    assert "30s" in prompt or "30秒" in prompt
    assert "60-80" in prompt  # word count target

    print(f"[OK] 30s prompt built successfully ({len(prompt)} chars)")
    print(f"  Prompt preview: {prompt[:200]}...")


def test_prompt_builder_2min_script(sample_nodes, sample_edges, default_options):
    """Test building prompt for 2-minute script"""
    builder = ProfessionalPromptBuilder()

    mock_rag_context = {
        "chunks": [],
        "suggested_patterns": ["event-driven", "saga"],
    }

    prompt = builder.build_script_prompt(
        nodes=sample_nodes,
        edges=sample_edges,
        duration="2min",
        rag_context=mock_rag_context,
        options=default_options
    )

    # Verify 2min-specific content
    assert "2min" in prompt or "2分钟" in prompt
    assert "280-320" in prompt  # word count target

    # Should have more detailed requirements than 30s
    assert len(prompt) > 1000

    print(f"[OK] 2min prompt built successfully ({len(prompt)} chars)")


def test_prompt_builder_5min_script(sample_nodes, sample_edges, default_options):
    """Test building prompt for 5-minute script"""
    builder = ProfessionalPromptBuilder()

    mock_rag_context = {
        "chunks": [
            {
                "content": "Microservices architecture best practices...",
                "metadata": {"filename": "microservices-guide.pdf"}
            }
        ],
        "suggested_patterns": ["microservices", "api-gateway"],
    }

    prompt = builder.build_script_prompt(
        nodes=sample_nodes,
        edges=sample_edges,
        duration="5min",
        rag_context=mock_rag_context,
        options=default_options
    )

    # Verify 5min-specific content
    assert "5min" in prompt or "5分钟" in prompt
    assert "700-800" in prompt  # word count target

    # Should be the most detailed
    assert len(prompt) > 2000

    # Should include RAG context
    assert "microservices-guide.pdf" in prompt or "来源" in prompt

    print(f"[OK] 5min prompt built successfully ({len(prompt)} chars)")


def test_prompt_builder_audience_adaptation(sample_nodes, sample_edges):
    """Test prompt builder adapts to different audiences"""
    builder = ProfessionalPromptBuilder()
    mock_rag_context = {"chunks": [], "suggested_patterns": []}

    # Executive audience
    exec_options = ScriptOptions(
        tone="professional",
        audience="executive",
        focus_areas=["ROI", "business-value"]
    )
    exec_prompt = builder.build_script_prompt(
        sample_nodes, sample_edges, "2min", mock_rag_context, exec_options
    )

    # Technical audience
    tech_options = ScriptOptions(
        tone="technical",
        audience="technical",
        focus_areas=["architecture", "performance"]
    )
    tech_prompt = builder.build_script_prompt(
        sample_nodes, sample_edges, "2min", mock_rag_context, tech_options
    )

    # Prompts should be different
    assert exec_prompt != tech_prompt

    # Executive prompt should mention business value
    assert "executive" in exec_prompt.lower() or "高管" in exec_prompt

    # Technical prompt should mention technical details
    assert "technical" in tech_prompt.lower() or "技术" in tech_prompt

    print("[OK] Prompt builder adapts to different audiences")


# ============================================================
# Test 2: RAGSpeechScriptGenerator - Mock Mode
# ============================================================

@pytest.mark.asyncio
async def test_script_generator_stream_30s(sample_nodes, sample_edges, default_options):
    """Test streaming generation for 30s script (mock mode)"""
    generator = RAGSpeechScriptGenerator()

    events: List[StreamEvent] = []

    async for event in generator.generate_speech_script_stream(
        nodes=sample_nodes,
        edges=sample_edges,
        duration="30s",
        options=default_options
    ):
        events.append(event)

    # Verify event sequence
    event_types = [e.type for e in events]

    assert "CONTEXT_SEARCH" in event_types
    assert "CONTEXT_FOUND" in event_types
    assert "GENERATION_START" in event_types
    assert "COMPLETE" in event_types

    # Verify complete event has required data
    complete_event = [e for e in events if e.type == "COMPLETE"][0]
    assert "script" in complete_event.data
    assert "word_count" in complete_event.data
    assert "rag_sources" in complete_event.data

    script_data = complete_event.data["script"]
    assert "intro" in script_data
    assert "body" in script_data
    assert "conclusion" in script_data

    print(f"[OK] 30s script generated successfully ({len(events)} events)")
    print(f"  Word count: {complete_event.data['word_count']}")


@pytest.mark.asyncio
async def test_script_generator_stream_2min(sample_nodes, sample_edges, default_options):
    """Test streaming generation for 2min script (mock mode)"""
    generator = RAGSpeechScriptGenerator()

    events: List[StreamEvent] = []

    async for event in generator.generate_speech_script_stream(
        nodes=sample_nodes,
        edges=sample_edges,
        duration="2min",
        options=default_options
    ):
        events.append(event)

    complete_event = [e for e in events if e.type == "COMPLETE"][0]
    word_count = complete_event.data["word_count"]

    # 2min should have ~280-320 words
    assert 200 < word_count < 400

    print(f"[OK] 2min script generated successfully")
    print(f"  Word count: {word_count} (target: 280-320)")


@pytest.mark.asyncio
async def test_script_generator_stream_5min(sample_nodes, sample_edges, default_options):
    """Test streaming generation for 5min script (mock mode)"""
    generator = RAGSpeechScriptGenerator()

    events: List[StreamEvent] = []

    async for event in generator.generate_speech_script_stream(
        nodes=sample_nodes,
        edges=sample_edges,
        duration="5min",
        options=default_options
    ):
        events.append(event)

    complete_event = [e for e in events if e.type == "COMPLETE"][0]
    word_count = complete_event.data["word_count"]

    # 5min should have ~700-800 words (allow some flexibility)
    assert 600 < word_count < 1200

    print(f"[OK] 5min script generated successfully")
    print(f"  Word count: {word_count} (target: 700-800)")


# ============================================================
# Test 3: Actual API Call to Custom Claude Endpoint
# ============================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_actual_api_call_custom_claude(sample_nodes, sample_edges):
    """
    Test actual API call to custom Claude endpoint

    Uses provided credentials:
    - Base URL: https://www.linkflow.run/v1
    - Model: claude-sonnet-4-5-20250929
    - API Key: sk-7oflvgMRXPZe0skck0qIqsFuDSvOBKiMqqGiC0Sx9gzAsALh
    """
    from openai import OpenAI

    # Initialize custom client
    client = OpenAI(
        api_key="sk-7oflvgMRXPZe0skck0qIqsFuDSvOBKiMqqGiC0Sx9gzAsALh",
        base_url="https://www.linkflow.run/v1"
    )

    # Build a simple test prompt
    builder = ProfessionalPromptBuilder()
    mock_rag_context = {
        "chunks": [],
        "suggested_patterns": ["microservices"],
    }

    prompt = builder.build_script_prompt(
        nodes=sample_nodes,
        edges=sample_edges,
        duration="30s",
        rag_context=mock_rag_context,
        options=ScriptOptions(
            tone="professional",
            audience="mixed",
            focus_areas=["scalability"]
        )
    )

    print(f"\n[EMOJI] Calling Custom Claude API...")
    print(f"   Base URL: https://www.linkflow.run/v1")
    print(f"   Model: claude-sonnet-4-5-20250929")
    print(f"   Prompt length: {len(prompt)} chars")

    try:
        # Make API call
        response = client.chat.completions.create(
            model="claude-sonnet-4-5-20250929",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )

        # Verify response structure
        assert response is not None
        assert hasattr(response, 'choices')
        assert len(response.choices) > 0

        generated_text = response.choices[0].message.content
        assert generated_text is not None
        assert len(generated_text) > 0

        # Clean all non-ASCII characters for Windows console
        import re
        clean_text = re.sub(r'[^\x00-\x7F\u4e00-\u9fff]+', '', generated_text)

        print(f"\n[OK] API call successful!")
        print(f"   Response length: {len(generated_text)} chars")
        print(f"   Word count (raw): {len(generated_text.split())} words")
        print(f"\n[DOC] Generated Script Preview (first 500 chars):")
        print(f"   {clean_text[:500]}...")

        # Verify script structure (should contain sections)
        has_intro = "[INTRO]" in generated_text or "开场" in generated_text or "intro" in generated_text.lower()
        has_body = "[BODY]" in generated_text or "主体" in generated_text or "body" in generated_text.lower()
        has_conclusion = "[CONCLUSION]" in generated_text or "结尾" in generated_text or "conclusion" in generated_text.lower()

        print(f"\n[STATS] Script Structure Check:")
        print(f"   Has Intro: {has_intro}")
        print(f"   Has Body: {has_body}")
        print(f"   Has Conclusion: {has_conclusion}")

        return response

    except Exception as e:
        print(f"\n[FAIL] API call failed: {e}")
        pytest.fail(f"API call failed: {e}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_actual_api_streaming_custom_claude(sample_nodes, sample_edges):
    """
    Test actual streaming API call to custom Claude endpoint
    """
    from openai import OpenAI

    client = OpenAI(
        api_key="sk-7oflvgMRXPZe0skck0qIqsFuDSvOBKiMqqGiC0Sx9gzAsALh",
        base_url="https://www.linkflow.run/v1"
    )

    builder = ProfessionalPromptBuilder()
    mock_rag_context = {
        "chunks": [],
        "suggested_patterns": ["microservices"],
    }

    prompt = builder.build_script_prompt(
        nodes=sample_nodes,
        edges=sample_edges,
        duration="30s",
        rag_context=mock_rag_context,
        options=ScriptOptions(tone="professional", audience="mixed", focus_areas=["scalability"])
    )

    print(f"\n[EMOJI] Testing Streaming API Call...")

    try:
        # Make streaming API call
        stream = client.chat.completions.create(
            model="claude-sonnet-4-5-20250929",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
            stream=True
        )

        accumulated_text = ""
        chunk_count = 0

        for chunk in stream:
            # Check if chunk has choices and delta content
            if (hasattr(chunk, 'choices') and
                len(chunk.choices) > 0 and
                hasattr(chunk.choices[0], 'delta') and
                hasattr(chunk.choices[0].delta, 'content') and
                chunk.choices[0].delta.content):
                token = chunk.choices[0].delta.content
                accumulated_text += token
                chunk_count += 1

        # Clean all non-ASCII characters for Windows console
        import re
        clean_text = re.sub(r'[^\x00-\x7F\u4e00-\u9fff]+', '', accumulated_text)

        print(f"\n[OK] Streaming API call successful!")
        print(f"   Total chunks: {chunk_count}")
        print(f"   Total text length: {len(accumulated_text)} chars")
        print(f"   Word count: {len(accumulated_text.split())} words")
        print(f"\n[DOC] Streamed Script Preview (first 500 chars):")
        print(f"   {clean_text[:500]}...")

        assert len(accumulated_text) > 0
        assert chunk_count > 0

        return accumulated_text

    except Exception as e:
        print(f"\n[FAIL] Streaming API call failed: {e}")
        pytest.fail(f"Streaming API call failed: {e}")


# ============================================================
# Test 4: Utility Functions
# ============================================================

def test_build_context_query(sample_nodes, sample_edges):
    """Test building RAG context query"""
    generator = RAGSpeechScriptGenerator()

    query = generator.build_context_query(sample_nodes, sample_edges, "2min")

    assert isinstance(query, str)
    assert len(query) > 0

    # Should mention components
    assert "API Gateway" in query or "api-gateway" in query

    print(f"[OK] Context query built: {query[:100]}...")


def test_estimate_duration():
    """Test duration estimation"""
    generator = RAGSpeechScriptGenerator()

    # 150 words ~= 60 seconds at normal speaking rate
    text_150 = " ".join(["word"] * 150)
    duration = generator.estimate_duration(text_150)

    assert 50 <= duration <= 70  # Should be around 60 seconds

    print(f"[OK] Duration estimation works: 150 words = ~{duration}s")


def test_extract_section():
    """Test section extraction from full script"""
    generator = RAGSpeechScriptGenerator()

    full_script = """
[INTRO]
This is the introduction.

[BODY]
This is the body section.

[CONCLUSION]
This is the conclusion.
"""

    intro = generator.extract_section(full_script, "intro")
    body = generator.extract_section(full_script, "body")
    conclusion = generator.extract_section(full_script, "conclusion")

    assert "introduction" in intro.lower()
    assert "body" in body.lower()
    assert "conclusion" in conclusion.lower()

    print("[OK] Section extraction works correctly")


# ============================================================
# Test 5: Service Factory
# ============================================================

def test_service_factory():
    """Test get_rag_speech_script_generator factory"""
    service = get_rag_speech_script_generator()

    assert service is not None
    assert isinstance(service, RAGSpeechScriptGenerator)

    # Should return same instance (singleton)
    service2 = get_rag_speech_script_generator()
    assert service is service2

    print("[OK] Service factory works correctly")


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("[EMOJI] Running Speech Script RAG Service Tests")
    print("=" * 70)

    # Run pytest with verbose output
    import sys
    pytest.main([
        __file__,
        "-v",
        "-s",  # Show print statements
        "--tb=short",  # Short traceback format
        "-m", "not integration"  # Skip integration tests by default
    ])

    print("\n" + "=" * 70)
    print("[INFO]  To run integration tests (actual API calls):")
    print("   pytest test_speech_script_rag.py -v -s -m integration")
    print("=" * 70)
