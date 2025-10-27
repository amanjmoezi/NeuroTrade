"""
AI Trading Advisor - OpenAI Integration
"""
import os
import json
from typing import Dict
from openai import AsyncOpenAI
from src.core.config import Config


class AITradingAdvisor:
    """AI Trading Advisor using OpenAI"""
    
    def __init__(self, config: Config):
        self.client = AsyncOpenAI(
            api_key=config.openai_key,
            base_url=config.openai_base_url,
            timeout=config.ai_timeout
        )
        self.config = config
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file"""
        prompt_path = "init/systemPrompt.txt"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                print("✅ SYSTEM PROMPT LOADED")
                return f.read()
        return "You are an ICT trading expert."
    
    async def get_signal(self, market_data: Dict) -> Dict:
        """Get Trading Signal from AI"""
        print("🤖 Requesting ICT signal from AI")
        
        # Validate market data first
        if not market_data or 'market_data' not in market_data:
            error_msg = "خطا: داده‌های بازار ناقص است"
            print(f"🔴 {error_msg}")
            return {
                "error": error_msg,
                "error_type": "DATA_INCOMPLETE",
                "user_message": "❌ داده‌های بازار به درستی دریافت نشد. لطفاً دوباره تلاش کنید."
            }
        
        
        try:
            # Prepare API call parameters
            api_params = {
                "model": self.config.ai_model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": json.dumps(market_data, indent=2)}
                ],
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "response_format": {"type": "json_object"}
            }
            
            
            completion = await self.client.chat.completions.create(**api_params)
            
            content = completion.choices[0].message.content
            if not content or content.strip() == "":
                error_msg = "هوش مصنوعی پاسخ خالی برگرداند"
                print(f"🔴 {error_msg}")
                return {
                    "error": error_msg,
                    "error_type": "EMPTY_RESPONSE",
                    "user_message": "❌ خطا در دریافت سیگنال از هوش مصنوعی. لطفاً دوباره تلاش کنید."
                }
            
            try:
                response = json.loads(content)
                
                # Check if response itself contains an error field
                if "error" in response and response["error"]:
                    print(f"🔴 AI returned error: {response['error']}")
                    return {
                        "error": response["error"],
                        "error_type": "AI_ERROR",
                        "user_message": f"❌ خطا در تحلیل: {response['error']}"
                    }
                
                
                print("✅ AI signal received")
                
                return response
                
            except json.JSONDecodeError as je:
                error_msg = f"خطا در تجزیه پاسخ JSON: {str(je)}"
                print(f"🔴 {error_msg}")
                print(f"Response content: {content[:200]}")
                return {
                    "error": error_msg,
                    "error_type": "JSON_PARSE_ERROR",
                    "user_message": "❌ خطا در پردازش پاسخ هوش مصنوعی. لطفاً دوباره تلاش کنید.",
                    "raw_content": content[:500]
                }
            
        except Exception as e:
            error_msg = f"خطا در ارتباط با هوش مصنوعی: {str(e)}"
            print(f"🔴 {error_msg}")
            
            # Provide user-friendly error messages
            user_message = "❌ خطا در ارتباط با سرور هوش مصنوعی."
            if "timeout" in str(e).lower():
                user_message = "❌ زمان انتظار تمام شد. لطفاً دوباره تلاش کنید."
            elif "connection" in str(e).lower():
                user_message = "❌ خطا در اتصال به سرور. لطفاً اتصال اینترنت خود را بررسی کنید."
            elif "api key" in str(e).lower():
                user_message = "❌ خطا در احراز هویت API. لطفاً تنظیمات را بررسی کنید."
            
            return {
                "error": error_msg,
                "error_type": "API_ERROR",
                "user_message": user_message,
                "exception_type": type(e).__name__
            }
