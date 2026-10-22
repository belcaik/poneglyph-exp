# SpanReader v1 Diagnostics

## Diagnostic 1: Character-to-Token Alignment

### Sentence 0: `このまま逃げてても 埒(らち)が明かねえな`

**Tokenization:**
```
  Token 0: [CLS] -> chars: none (special)
  Token 1: "この" -> chars 0-1 "この"
  Token 2: "まま" -> chars 2-3 "まま"
  Token 3: "逃げ" -> chars 4-5 "逃げ"
  Token 4: "て" -> chars 6-6 "て"
  Token 5: "て" -> chars 7-7 "て"
  Token 6: "も" -> chars 8-8 "も"
  Token 7: "▁" -> chars 9-9 " "
  Token 8: "<0xE5>" -> chars 10-10 "埒"
  Token 9: "<0x9F>" -> chars 10-10 "埒"
  Token 10: "<0x92>" -> chars 10-10 "埒"
  Token 11: "(" -> chars 11-11 "("
  Token 12: "らち" -> chars 12-13 "らち"
  Token 13: ")" -> chars 14-14 ")"
  Token 14: "が" -> chars 15-15 "が"
  Token 15: "明か" -> chars 16-17 "明か"
  Token 16: "ねえ" -> chars 18-19 "ねえ"
  Token 17: "な" -> chars 20-20 "な"
  Token 18: [SEP] -> chars: none (special)
```

**Char-to-token map:** `[1, 1, 2, 2, 3, 3, 4, 5, 6, 7, 10, 11, 12, 12, 13, 14, 15, 15, 16, 16, 17]`

- Span `逃げてても` (chars 4-8): actual=`逃げてても` tokens=[3, 4, 5, 6] **OK**
- Span `埒` (chars 10-10): actual=`埒` tokens=[10] **OK**
- Span `明かねえ` (chars 16-19): actual=`明かねえ` tokens=[15, 16] **OK**

### Sentence 1: `フリクションロスは少ないほど ギアはよく回ります`

**Tokenization:**
```
  Token 0: [CLS] -> chars: none (special)
  Token 1: "フリクション" -> chars 0-5 "フリクション"
  Token 2: "ロス" -> chars 6-7 "ロス"
  Token 3: "は" -> chars 8-8 "は"
  Token 4: "少" -> chars 9-9 "少"
  Token 5: "ない" -> chars 10-11 "ない"
  Token 6: "ほど" -> chars 12-13 "ほど"
  Token 7: "▁" -> chars 14-14 " "
  Token 8: "ギア" -> chars 15-16 "ギア"
  Token 9: "は" -> chars 17-17 "は"
  Token 10: "よく" -> chars 18-19 "よく"
  Token 11: "回り" -> chars 20-21 "回り"
  Token 12: "ます" -> chars 22-23 "ます"
  Token 13: [SEP] -> chars: none (special)
```

**Char-to-token map:** `[1, 1, 1, 1, 1, 1, 2, 2, 3, 4, 5, 5, 6, 6, 7, 8, 8, 9, 10, 10, 11, 11, 12, 12]`

- Span `少ない` (chars 9-11): actual=`少ない` tokens=[4, 5] **OK**
- Span `回ります` (chars 20-23): actual=`回ります` tokens=[11, 12] **OK**

### Sentence 2: `さて ここからが話の メインユニットです`

**Tokenization:**
```
  Token 0: [CLS] -> chars: none (special)
  Token 1: "さて" -> chars 0-1 "さて"
  Token 2: "▁" -> chars 2-2 " "
  Token 3: "ここ" -> chars 3-4 "ここ"
  Token 4: "から" -> chars 5-6 "から"
  Token 5: "が" -> chars 7-7 "が"
  Token 6: "話" -> chars 8-8 "話"
  Token 7: "の" -> chars 9-9 "の"
  Token 8: "▁" -> chars 10-10 " "
  Token 9: "メイン" -> chars 11-13 "メイン"
  Token 10: "ユニット" -> chars 14-17 "ユニット"
  Token 11: "です" -> chars 18-19 "です"
  Token 12: [SEP] -> chars: none (special)
```

**Char-to-token map:** `[1, 1, 2, 3, 3, 4, 4, 5, 6, 7, 8, 9, 9, 9, 10, 10, 10, 10, 11, 11]`

- Span `話` (chars 8-8): actual=`話` tokens=[6] **OK**

### Sentence 3: `ナミさ〜ん！ クソ剣士 お前なんとかしろ！`

**Tokenization:**
```
  Token 0: [CLS] -> chars: none (special)
  Token 1: "ナミ" -> chars 0-1 "ナミ"
  Token 2: "さ" -> chars 2-2 "さ"
  Token 3: "〜" -> chars 3-3 "〜"
  Token 4: "ん" -> chars 4-4 "ん"
  Token 5: "！" -> chars 5-5 "！"
  Token 6: "▁" -> chars 6-6 " "
  Token 7: "クソ" -> chars 7-8 "クソ"
  Token 8: "剣" -> chars 9-9 "剣"
  Token 9: "士" -> chars 10-10 "士"
  Token 10: "▁" -> chars 11-11 " "
  Token 11: "お" -> chars 12-12 "お"
  Token 12: "前" -> chars 13-13 "前"
  Token 13: "なんとか" -> chars 14-17 "なんとか"
  Token 14: "しろ" -> chars 18-19 "しろ"
  Token 15: "！" -> chars 20-20 "！"
  Token 16: [SEP] -> chars: none (special)
```

**Char-to-token map:** `[1, 1, 2, 3, 4, 5, 6, 7, 7, 8, 9, 10, 11, 12, 13, 13, 13, 13, 14, 14, 15]`

- Span `剣士` (chars 9-10): actual=`剣士` tokens=[8, 9] **OK**
- Span `前` (chars 13-13): actual=`前` tokens=[12] **OK**

### Sentence 4: `回転斧(おの)〜！`

**Tokenization:**
```
  Token 0: [CLS] -> chars: none (special)
  Token 1: "回転" -> chars 0-1 "回転"
  Token 2: "斧" -> chars 2-2 "斧"
  Token 3: "(" -> chars 3-3 "("
  Token 4: "おの" -> chars 4-5 "おの"
  Token 5: ")" -> chars 6-6 ")"
  Token 6: "〜" -> chars 7-7 "〜"
  Token 7: "！" -> chars 8-8 "！"
  Token 8: [SEP] -> chars: none (special)
```

**Char-to-token map:** `[1, 1, 2, 3, 4, 4, 5, 6, 7]`

- Span `回転` (chars 0-1): actual=`回転` tokens=[1] **OK**
- Span `斧` (chars 2-2): actual=`斧` tokens=[2] **OK**

### Sentence 5: `制御不能って どういうこと!?`

**Tokenization:**
```
  Token 0: [CLS] -> chars: none (special)
  Token 1: "制御" -> chars 0-1 "制御"
  Token 2: "不能" -> chars 2-3 "不能"
  Token 3: "って" -> chars 4-5 "って"
  Token 4: "▁" -> chars 6-6 " "
  Token 5: "どういう" -> chars 7-10 "どういう"
  Token 6: "こと" -> chars 11-12 "こと"
  Token 7: "!?" -> chars 13-14 "!?"
  Token 8: [SEP] -> chars: none (special)
```

**Char-to-token map:** `[1, 1, 2, 2, 3, 3, 4, 5, 5, 5, 5, 6, 6, 7, 7]`

- Span `制御不能` (chars 0-3): actual=`制御不能` tokens=[1, 2] **OK**

### Sentence 6: `ああ！ あの旗印は！`

**Tokenization:**
```
  Token 0: [CLS] -> chars: none (special)
  Token 1: "ああ" -> chars 0-1 "ああ"
  Token 2: "！" -> chars 2-2 "！"
  Token 3: "▁" -> chars 3-3 " "
  Token 4: "あの" -> chars 4-5 "あの"
  Token 5: "旗" -> chars 6-6 "旗"
  Token 6: "印" -> chars 7-7 "印"
  Token 7: "は" -> chars 8-8 "は"
  Token 8: "！" -> chars 9-9 "！"
  Token 9: [SEP] -> chars: none (special)
```

**Char-to-token map:** `[1, 1, 2, 3, 4, 4, 5, 6, 7, 8]`

- Span `旗印` (chars 6-7): actual=`旗印` tokens=[5, 6] **OK**

### Sentence 7: `おう こら 今なんつった ああ？`

**Tokenization:**
```
  Token 0: [CLS] -> chars: none (special)
  Token 1: "おう" -> chars 0-1 "おう"
  Token 2: "▁" -> chars 2-2 " "
  Token 3: "こら" -> chars 3-4 "こら"
  Token 4: "▁" -> chars 5-5 " "
  Token 5: "今" -> chars 6-6 "今"
  Token 6: "なん" -> chars 7-8 "なん"
  Token 7: "つ" -> chars 9-9 "つ"
  Token 8: "った" -> chars 10-11 "った"
  Token 9: "▁" -> chars 12-12 " "
  Token 10: "ああ" -> chars 13-14 "ああ"
  Token 11: "？" -> chars 15-15 "？"
  Token 12: [SEP] -> chars: none (special)
```

**Char-to-token map:** `[1, 1, 2, 3, 3, 4, 5, 6, 6, 7, 8, 8, 9, 10, 10, 11]`

- Span `今` (chars 6-6): actual=`今` tokens=[5] **OK**

### Sentence 8: `“飲み干す時”じゃなくて “飲み干すトキ”って…`

**Tokenization:**
```
  Token 0: [CLS] -> chars: none (special)
  Token 1: "“" -> chars 0-0 "“"
  Token 2: "飲み干" -> chars 1-3 "飲み干"
  Token 3: "す" -> chars 4-4 "す"
  Token 4: "時" -> chars 5-5 "時"
  Token 5: "”" -> chars 6-6 "”"
  Token 6: "じゃ" -> chars 7-8 "じゃ"
  Token 7: "なく" -> chars 9-10 "なく"
  Token 8: "て" -> chars 11-11 "て"
  Token 9: "▁“" -> chars 12-13 " “"
  Token 10: "飲み干" -> chars 14-16 "飲み干"
  Token 11: "す" -> chars 17-17 "す"
  Token 12: "トキ" -> chars 18-19 "トキ"
  Token 13: "”" -> chars 20-20 "”"
  Token 14: "って" -> chars 21-22 "って"
  Token 15: "…" -> chars 23-23 "…"
  Token 16: [SEP] -> chars: none (special)
```

**Char-to-token map:** `[1, 2, 2, 2, 3, 4, 5, 6, 6, 7, 7, 8, 9, 9, 10, 10, 10, 11, 12, 12, 13, 14, 14, 15]`

- Span `飲み干す` (chars 1-4): actual=`飲み干す` tokens=[2, 3] **OK**
- Span `時` (chars 5-5): actual=`時` tokens=[4] **OK**
- Span `飲み干す` (chars 14-17): actual=`飲み干す` tokens=[10, 11] **OK**

### Sentence 9: `まあ 結果 騙したようなもんじゃな すまなんだ`

**Tokenization:**
```
  Token 0: [CLS] -> chars: none (special)
  Token 1: "まあ" -> chars 0-1 "まあ"
  Token 2: "▁" -> chars 2-2 " "
  Token 3: "結果" -> chars 3-4 "結果"
  Token 4: "▁" -> chars 5-5 " "
  Token 5: "騙" -> chars 6-6 "騙"
  Token 6: "した" -> chars 7-8 "した"
  Token 7: "よう" -> chars 9-10 "よう"
  Token 8: "な" -> chars 11-11 "な"
  Token 9: "も" -> chars 12-12 "も"
  Token 10: "んじゃ" -> chars 13-15 "んじゃ"
  Token 11: "な" -> chars 16-16 "な"
  Token 12: "▁" -> chars 17-17 " "
  Token 13: "すま" -> chars 18-19 "すま"
  Token 14: "なん" -> chars 20-21 "なん"
  Token 15: "だ" -> chars 22-22 "だ"
  Token 16: [SEP] -> chars: none (special)
```

**Char-to-token map:** `[1, 1, 2, 3, 3, 4, 5, 6, 6, 7, 7, 8, 9, 10, 10, 10, 11, 12, 13, 13, 14, 14, 15]`

- Span `結果` (chars 3-4): actual=`結果` tokens=[3] **OK**
- Span `騙した` (chars 6-8): actual=`騙した` tokens=[5, 6] **OK**

**Verdict:** PASS — 0 issues in 45 total span characters

## Diagnostic 2: Position Head Predictions

### Sentence 0: `このまま逃げてても 埒(らち)が明かねえな`

**Gold spans:** [(4, 8), (10, 10), (16, 19)]

- **Q29** (exists=0.97): start=[0.50@5, 0.50@4, 0.00@6] end=[1.00@8, 0.00@7, 0.00@6] → (4,8) `逃げてても` 
- **Q11** (exists=0.91): start=[0.50@17, 0.50@16, 0.00@15] end=[0.50@19, 0.50@18, 0.00@20] → (16,18) `明かね` 
- **Q27** (exists=0.44): start=[1.00@10, 0.00@5, 0.00@4] end=[1.00@10, 0.00@13, 0.00@12] → (10,10) `埒` 
- **Q16** (exists=0.19): start=[0.50@5, 0.50@4, 0.00@10] end=[1.00@10, 0.00@6, 0.00@8] → (4,10) `逃げてても 埒` 
- **Q28** (exists=0.10): start=[0.50@17, 0.50@16, 0.00@20] end=[1.00@20, 0.00@17, 0.00@16] → (16,20) `明かねえな` 
- **Q9** (exists=0.08): start=[0.50@17, 0.50@16, 0.00@15] end=[0.50@17, 0.50@16, 0.00@18] → (16,16) `明` 

### Sentence 1: `フリクションロスは少ないほど ギアはよく回ります`

**Gold spans:** [(9, 11), (20, 23)]

- **Q29** (exists=0.98): start=[1.00@9, 0.00@11, 0.00@10] end=[0.50@11, 0.50@10, 0.00@9] → (9,10) `少な` 
- **Q11** (exists=0.96): start=[0.50@21, 0.50@20, 0.00@18] end=[0.50@23, 0.50@22, 0.00@20] → (20,22) `回りま` 
- **Q16** (exists=0.08): start=[1.00@9, 0.00@1, 0.00@0] end=[0.50@11, 0.50@10, 0.00@9] → (9,10) `少な` 
- **Q28** (exists=0.02): start=[0.50@21, 0.50@20, 0.00@18] end=[0.50@23, 0.50@22, 0.00@18] → (20,22) `回りま` 
- **Q23** (exists=0.00): start=[1.00@9, 0.00@21, 0.00@20] end=[1.00@9, 0.00@11, 0.00@10] → (9,9) `少` 
- **Q8** (exists=0.00): start=[1.00@9, 0.00@13, 0.00@12] end=[0.50@13, 0.50@12, 0.00@9] → (9,12) `少ないほ` 

### Sentence 2: `さて ここからが話の メインユニットです`

**Gold spans:** [(8, 8)]

- **Q16** (exists=0.99): start=[1.00@8, 0.00@9, 0.00@7] end=[1.00@8, 0.00@7, 0.00@9] → (8,8) `話` 
- **Q9** (exists=0.01): start=[0.33@13, 0.33@12, 0.33@11] end=[0.25@16, 0.25@15, 0.25@14] → (11,14) `メインユ` 
- **Q27** (exists=0.00): start=[0.33@13, 0.33@12, 0.33@11] end=[0.19@6, 0.19@5, 0.15@14] → (11,5) `` SWAPPED
- **Q28** (exists=0.00): start=[0.33@13, 0.33@12, 0.33@11] end=[0.25@16, 0.25@15, 0.25@14] → (11,14) `メインユ` 
- **Q7** (exists=0.00): start=[0.33@13, 0.33@12, 0.33@11] end=[0.27@13, 0.27@12, 0.27@11] → (11,11) `メ` 
- **Q23** (exists=0.00): start=[1.00@8, 0.00@9, 0.00@0] end=[1.00@8, 0.00@9, 0.00@7] → (8,8) `話` 

### Sentence 3: `ナミさ〜ん！ クソ剣士 お前なんとかしろ！`

**Gold spans:** [(9, 10), (13, 13)]

- **Q16** (exists=1.00): start=[1.00@9, 0.00@10, 0.00@2] end=[1.00@10, 0.00@9, 0.00@4] → (9,10) `剣士` 
- **Q9** (exists=0.47): start=[1.00@12, 0.00@13, 0.00@7] end=[1.00@13, 0.00@15, 0.00@14] → (12,13) `お前` 
- **Q8** (exists=0.27): start=[1.00@13, 0.00@12, 0.00@7] end=[1.00@13, 0.00@12, 0.00@14] → (13,13) `前` 
- **Q29** (exists=0.09): start=[1.00@12, 0.00@13, 0.00@9] end=[1.00@13, 0.00@15, 0.00@14] → (12,13) `お前` 
- **Q17** (exists=0.03): start=[1.00@13, 0.00@12, 0.00@18] end=[1.00@13, 0.00@15, 0.00@14] → (13,13) `前` 
- **Q27** (exists=0.02): start=[1.00@9, 0.00@10, 0.00@12] end=[1.00@10, 0.00@13, 0.00@9] → (9,10) `剣士` 

### Sentence 4: `回転斧(おの)〜！`

**Gold spans:** [(0, 1), (2, 2)]

- **Q16** (exists=0.99): start=[0.50@1, 0.50@0, 0.00@2] end=[0.54@2, 0.23@1, 0.23@0] → (0,2) `回転斧` 
- **Q9** (exists=0.08): start=[1.00@2, 0.00@1, 0.00@0] end=[1.00@2, 0.00@1, 0.00@0] → (2,2) `斧` 
- **Q8** (exists=0.02): start=[0.49@1, 0.49@0, 0.01@2] end=[0.99@2, 0.00@1, 0.00@0] → (0,2) `回転斧` 
- **Q27** (exists=0.01): start=[0.50@1, 0.50@0, 0.00@2] end=[1.00@2, 0.00@1, 0.00@0] → (0,2) `回転斧` 
- **Q28** (exists=0.00): start=[0.49@1, 0.49@0, 0.03@2] end=[0.48@5, 0.48@4, 0.03@6] → (0,4) `回転斧(お` 
- **Q11** (exists=0.00): start=[0.50@1, 0.50@0, 0.00@2] end=[0.48@5, 0.48@4, 0.03@6] → (0,4) `回転斧(お` 

### Sentence 5: `制御不能って どういうこと!?`

**Gold spans:** [(0, 3)]

- **Q16** (exists=0.99): start=[0.50@1, 0.50@0, 0.00@2] end=[0.50@3, 0.50@2, 0.00@0] → (0,2) `制御不` 
- **Q9** (exists=0.01): start=[0.50@1, 0.50@0, 0.00@2] end=[0.50@3, 0.50@2, 0.00@0] → (0,2) `制御不` 
- **Q27** (exists=0.01): start=[0.50@1, 0.50@0, 0.00@2] end=[0.50@3, 0.50@2, 0.00@0] → (0,2) `制御不` 
- **Q8** (exists=0.00): start=[0.50@1, 0.50@0, 0.00@2] end=[0.50@1, 0.50@0, 0.00@2] → (0,0) `制` 
- **Q28** (exists=0.00): start=[0.50@1, 0.50@0, 0.00@2] end=[0.94@6, 0.02@5, 0.02@4] → (0,6) `制御不能って ` 
- **Q0** (exists=0.00): start=[0.50@1, 0.50@0, 0.00@2] end=[0.50@1, 0.50@0, 0.00@6] → (0,0) `制` 

### Sentence 6: `ああ！ あの旗印は！`

**Gold spans:** [(6, 7)]

- **Q16** (exists=0.99): start=[1.00@6, 0.00@7, 0.00@3] end=[1.00@7, 0.00@6, 0.00@2] → (6,7) `旗印` 
- **Q9** (exists=0.00): start=[1.00@6, 0.00@7, 0.00@2] end=[1.00@7, 0.00@6, 0.00@9] → (6,7) `旗印` 
- **Q27** (exists=0.00): start=[1.00@6, 0.00@7, 0.00@0] end=[1.00@7, 0.00@6, 0.00@8] → (6,7) `旗印` 
- **Q28** (exists=0.00): start=[0.81@7, 0.18@6, 0.00@0] end=[1.00@9, 0.00@3, 0.00@8] → (7,9) `印は！` 
- **Q8** (exists=0.00): start=[0.96@6, 0.04@7, 0.00@0] end=[1.00@6, 0.00@9, 0.00@4] → (6,6) `旗` 
- **Q0** (exists=0.00): start=[1.00@3, 0.00@2, 0.00@6] end=[1.00@6, 0.00@3, 0.00@9] → (3,6) ` あの旗` 

### Sentence 7: `おう こら 今なんつった ああ？`

**Gold spans:** [(6, 6)]

- **Q16** (exists=0.98): start=[1.00@6, 0.00@5, 0.00@2] end=[1.00@6, 0.00@8, 0.00@7] → (6,6) `今` 
- **Q28** (exists=0.00): start=[0.50@8, 0.50@7, 0.00@3] end=[0.50@11, 0.50@10, 0.00@7] → (7,10) `なんつっ` 
- **Q23** (exists=0.00): start=[1.00@6, 0.00@1, 0.00@0] end=[1.00@6, 0.00@8, 0.00@7] → (6,6) `今` 
- **Q17** (exists=0.00): start=[1.00@6, 0.00@8, 0.00@7] end=[1.00@6, 0.00@8, 0.00@7] → (6,6) `今` 
- **Q9** (exists=0.00): start=[0.50@8, 0.50@7, 0.00@3] end=[0.50@11, 0.50@10, 0.00@7] → (7,10) `なんつっ` 
- **Q12** (exists=0.00): start=[1.00@6, 0.00@8, 0.00@7] end=[1.00@6, 0.00@8, 0.00@7] → (6,6) `今` 

### Sentence 8: `“飲み干す時”じゃなくて “飲み干すトキ”って…`

**Gold spans:** [(1, 4), (5, 5), (14, 17)]

- **Q16** (exists=0.98): start=[1.00@5, 0.00@11, 0.00@4] end=[1.00@5, 0.00@11, 0.00@23] → (5,5) `時` 
- **Q11** (exists=0.96): start=[0.33@16, 0.33@15, 0.33@14] end=[1.00@17, 0.00@4, 0.00@0] → (14,17) `飲み干す` 
- **Q29** (exists=0.82): start=[0.33@3, 0.33@2, 0.33@1] end=[1.00@4, 0.00@2, 0.00@1] → (1,4) `飲み干す` 
- **Q28** (exists=0.01): start=[0.33@16, 0.33@15, 0.33@14] end=[0.27@16, 0.27@15, 0.27@14] → (14,14) `飲` 
- **Q9** (exists=0.00): start=[0.33@16, 0.33@15, 0.33@14] end=[1.00@17, 0.00@20, 0.00@14] → (14,17) `飲み干す` 
- **Q27** (exists=0.00): start=[0.33@3, 0.33@2, 0.33@1] end=[1.00@4, 0.00@2, 0.00@1] → (1,4) `飲み干す` 

### Sentence 9: `まあ 結果 騙したようなもんじゃな すまなんだ`

**Gold spans:** [(3, 4), (6, 8)]

- **Q16** (exists=0.99): start=[0.50@4, 0.50@3, 0.00@2] end=[0.50@4, 0.50@3, 0.00@5] → (3,3) `結` 
- **Q11** (exists=0.92): start=[1.00@6, 0.00@8, 0.00@7] end=[0.50@8, 0.50@7, 0.00@9] → (6,7) `騙し` 
- **Q28** (exists=0.01): start=[1.00@6, 0.00@19, 0.00@18] end=[1.00@16, 0.00@11, 0.00@22] → (6,16) `騙したようなもんじゃな` 
- **Q9** (exists=0.00): start=[1.00@6, 0.00@19, 0.00@18] end=[1.00@11, 0.00@16, 0.00@13] → (6,11) `騙したような` 
- **Q24** (exists=0.00): start=[1.00@6, 0.00@11, 0.00@18] end=[1.00@11, 0.00@14, 0.00@13] → (6,11) `騙したような` 
- **Q6** (exists=0.00): start=[1.00@6, 0.00@4, 0.00@3] end=[1.00@11, 0.00@10, 0.00@9] → (6,11) `騙したような` 

**Summary over 10 sentences:**
- Correct spans: 8/18
- Off-by-one: 7/18
- Diffuse predictions (max_prob < 0.15): 0
- Start > End: 1

**Diagnosis:** Position heads working but imprecise.

## Diagnostic 3: Hungarian Matching Stability

### Sentence 0: `このまま逃げてても 埒(らち)が明かねえな...`

Gold spans: 3

| Gold # | Gold Pos | Matched Query | Cost | Query Exists Prob |
|--------|----------|--------------|------|------------------|
| 2 | (16,19) | Q11 | 7.13 | 0.914 |
| 1 | (10,10) | Q27 | 2.64 | 0.442 |
| 0 | (4,8) | Q29 | 3.54 | 0.966 |

### Sentence 1: `フリクションロスは少ないほど ギアはよく回ります...`

Gold spans: 2

| Gold # | Gold Pos | Matched Query | Cost | Query Exists Prob |
|--------|----------|--------------|------|------------------|
| 1 | (20,23) | Q11 | 7.01 | 0.961 |
| 0 | (9,11) | Q29 | 3.52 | 0.975 |

### Sentence 2: `さて ここからが話の メインユニットです...`

Gold spans: 1

| Gold # | Gold Pos | Matched Query | Cost | Query Exists Prob |
|--------|----------|--------------|------|------------------|
| 0 | (8,8) | Q16 | 0.01 | 0.995 |

### Sentence 3: `ナミさ〜ん！ クソ剣士 お前なんとかしろ！...`

Gold spans: 2

| Gold # | Gold Pos | Matched Query | Cost | Query Exists Prob |
|--------|----------|--------------|------|------------------|
| 1 | (13,13) | Q8 | 2.60 | 0.274 |
| 0 | (9,10) | Q16 | 0.01 | 0.996 |

Unmatched queries with exists>0.3: [(9, '0.47')]

### Sentence 4: `回転斧(おの)〜！...`

Gold spans: 2

| Gold # | Gold Pos | Matched Query | Cost | Query Exists Prob |
|--------|----------|--------------|------|------------------|
| 1 | (2,2) | Q9 | 5.17 | 0.076 |
| 0 | (0,1) | Q16 | 10.81 | 0.987 |

## Diagnostic 4: Loss Component Breakdown

| Component | Raw Loss | Weighted | % of Total |
|-----------|----------|----------|:-----------:|
| exist | 0.084 | 0.167 | 1.2% |
| start | 0.490 | 2.452 | 17.2% |
| end | 0.729 | 3.645 | 25.5% |
| type | 0.157 | 0.157 | 1.1% |
| reading | 2.616 | 7.849 | 55.0% |
| **total** | | **14.271** | 100% |

**Position loss: 43% of total.**

## Diagnostic 5: Prediction Visualization

### Sentence 0: `このまま逃げてても 埒(らち)が明かねえな`

```
Text: こ  の  ま  ま  逃  げ  て  て  も     埒  (  ら  ち  )  が  明  か  ね  え  な 
Gold: O  O  O  O  B  I  I  I  I  O  B  O  O  O  O  O  B  I  I  I  O 
Pred: O  O  O  O  B  I  I  I  I  O  O  O  O  O  O  O  B  I  I  O  O 
```

Correct: 1 Missed: ['明かねえ', '埒'] Extra: ['明かね']

### Sentence 1: `フリクションロスは少ないほど ギアはよく回ります`

```
Text: フ  リ  ク  シ  ョ  ン  ロ  ス  は  少  な  い  ほ  ど     ギ  ア  は  よ  く  回  り  ま  す 
Gold: O  O  O  O  O  O  O  O  O  B  I  I  O  O  O  O  O  O  O  O  B  I  I  I 
Pred: O  O  O  O  O  O  O  O  O  B  I  O  O  O  O  O  O  O  O  O  B  I  I  O 
```

Missed: ['少ない', '回ります'] Extra: ['少な', '回りま']

### Sentence 2: `さて ここからが話の メインユニットです`

```
Text: さ  て     こ  こ  か  ら  が  話  の     メ  イ  ン  ユ  ニ  ッ  ト  で  す 
Gold: O  O  O  O  O  O  O  O  B  O  O  O  O  O  O  O  O  O  O  O 
Pred: O  O  O  O  O  O  O  O  B  O  O  O  O  O  O  O  O  O  O  O 
```

Correct: 1 

### Sentence 3: `ナミさ〜ん！ クソ剣士 お前なんとかしろ！`

```
Text: ナ  ミ  さ  〜  ん  ！     ク  ソ  剣  士     お  前  な  ん  と  か  し  ろ  ！ 
Gold: O  O  O  O  O  O  O  O  O  B  I  O  O  B  O  O  O  O  O  O  O 
Pred: O  O  O  O  O  O  O  O  O  B  I  O  O  O  O  O  O  O  O  O  O 
```

Correct: 1 Missed: ['前'] 

### Sentence 4: `回転斧(おの)〜！`

```
Text: 回  転  斧  (  お  の  )  〜  ！ 
Gold: B  I  B  O  O  O  O  O  O 
Pred: B  I  I  O  O  O  O  O  O 
```

Missed: ['斧', '回転'] Extra: ['回転斧']

### Sentence 5: `制御不能って どういうこと!?`

```
Text: 制  御  不  能  っ  て     ど  う  い  う  こ  と  !  ? 
Gold: B  I  I  I  O  O  O  O  O  O  O  O  O  O  O 
Pred: B  I  I  O  O  O  O  O  O  O  O  O  O  O  O 
```

Missed: ['制御不能'] Extra: ['制御不']

### Sentence 6: `ああ！ あの旗印は！`

```
Text: あ  あ  ！     あ  の  旗  印  は  ！ 
Gold: O  O  O  O  O  O  B  I  O  O 
Pred: O  O  O  O  O  O  B  I  O  O 
```

Correct: 1 

### Sentence 7: `おう こら 今なんつった ああ？`

```
Text: お  う     こ  ら     今  な  ん  つ  っ  た     あ  あ  ？ 
Gold: O  O  O  O  O  O  B  O  O  O  O  O  O  O  O  O 
Pred: O  O  O  O  O  O  B  O  O  O  O  O  O  O  O  O 
```

Correct: 1 

### Sentence 8: `“飲み干す時”じゃなくて “飲み干すトキ”って…`

```
Text: “  飲  み  干  す  時  ”  じ  ゃ  な  く  て     “  飲  み  干  す  ト  キ  ”  っ  て  … 
Gold: O  B  I  I  I  B  O  O  O  O  O  O  O  O  B  I  I  I  O  O  O  O  O  O 
Pred: O  B  I  I  I  B  O  O  O  O  O  O  O  O  B  I  I  I  O  O  O  O  O  O 
```

Correct: 3 

### Sentence 9: `まあ 結果 騙したようなもんじゃな すまなんだ`

```
Text: ま  あ     結  果     騙  し  た  よ  う  な  も  ん  じ  ゃ  な     す  ま  な  ん  だ 
Gold: O  O  O  B  I  O  B  I  I  O  O  O  O  O  O  O  O  O  O  O  O  O  O 
Pred: O  O  O  B  O  O  B  I  O  O  O  O  O  O  O  O  O  O  O  O  O  O  O 
```

Missed: ['騙した', '結果'] Extra: ['騙し', '結']

## Conclusion: Root Cause & Recommended Fix

### Findings Summary

| Diagnostic | Result | Verdict |
|------------|--------|---------|
| 1. Char-to-token alignment | 0/45 errors | **PASS** — pooling is correct |
| 2. Position head predictions | 8/18 exact, 7/18 off-by-one, 0 diffuse | **Imprecise but not broken** |
| 3. Hungarian matching | Consistent query assignments (Q16, Q11, Q29 specialize) | **Stable** |
| 4. Loss breakdown | Position 43%, Reading 55%, Exist 1.2%, Type 1.1% | **Reading dominates** |
| 5. Visualization | Systematic short-by-1 at span ends | **End boundary truncation** |

### Root Cause: END BOUNDARY TRUNCATION

The position heads are NOT diffuse or broken. They point sharply (max_prob often >0.5). But there is a **systematic pattern of predicting spans 1 character too short at the end**:

- `少ない` (gold end=11) → predicted `少な` (end=10) — missing い
- `回ります` (gold end=23) → predicted `回りま` (end=22) — missing す
- `明かねえ` (gold end=19) → predicted `明かね` (end=18) — missing え
- `制御不能` (gold end=3) → predicted `制御不` (end=2) — missing 能
- `結果` (gold end=4) → predicted `結` (end=3) — missing 果
- `騙した` (gold end=8) → predicted `騙し` (end=7) — missing た

This is **not a data quality issue**. The gold labels are correct. The model consistently underestimates end positions by 1.

### Why This Happens

The end position uses **inclusive indexing** in gold labels (`gold_end = end - 1` in `SpanReaderDataset.__getitem__`). When DeBERTa tokenizes a span like `少ない` into tokens `["少", "ない"]`, the CharPooling maps:
- char 9 (少) → token 4
- char 10 (な) → token 5
- char 11 (い) → token 5

Characters 10 and 11 **share the same token representation** (token 5). The position head must distinguish between ending at char 10 vs 11, but both have identical hidden states from CharPooling. It cannot differentiate them.

### Secondary Issue: Reading Loss Dominates (55%)

The reading classifier has 8,463 classes — a massive softmax that dominates the gradient signal. This dilutes the position learning signal.

### Recommended Fixes (Priority Order)

1. **Fix CharPooling**: Instead of picking a single token per character, interpolate within each token's span. Characters at the start of a token get the token's representation slightly modified by position. Use a learned positional offset within each token.

2. **Reduce reading vocab or use staged training**: Train span detection only (freeze reading head) for the first 5 epochs, then unfreeze. This lets position heads learn without the reading gradient drowning them.

3. **Increase position loss weight**: λ_pos from 5.0 to 10.0, or reduce λ_read_cls from 3.0 to 1.0.

4. **Use sub-character position encoding**: Add a small MLP that takes (token_hidden, char_position_within_token) → char_hidden. This gives different representations to chars at positions 0, 1, 2 within the same token.
