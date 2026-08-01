# Twitter 内部重复提示词整理（88 条 / 53 组）

- 数据源：`shuixian-prompts/data/prompts-twitter.json`（本地==部署，3948 条）
- 重复判定：标题 + 提示词 文本完全相同（图片可能不同）
- 重复组数：**53**；多余（应处理）条目：**88**
- 多余条目来源分布：{'promptsref': 84, None: 1, 'webtomind': 3}

> 每组第一条为「保留项」（id 最小），其余为「重复项」。图片列注明各条目图片数及是否互不相同——若图不同，删除重复项会丢图，请按需决定合并或保留。

## 组 1　（18 条，多 17 条）
- 标题：`人物摄影作品`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`Transform the people in the image into real people. Create a photo that looks li`
- 图片：各组图互不相同，全组去重后共 **36** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32490 | promptsref | 摄影/电影感/写实场景 | 2 | 49806_out.png |
| 重复 | 32736 | promptsref | 摄影/电影感/写实场景 | 2 | 39283_out.png |
| 重复 | 32778 | promptsref | 摄影/电影感/写实场景 | 2 | 37703_out.png |
| 重复 | 32780 | promptsref | 摄影/电影感/写实场景 | 2 | 37680_out.png |
| 重复 | 32793 | promptsref | 摄影/电影感/写实场景 | 2 | 37255_out.png |
| 重复 | 32915 | promptsref | 摄影/电影感/写实场景 | 2 | 32454_out.png |
| 重复 | 32933 | promptsref | 摄影/电影感/写实场景 | 2 | 31970_out.png |
| 重复 | 32934 | promptsref | 摄影/电影感/写实场景 | 2 | 31929_out.png |
| 重复 | 32955 | promptsref | 摄影/电影感/写实场景 | 2 | 31499_out.png |
| 重复 | 32956 | promptsref | 摄影/电影感/写实场景 | 2 | 31494_out.png |
| 重复 | 32957 | promptsref | 摄影/电影感/写实场景 | 2 | 31493_out.png |
| 重复 | 32967 | promptsref | 摄影/电影感/写实场景 | 2 | 31410_out.png |
| 重复 | 32968 | promptsref | 摄影/电影感/写实场景 | 2 | 31407_out.png |
| 重复 | 32969 | promptsref | 摄影/电影感/写实场景 | 2 | 31405_out.png |
| 重复 | 32970 | promptsref | 摄影/电影感/写实场景 | 2 | 31404_out.png |
| 重复 | 32977 | promptsref | 摄影/电影感/写实场景 | 2 | 31365_out.png |
| 重复 | 32978 | promptsref | 摄影/电影感/写实场景 | 2 | 31364_out.png |
| 重复 | 32980 | promptsref | 摄影/电影感/写实场景 | 2 | 31362_out.png |

## 组 2　（7 条，多 6 条）
- 标题：`像素AI 生成图片`
- 分类：3D/游戏/像素/等距　|　提示词前 80 字：`Redraw the attached image in the most clumsy, scribbly, and utterly pathetic way`
- 图片：各组图互不相同，全组去重后共 **12** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32959 | promptsref | 3D/游戏/像素/等距 | 2 | 31446_out.png |
| 重复 | 33042 | promptsref | 3D/游戏/像素/等距 | 1 | 30322_out.png |
| 重复 | 33223 | promptsref | 3D/游戏/像素/等距 | 1 | 15535_out.png |
| 重复 | 33536 | promptsref | 3D/游戏/像素/等距 | 2 | 2800_out.png |
| 重复 | 33617 | promptsref | 3D/游戏/像素/等距 | 2 | 2447_out.png |
| 重复 | 33629 | promptsref | 3D/游戏/像素/等距 | 2 | 2422_out.png |
| 重复 | 33631 | promptsref | 3D/游戏/像素/等距 | 2 | 2416_out.png |

## 组 3　（5 条，多 4 条）
- 标题：`高级感标志/品牌设计`
- 分类：Logo/品牌/VI　|　提示词前 80 字：`Generate an image of an analysis report.

First, analyze the head shape in the`
- 图片：各组图互不相同，全组去重后共 **9** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33360 | promptsref | Logo/品牌/VI | 1 | 5849_out.png |
| 重复 | 33364 | promptsref | Logo/品牌/VI | 2 | 5507_out.png |
| 重复 | 33476 | promptsref | Logo/品牌/VI | 2 | 3048_out.png |
| 重复 | 33477 | promptsref | Logo/品牌/VI | 2 | 3047_out.png |
| 重复 | 33518 | promptsref | Logo/品牌/VI | 2 | 2865_out.png |

## 组 4　（4 条，多 3 条）
- 标题：`围绕任意主题对象生成一张图文拼贴感很强的视觉图像：主题对象以…`
- 分类：商业海报/广告/社媒　|　提示词前 80 字：`围绕任意主题对象生成一张图文拼贴感很强的视觉图像：主题对象以极近距离的主形体进入画面，占据一侧主要视觉重量，只露出最有识别度的局部边缘、表面、轮廓或核心细节，另`
- 图片：各组图互不相同，全组去重后共 **4** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33136 | promptsref | 商业海报/广告/社媒 | 1 | 20499_out.png |
| 重复 | 33137 | promptsref | 商业海报/广告/社媒 | 1 | 20498_out.png |
| 重复 | 33138 | promptsref | 商业海报/广告/社媒 | 1 | 20497_out.png |
| 重复 | 33139 | promptsref | 商业海报/广告/社媒 | 1 | 20496_out.png |

## 组 5　（4 条，多 3 条）
- 标题：`AI 生成图片`
- 分类：其他综合　|　提示词前 80 字：`Create a landing page using this image as a reference for style and color`
- 图片：各组图互不相同，全组去重后共 **8** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33559 | promptsref | 其他综合 | 2 | 2647_out.png |
| 重复 | 33607 | promptsref | 其他综合 | 2 | 2475_out.png |
| 重复 | 33667 | promptsref | 其他综合 | 2 | 2318_out.png |
| 重复 | 33672 | promptsref | 其他综合 | 2 | 2306_out.png |

## 组 6　（4 条，多 3 条）
- 标题：`插画角色`
- 分类：插画/涂鸦/手绘风　|　提示词前 80 字：`Generate a vertical page of a game strategy guide, with this character's full bo`
- 图片：各组图互不相同，全组去重后共 **8** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33670 | promptsref | 插画/涂鸦/手绘风 | 2 | 2309_out.png |
| 重复 | 33671 | promptsref | 插画/涂鸦/手绘风 | 2 | 2308_out.png |
| 重复 | 33718 | promptsref | 插画/涂鸦/手绘风 | 2 | 2122_out.png |
| 重复 | 33735 | promptsref | 插画/涂鸦/手绘风 | 2 | 2082_out.png |

## 组 7　（3 条，多 2 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`Design a high-end gacha summon page for a new mobile game titled [Game Title], i`
- 图片：各组图互不相同，全组去重后共 **5** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32428 | promptsref | 摄影/电影感/写实场景 | 2 | 53483_out.png |
| 重复 | 33382 | promptsref | 摄影/电影感/写实场景 | 2 | 4833_out.png |
| 重复 | 33465 | promptsref | 摄影/电影感/写实场景 | 1 | 3094_out.png |

## 组 8　（3 条，多 2 条）
- 标题：`电影感汽车`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`[Car full description and movie-accurate details], three-quarter view, vector ar`
- 图片：各组图互不相同，全组去重后共 **3** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32503 | promptsref | 摄影/电影感/写实场景 | 1 | 49276_out.png |
| 重复 | 32504 | promptsref | 摄影/电影感/写实场景 | 1 | 49275_out.png |
| 重复 | 32609 | promptsref | 摄影/电影感/写实场景 | 1 | 43872_out.png |

## 组 9　（3 条，多 2 条）
- 标题：`街拍女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`Create an image where the character looks more like a real and beautiful person,`
- 图片：各组图互不相同，全组去重后共 **6** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32917 | promptsref | 摄影/电影感/写实场景 | 2 | 32450_out.png |
| 重复 | 32918 | promptsref | 摄影/电影感/写实场景 | 2 | 32449_out.png |
| 重复 | 32932 | promptsref | 摄影/电影感/写实场景 | 2 | 31975_out.png |

## 组 10　（3 条，多 2 条）
- 标题：`一个英雄联盟原创角色， 黑暗恶魔，全身照，为了守护爱人而陷入…`
- 分类：头像/人像/写真　|　提示词前 80 字：`一个英雄联盟原创角色， 黑暗恶魔，全身照，为了守护爱人而陷入黑暗，散发充满眼睛的黑烟，让人印象深刻的角色。超大色块塑形，减少细节，减少纹理噪点，面部采用大面积几`
- 图片：各组图互不相同，全组去重后共 **6** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32973 | promptsref | 头像/人像/写真 | 2 | 31372_out.png |
| 重复 | 32974 | promptsref | 头像/人像/写真 | 2 | 31371_out.png |
| 重复 | 32975 | promptsref | 头像/人像/写真 | 2 | 31370_out.png |

## 组 11　（3 条，多 2 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`naah™️. Act as a Fashion Photographer and Graphic Designer specializing in luxur`
- 图片：各组图互不相同，全组去重后共 **5** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33163 | promptsref | 摄影/电影感/写实场景 | 2 | 19138_out.png |
| 重复 | 33170 | promptsref | 摄影/电影感/写实场景 | 2 | 18265_out.png |
| 重复 | 33253 | promptsref | 摄影/电影感/写实场景 | 1 | 13012_out.png |

## 组 12　（2 条，多 1 条）
- 标题：`请使用下面的prompt生成4张独立的图片（注意，不是collage多张图片到一张图片，而是4张独立图片）：-`
- 分类：头像/人像/写真　|　提示词前 80 字：`比例：3:4
主题：{女孩A}和{女孩B}身穿泳装，在泳池中戏水
风格：半写实日漫 + UE5超写实 + CG高亮肌肤 + 极繁主义
构图：莫兰迪色调的纯色色块`
- 图片：各组图互不相同，全组去重后共 **5** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32019 | None | 头像/人像/写真 | 4 | 2081022771140927695.jpg |
| 重复 | 32020 | None | 头像/人像/写真 | 1 | 2081021070770045212.jpg |

## 组 13　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`Preserve the reference character’s:
- face identity
- facial proportions
- eye s`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32283 | promptsref | 摄影/电影感/写实场景 | 1 | 55270_out.png |
| 重复 | 32285 | promptsref | 摄影/电影感/写实场景 | 1 | 55268_out.png |

## 组 14　（2 条，多 1 条）
- 标题：`使用提供的参考图像。严格的面部与身份锁定：100% 精确保留…`
- 分类：头像/人像/写真　|　提示词前 80 字：`使用提供的参考图像。严格的面部与身份锁定：100% 精确保留主体的外貌。不得更改面部特征、面部比例、皮肤纹理、头发颜色或整体身份。应用电影胶片颗粒效果。
一幅捕`
- 图片：各组图互不相同，全组去重后共 **4** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32290 | promptsref | 头像/人像/写真 | 2 | 55031_out.png |
| 重复 | 32319 | promptsref | 头像/人像/写真 | 2 | 51891_out.png |

## 组 15　（2 条，多 1 条）
- 标题：`极简标志/品牌设计`
- 分类：Logo/品牌/VI　|　提示词前 80 字：`Vertical smartphone outdoor flash snapshot with realistic casual lifestyle-photo`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32298 | promptsref | Logo/品牌/VI | 1 | 54711_out.png |
| 重复 | 32670 | promptsref | Logo/品牌/VI | 1 | 40914_out.png |

## 组 16　（2 条，多 1 条）
- 标题：`字体设计`
- 分类：字体/排版/标题设计　|　提示词前 80 字：`full-color action shot, subject airborne, fragmented into overlapping tilted pan`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32311 | promptsref | 字体/排版/标题设计 | 1 | 53682_out.png |
| 重复 | 32971 | promptsref | 字体/排版/标题设计 | 1 | 31376_out.png |

## 组 17　（2 条，多 1 条）
- 标题：`霓虹女性`
- 分类：头像/人像/写真　|　提示词前 80 字：`9:16，photorealistic, CCD flash nightlife portrait, direct frontal flash, cool-to`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32342 | promptsref | 头像/人像/写真 | 1 | 50907_out.png |
| 重复 | 33988 | webtomind | 头像/人像/写真 | 1 | 139f1032-a885-4484-a775-44c038e3e3… |

## 组 18　（2 条，多 1 条）
- 标题：`AI 生成图片`
- 分类：其他综合　|　提示词前 80 字：`Cosplay`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32376 | promptsref | 其他综合 | 1 | 56481_out.png |
| 重复 | 32775 | promptsref | 其他综合 | 1 | 37741_out.png |

## 组 19　（2 条，多 1 条）
- 标题：`生成一张旅行生活照九宫格风格的单张拼贴图：同一位年轻女性在海…`
- 分类：头像/人像/写真　|　提示词前 80 字：`生成一张旅行生活照九宫格风格的单张拼贴图：同一位年轻女性在海边小城的一天，包含街边咖啡、海风自拍、黄昏背影、手拿冰饮等自然瞬间。整体像真实手机生活记录但画面高级`
- 图片：各组图互不相同，全组去重后共 **3** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32492 | promptsref | 头像/人像/写真 | 2 | 49608_out.png |
| 重复 | 32505 | promptsref | 头像/人像/写真 | 1 | 49273_out.png |

## 组 20　（2 条，多 1 条）
- 标题：`赛博朋克女性`
- 分类：头像/人像/写真　|　提示词前 80 字：`A luxury editorial sports campaign poster featuring an elegant female model insp`
- 图片：各组图互不相同，全组去重后共 **3** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32510 | promptsref | 头像/人像/写真 | 2 | 49185_out.png |
| 重复 | 32517 | promptsref | 头像/人像/写真 | 1 | 48395_out.png |

## 组 21　（2 条，多 1 条）
- 标题：`生成一张 9:16 竖版高级科幻机甲电影角色海报，真人电影质…`
- 分类：商业海报/广告/社媒　|　提示词前 80 字：`生成一张 9:16 竖版高级科幻机甲电影角色海报，真人电影质感，院线 IMAX 主视觉风格。

角色是一位银白色凌乱短发的年轻男性机甲驾驶员，皮肤苍白细腻，`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32549 | promptsref | 商业海报/广告/社媒 | 1 | 46862_out.png |
| 重复 | 33692 | promptsref | 商业海报/广告/社媒 | 1 | 2210_out.png |

## 组 22　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`Create a high-resolution 8K portrait poster in an Urban Fashion Editorial Collag`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32619 | promptsref | 摄影/电影感/写实场景 | 1 | 43473_out.png |
| 重复 | 33521 | promptsref | 摄影/电影感/写实场景 | 1 | 2839_out.png |

## 组 23　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`Ultra-realistic cinematic portrait photography. Vertical 9:16 composition. Low-a`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32741 | promptsref | 摄影/电影感/写实场景 | 1 | 38808_out.png |
| 重复 | 33098 | promptsref | 摄影/电影感/写实场景 | 1 | 28780_out.png |

## 组 24　（2 条，多 1 条）
- 标题：`赛博朋克角色`
- 分类：其他综合　|　提示词前 80 字：`one oversized foreground object, same scale as character or larger, highly detai`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32759 | promptsref | 其他综合 | 1 | 38061_out.png |
| 重复 | 32792 | promptsref | 其他综合 | 1 | 37352_out.png |

## 组 25　（2 条，多 1 条）
- 标题：`90年代OVA剧场版动画风格《英雄联盟》阿狸，保留原著浅粉色…`
- 分类：插画/涂鸦/手绘风　|　提示词前 80 字：`90年代OVA剧场版动画风格《英雄联盟》阿狸，保留原著浅粉色长发、冷艳眼神与天空术式气质。复古柔焦丙烯插画绘画风格，细腻厚涂，90年代动画设定海报，非真人、P·`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32834 | promptsref | 插画/涂鸦/手绘风 | 1 | 35843_out.png |
| 重复 | 32870 | promptsref | 插画/涂鸦/手绘风 | 1 | 33820_out.png |

## 组 26　（2 条，多 1 条）
- 标题：`霓虹情侣`
- 分类：UI/App/网页/SaaS　|　提示词前 80 字：`Create a 9:16 image in the "Clean Triptych Travel Vlog Thumbnail" style.

Subj`
- 图片：各组图互不相同，全组去重后共 **3** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32843 | promptsref | UI/App/网页/SaaS | 2 | 35810_out.png |
| 重复 | 33337 | promptsref | UI/App/网页/SaaS | 1 | 6498_out.png |

## 组 27　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`Serena Antonietta from The first descendant, rendered in an Kubo tite-style thic`
- 图片：各组图互不相同，全组去重后共 **4** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32884 | promptsref | 摄影/电影感/写实场景 | 2 | 33149_out.png |
| 重复 | 32885 | promptsref | 摄影/电影感/写实场景 | 2 | 33148_out.png |

## 组 28　（2 条，多 1 条）
- 标题：`人角色介绍卡，全身照+技能`
- 分类：其他综合　|　提示词前 80 字：`人角色介绍卡，全身照+技能`
- 图片：各组图互不相同，全组去重后共 **4** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32898 | promptsref | 其他综合 | 2 | 32892_out.png |
| 重复 | 32900 | promptsref | 其他综合 | 2 | 32889_out.png |

## 组 29　（2 条，多 1 条）
- 标题：`极简动物`
- 分类：插画/涂鸦/手绘风　|　提示词前 80 字：`Playful flat-vector poster illustration of [HUMAN] posing with [ANIMAL] in [POSE`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32940 | promptsref | 插画/涂鸦/手绘风 | 1 | 31604_out.png |
| 重复 | 32941 | promptsref | 插画/涂鸦/手绘风 | 1 | 31602_out.png |

## 组 30　（2 条，多 1 条）
- 标题：`3D女性`
- 分类：头像/人像/写真　|　提示词前 80 字：`A professional sports graphic design poster of [Player Name], designed in a clea`
- 图片：各组图互不相同，全组去重后共 **3** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32948 | promptsref | 头像/人像/写真 | 2 | 31577_out.png |
| 重复 | 33054 | promptsref | 头像/人像/写真 | 1 | 30022_out.png |

## 组 31　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`a cinematic night street portrait, y2k aesthetic, an extremely beautiful young w`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 32985 | promptsref | 摄影/电影感/写实场景 | 1 | 31353_out.png |
| 重复 | 33006 | promptsref | 摄影/电影感/写实场景 | 1 | 31053_out.png |

## 组 32　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`Use case: photorealistic-natural
Asset type: portrait image, intended aspect ra`
- 图片：各组图互不相同，全组去重后共 **3** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33043 | promptsref | 摄影/电影感/写实场景 | 2 | 30173_out.png |
| 重复 | 33288 | promptsref | 摄影/电影感/写实场景 | 1 | 9791_out.png |

## 组 33　（2 条，多 1 条）
- 标题：`AI 生成图片`
- 分类：其他综合　|　提示词前 80 字：`Transformez le style de dessin de l'image. En un style de dessin un peu chibi ma`
- 图片：各组图互不相同，全组去重后共 **4** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33095 | promptsref | 其他综合 | 2 | 28860_out.png |
| 重复 | 33156 | promptsref | 其他综合 | 2 | 19315_out.png |

## 组 34　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：头像/人像/写真　|　提示词前 80 字：`Create a AAA-quality Unreal Engine 5 outfit selection screen for 【ganyu from gen`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33131 | promptsref | 头像/人像/写真 | 1 | 20662_out.png |
| 重复 | 33176 | promptsref | 头像/人像/写真 | 1 | 17879_out.png |

## 组 35　（2 条，多 1 条）
- 标题：`街拍女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`A 9:16 vertical late-night candid smartphone-style image, showing a fictional Ju`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33166 | promptsref | 摄影/电影感/写实场景 | 1 | 18858_out.png |
| 重复 | 33306 | promptsref | 摄影/电影感/写实场景 | 1 | 8069_out.png |

## 组 36　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`Generate a vertical 9:16 cinematic visual poster with the theme of "Social media`
- 图片：各组图互不相同，全组去重后共 **3** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33199 | promptsref | 摄影/电影感/写实场景 | 2 | 17139_out.png |
| 重复 | 33352 | promptsref | 摄影/电影感/写实场景 | 1 | 6111_out.png |

## 组 37　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`FORMAT:
4:5 vertical premium smartphone campaign poster, ultra-high resolution `
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33221 | promptsref | 摄影/电影感/写实场景 | 1 | 15613_out.png |
| 重复 | 33612 | promptsref | 摄影/电影感/写实场景 | 1 | 2470_out.png |

## 组 38　（2 条，多 1 条）
- 标题：`3D3D 渲染`
- 分类：3D/游戏/像素/等距　|　提示词前 80 字：`Cutting-edge internet operations visual design master standard, Behance / Dribbb`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33257 | promptsref | 3D/游戏/像素/等距 | 1 | 11972_out.png |
| 重复 | 33258 | promptsref | 3D/游戏/像素/等距 | 1 | 11971_out.png |

## 组 39　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`Kuchiki Rukia from Bleach, rendered in an Kubo tite-style thick paint illustrati`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33350 | promptsref | 摄影/电影感/写实场景 | 1 | 6219_out.png |
| 重复 | 33424 | promptsref | 摄影/电影感/写实场景 | 1 | 3542_out.png |

## 组 40　（2 条，多 1 条）
- 标题：`3D女性`
- 分类：头像/人像/写真　|　提示词前 80 字：`Transform the provided reference image into a cozy aesthetic scrapbook-style com`
- 图片：各组图互不相同，全组去重后共 **3** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33368 | promptsref | 头像/人像/写真 | 2 | 5387_out.png |
| 重复 | 33593 | promptsref | 头像/人像/写真 | 1 | 2522_out.png |

## 组 41　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`A high-definition, realistic broadcast shot of a young woman sitting in a crowde`
- 图片：各组图互不相同，全组去重后共 **3** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33371 | promptsref | 摄影/电影感/写实场景 | 2 | 5276_out.png |
| 重复 | 33457 | promptsref | 摄影/电影感/写实场景 | 1 | 3122_out.png |

## 组 42　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`@Image1
 = main character identity reference

Create a polished fantasy chara`
- 图片：各组图互不相同，全组去重后共 **3** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33394 | promptsref | 摄影/电影感/写实场景 | 1 | 4428_out.png |
| 重复 | 33395 | promptsref | 摄影/电影感/写实场景 | 2 | 4419_out.png |

## 组 43　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：头像/人像/写真　|　提示词前 80 字：`Reverse haze, diffused blur, soft focus, close-up shot of an ethereal and pure b`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33398 | promptsref | 头像/人像/写真 | 1 | 4101_out.png |
| 重复 | 33501 | promptsref | 头像/人像/写真 | 1 | 2924_out.png |

## 组 44　（2 条，多 1 条）
- 标题：`「このキャラクターで背景を実写の街中にし、服や髪の色を変えら…`
- 分类：UI/App/网页/SaaS　|　提示词前 80 字：`「このキャラクターで背景を実写の街中にし、服や髪の色を変えられるUIのデザインを画面いっぱいに表示してください。背景を変えられるボタンなども表示してください。」`
- 图片：各组图互不相同，全组去重后共 **4** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33401 | promptsref | UI/App/网页/SaaS | 2 | 4055_out.png |
| 重复 | 33402 | promptsref | UI/App/网页/SaaS | 2 | 4054_out.png |

## 组 45　（2 条，多 1 条）
- 标题：`极简女性`
- 分类：头像/人像/写真　|　提示词前 80 字：`Create a fashion styling analysis infographic focused on women’s outfit tips, us`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33405 | promptsref | 头像/人像/写真 | 1 | 3999_out.png |
| 重复 | 33406 | promptsref | 头像/人像/写真 | 1 | 3997_out.png |

## 组 46　（2 条，多 1 条）
- 标题：`电影感字体设计`
- 分类：字体/排版/标题设计　|　提示词前 80 字：`Boa Hancock from One Piece, illustrated in a Kubo Tite-inspired thick paint styl`
- 图片：各组图互不相同，全组去重后共 **3** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33419 | promptsref | 字体/排版/标题设计 | 2 | 3686_out.png |
| 重复 | 33513 | promptsref | 字体/排版/标题设计 | 1 | 2886_out.png |

## 组 47　（2 条，多 1 条）
- 标题：`高级感人物`
- 分类：头像/人像/写真　|　提示词前 80 字：`Create a premium, highly believable Lootbox / Capsule Drop Ad for an imaginary d`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33442 | promptsref | 头像/人像/写真 | 1 | 3278_out.png |
| 重复 | 33443 | promptsref | 头像/人像/写真 | 1 | 3277_out.png |

## 组 48　（2 条，多 1 条）
- 标题：`电影感女性`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`Yor from SpyxFamily, rendered in an Kubo tite-style thick paint illustration. Si`
- 图片：各组图互不相同，全组去重后共 **4** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33516 | promptsref | 摄影/电影感/写实场景 | 2 | 2878_out.png |
| 重复 | 33537 | promptsref | 摄影/电影感/写实场景 | 2 | 2793_out.png |

## 组 49　（2 条，多 1 条）
- 标题：`角色标志/品牌设计`
- 分类：Logo/品牌/VI　|　提示词前 80 字：`Sam Altman as a Major League Baseball player holding a bat in batting stance. Co`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33564 | promptsref | Logo/品牌/VI | 1 | 2618_out.png |
| 重复 | 33701 | promptsref | Logo/品牌/VI | 1 | 2189_out.png |

## 组 50　（2 条，多 1 条）
- 标题：`AI 生成图片`
- 分类：其他综合　|　提示词前 80 字：`Create an artwork, a design of Jude Bellingham, advanced design level, 3:2, Mac `
- 图片：各组图互不相同，全组去重后共 **3** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33668 | promptsref | 其他综合 | 2 | 2316_out.png |
| 重复 | 33741 | promptsref | 其他综合 | 1 | 2076_out.png |

## 组 51　（2 条，多 1 条）
- 标题：`电影感建筑`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`Generate a high-aesthetic "Contour Universe / Collectible Narrative Poster" base`
- 图片：各组图互不相同，全组去重后共 **2** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33679 | promptsref | 摄影/电影感/写实场景 | 1 | 2288_out.png |
| 重复 | 33700 | promptsref | 摄影/电影感/写实场景 | 1 | 2190_out.png |

## 组 52　（2 条，多 1 条）
- 标题：`“周末出去Shopping”🥳`
- 分类：摄影/电影感/写实场景　|　提示词前 80 字：`摄影风格：冷白清透CCD生活照风
写真方向：都市约会生活照
场景方向：浅色美妆集合店 / 玻璃陈列柜 / 冷白灯带 / 干净试妆台
服装方向：冷粉色U领贴身短袖`
- 图片：各组图互不相同，全组去重后共 **4** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33911 | webtomind | 摄影/电影感/写实场景 | 2 | ce39b882-b4d9-410a-8b07-66abd1afc4… |
| 重复 | 33969 | webtomind | 摄影/电影感/写实场景 | 2 | 6abd3154-b204-4843-ab00-66ce977f74… |

## 组 53　（2 条，多 1 条）
- 标题：`角色一致性设定表`
- 分类：其他综合　|　提示词前 80 字：`CHARACTER: [CHARACTER NAME]

Create ONE professional animation character sheet.
`
- 图片：各组图互不相同，全组去重后共 **8** 张独特图

| 角色 | id | source | 分类 | 图数 | 图片样本 |
|---|---|---|---|---|---|
| 保留 | 33919 | webtomind | 其他综合 | 4 | 57e08435-8add-4171-9946-f1a8406063… |
| 重复 | 33972 | webtomind | 其他综合 | 4 | 23586294-7d79-4108-8e00-5384570ac9… |
