"""
AI Trading Advisor - OpenAI Integration
"""
import os
import json
import re
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
    
    def _clean_json_response(self, content: str) -> str:
        """Clean AI response by removing markdown code blocks and extra formatting"""
        if not content:
            return content
        
        original = content
        
        # Remove markdown code blocks (```json ... ``` or ``` ... ```)
        content = re.sub(r'^```(?:json)?\s*\n', '', content.strip(), flags=re.MULTILINE)
        content = re.sub(r'\n```\s*$', '', content.strip(), flags=re.MULTILINE)
        
        # Remove any leading/trailing whitespace
        content = content.strip()
        
        # Try to extract just the JSON object if there's text before/after
        # Look for the first { and last }
        first_brace = content.find('{')
        last_brace = content.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
            # Check if there's significant text before the JSON
            before_json = content[:first_brace].strip()
            after_json = content[last_brace+1:].strip()
            
            if before_json or after_json:
                print(f"⚠️ Found extra text around JSON (before: {len(before_json)} chars, after: {len(after_json)} chars)")
                content = content[first_brace:last_brace+1]
        
        return content
    
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
            
            # Clean the response to remove markdown code blocks
            original_content = content
            content = self._clean_json_response(content)
            
            # Log if cleaning was necessary
            if original_content != content:
                print("🧹 Cleaned markdown formatting from AI response")
            
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
                print(f"🔍 Full response content (first 500 chars):\n{content[:500]}")
                print(f"🔍 Full response content (last 200 chars):\n{content[-200:]}")
                print(f"🔍 Response length: {len(content)} characters")
                
                # Try to extract the first valid JSON object if there's extra data
                try:
                    # Find the first complete JSON object
                    decoder = json.JSONDecoder()
                    response, idx = decoder.raw_decode(content)
                    
                    remaining = content[idx:].strip()
                    if remaining:
                        print(f"⚠️ Found extra data after JSON: {remaining[:100]}")
                    
                    print("✅ Successfully extracted first JSON object")
                    return response
                    
                except Exception as e2:
                    print(f"🔴 Failed to extract JSON: {str(e2)}")
                
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
