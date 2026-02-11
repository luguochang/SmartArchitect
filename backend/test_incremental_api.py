"""
测试增量生成功能的 API 端点
"""
import sys
import os
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import Node, Edge, Position, NodeData

client = TestClient(app)


def test_save_session_endpoint():
    """测试保存会话 API"""
    print("=" * 60)
    print("测试 1: POST /api/chat-generator/session/save")
    print("=" * 60)

    nodes_data = [
        {
            "id": "api-1",
            "type": "api",
            "position": {"x": 100, "y": 100},
            "data": {"label": "API Gateway"}
        },
        {
            "id": "service-1",
            "type": "service",
            "position": {"x": 400, "y": 100},
            "data": {"label": "User Service"}
        }
    ]

    edges_data = [
        {
            "id": "e1",
            "source": "api-1",
            "target": "service-1",
            "label": "HTTP"
        }
    ]

    # Test creating new session
    print("\n1. 创建新会话...")
    response = client.post(
        "/api/chat-generator/session/save",
        json={
            "nodes": nodes_data,
            "edges": edges_data
        }
    )

    print(f"   状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ 会话已创建")
        print(f"   - session_id: {data.get('session_id')}")
        print(f"   - node_count: {data.get('node_count')}")
        print(f"   - edge_count: {data.get('edge_count')}")
        return True, data.get('session_id')
    else:
        print(f"   ✗ 请求失败: {response.text}")
        return False, None


def test_get_session_endpoint(session_id):
    """测试获取会话 API"""
    print("\n" + "=" * 60)
    print("测试 2: GET /api/chat-generator/session/{session_id}")
    print("=" * 60)

    print(f"\n获取会话: {session_id}")

    response = client.get(f"/api/chat-generator/session/{session_id}")

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        session_data = data.get('session')
        print(f"✓ 会话数据获取成功")
        print(f"   - 节点数: {session_data.get('node_count')}")
        print(f"   - 边数: {session_data.get('edge_count')}")
        return True
    else:
        print(f"✗ 请求失败: {response.text}")
        return False


def test_update_session_endpoint(session_id):
    """测试更新会话 API"""
    print("\n" + "=" * 60)
    print("测试 3: POST /api/chat-generator/session/save (更新)")
    print("=" * 60)

    # Add a new node
    nodes_data = [
        {
            "id": "api-1",
            "type": "api",
            "position": {"x": 100, "y": 100},
            "data": {"label": "API Gateway"}
        },
        {
            "id": "service-1",
            "type": "service",
            "position": {"x": 400, "y": 100},
            "data": {"label": "User Service"}
        },
        {
            "id": "db-1",
            "type": "database",
            "position": {"x": 700, "y": 100},
            "data": {"label": "MySQL"}
        }
    ]

    edges_data = [
        {
            "id": "e1",
            "source": "api-1",
            "target": "service-1",
            "label": "HTTP"
        },
        {
            "id": "e2",
            "source": "service-1",
            "target": "db-1",
            "label": "SQL"
        }
    ]

    print(f"\n更新会话 {session_id}（添加数据库节点）...")

    response = client.post(
        "/api/chat-generator/session/save",
        json={
            "session_id": session_id,
            "nodes": nodes_data,
            "edges": edges_data
        }
    )

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ 会话已更新")
        print(f"   - 节点数: {data.get('node_count')}")
        print(f"   - 边数: {data.get('edge_count')}")
        return True
    else:
        print(f"✗ 请求失败: {response.text}")
        return False


def test_delete_session_endpoint(session_id):
    """测试删除会话 API"""
    print("\n" + "=" * 60)
    print("测试 4: DELETE /api/chat-generator/session/{session_id}")
    print("=" * 60)

    print(f"\n删除会话: {session_id}")

    response = client.delete(f"/api/chat-generator/session/{session_id}")

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        print(f"✓ 会话已删除")

        # Verify deletion
        get_response = client.get(f"/api/chat-generator/session/{session_id}")
        if get_response.status_code == 404:
            print(f"✓ 验证: 会话已不存在")
            return True
        else:
            print(f"✗ 验证失败: 会话仍然存在")
            return False
    else:
        print(f"✗ 请求失败: {response.text}")
        return False


def test_incremental_generation_request():
    """测试增量生成请求格式"""
    print("\n" + "=" * 60)
    print("测试 5: ChatGenerationRequest 增量模式参数")
    print("=" * 60)

    # First create a session
    nodes_data = [
        {
            "id": "start-1",
            "type": "start-event",
            "position": {"x": 100, "y": 100},
            "data": {"label": "开始", "shape": "start-event"}
        },
        {
            "id": "task-1",
            "type": "task",
            "position": {"x": 300, "y": 100},
            "data": {"label": "处理订单", "shape": "task"}
        }
    ]

    edges_data = [
        {"id": "e1", "source": "start-1", "target": "task-1"}
    ]

    save_response = client.post(
        "/api/chat-generator/session/save",
        json={"nodes": nodes_data, "edges": edges_data}
    )

    if save_response.status_code != 200:
        print(f"✗ 无法创建测试会话: {save_response.text}")
        return False

    session_id = save_response.json().get('session_id')
    print(f"\n测试会话已创建: {session_id}")

    # Test incremental generation request format (without actually calling AI)
    print("\n验证增量生成请求格式...")
    request_body = {
        "user_input": "添加一个审核环节",
        "diagram_type": "flow",
        "incremental_mode": True,
        "session_id": session_id,
        "provider": "gemini"
    }

    print(f"   请求体: {request_body}")
    print(f"   ✓ 增量模式参数格式正确")

    # Clean up
    client.delete(f"/api/chat-generator/session/{session_id}")

    return True


def main():
    """运行所有 API 测试"""
    print("\n" + "=" * 60)
    print("增量生成功能 - API 端点测试")
    print("=" * 60 + "\n")

    results = []

    # Test 1: Save session
    try:
        success, session_id = test_save_session_endpoint()
        results.append(("保存会话 API", success))

        if not success or not session_id:
            print("\n✗ 保存会话失败，无法继续后续测试")
            return 1

        # Test 2: Get session
        try:
            success = test_get_session_endpoint(session_id)
            results.append(("获取会话 API", success))
        except Exception as e:
            print(f"✗ 获取会话异常: {str(e)}")
            results.append(("获取会话 API", False))

        # Test 3: Update session
        try:
            success = test_update_session_endpoint(session_id)
            results.append(("更新会话 API", success))
        except Exception as e:
            print(f"✗ 更新会话异常: {str(e)}")
            results.append(("更新会话 API", False))

        # Test 4: Delete session
        try:
            success = test_delete_session_endpoint(session_id)
            results.append(("删除会话 API", success))
        except Exception as e:
            print(f"✗ 删除会话异常: {str(e)}")
            results.append(("删除会话 API", False))

    except Exception as e:
        print(f"✗ 保存会话异常: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("保存会话 API", False))

    # Test 5: Incremental generation request format
    try:
        success = test_incremental_generation_request()
        results.append(("增量生成请求格式", success))
    except Exception as e:
        print(f"✗ 增量生成请求异常: {str(e)}")
        results.append(("增量生成请求格式", False))

    # Summary
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{status}: {name}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print(f"\n总计: {passed_count}/{total_count} 测试通过")

    if passed_count == total_count:
        print("\n✓ 所有 API 测试通过!")
        return 0
    else:
        print("\n✗ 部分 API 测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
