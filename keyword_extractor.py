"""
關鍵字提取與推薦模組
用於分析文章內容，提取關鍵主題並推薦熱門相關標籤
"""
import jieba.analyse
import logging
import re
import random
from collections import Counter

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 載入結巴分詞的 TF-IDF 和 TextRank 分析工具
jieba.analyse.set_stop_words("dict/stop_words.txt")
jieba.analyse.set_idf_path("dict/idf.txt.big")

# 各看板熱門關鍵字（模擬資料）
# 這些關鍵字可以通過爬蟲獲取或資料分析來更新
POPULAR_KEYWORDS = {
    'mood': [
        {'keyword': '紓壓', 'popularity': 98, 'related': ['壓力', '放鬆', '心情']},
        {'keyword': '自我成長', 'popularity': 95, 'related': ['進步', '學習', '挑戰']},
        {'keyword': '焦慮', 'popularity': 92, 'related': ['緊張', '不安', '壓力']},
        {'keyword': '療癒', 'popularity': 90, 'related': ['舒壓', '放鬆', '心靈']},
        {'keyword': '孤獨', 'popularity': 89, 'related': ['寂寞', '一個人', '獨處']},
        {'keyword': '憂鬱', 'popularity': 87, 'related': ['難過', '低落', '心情']},
        {'keyword': '感恩', 'popularity': 85, 'related': ['謝謝', '珍惜', '幸福']},
        {'keyword': '人際關係', 'popularity': 83, 'related': ['朋友', '社交', '互動']},
        {'keyword': '成就感', 'popularity': 81, 'related': ['完成', '目標', '滿足']},
        {'keyword': '自信', 'popularity': 80, 'related': ['肯定', '勇氣', '相信']},
        # 新增的心情板熱門關鍵字
        {'keyword': '心情不好', 'popularity': 94, 'related': ['難過', '不開心', '壓抑']},
        {'keyword': '抒發', 'popularity': 91, 'related': ['表達', '宣洩', '心情']},
        {'keyword': '生活壓力', 'popularity': 88, 'related': ['壓力', '忙碌', '疲憊']},
        {'keyword': '快樂', 'popularity': 86, 'related': ['開心', '幸福', '滿足']},
        {'keyword': '情緒管理', 'popularity': 84, 'related': ['控制', '處理', '情緒']},
        {'keyword': '正能量', 'popularity': 82, 'related': ['積極', '樂觀', '正向']},
        {'keyword': '失落', 'popularity': 79, 'related': ['迷茫', '失去', '空虛']},
        {'keyword': '感動', 'popularity': 77, 'related': ['溫暖', '觸動', '淚水']},
        {'keyword': '創傷', 'popularity': 75, 'related': ['傷害', '痛苦', '治療']},
        {'keyword': '懷舊', 'popularity': 73, 'related': ['回憶', '過去', '思念']}
    ],
    'relationship': [
        {'keyword': '前任', 'popularity': 98, 'related': ['分手', '復合', '舊情人']},
        {'keyword': '曖昧', 'popularity': 96, 'related': ['捉摸不定', '柏拉圖', '柏拉圖式']},
        {'keyword': '告白', 'popularity': 94, 'related': ['表白', '喜歡', '心意']},
        {'keyword': '分手', 'popularity': 93, 'related': ['結束', '放下', '難過']},
        {'keyword': '劈腿', 'popularity': 91, 'related': ['背叛', '出軌', '欺騙']},
        {'keyword': '相處模式', 'popularity': 90, 'related': ['習慣', '空間', '磨合']},
        {'keyword': '吵架', 'popularity': 88, 'related': ['爭執', '冷戰', '溝通']},
        {'keyword': '暗戀', 'popularity': 86, 'related': ['單戀', '喜歡', '偷偷']},
        {'keyword': '異地戀', 'popularity': 85, 'related': ['距離', '遠距離', '思念']},
        {'keyword': '相親', 'popularity': 82, 'related': ['約會', '第一次見面', '介紹']},
        # 新增的感情板熱門關鍵字
        {'keyword': '交往', 'popularity': 95, 'related': ['戀愛', '情侶', '關係']},
        {'keyword': '失戀', 'popularity': 92, 'related': ['分手', '放下', '傷心']},
        {'keyword': '戀愛技巧', 'popularity': 89, 'related': ['追求', '攻略', '技巧']},
        {'keyword': '感情問題', 'popularity': 87, 'related': ['困擾', '疑惑', '建議']},
        {'keyword': '婚姻', 'popularity': 84, 'related': ['結婚', '伴侶', '經營']},
        {'keyword': '長跑', 'popularity': 81, 'related': ['長期', '穩定', '關係']},
        {'keyword': '曖昧期', 'popularity': 80, 'related': ['曖昧', '暧昧', '捉摸不定']},
        {'keyword': '挽回', 'popularity': 79, 'related': ['挽救', '挽留', '挽回前任']},
        {'keyword': '感情觀', 'popularity': 78, 'related': ['價值觀', '感情觀念', '愛情觀']},
        {'keyword': '網戀', 'popularity': 77, 'related': ['線上交友', '遠距戀愛', '見面']}
    ],
    'talk': [
        {'keyword': '心得分享', 'popularity': 97, 'related': ['經驗', '推薦', '想法']},
        {'keyword': '求推薦', 'popularity': 95, 'related': ['意見', '建議', '推薦']},
        {'keyword': '時事', 'popularity': 93, 'related': ['新聞', '熱門', '討論']},
        {'keyword': '美食', 'popularity': 92, 'related': ['餐廳', '食物', '推薦']},
        {'keyword': '職場', 'popularity': 90, 'related': ['工作', '上班', '同事']},
        {'keyword': '電影', 'popularity': 88, 'related': ['影評', '推薦', '心得']},
        {'keyword': '旅遊', 'popularity': 87, 'related': ['景點', '行程', '規劃']},
        {'keyword': '3C', 'popularity': 85, 'related': ['手機', '電腦', '購買']},
        {'keyword': '健身', 'popularity': 83, 'related': ['運動', '減肥', '健康']},
        {'keyword': '追劇', 'popularity': 82, 'related': ['推薦', '心得', '評價']},
        # 新增的閒聊板熱門關鍵字
        {'keyword': '問卦', 'popularity': 96, 'related': ['問題', '好奇', '討論']},
        {'keyword': '分享', 'popularity': 94, 'related': ['心得', '經驗', '推薦']},
        {'keyword': '求解', 'popularity': 91, 'related': ['疑問', '請教', '解答']},
        {'keyword': '學生', 'popularity': 89, 'related': ['大學', '課業', '校園']},
        {'keyword': '科技', 'popularity': 86, 'related': ['手機', '電腦', '數位']},
        {'keyword': '八卦', 'popularity': 84, 'related': ['gossip', '熱門', '話題']},
        {'keyword': '女孩', 'popularity': 81, 'related': ['女生', '女性', '話題']},
        {'keyword': '男孩', 'popularity': 80, 'related': ['男生', '男性', '話題']},
        {'keyword': '疑問', 'popularity': 79, 'related': ['問題', '好奇', '請教']},
        {'keyword': '爆料', 'popularity': 78, 'related': ['分享', '揭露', '秘密']}
    ]
}

# 一般性熱門關鍵字（跨看板）
GENERAL_POPULAR_KEYWORDS = [
    {'keyword': '心得', 'popularity': 99, 'related': ['分享', '經驗', '體驗']},
    {'keyword': '推薦', 'popularity': 98, 'related': ['好用', '分享', '評價']},
    {'keyword': '問題', 'popularity': 97, 'related': ['疑問', '求解', '幫助']},
    {'keyword': '討論', 'popularity': 96, 'related': ['意見', '想法', '交流']},
    {'keyword': '求助', 'popularity': 95, 'related': ['幫忙', '意見', '困擾']},
    {'keyword': '大家', 'popularity': 94, 'related': ['各位', '大家都', '問問']},
    {'keyword': '分享', 'popularity': 93, 'related': ['心得', '推薦', '經驗']},
    {'keyword': '經驗', 'popularity': 91, 'related': ['體驗', '過程', '親身']},
    {'keyword': '想問', 'popularity': 90, 'related': ['請問', '疑問', '好奇']},
    {'keyword': '好奇', 'popularity': 88, 'related': ['想知道', '疑問', '請問']}
]

def preprocess_text(text):
    """
    預處理文本，移除URL、特殊符號等
    """
    # 移除URL
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    # 移除標點符號和特殊字元
    text = re.sub(r'[^\w\s]', '', text)
    return text

def extract_keywords(text, method='mixed', num_keywords=10):
    """
    提取文本中的關鍵詞
    
    參數:
        text (str): 文本內容
        method (str): 'tfidf', 'textrank' 或 'mixed'
        num_keywords (int): 返回的關鍵詞數量
    
    返回:
        list: 關鍵詞列表，每個元素是 (關鍵詞, 權重) 的元組
    """
    text = preprocess_text(text)
    
    if method == 'tfidf':
        # 使用 TF-IDF 算法提取關鍵詞
        keywords = jieba.analyse.extract_tags(text, topK=num_keywords, withWeight=True)
    elif method == 'textrank':
        # 使用 TextRank 算法提取關鍵詞
        keywords = jieba.analyse.textrank(text, topK=num_keywords, withWeight=True)
    else:  # mixed - 結合 TF-IDF 和 TextRank
        # 分別使用兩種方法提取關鍵詞
        tfidf_keywords = jieba.analyse.extract_tags(text, topK=num_keywords*2, withWeight=True)
        textrank_keywords = jieba.analyse.textrank(text, topK=num_keywords*2, withWeight=True)
        
        # 合併兩種方法的結果
        keyword_weights = {}
        
        # TF-IDF 權重，權重 * 0.6
        for word, weight in tfidf_keywords:
            keyword_weights[word] = weight * 0.6
        
        # TextRank 權重，權重 * 0.4 (如果該詞已經在 TF-IDF 中出現，則加權)
        for word, weight in textrank_keywords:
            if word in keyword_weights:
                keyword_weights[word] += weight * 0.4
            else:
                keyword_weights[word] = weight * 0.4
        
        # 排序並選擇前 N 個關鍵詞
        keywords = sorted(keyword_weights.items(), key=lambda x: x[1], reverse=True)[:num_keywords]
    
    # 移除過短的關鍵詞（通常不太有意義）
    filtered_keywords = [(word, weight) for word, weight in keywords if len(word) > 1]
    
    # 如果過濾後的關鍵詞數量不足，再補充一些
    if len(filtered_keywords) < num_keywords and len(keywords) > len(filtered_keywords):
        remaining = [kw for kw in keywords if kw not in filtered_keywords]
        filtered_keywords.extend(remaining[:num_keywords - len(filtered_keywords)])
    
    return filtered_keywords

def get_related_popular_keywords(keywords, category, max_keywords=5):
    """
    根據提取的關鍵詞，推薦相關的熱門關鍵字
    
    參數:
        keywords (list): 提取的關鍵詞列表，每個元素是 (關鍵詞, 權重) 的元組
        category (str): 文章類別 ('mood', 'relationship', 'talk')
        max_keywords (int): 返回的熱門關鍵字數量
    
    返回:
        list: 熱門關鍵字列表，每個元素是一個字典，包含關鍵字和熱門度
    """
    # 獲取特定類別的熱門關鍵字
    category_keywords = POPULAR_KEYWORDS.get(category, [])
    if not category_keywords:
        # 如果沒有特定類別的關鍵字，使用一般性熱門關鍵字
        category_keywords = GENERAL_POPULAR_KEYWORDS
    
    # 將提取的關鍵詞轉換為列表並保留權重
    extracted_keywords_with_weight = {k: w for k, w in keywords}
    extracted_keywords = list(extracted_keywords_with_weight.keys())
    
    # 計算熱門關鍵字與提取關鍵詞的相關度
    keyword_scores = []
    for popular_keyword in category_keywords:
        score = 0
        
        # 檢查熱門關鍵字是否在提取的關鍵詞中
        if popular_keyword['keyword'] in extracted_keywords:
            # 直接匹配給予較高分數，並考慮關鍵詞權重
            keyword_weight = extracted_keywords_with_weight.get(popular_keyword['keyword'], 1.0)
            score += 10 * keyword_weight  # 增加直接匹配的權重
        
        # 檢查相關關鍵詞是否在提取的關鍵詞中
        for related in popular_keyword['related']:
            if related in extracted_keywords:
                # 相關詞匹配給予適中分數，並考慮關鍵詞權重
                keyword_weight = extracted_keywords_with_weight.get(related, 0.5)
                score += 5 * keyword_weight  # 增加相關詞匹配的權重
            
            # 進一步檢查部分匹配（關鍵詞包含情況）
            else:
                for extracted_kw in extracted_keywords:
                    # 如果提取的關鍵詞包含相關詞或相關詞包含提取的關鍵詞
                    if related in extracted_kw or extracted_kw in related:
                        keyword_weight = extracted_keywords_with_weight.get(extracted_kw, 0.3)
                        score += 2 * keyword_weight  # 部分匹配給予較低分數
        
        # 考慮熱門度因素，但降低其權重比例
        popularity_factor = popular_keyword['popularity'] / 100
        
        # 最終得分：關鍵詞匹配得分 * 0.7 + 熱門度 * 0.3
        final_score = (score * 0.7 + popularity_factor * 0.3) if score > 0 else popularity_factor * 0.1
        
        keyword_scores.append({
            'keyword': popular_keyword['keyword'],
            'popularity': popular_keyword['popularity'],
            'score': final_score,
            'related': popular_keyword['related']
        })
    
    # 根據得分排序
    keyword_scores.sort(key=lambda x: x['score'], reverse=True)
    
    # 如果沒有足夠的相關熱門關鍵字，添加一些基於類別相關的熱門關鍵字
    if len([k for k in keyword_scores if k['score'] > 0.1]) < max_keywords:
        additional_keywords = [k for k in category_keywords if k['keyword'] not in [x['keyword'] for x in keyword_scores[:max_keywords]]]
        # 根據熱門度排序
        additional_keywords.sort(key=lambda x: x['popularity'], reverse=True)
        # 加入一定數量的額外關鍵字
        for kw in additional_keywords[:max_keywords - len([k for k in keyword_scores if k['score'] > 0.1])]:
            keyword_scores.append({
                'keyword': kw['keyword'],
                'popularity': kw['popularity'],
                'score': 0.05,  # 給予較低的得分
                'related': kw['related']
            })
        # 重新排序
        keyword_scores.sort(key=lambda x: x['score'], reverse=True)
    
    # 返回推薦的熱門關鍵字
    result = keyword_scores[:max_keywords]
    
    # 確保返回的關鍵字是唯一的
    seen_keywords = set()
    unique_result = []
    for item in result:
        if item['keyword'] not in seen_keywords:
            seen_keywords.add(item['keyword'])
            unique_result.append({
                'keyword': item['keyword'],
                'popularity': item['popularity'],
                'related': item['related']
            })
    
    return unique_result

def generate_hot_keywords(text, category, max_extracted=15, max_recommended=5):
    """
    從文本中提取關鍵詞並推薦熱門關鍵字
    
    參數:
        text (str): 文本內容
        category (str): 文章類別 ('mood', 'relationship', 'talk')
        max_extracted (int): 從文本中提取的關鍵詞數量
        max_recommended (int): 推薦的熱門關鍵字數量
    
    返回:
        dict: 包含提取的關鍵詞和推薦的熱門關鍵字
    """
    try:
        # 使用混合方法提取關鍵詞 (結合 TF-IDF 和 TextRank)
        keywords = extract_keywords(text, method='mixed', num_keywords=max_extracted)
        
        # 獲取推薦的熱門關鍵字
        recommended_keywords = get_related_popular_keywords(
            keywords, 
            category, 
            max_keywords=max_recommended
        )
        
        # 獲取原始提取的關鍵詞（僅包含詞彙，不包含權重）
        extracted_keywords = [k for k, _ in keywords[:10]]
        
        return {
            'extracted_keywords': extracted_keywords,
            'recommended_hot_keywords': recommended_keywords
        }
    
    except Exception as e:
        logger.error(f"生成熱門關鍵字時發生錯誤: {str(e)}")
        # 返回一些默認關鍵字
        default_keywords = [k['keyword'] for k in GENERAL_POPULAR_KEYWORDS[:max_recommended]]
        return {
            'extracted_keywords': [],
            'recommended_hot_keywords': [
                {
                    'keyword': kw,
                    'popularity': 80 + random.randint(0, 15),
                    'related': []
                } for kw in default_keywords
            ]
        }

# 示例用法
if __name__ == "__main__":
    test_text = """
    最近和男友吵架，他說我們之間的溝通有問題，總是無法理解對方的想法。
    我很愛他，但這種溝通不良的情況讓我感到很沮喪。我們在一起三年了，
    這類的問題似乎越來越頻繁，不知道該怎麼解決。有人有類似的經驗嗎？
    """
    
    result = generate_hot_keywords(test_text, 'relationship')
    print("提取的關鍵詞:")
    for keyword in result['extracted_keywords']:
        print(f"- {keyword}")
    
    print("\n推薦的熱門關鍵字:")
    for keyword in result['recommended_hot_keywords']:
        print(f"- {keyword['keyword']} (熱門度: {keyword['popularity']}%)")
        print(f"  相關詞: {', '.join(keyword['related'])}") 