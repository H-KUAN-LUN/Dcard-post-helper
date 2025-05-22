# Dcard文章分類器

這是一個基於機器學習的Dcard文章分類系統，可以自動判斷文章應該發布在哪個看板（心情、感情、閒聊）。

## 功能特點

- 使用集成學習方法（投票分類器）結合多個機器學習模型
- 提供直觀的網頁介面
- 即時顯示分類結果和各類別機率
- 支援中文文本處理
- 響應式設計，支援手機瀏覽

## 系統需求

- Python 3.8+
- 相關Python套件（見requirements.txt）

## 安裝步驟

1. 克隆專案：
```bash
git clone [專案URL]
cd [專案目錄]
```

2. 安裝所需套件：
```bash
pip install -r requirements.txt
```

3. 確保模型檔案存在：
- voting_classifier_model.joblib
- tfidf_vectorizer.joblib

## 使用方法

1. 啟動Flask應用：
```bash
python app.py
```

2. 打開瀏覽器訪問：
```
http://localhost:5000
```

3. 在文字框中輸入文章內容，點擊「分析文章」按鈕

4. 系統會顯示：
   - 建議發布的看板
   - 各類別的預測機率

## 技術實現細節

### 1. 資料前處理流程

#### 1.1 文本清理
- 移除URL：使用正則表達式 `re.sub(r'http\S+|www\S+|https\S+', '', text)`
- 移除標點符號：使用正則表達式 `re.sub(r'[^\w\s]', '', text)`
- 使用jieba進行中文分詞

#### 1.2 特徵工程
- 使用TF-IDF向量化文本
  - 最大特徵數：5000
  - 使用jieba分詞結果作為輸入

### 2. 模型訓練

#### 2.1 基礎分類器
1. 邏輯迴歸（Logistic Regression）
2. 決策樹（Decision Tree）
3. 支持向量機（SVM）
4. 隨機森林（Random Forest）

#### 2.2 集成學習
- 使用軟投票（Soft Voting）策略
- 結合四個基礎分類器的預測結果

#### 2.3 模型評估
- 使用分類報告（classification_report）評估
- 評估指標：
  - 準確率（Accuracy）
  - 精確率（Precision）
  - 召回率（Recall）
  - F1分數

### 3. 模型部署

#### 3.1 模型保存
- 使用joblib保存模型和向量化器
- 保存檔案：
  - voting_classifier_model.joblib
  - tfidf_vectorizer.joblib

#### 3.2 Web應用
- 使用Flask框架提供Web服務
- 提供RESTful API接口
- 使用Bootstrap實現響應式前端界面

## 專案結構

```
project/
├── app.py              # Flask應用主程式
├── requirements.txt    # 依賴套件清單
├── templates/          # HTML模板
│   └── index.html     # 主頁面
├── models/            # 模型檔案
│   ├── voting_classifier_model.joblib
│   └── tfidf_vectorizer.joblib
└── README.md          # 說明文件
```

## 技術細節

- 前端：HTML, CSS, JavaScript, Bootstrap 5
- 後端：Flask
- 機器學習：scikit-learn
- 中文處理：jieba
- 數據處理：pandas, numpy

## 未來改進方向

1. 添加更多分類器
2. 優化特徵工程
3. 實現模型自動更新
4. 添加用戶反饋機制
5. 支援更多看板分類

## 注意事項

- 確保模型檔案和應用程式在同一目錄下
- 建議在虛擬環境中運行專案
- 首次運行時需要下載jieba的詞典檔案
