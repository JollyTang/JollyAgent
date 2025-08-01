"""Test API connection to SiliconFlow."""

import json
import os
from typing import Dict, Any

import pytest
import requests

from src.config import get_config


def test_siliconflow_api_connection():
    """Test connection to SiliconFlow API."""
    config = get_config()

    # API请求URL
    url = f"{config.llm.base_url}/chat/completions"

    # 请求头
    headers = {
        "Authorization": f"Bearer {config.llm.api_key}",
        "Content-Type": "application/json",
    }

    # 请求数据
    data = {
        "model": config.llm.model,
        "messages": [
            {
                "role": "user",
                "content": "Hello, please respond with 'API connection successful'",
            }
        ],
        "temperature": config.llm.temperature,
        "max_tokens": config.llm.max_tokens,
    }

    try:
        # 发送请求
        response = requests.post(url, headers=headers, json=data, timeout=30)

        # 检查响应状态
        assert (
            response.status_code == 200
        ), f"API request failed: {response.status_code}"

        # 解析响应
        result = response.json()

        # 检查响应结构
        assert "choices" in result, "Response missing 'choices' field"
        assert len(result["choices"]) > 0, "No choices in response"

        # 检查消息内容
        choice = result["choices"][0]
        assert "message" in choice, "Choice missing 'message' field"
        assert "content" in choice["message"], "Message missing 'content' field"

        # 打印响应内容（用于调试）
        content = choice["message"]["content"]
        print(f"API Response: {content}")

        # 验证响应不为空
        assert content.strip(), "API response is empty"

    except requests.exceptions.RequestException as e:
        pytest.fail(f"API request failed: {e}")
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse JSON response: {e}")


def test_config_values():
    """Test that configuration values are correctly set."""
    config = get_config()

    # 验证配置值
    assert config.llm.base_url == "https://api.siliconflow.cn/v1"
    assert config.llm.model == "Qwen/QwQ-32B"
    assert config.llm.api_key == "sk-atpfqgdfpusndwvlufdyxjkriuwepbbrpnrwuctdydmeqyaz"
    assert config.llm.temperature == 0.1
    assert config.llm.max_tokens == 4096


if __name__ == "__main__":
    # 直接运行测试
    test_config_values()
    print("Configuration test passed!")

    # 运行API连接测试
    test_siliconflow_api_connection()
    print("API connection test passed!")
