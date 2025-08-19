#novel_generator/common.py
# -*- coding: utf-8 -*-
"""
通用重试、清洗、日志工具
"""
import logging
import re
import time
import traceback

def call_with_retry(func, max_retries=3, sleep_time=2, fallback_return=None, **kwargs):
    """
    通用的重试机制封装。
    :param func: 要执行的函数
    :param max_retries: 最大重试次数
    :param sleep_time: 重试前的等待秒数
    :param fallback_return: 如果多次重试仍失败时的返回值
    :param kwargs: 传给func的命名参数
    :return: func的结果，若失败则返回 fallback_return
    """
    for attempt in range(1, max_retries + 1):
        try:
            return func(**kwargs)
        except Exception as e:
            logging.warning(f"[call_with_retry] Attempt {attempt} failed with error: {e}")
            traceback.print_exc()
            if attempt < max_retries:
                time.sleep(sleep_time)
            else:
                logging.error("Max retries reached, returning fallback_return.")
                return fallback_return

def remove_think_tags(text: str) -> str:
    """移除 <think>...</think> 包裹的内容"""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

def debug_log(prompt: str, response_content: str):
    logging.info(
        f"\n[#########################################  Prompt  #########################################]\n{prompt}\n"
    )
    logging.info(
        f"\n[######################################### Response #########################################]\n{response_content}\n"
    )

def invoke_with_cleaning(llm_adapter, prompt: str, max_retries: int = 3) -> str:
    """调用 LLM 并清理返回结果"""
    print("\n" + "="*50)
    print("发送到 LLM 的提示词:")
    print("-"*50)
    print(prompt)
    print("="*50 + "\n")
    
    result = ""
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            result = llm_adapter.invoke(prompt)
            print("\n" + "="*50)
            print("LLM 返回的内容:")
            print("-"*50)
            print(result if result else "[空响应]")
            print("="*50 + "\n")
            
            # 清理结果中的特殊格式标记
            if result:
                result = result.replace("```json", "").replace("```", "").strip()
                if result:
                    logging.info(f"LLM调用成功，返回{len(result)}字符")
                    return result
            
            logging.warning(f"LLM返回空内容，重试 ({retry_count + 1}/{max_retries})")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(2)  # 重试前等待2秒
                
        except Exception as e:
            last_error = e
            logging.error(f"LLM调用失败 ({retry_count + 1}/{max_retries}): {str(e)}")
            print(f"调用失败 ({retry_count + 1}/{max_retries}): {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(2)  # 重试前等待2秒
    
    # 所有重试都失败后的处理
    if last_error:
        logging.error(f"LLM调用彻底失败，所有{max_retries}次重试均失败: {last_error}")
        print(f"⚠️ LLM调用彻底失败，所有{max_retries}次重试均失败")
        
    return result

