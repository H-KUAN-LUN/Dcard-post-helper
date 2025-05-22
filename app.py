from flask import Flask, request, jsonify, render_template
import joblib
import jieba
import re
import logging
import os
from dotenv import load_dotenv
# 導入標題生成模塊
from title_generator import generate_titles, mock_generate_titles, get_api_key_instructions
# 導入關鍵字提取與推薦模塊
from keyword_extractor import generate_hot_keywords

# 載入 .env 檔案中的環境變數
load_dotenv()
logging.info("嘗試載入 .env 檔案中的環境變數")

app = Flask(__name__)

# 設置日誌級別
logging.basicConfig(level=logging.INFO)

# 檢查是否設置了 Gemini API 密鑰
has_api_key = os.getenv("GEMINI_API_KEY") is not None
if has_api_key:
    logging.info(f"成功讀取到 GEMINI_API_KEY 環境變數")
else:
    logging.warning("未設置 Gemini API 密鑰，將使用本地標題生成功能")
    # 檢查 .env 檔案是否存在
    if os.path.exists('.env'):
        logging.info("檢測到 .env 檔案存在，但未能讀取 GEMINI_API_KEY")
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()
            logging.info(f".env 檔案內容的前幾行: {env_content[:100]}...")
    else:
        logging.info("未找到 .env 檔案")

# 載入模型和向量化器
model = joblib.load('Dcard-posts-classification-main/voting_classifier_model.joblib')
vectorizer = joblib.load('Dcard-posts-classification-main/tfidf_vectorizer.joblib')

def preprocess_text(text):
    # 移除URL
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    # 移除標點符號
    text = re.sub(r'[^\w\s]', '', text)
    # 分詞
    words = jieba.cut(text)
    return ' '.join(words)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': '請提供文章內容'}), 400
    
    # 處理文本
    processed_text = preprocess_text(text)
    # 轉換為TF-IDF特徵
    features = vectorizer.transform([processed_text]).toarray()  # 轉換為密集矩陣
    # 預測
    prediction = model.predict(features)
    # 獲取預測機率
    probabilities = model.predict_proba(features)
    
    # 記錄預測結果類型和值
    logging.info(f"預測結果類型: {type(prediction[0])}, 值: {prediction[0]}")
    
    # 定義所有支持的類別和對應的索引
    valid_categories = ['mood', 'relationship', 'talk']
    
    # 獲取預測類別
    predicted_category = prediction[0]
    
    # 如果預測結果是數字，轉換為對應的字串標籤
    if isinstance(predicted_category, (int, float)):
        if int(predicted_category) < len(valid_categories):
            predicted_category = valid_categories[int(predicted_category)]
        else:
            # 默認使用第一個類別
            logging.warning(f"預測結果 {predicted_category} 超出範圍，使用默認類別")
            predicted_category = valid_categories[0]
    elif predicted_category not in valid_categories:
        # 如果是字串但不在有效類別列表中，使用默認類別
        logging.warning(f"預測結果 '{predicted_category}' 不在有效類別列表中，使用默認類別")
        predicted_category = valid_categories[0]
    
    # 記錄最終類別
    logging.info(f"最終預測類別: {predicted_category}")
    
    # 構建結果
    result = {
        'category': predicted_category,
        'category_name': '心情板' if predicted_category == 'mood' else ('感情板' if predicted_category == 'relationship' else '閒聊板'),
        'probabilities': {}
    }
    
    # 確保所有類別都有對應的概率值
    for i, category in enumerate(valid_categories):
        if i < len(probabilities[0]):
            result['probabilities'][category] = float(probabilities[0][i])
        else:
            # 如果索引超出範圍，設置為0
            result['probabilities'][category] = 0.0
    
    # 添加中文名稱到結果中
    result['probability_names'] = {
        'mood': '心情板',
        'relationship': '感情板',
        'talk': '閒聊板'
    }
    
    # 生成標題建議
    try:
        # 根據是否有API密鑰選擇使用實際或模擬功能
        if has_api_key:
            suggested_titles = generate_titles(text, predicted_category, num_titles=3)
            api_instructions = None
        else:
            suggested_titles = mock_generate_titles(text, predicted_category, num_titles=3)
            # 添加 API 密鑰設置說明
            api_instructions = get_api_key_instructions()
        
        result['suggested_titles'] = suggested_titles
        if api_instructions:
            result['api_instructions'] = api_instructions
        
        logging.info(f"為文章生成了 {len(suggested_titles)} 個標題建議")
    except Exception as e:
        logging.error(f"生成標題時發生錯誤: {str(e)}")
        result['suggested_titles'] = ["無法生成標題建議"]
    
    # 生成熱門關鍵字推薦
    try:
        keywords_result = generate_hot_keywords(text, predicted_category, max_extracted=15, max_recommended=5)
        result['extracted_keywords'] = keywords_result['extracted_keywords']
        result['hot_keywords'] = keywords_result['recommended_hot_keywords']
        logging.info(f"為文章生成了 {len(result['hot_keywords'])} 個熱門關鍵字推薦")
    except Exception as e:
        logging.error(f"生成熱門關鍵字時發生錯誤: {str(e)}")
        result['hot_keywords'] = []
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000) 