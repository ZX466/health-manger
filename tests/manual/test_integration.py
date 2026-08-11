"""
整合功能验证测试
验证从参考项目借鉴的优势元素是否正确整合
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_feature_mapping():
    print("\n=== 测试特征映射模块 ===")
    from tongue.feature_mapping import (
        get_feature_label, get_feature_description, 
        get_status_info, label_to_code
    )
    
    tongue_label = get_feature_label("tongue_color", 1, "cn")
    assert tongue_label == "淡红", f"舌色标签错误: {tongue_label}"
    print(f"  ✓ 舌色标签 (cn): {tongue_label}")
    
    tongue_label_en = get_feature_label("tongue_color", 1, "en")
    assert tongue_label_en == "Light red", f"舌色英文标签错误: {tongue_label_en}"
    print(f"  ✓ 舌色标签 (en): {tongue_label_en}")
    
    desc = get_feature_description("tongue_color", "淡红")
    assert "正常" in desc, f"舌色描述错误: {desc}"
    print(f"  ✓ 舌色描述: {desc}")
    
    status = get_status_info(100)
    assert status["status"] == "completed", f"状态信息错误: {status}"
    print(f"  ✓ 状态信息: {status}")
    
    code = label_to_code("tongue_color", "淡红")
    assert code == 1, f"标签转编码错误: {code}"
    print(f"  ✓ 标签转编码: 淡红 -> {code}")
    
    print("特征映射模块测试通过 ✓")


def test_async_tasks():
    print("\n=== 测试异步任务模块 ===")
    from async_tasks import AsyncTaskQueue
    
    queue = AsyncTaskQueue(max_workers=1)
    
    def sample_task(x, y):
        return {"result": x + y}
    
    task_id = queue.submit_task("test_task_1", sample_task, args=(5, 3))
    print(f"  ✓ 任务已提交: {task_id}")
    
    status = queue.get_task_status(task_id)
    assert status is not None, "任务状态获取失败"
    print(f"  ✓ 任务状态: {status['status']}")
    
    print("异步任务模块测试通过 ✓")



def test_chat_session_module():
    print("\n=== 测试会话管理模块 ===")
    from chat_session import ChatSession, ChatMessage
    
    assert hasattr(ChatSession, '__tablename__'), "ChatSession 表名未定义"
    assert ChatSession.__tablename__ == "chat_sessions", f"表名错误: {ChatSession.__tablename__}"
    print(f"  ✓ ChatSession 表名: {ChatSession.__tablename__}")
    
    assert hasattr(ChatMessage, '__tablename__'), "ChatMessage 表名未定义"
    assert ChatMessage.__tablename__ == "chat_messages", f"表名错误: {ChatMessage.__tablename__}"
    print(f"  ✓ ChatMessage 表名: {ChatMessage.__tablename__}")
    
    print("会话管理模块测试通过 ✓")


def test_schemas():
    print("\n=== 测试 Schema 定义 ===")
    from schemas import (
        ChatSessionCreate, ChatMessageCreate, AsyncTaskStatus
    )
    
    session_create = ChatSessionCreate(title="测试会话")
    assert session_create.title == "测试会话", "会话创建 Schema 错误"
    print(f"  ✓ ChatSessionCreate: {session_create.title}")
    
    message_create = ChatMessageCreate(content="测试消息")
    assert message_create.content == "测试消息", "消息创建 Schema 错误"
    print(f"  ✓ ChatMessageCreate: {message_create.content}")
    
    task_status = AsyncTaskStatus(task_id="test", status="pending")
    assert task_status.task_id == "test", "任务状态 Schema 错误"
    print(f"  ✓ AsyncTaskStatus: {task_status.task_id}")
    
    print("Schema 定义测试通过 ✓")


def test_routers():
    print("\n=== 测试路由模块 ===")
    from routers.chat import router
    
    routes = [route.path for route in router.routes]
    
    print(f"  实际路由: {routes}")
    
    expected_routes = [
        "/session", "/sessions", 
        "/session/{session_id}/messages",
        "/session/{session_id}/message",
        "/session/{session_id}/tongue-context",
        "/session/{session_id}"
    ]
    
    for expected in expected_routes:
        found = any(expected in route for route in routes)
        assert found, f"路由缺失: {expected}"
        print(f"  ✓ 路由存在: {expected}")
    
    print("路由模块测试通过 ✓")


def main():
    print("=" * 50)
    print("整合功能验证测试")
    print("=" * 50)
    
    try:
        test_feature_mapping()
        test_async_tasks()

        test_chat_session_module()
        test_schemas()
        test_routers()
        
        print("\n" + "=" * 50)
        print("所有测试通过 ✓")
        print("=" * 50)
        return True
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
