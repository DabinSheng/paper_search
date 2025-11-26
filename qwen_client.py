import requests
import json
from typing import Optional
from config import Config


class QwenClient:
    """Qwen API客户端，用于文本翻译"""
    
    def __init__(self):
        self.api_key = Config.QWEN_API_KEY
        self.api_url = Config.QWEN_API_URL
        self.model = Config.QWEN_MODEL
        
    def translate_to_chinese(self, text: str) -> Optional[str]:
        """
        将英文文本翻译成中文
        
        Args:
            text: 需要翻译的英文文本
            
        Returns:
            翻译后的中文文本，失败返回None
        """
        if not text or not text.strip():
            return ""
            
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            prompt = f"请将以下英文翻译成中文，只返回翻译结果，不要有任何解释：\n\n{text}"
            
            # 使用OpenAI兼容模式的API格式
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = requests.post(
                self.api_url + "/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                # OpenAI兼容格式的响应
                if 'choices' in result and len(result['choices']) > 0:
                    translation = result['choices'][0]['message']['content']
                    return translation.strip()
            else:
                print(f"翻译失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"翻译出错: {str(e)}")
            return None
    
    def batch_translate(self, texts: list[str]) -> list[Optional[str]]:
        """
        批量翻译文本
        
        Args:
            texts: 需要翻译的文本列表
            
        Returns:
            翻译结果列表
        """
        results = []
        for text in texts:
            translation = self.translate_to_chinese(text)
            results.append(translation)
        return results


# 创建全局客户端实例
qwen_client = QwenClient()
