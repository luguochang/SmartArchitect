"""
诊断流式传输 - 检查是实时流式还是批量返回
"""
import requests
import time
import json

url = "http://localhost:8000/api/excalidraw/generate-stream"

payload = {
    "prompt": "画一个简单的登录流程",
    "provider": "custom",
    "api_key": "sk-7oflvgMRXPZe0skck0qIqsFuDSvOBKiMqqGiC0Sx9gzAsALh",
    "base_url": "https://www.linkflow.run/v1",
    "model_name": "claude-sonnet-4-5-20250929",
    "width": 1200,
    "height": 800
}

print("=" * 80)
print("流式传输诊断测试")
print("=" * 80)
print(f"开始时间: {time.strftime('%H:%M:%S')}")
print()

try:
    response = requests.post(url, json=payload, stream=True, timeout=120)

    print(f"状态码: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print()
    print("=" * 80)
    print("实时输出 (每条事件显示接收时间)")
    print("=" * 80)

    start_time = time.time()
    event_count = 0
    token_count = 0
    last_event_time = start_time

    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue

        current_time = time.time()
        elapsed = current_time - start_time
        interval = current_time - last_event_time
        last_event_time = current_time

        event_count += 1

        # 显示时间戳和事件内容
        if "[TOKEN]" in line:
            token_count += 1
            if token_count <= 5 or token_count % 50 == 0:  # 只显示前5个和每50个
                print(f"[{elapsed:.2f}s +{interval:.3f}s] Token #{token_count}: {line[:100]}")
        elif "[START]" in line or "[CALL]" in line or "[RESULT]" in line or "[END]" in line:
            print(f"[{elapsed:.2f}s +{interval:.3f}s] {line[:150]}")

    total_time = time.time() - start_time

    print()
    print("=" * 80)
    print(f"总耗时: {total_time:.2f}秒")
    print(f"总事件数: {event_count}")
    print(f"Token数: {token_count}")

    if token_count > 0:
        avg_interval = total_time / token_count
        print(f"平均每token间隔: {avg_interval*1000:.1f}ms")

        if avg_interval < 0.01:  # 小于10ms说明可能是批量返回
            print()
            print("⚠️  警告: Token间隔过短 (<10ms)，可能是批量返回而非真正流式！")
        else:
            print()
            print("✅ Token间隔正常，确认为实时流式传输")
    else:
        print()
        print("❌ 未收到任何TOKEN事件")

except requests.exceptions.ConnectionError:
    print("\n❌ 连接失败: 后端服务未启动")
    print("请运行: cd backend && python -m app.main")
except requests.exceptions.Timeout:
    print("\n❌ 请求超时 (120s)")
except KeyboardInterrupt:
    print("\n\n⚠️  用户中断")
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
