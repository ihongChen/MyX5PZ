# X5指標運算邏輯

###### tags: `二階筆記`,`指標計算`

# 目的
由列印日績效檔案(`PL-3001_YM_1_60_1_0.txt`)，整理(單/多)策略商品在不同`riskR`下的淨值曲線，重現X5指標結果，用以理解x5指標計算邏輯。

# 問題
結果並==不完全相同==(趨勢接近但有誤差，組合誤差更大)，如下:
- 績效檔 `PL-3001_YM_1_60_1_0.txt`
- riskR = 0.01 

![](https://i.imgur.com/6Z9gxtV.png)
![](https://i.imgur.com/JFtQMAc.png)

> 我的計算邏輯(橘線),X5表單跑出結果(藍線)
# 計算步驟

整檔[口數管理輸出與淨值計算.xlsx](https://drive.google.com/open?id=1CE7FAIRq0_5u3HjNqgazh60AEcg8q7Bi)，相關程式碼請看附件[^first]

[^first]: 程式與文件在[這裡](https://github.com/ihongChen/MyX5PZ)

1. 藉由` python portfolio-eval.py` 整檔同一目錄下之`PL-3001_YM_1_60_0.txt`匯出成csv檔`portfolio-test.csv`
2. 其中python整檔邏輯如下
    - 讀取txt檔資料 (A欄~H欄)
        - 依序為 
            - (A欄) 日期  (後接`=`)
            - (B欄) 未平倉損益/(ATR金額) (後接 `_`)
            - (C欄) 未平倉單進場的前一天(Session Day) (後接 `#`)
            - (D欄) 本日出場次數 (後接`#`)
            - (E欄) 已平倉金額/(ATR金額) (後接 `_`)
            - (F欄) 已平倉單進場的前一天(Session Day) 
                > 若本日有大於一筆出場，則重複 (E,F)於後面欄位 (G,H)
                
3. 由`portfolio-test.csv`中 A欄~H欄，複製於Excel檔中 **口數管理輸出與淨值計算計算.xlsx** 

4. (製作I欄) **已平倉byATR**
    =  (E欄) + (G欄) = 已平倉的實現損益 = sum(當日出場的實現損益)
    
5. (製作J欄) **已平倉累加byATR** 
    = 加總到目前日期為止之已平倉實現之獲利
    = sum(I2:I當前列)
    
6. (製作K欄) **(1+已平倉\*riskR)**
    已實現損益(獲利倍數) = (1+ J欄 * riskR<$O$2>)
7. (製作L欄) **X5計算**
    由X5指標表單匯出單商品`PL-3001_YM_1_60_1_0.txt`之績效
透過vlookup對齊日期相對應的淨值
8. (製作M欄) ==**未平倉驗算**==(比較結果)
    已實現損益 + 當日未平倉損益 = K欄 + B欄\*riskR<$O$2>

(note:步驟 3~8由[.py](https://github.com/ihongChen/MyX5PZ/blob/master/portfolio-eval.py#L65-L92)的`cal_profit`實現)
# 比較
### 單一價格圖 
L欄 vs M欄
![](https://i.imgur.com/VbjtAp9.png)
誤差約1.5%


### 四種價格圖 [^second]

[^second]:  由[.py檔](https://github.com/ihongChen/MyX5PZ/blob/master/portfolio-eval.py#L137-L146)算出

取用績效檔: 


| 績效檔  | 風險值(riskR) |
| -------- | -------- |
| PL-3001_NQ_1_60_1_0.txt     | 0.01     | 
|PL-3001_NQ_1_480_1_0.txt|0.01|
|PL-3001_YM_1_60_1_0.txt|0.01|
|PL-3001_YM_1_240_1_0.txt|0.01|

測試結果:

淨值曲線
![](https://i.imgur.com/4ynBxAz.png)

![](https://i.imgur.com/kt8tAcd.png)

誤差約25%

## 提問

注意到X5表單裡面輸出之精度為==小數後四位==

![](https://i.imgur.com/olrKQYu.png)

Q1. 誤差來源是否可能為此?
Q2. (或)上述計算邏輯有誤?

>(x5回覆) 
> 
> 你提到的小數點精位數可能是一個問題,但不該有這麼大的影響. 
> 事實上, 小數點誤差一定會存在,而且更大,因為我們只能用整數口數來交易 
 
> 在超五團隊的開發流程中,會有一個作業是比對指標算出來的報酬率與TS回測出來的差異
誤差要小於一定數值內(<3% or <5%) 

> X5指標不是一個固定式的計算程式
而是一個規則式(rule-base)的測試平台
有GUI可以依照使用者的偏好來調整測試規則與參數

>在你的分析報告中
我只看到RiskR設定的數值
那就暫且假設其他參數都用預設值
請留意指標參數中有一個ResetDays =365
它的意思是每隔365天會重置組合淨值
這是一階課程1003資金管理提到的Equity reset model
透過它會有年複利的概念

>請你依此修正你的計算方式,再比對看看

# (修正)加入資產重置`ResetDays`邏輯


### 四張價格圖
- ResetDays = 365

| 績效檔  | 風險值(riskR) | 
| -------- | -------- |
| PL-3001_NQ_1_60_1_0.txt     | 0.01     | 
|PL-3001_NQ_1_480_1_0.txt|0.01|
|PL-3001_YM_1_60_1_0.txt|0.01|
|PL-3001_YM_1_240_1_0.txt|0.01|

#### 實驗結果

![](https://i.imgur.com/otzsGql.png)
