# test_proxy.py
# -*- coding: utf-8 -*-
"""
HTTP(S) 代理功能测试
演示如何配置和使用代理功能
"""
import logging
from proxy_manager import proxy_manager

def test_proxy_basic():
    """测试基本代理功能"""
    print("=== HTTP(S) 代理功能测试 ===")
    
    # 1. 查看当前代理状态
    print("1. 当前代理状态:")
    status = proxy_manager.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n2. 配置代理设置:")
    # 配置代理（示例配置，请根据实际情况修改）
    proxy_manager.configure(
        http_proxy="http://127.0.0.1:7890",  # 替换为你的代理地址
        https_proxy="http://127.0.0.1:7890", # 替换为你的代理地址
        no_proxy="localhost,127.0.0.1",
        enabled=True
    )
    
    # 查看配置后的状态
    print("   代理配置完成!")
    status = proxy_manager.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n3. 测试代理连接:")
    # 测试代理连接
    success = proxy_manager.test_proxy("https://httpbin.org/ip")
    print(f"   代理测试结果: {'成功' if success else '失败'}")
    
    print("\n4. 获取requests会话:")
    # 演示如何获取配置了代理的session
    session = proxy_manager.get_session()
    print(f"   Session代理配置: {session.proxies}")
    
    print("\n5. 禁用代理:")
    # 禁用代理
    proxy_manager.configure(enabled=False)
    print("   代理已禁用")
    
def test_proxy_with_adapters():
    """演示适配器如何使用代理"""
    print("\n=== 适配器代理使用演示 ===")
    
    # 启用代理
    proxy_manager.configure(
        http_proxy="http://127.0.0.1:7890",
        https_proxy="http://127.0.0.1:7890", 
        enabled=True
    )
    
    print("1. Embedding适配器代理使用:")
    try:
        from embedding_adapters import OllamaEmbeddingAdapter
        # 创建适配器时会自动使用代理管理器
        adapter = OllamaEmbeddingAdapter(
            model_name="nomic-embed-text",
            base_url="http://localhost:11434"
        )
        print("   ✅ OllamaEmbeddingAdapter 已配置代理支持")
    except Exception as e:
        print(f"   ❌ OllamaEmbeddingAdapter 错误: {e}")
    
    print("\n2. LLM适配器代理使用:")
    try:
        from llm_adapters import OpenAIAdapter
        # 创建适配器时会自动应用代理设置
        adapter = OpenAIAdapter(
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model_name="gpt-3.5-turbo",
            max_tokens=100,
            temperature=0.7
        )
        print("   ✅ OpenAIAdapter 已配置代理支持")
    except Exception as e:
        print(f"   ❌ OpenAIAdapter 错误: {e}")
    
    # 禁用代理
    proxy_manager.configure(enabled=False)
    print("\n   代理已禁用，适配器将直接连接")

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        test_proxy_basic()
        test_proxy_with_adapters()
        
        print("\n" + "="*50)
        print("代理功能测试完成!")
        print("="*50)
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()