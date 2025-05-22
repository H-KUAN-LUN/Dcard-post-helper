import os
import logging
import time
import json
import re
import requests
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 設置 Gemini API 密鑰
# 需要在環境變數中設置 GEMINI_API_KEY
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    logger.info(f"成功從環境變數中讀取到 GEMINI_API_KEY: {api_key[:4]}...")
    GEMINI_API_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
else:
    logger.warning("未設置 GEMINI_API_KEY 環境變數，標題生成功能將無法使用")
    
    # 檢查環境中的所有變數，看是否有類似的 API 密鑰
    env_vars = [key for key in os.environ.keys() if 'KEY' in key or 'API' in key]
    if env_vars:
        logger.info(f"在環境中找到的可能相關變數: {env_vars}")

# 看板風格特徵定義
BOARD_STYLES = {
    'mood': {
        'description': '心情板主要分享個人情緒、心情感受和日常生活',
        'tone': '真誠、表達情感、個人化',
        'examples': [
            '今天的小確幸：一杯熱奶茶和陽光',
            '考完試的解脫感⋯⋯終於可以好好睡一覺了',
            '獨自一人的週末，其實也很美好',
            '總是習慣性太在意別人的看法',
            '我好像忘了怎麼和人相處'
        ]
    },
    'relationship': {
        'description': '感情板討論兩性關係、戀愛話題、情感困擾',
        'tone': '情感豐富、尋求建議、探討關係',
        'examples': [
            '男友和他的女性朋友太親密，該介意嗎？',
            '分手後該如何徹底忘記對方？',
            '喜歡上有女友的學長...該怎麼辦',
            '戀愛中最讓你感到安心的瞬間是什麼',
            '交往三年，他突然說想要空間...'
        ]
    },
    'talk': {
        'description': '閒聊板包含各種輕鬆話題、分享想法、討論時事',
        'tone': '輕鬆、好奇、討論型',
        'examples': [
            '有哪些冷知識是大家不太知道的？',
            '你們會在意另一半的過去嗎？',
            '有推薦的追劇APP嗎？',
            '一個人旅行真的很爽欸！',
            '最近有什麼好看的電影推薦？'
        ]
    }
}

def generate_titles(text, category, num_titles=3, max_retries=3):
    """
    根據文章內容和類別使用 Gemini API 生成適合的標題
    
    參數:
        text (str): 文章內容
        category (str): 文章分類 ('mood', 'relationship', 'talk')
        num_titles (int): 要生成的標題數量
        max_retries (int): 最大重試次數
    
    返回:
        list: 生成的標題列表
    """
    if not api_key:
        logger.error("未設置 Gemini API 密鑰，無法生成標題")
        return ["請設置 GEMINI_API_KEY 以啟用標題生成功能"]
    
    # 獲取對應類別的風格指南
    style_guide = BOARD_STYLES.get(category, BOARD_STYLES['talk'])
    
    # 準備內容摘要 (限制長度以減少token消耗)
    content_summary = text[:500] + ('...' if len(text) > 500 else '')
    
    # 構建提示詞
    prompt = f"""
    請幫我為以下文章內容生成{num_titles}個適合在Dcard {style_guide['description']} 發布的標題。
    
    文章內容：
    {content_summary}
    
    標題風格要求：
    - 符合{style_guide['tone']}的語調
    - 吸引人且能引起共鳴
    - 長度控制在15-25個字以內
    - 符合Dcard {category}板的風格
    
    參考標題範例：
    {', '.join(style_guide['examples'][:3])}
    
    請直接給出{num_titles}個標題，每個標題一行，以數字編號，不要有額外的說明。
    """
    
    # 構建 Gemini API 請求
    request_data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    retry_count = 0
    while retry_count < max_retries:
        try:
            # 發送 API 請求
            response = requests.post(
                GEMINI_API_ENDPOINT,
                headers=headers,
                json=request_data
            )
            
            # 檢查響應狀態
            if response.status_code == 200:
                # 解析響應
                response_data = response.json()
                if 'candidates' in response_data and len(response_data['candidates']) > 0:
                    content = response_data['candidates'][0]['content']
                    if 'parts' in content and len(content['parts']) > 0:
                        titles_text = content['parts'][0]['text'].strip()
                        
                        # 解析標題，使用正則表達式匹配數字編號開頭的行
                        titles = re.findall(r'^\d+\.?\s*(.+)$', titles_text, re.MULTILINE)
                        
                        # 確保我們至少得到一個標題
                        if titles:
                            return titles[:num_titles]  # 限制返回標題數量
            
            # 如果沒有返回或解析失敗，記錄錯誤
            logger.warning(f"Gemini API 回應解析失敗，狀態碼: {response.status_code}")
            logger.warning(f"回應內容: {response.text}")
            retry_count += 1
            time.sleep(1)  # 延遲一秒再重試
                
        except Exception as e:
            logger.error(f"生成標題時發生錯誤: {str(e)}")
            retry_count += 1
            time.sleep(1)  # 延遲一秒再重試
    
    # 如果多次嘗試後仍然失敗，返回一個默認標題
    return ["我的Dcard文章", f"分享一些關於{style_guide['description']}的想法", "想聽聽大家的看法"]

# 模擬生成標題的函數 (測試用，不需要API密鑰)
def mock_generate_titles(text, category, num_titles=3):
    """用於測試的本地標題生成函數 - 更智能的版本"""
    style_guide = BOARD_STYLES.get(category, BOARD_STYLES['talk'])
    
    # 簡單的關鍵詞列表
    mood_keywords = ["心情", "感受", "難過", "開心", "煩惱", "壓力", "生活", "疲倦", "孤單", "焦慮"]
    relationship_keywords = ["男友", "女友", "感情", "戀愛", "分手", "告白", "交往", "曖昧", "前任", "喜歡"]
    talk_keywords = ["問題", "大家", "推薦", "心得", "分享", "求助", "想問", "經驗", "建議", "討論"]
    
    # 取得特定類別的關鍵詞
    keywords = {
        'mood': mood_keywords,
        'relationship': relationship_keywords,
        'talk': talk_keywords
    }.get(category, talk_keywords)
    
    # 根據文本內容尋找關鍵詞
    found_keywords = []
    for keyword in keywords:
        if keyword in text:
            found_keywords.append(keyword)
    
    # 如果找不到關鍵詞，使用預設關鍵詞
    if not found_keywords:
        import random
        found_keywords = random.sample(keywords, min(3, len(keywords)))
    
    # 根據關鍵詞和類別生成更相關的標題
    import random
    titles = []
    
    # 標題模板
    mood_templates = [
        "今天的{}，讓我有點{}",
        "為什麼我總是{}的時候感到{}",
        "分享一下關於{}的小{}",
        "突然間感到{}，是不是因為{}",
        "{}時的那種{}感覺，有人懂嗎",
        "對於{}，我的{}心情"
    ]
    
    relationship_templates = [
        "當{}遇到{}，我該怎麼辦",
        "和{}之間的{}問題",
        "{}後他的{}舉動，這代表什麼",
        "對於{}，你們會選擇{}嗎",
        "{}中的{}困擾，求解答",
        "關於{}的{}問題，想聽聽大家意見"
    ]
    
    talk_templates = [
        "有沒有人知道關於{}的{}",
        "想問問大家對{}的{}看法",
        "{}時有什麼推薦的{}嗎",
        "分享一下我的{}{}經驗",
        "大家都怎麼處理{}的{}情況",
        "關於{}，有什麼{}建議"
    ]
    
    templates = {
        'mood': mood_templates,
        'relationship': relationship_templates,
        'talk': talk_templates
    }.get(category, talk_templates)
    
    # 生成指定數量的標題
    for _ in range(num_titles):
        if random.random() < 0.3 and style_guide['examples']:
            # 30% 機會直接使用範例標題
            titles.append(random.choice(style_guide['examples']))
        else:
            # 70% 機會使用模板生成標題
            template = random.choice(templates)
            keyword1 = random.choice(found_keywords)
            remaining_keywords = [k for k in found_keywords if k != keyword1] or found_keywords
            keyword2 = random.choice(remaining_keywords)
            titles.append(template.format(keyword1, keyword2))
    
    # 確保標題不重複
    unique_titles = list(set(titles))
    while len(unique_titles) < num_titles and len(templates) > 0:
        template = random.choice(templates)
        keyword1 = random.choice(found_keywords)
        remaining_keywords = [k for k in found_keywords if k != keyword1] or found_keywords
        keyword2 = random.choice(remaining_keywords)
        new_title = template.format(keyword1, keyword2)
        if new_title not in unique_titles:
            unique_titles.append(new_title)
    
    return unique_titles[:num_titles]

# 輔助函數：顯示如何設置 API 密鑰的說明
def get_api_key_instructions():
    """返回如何設置 API 密鑰的詳細說明"""
    instructions = """
如何設置 Google Gemini API 密鑰：

1. 前往 Google AI Studio (https://makersuite.google.com/app/apikey) 獲取 API 密鑰
2. 登入您的 Google 帳號並創建 API 密鑰
3. 複製生成的 API 密鑰

4. 在命令行中設置環境變數：

   Windows:
   set GEMINI_API_KEY=your_api_key_here

   macOS/Linux:
   export GEMINI_API_KEY=your_api_key_here

5. 重新啟動應用程序

注意：請妥善保管您的 API 密鑰，不要將其分享給他人或提交到公共代碼庫。
"""
    return instructions

# 測試代碼
if __name__ == "__main__":
    test_text = "今天心情非常低落，因為我最近失戀了。我們交往了兩年，但他說我們不合適。我不知道該怎麼辦，很需要有人安慰我。"
    # 如果設置了API密鑰，使用實際生成函數；否則使用模擬函數
    if api_key:
        titles = generate_titles(test_text, 'mood')
    else:
        titles = mock_generate_titles(test_text, 'mood')
    
    print("生成的標題:")
    for i, title in enumerate(titles, 1):
        print(f"{i}. {title}") 