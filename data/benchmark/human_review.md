# Benchmark Human Review
Models compared: claude_v2, gemini, qwen7b vs v7 GT

## Sentence 1 (hirogaru)
"笛の教室をしています。女の子が笛を吹く機会が少ないので、女の子に笛を教えたいと思いました。女の子が笛を習って、将来、自分のこどもに教えられるといいと思います。それからコンサートもときどき開いています。今、笛を吹く人が減って、お祭りでテープの音を使うことがあります。笛に興味を持つ人が増えるように活動しています。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| お祭り | おまつり | おまつり | おまつり | — | model_extra |
| が | — | — | ga, ga, ga, ga | — | model_extra |
| ことがあります | — | — | ことがあります | — | model_extra |
| こども | — | — | こども | — | model_extra |
| しています | — | — | していいます, していいます | — | model_extra |
| それから | — | — | それから | — | model_extra |
| で | — | — | de | — | model_extra |
| といい | — | — | といい | — | model_extra |
| ときどき | — | — | ときどき | — | model_extra |
| と思いました | — | — | thought | — | model_extra |
| と思います | — | — | とおもいます | — | model_extra |
| に | — | — | ni, ni, ni | — | model_extra |
| の | — | — | no, no | — | model_extra |
| も | — | — | mo | — | model_extra |
| ように | — | — | ように | — | model_extra |
| を | — | — | wo, wo, wo, wo, wo | — | model_extra |
| を使う | — | — | つかう | — | model_extra |
| を持つ | — | — | もつ | — | model_extra |
| コンサート | — | — | こんさーと | — | model_extra |
| テープ | — | — | ていぱ | — | model_extra |
| 人が | — | — | ひとが | — | model_extra |
| 使う | つかう | つかう | — | つかう | coverage_diff |
| 吹く | ふく, ふく | ふく, ふく | ふく, ふく | ふくく, ふく | reading_diff |
| 女 | — | — | — | おんな, おんな, おんな | model_missing |
| 女の子 | おんなのこ, おんなのこ, おんなのこ | おんなのこ, おんなのこ, おんなのこ | おんなのこ, おんなのこ, おんなのこ | — | model_extra |
| 子 | — | — | — | こ, こ, こ | model_missing |
| 少ない | すくない | すくない | — | すくない | coverage_diff |
| 少ないので | — | — | すくなので | — | model_extra |
| 思いました | おもいました | おもいました | — | おもいました | coverage_diff |
| 思います | おもいます | おもいます | — | おもいます | coverage_diff |
| 持つ | もつ | もつ | — | もつ | coverage_diff |
| 活動 | — | — | かつどう | — | model_extra |
| 活動して | — | — | — | かつどうして | model_missing |
| 活動しています | かつどうしています | かつどうしています | — | — | model_extra |
| 祭り | — | — | — | まつり | model_missing |
| 笛 | ふえ, ふえ, ふえ, ふえ, ふえ, ふえ | ふえ, ふえ, ふえ, ふえ, ふえ, ふえ | ぶえ, ぶえ, ぶえ, ぶえ, ぶえ, ぶえ | ふえ, ふえ, ふえ, ふえ, ふえ, ふえ | reading_diff |
| 習って | ならって | ならって | ならめて | ならって | reading_diff |
| 自分 | じぶん | じぶん | — | — | model_extra |
| 自分の | — | — | じぶんの | — | model_extra |
| 自分のこど | — | — | — | じぶんのこど | model_missing |
| 開いて | — | — | — | ひらいて | model_missing |
| 開いています | ひらいています | ひらいています | あいています | — | model_extra |

## Sentence 2 (hirogaru)
"午前4時、堤防へ釣りに行く人が港にたくさん集まっています。船は、堤防で釣りをする人のために1日に何回も行きます。この日は８回くらい出発しました。一番最初の4時半の船に乗りました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 1日 | いちにち | いちにち | ついたち | — | model_extra |
| 4時 | よじ | — | よじ | — | model_extra |
| 8回 | — | — | はっかい | — | model_extra |
| くらい | — | — | くらい | — | model_extra |
| この日 | — | — | こんにち | — | model_extra |
| たくさん | — | — | たんかん | — | model_extra |
| ために | — | — | のぞみに | — | model_extra |
| で | — | — | で | — | model_extra |
| に | — | — | に, に, に | — | model_extra |
| に行く | — | — | いきに | — | model_extra |
| へ | — | — | に | — | model_extra |
| をする | — | — | する | — | model_extra |
| 一番 | — | いちばん | — | — | model_extra |
| 一番最初 | いちばんさいしょ | — | — | いちばんさいしょ | coverage_diff |
| 一番最初の | — | — | いちばんさいしだの | — | model_extra |
| 乗りました | のりました | のりました | の乘りました | のりました | reading_diff |
| 何回 | なんかい | なんかい | — | なんかい | coverage_diff |
| 何回も | — | — | なんかいも | — | model_extra |
| 午前 | ごぜん | — | ごぜん | — | model_extra |
| 午前4時 | — | ごぜんよじ | — | ごぜんよじ | coverage_diff |
| 回くらい | — | — | — | かいくらい | model_missing |
| 日 | ひ | ひ | — | にち, ひ | reading_diff |
| 最初 | — | さいしょ | — | — | model_extra |
| 船 | ふね, ふね | ふね, ふね | ふな | ふね, ふね | reading_diff |
| 船は | — | — | ふなは | — | model_extra |
| 行く | いく | いく | — | いく | coverage_diff |
| 集まって | — | — | — | あつまって | model_missing |
| 集まっています | あつまっています | あつまっています | しゅうまっています | — | model_extra |
| ８回 | はちかい | はちかい | — | — | model_extra |

## Sentence 3 (hirogaru)
"試合は二人でします。でも、二人は戦いません。型を見せて、どちらが美しいか、迫力があるか、審判が決めます。体が大きい人と小さい人、若い人と年をとった人、そして男性と女性が試合をすることもあります。ほかの武道と違っていて、おもしろいですね。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、, 、, 、, 、, 、, 、 | — | model_extra |
| 。 | — | — | 。, 。 | — | model_extra |
| おもしろい | — | — | おもしろい | — | model_extra |
| が | — | — | が, が, が, が | — | model_extra |
| があるか | — | — | があるか | — | model_extra |
| します | — | — | しめす | — | model_extra |
| することもあります | — | — | することもあります | — | model_extra |
| そして | — | — | そして | — | model_extra |
| で | — | — | で | — | model_extra |
| ですね | — | — | ですね | — | model_extra |
| でも | — | — | でも | — | model_extra |
| と | — | — | と, と, と, と | — | model_extra |
| とった | — | — | とっていた | — | model_extra |
| どちら | — | — | どなた | — | model_extra |
| は | — | — | は, は | — | model_extra |
| ほかの | — | — | ほかの | — | model_extra |
| を | — | — | を | — | model_extra |
| 大きい | おおきい | おおきい | おおい | おおきい | reading_diff |
| 女性 | じょせい | じょせい | じょし | じょせい | reading_diff |
| 年 | とし | とし | — | とし | coverage_diff |
| 年を | — | — | としを | — | model_extra |
| 戦いません | たたかいません | たたかいません | たべません | たたかいません | reading_diff |
| 美しい | うつくしい | うつくしい | — | うつくしい | coverage_diff |
| 美しいか | — | — | うつくしいか | — | model_extra |
| 若い | わかい | わかい | おさな | わかい | reading_diff |
| 試合を | — | — | しあいを | — | model_extra |
| 違っていて | ちがっていて | ちがっていて | ちがっていいて | ちがっていて | reading_diff |

## Sentence 4 (hirogaru)
"先生の話です。「私は、練習のとき墨汁を使いますが、作品を書くとき墨を使います。墨は時間がかかりますから、「早く書きたい」という気持ちになります。でも、長い時間、墨をすると、気持ちがとても落ち着きます。作品を書くために集中もできます。準備に時間を使って、集中して書くことは、とても大切です。」"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、, 、, 、, 、, 、, 、, 、 | — | model_extra |
| 。 | — | — | 。, 。, 。, 。, 。 | — | model_extra |
| 「 | — | — | 「 | — | model_extra |
| かかります | — | — | かかるいます | — | model_extra |
| から | — | — | から | — | model_extra |
| が | — | — | が, が, が | — | model_extra |
| ことは | — | — | ことは | — | model_extra |
| して | — | — | して | — | model_extra |
| すると | — | — | すると | — | model_extra |
| ために | — | — | のぞみに | — | model_extra |
| できます | — | — | できます | — | model_extra |
| です | — | — | です, です | — | model_extra |
| でも | — | — | でも | — | model_extra |
| という | — | — | という | — | model_extra |
| とき | — | — | とき, とき | — | model_extra |
| とても | — | — | とても, とても | — | model_extra |
| に | — | — | に | — | model_extra |
| になります | — | — | なります | — | model_extra |
| の | — | — | の, の | — | model_extra |
| は | — | — | は, は | — | model_extra |
| も | — | — | も | — | model_extra |
| を | — | — | を, を, を, を, を, を | — | model_extra |
| 使いますが | つかいますが | — | — | — | model_extra |
| 墨汁 | ぼくじゅう | ぼくじゅう | ぼくじ | ぼくじゅう | reading_diff |
| 書きたい | かきたい | かきたい | かいたい | かきたい | reading_diff |
| 書きます | — | — | かきます | — | model_extra |
| 着きます | — | — | — | つきます | model_missing |
| 落ち | — | — | — | おち | model_missing |
| 落ち着きます | おちつきます | おちつきます | のろいきます | — | model_extra |
| 話 | はなし | はなし | はな | はなし | reading_diff |
| 集中 | しゅうちゅう | しゅうちゅう | しゅうしん, しゅうしん | しゅうちゅう | reading_diff |
| 集中して | しゅうちゅうして | しゅうちゅうして | — | しゅうちゅうして | coverage_diff |

## Sentence 5 (hirogaru)
"普通の本屋で、本の値段は決まっていますが、ここでは自分で考えて値段を決めます。それが面白いです。売れなかったら安くします。自分で商売をしている気持ちになります。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| 。 | — | — | 。, 。, 。, 。 | — | model_extra |
| が | — | — | が | — | model_extra |
| ここ | — | — | ここ | — | model_extra |
| している | — | — | している | — | model_extra |
| それが | — | — | それがあ | — | model_extra |
| で | — | — | で, で | — | model_extra |
| になります | — | — | なります | — | model_extra |
| の | — | — | の, の | — | model_extra |
| は | — | — | は, は | — | model_extra |
| を | — | — | を | — | model_extra |
| 値段 | ねだん, ねだん | ねだん, ねだん | ねんじだん | ねだん, ねだん | reading_diff |
| 値段を決めます | — | — | ねんじをきめます | — | model_extra |
| 売れなかった | — | — | — | うれなかった | model_missing |
| 売れなかったら | うれなかったら | うれなかったら | うれなかったら | — | model_extra |
| 安くします | やすくします | やすくします | — | やすくします | coverage_diff |
| 安くなります | — | — | やすくなります | — | model_extra |
| 決まって | — | — | — | きまって | model_missing |
| 決まっています | — | きまっています | きまっています | — | model_extra |
| 決まっていますが | きまっていますが | — | — | — | model_extra |
| 決めます | きめます | きめます | — | きめます | coverage_diff |
| 自分 | じぶん, じぶん | じぶん, じぶん | — | じぶん, じぶん | coverage_diff |
| 自分で | — | — | じぶんで, じぶんで | — | model_extra |
| 面白い | おもしろい | おもしろい | — | おもしろい | coverage_diff |
| 面白いです | — | — | おもしろいです | — | model_extra |

## Sentence 6 (hirogaru)
"書道のSNSグループに参加しています。毎日ひとりが、書くことばを決めます。みんなは、そのことばを書いてSNSに写真をアップします。この日は「祝う」という字を書きました。いろいろな書が集まりました。どの書が好きですか。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| SNS | — | — | えぬえすえぬ | — | model_extra |
| SNSに | — | — | えぬえすえぬに | — | model_extra |
| 、 | — | — | 、, 、 | — | model_extra |
| 「祝う」 | — | — | 「たもう」 | — | model_extra |
| いろいろな | — | — | いろいろな | — | model_extra |
| この日は | — | — | このひは | — | model_extra |
| そのことばを | — | — | そのことばを | — | model_extra |
| という字を | — | — | というじを | — | model_extra |
| どの書が | — | — | どのしょが | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の | — | model_extra |
| ひとりが | — | — | ひとりが | — | model_extra |
| みんなは | — | — | みなさんは | — | model_extra |
| アップします | — | — | あっぷします | — | model_extra |
| グループ | — | — | ぐるーぐる | — | model_extra |
| 写真 | しゃしん | しゃしん | — | しゃしん | coverage_diff |
| 写真を | — | — | しゃしんを | — | model_extra |
| 参加して | — | — | — | さんかして | model_missing |
| 参加しています | さんかしています | さんかしています | さんかしていいます | — | model_extra |
| 好き | すき | すき | — | すき | coverage_diff |
| 字 | じ | じ | — | じ | coverage_diff |
| 日 | ひ | ひ | — | ひ | coverage_diff |
| 書 | しょ, しょ | しょ, しょ | — | しょ, しょ | coverage_diff |
| 書が | — | — | しょが | — | model_extra |
| 書く | かく | かく | — | かく | coverage_diff |
| 書くことばを | — | — | かくことばを | — | model_extra |
| 祝う | いわう | いわう | — | いわう | coverage_diff |
| 集まりました | あつまりました | あつまりました | しみらえました | あつまりました | reading_diff |

## Sentence 7 (hirogaru)
"山の近くにある寺に行きました。近くに住んでいる人のための寺ですから、観光客はあまり来ません。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| あまり | — | — | あまり | — | model_extra |
| ある | — | — | あある | — | model_extra |
| から | — | — | から | — | model_extra |
| ため | — | — | の | — | model_extra |
| に | — | — | ni, ni, ni | — | model_extra |
| の | — | — | no, no, の | — | model_extra |
| は | — | — | wa | — | model_extra |
| 住んで | — | — | — | すんで | model_missing |
| 住んでいる | すんでいる | すんでいる | すんでいる | — | model_extra |
| 来ません | きません | きません | こまない | きません | reading_diff |

## Sentence 8 (hirogaru)
"上には、木星や土星がありました。小さく地球も見えます。地球からの距離と、星の大きさを表しています。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| あり | — | — | あり | — | model_extra |
| から | — | — | から | — | model_extra |
| が | — | — | が | — | model_extra |
| と | — | — | と | — | model_extra |
| には | — | — | には | — | model_extra |
| の | — | — | の, の | — | model_extra |
| ました | — | — | ました | — | model_extra |
| も | — | — | も | — | model_extra |
| や | — | — | や | — | model_extra |
| を | — | — | を | — | model_extra |
| 木星 | もくせい | もくせい | きせい | もくせい | reading_diff |
| 表して | — | — | — | あらわして | model_missing |
| 表しています | あらわしています | あらわしています | ひょうしている | — | model_extra |

## Sentence 9 (hirogaru)
"ここは、中古の本を売っている店です。いろいろな人がここへ来て、読み終わった本を売ります。そして、店はその本を売ります。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 中古 | ちゅうこ | ちゅうこ | — | ちゅうこ | coverage_diff |
| 人 | ひと | ひと | — | ひと | coverage_diff |
| 売って | — | — | — | うって | model_missing |
| 売っている | うっている | うっている | — | — | model_extra |
| 売ります | うります, うります | うります, うります | — | うります, うります | coverage_diff |
| 店 | みせ, みせ | みせ, みせ | — | みせ, みせ | coverage_diff |
| 本 | ほん, ほん, ほん | ほん, ほん, ほん | — | ほん, ほん, ほん | coverage_diff |
| 来て | きて | きて | — | きて | coverage_diff |
| 終わった | — | — | — | おわった | model_missing |
| 読み | — | — | — | よみ | model_missing |
| 読み終わった | よみおわった | よみおわった | — | — | model_extra |

## Sentence 10 (hirogaru)
"和太鼓の演奏を見ました。このグループは、13年前から活動しています。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 13 | — | — | じゅうさん | — | model_extra |
| 13年前 | じゅうさんねんまえ | じゅうさんねんまえ | — | — | model_extra |
| から | — | — | から | — | model_extra |
| この | — | — | ここの | — | model_extra |
| しています | — | — | していいます | — | model_extra |
| に | — | — | ni | — | model_extra |
| の | — | — | no | — | model_extra |
| は | — | — | wa | — | model_extra |
| を | — | — | wo | — | model_extra |
| グループ | — | — | ぐるпп | — | model_extra |
| 前 | — | — | — | まえ | model_missing |
| 和 | — | — | わ | — | model_extra |
| 和太鼓 | わだいこ | わだいこ | — | わだいこ | coverage_diff |
| 太鼓 | — | — | たいこ | — | model_extra |
| 年 | — | — | — | ねん | model_missing |
| 年前 | — | — | ねんまえ | — | model_extra |
| 活動 | — | — | かつがく | — | model_extra |
| 活動して | — | — | — | かつどうして | model_missing |
| 活動しています | かつどうしています | かつどうしています | — | — | model_extra |

## Sentence 11 (hirogaru)
"大きい岩は砂浜の上にあって、自然の力を感じます。それで神社を作ったのかもしれません。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| 。 | — | — | 。, 。 | — | model_extra |
| あって | — | — | あって | — | model_extra |
| かもしれません | — | — | かのうするかもしれません | — | model_extra |
| それ | — | — | それ | — | model_extra |
| で | — | — | で, で | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の, の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| を | — | — | を, を | — | model_extra |
| 大きい | おおきい | おおきい | おおい | おおきい | reading_diff |
| 砂浜 | すなはま | すなはま | さはま | すなはま | reading_diff |

## Sentence 12 (hirogaru)
"鎖は、全部で200メートル以上あります。下を見ると怖くなりますから、下は見ないほうがいいです。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 200 | — | — | にひゃく | — | model_extra |
| あります | — | — | あります | — | model_extra |
| いい | — | — | いい | — | model_extra |
| から | — | — | kara | — | model_extra |
| で | — | — | de | — | model_extra |
| です | — | — | desu | — | model_extra |
| は | — | — | wa | — | model_extra |
| ほうが | — | — | 方が | — | model_extra |
| ると | — | — | ると | — | model_extra |
| を | — | — | o | — | model_extra |
| メートル | — | — | めーとる | — | model_extra |
| 下は | — | — | したは | — | model_extra |
| 以上 | いじょう | いじょう | いじょう | — | model_extra |
| 以上あります | — | — | — | いじょうあります | model_missing |
| 怖くなります | こわくなります | こわくなります | ふるrepidimasu | こわくなります | reading_diff |
| 見 | — | — | み | — | model_extra |
| 見る | — | みる | — | みる | coverage_diff |
| 見ると | みると | — | — | — | model_extra |
| 鎖 | くさり | くさり | さく | くさり | reading_diff |

## Sentence 13 (hirogaru)
"会社の近くにスーパーがあるので、ときどき昼休みにお弁当を買いに行きます。スーパーでは、たくさんのお弁当を売っています。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| ある | — | — | あり | — | model_extra |
| お弁当 | おべんとう, おべんとう | おべんとう, おべんとう | おべんとう, おべんとう | — | model_extra |
| が | — | — | ga | — | model_extra |
| たくさんの | — | — | たっかんさない | — | model_extra |
| で | — | — | de | — | model_extra |
| ときどき | — | — | ときどき | — | model_extra |
| に | — | — | ni, ni, ni | — | model_extra |
| の | — | — | no | — | model_extra |
| ので | — | — | で | — | model_extra |
| は | — | — | wa | — | model_extra |
| を | — | — | o, o | — | model_extra |
| スーパー | — | — | すぱー, すぱー | — | model_extra |
| 売って | — | — | — | うって | model_missing |
| 売っています | うっています | うっています | うつろっています | — | model_extra |
| 弁当 | — | — | — | べんとう, べんとう | model_missing |
| 昼休み | ひるやすみ | ひるやすみ | ちゅうやすみ | ひるやすみ | reading_diff |
| 行きます | いきます | — | いきます | いきます | coverage_diff |
| 買い | — | — | かisex | かい | reading_diff |
| 買いに | かいに | — | — | — | model_extra |
| 買いに行きます | — | かいにいきます | — | — | model_extra |

## Sentence 14 (hirogaru)
"でも、古い道場もあります。ここは、お城の中にある道場です。左の建物が道場で、右にお城が見えます。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| あります | — | — | あります | — | model_extra |
| ある | — | — | ある | — | model_extra |
| お城 | おしろ, おしろ | おしろ, おしろ | じょうじ, じょうじ | — | model_extra |
| が | — | — | が, が | — | model_extra |
| ここは | — | — | ここは | — | model_extra |
| で | — | — | で | — | model_extra |
| です | — | — | です | — | model_extra |
| でも | — | — | でも | — | model_extra |
| に | — | — | に | — | model_extra |
| の中 | — | — | なか | — | model_extra |
| も | — | — | も | — | model_extra |
| 中 | なか | なか | — | なか | coverage_diff |
| 古い | ふるい | ふるい | ふるい | — | model_extra |
| 右 | みぎ | みぎ | — | みぎ | coverage_diff |
| 右に | — | — | みぎに | — | model_extra |
| 城 | — | — | — | しろ, しろ | model_missing |
| 左 | ひだり | ひだり | — | ひだり | coverage_diff |
| 左の | — | — | ひだりの | — | model_extra |

## Sentence 15 (hirogaru)
"七五三は11月に行くことが多いです。着物を着る人もたくさんいます。この日はいい天気でした。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 11月 | じゅういちがつ | じゅういちがつ | じゅういちがつ | — | model_extra |
| いい | — | — | いい | — | model_extra |
| います | — | — | いります | — | model_extra |
| ことが多い | — | — | 多いです | — | model_extra |
| この | — | — | この | — | model_extra |
| たくさん | — | — | たんかん | — | model_extra |
| でした | — | — | でいました | — | model_extra |
| です | — | — | です | — | model_extra |
| に行く | — | — | いきに | — | model_extra |
| は | — | — | は, は | — | model_extra |
| も | — | — | も | — | model_extra |
| を | — | — | を | — | model_extra |
| 七五三 | しちごさん | しちごさん | ななご三四 | しちごさん | reading_diff |
| 多い | おおい | おおい | — | おおい | coverage_diff |
| 月 | — | — | — | がつ | model_missing |
| 行く | いく | いく | — | いく | coverage_diff |

## Sentence 16 (hirogaru)
"Q笛をどこで知りましたか。きっかけを教えてください。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| Q | — | — | Q | — | model_extra |
| か | — | — | か | — | model_extra |
| きっかけを | — | — | きっぱしあいを | — | model_extra |
| どこで | — | — | どこで | — | model_extra |
| を | — | — | を | — | model_extra |
| 教えて | おしえて | — | — | おしえて | coverage_diff |
| 教えてください | — | おしえてください | 教えてください | — | model_extra |
| 知りました | — | しりました | しりました | — | model_extra |
| 知りましたか | しりましたか | — | — | しりましたか | coverage_diff |
| 笛 | ふえ | ふえ | ぶえ | ふえ | reading_diff |

## Sentence 17 (hirogaru)
"服を作る人もいますが、私はインターネットの専門の店で買っています。着なくなった服は、友達にあげたり、売ったりします。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| あげたり | — | — | あげたり | — | model_extra |
| いますが | — | — | がいますが | — | model_extra |
| が | — | — | が | — | model_extra |
| で | — | — | で | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の, の | — | model_extra |
| は | — | — | は, は | — | model_extra |
| も | — | — | も | — | model_extra |
| インターネット | — | — | いんTERNET | — | model_extra |
| 友達 | ともだち | ともだち | ゆうだち | ともだち | reading_diff |
| 売った | — | — | — | うった | model_missing |
| 売ったり | うったり | — | うりたり | — | model_extra |
| 売ったりします | — | うったりします | — | — | model_extra |
| 店 | みせ | みせ | てん | みせ | reading_diff |
| 着 | — | — | — | き | model_missing |
| 着なくなった | きなくなった | きなくなった | きなくなった | — | model_extra |
| 買って | — | — | — | かって | model_missing |
| 買っています | かっています | かっています | かっています | — | model_extra |

## Sentence 18 (hirogaru)
"京都の夕方の空です。少し暗くなって、この後、夜景になりました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、, 、 | — | model_extra |
| この後 | — | — | このご | — | model_extra |
| です | — | — | desu | — | model_extra |
| になりました | — | — | なりました | — | model_extra |
| の | — | — | no, no | — | model_extra |
| 夕方 | ゆうがた | ゆうがた | ゆうがつ | ゆうがた | reading_diff |
| 後 | あと | あと | — | あと | coverage_diff |
| 暗くなって | くらくなって | くらくなって | あんになって | くらくなって | reading_diff |

## Sentence 19 (hirogaru)
"一瞬でも好きなキャラクターになれることです。コスプレをして撮った写真を見ているときは、とても幸せです。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| こと | — | — | こと | — | model_extra |
| して | — | — | して | — | model_extra |
| です | — | — | です, です | — | model_extra |
| でも | — | — | でも | — | model_extra |
| とき | — | — | とき | — | model_extra |
| とても | — | — | とても | — | model_extra |
| な | — | — | な | — | model_extra |
| になれる | — | — | になりえる | — | model_extra |
| は | — | — | は | — | model_extra |
| を | — | — | を, を | — | model_extra |
| キャラクター | — | — | きゃらくたー | — | model_extra |
| コスプレ | — | — | こすぷれ | — | model_extra |
| 好き | — | — | すき | — | model_extra |
| 好きな | すきな | すきな | — | すきな | coverage_diff |
| 幸せ | しあわせ | しあわせ | しずかい | しあわせ | reading_diff |
| 見て | — | — | — | みて | model_missing |
| 見ている | みている | みている | みている | — | model_extra |

## Sentence 20 (hirogaru)
"Q. どうしてウクレレの店を作りましたか。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| Q | — | — | Q | — | model_extra |
| か | — | — | か | — | model_extra |
| どうして | — | — | どうして | — | model_extra |
| の | — | — | の | — | model_extra |
| を | — | — | を | — | model_extra |
| ウクレレ | — | — | うくれれ | — | model_extra |
| 作りました | — | つくりました | つくりました | — | model_extra |
| 作りましたか | つくりましたか | — | — | つくりましたか | coverage_diff |
| 店 | みせ | みせ | てん | みせ | reading_diff |

## Sentence 21 (kahoku)
"東北野生動物保護管理センター（自然の中で生きる動物を研究している所）の小野田泰士さんは「台原森林公園は広いので、カモシカが住むこともできます。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| 「 | — | — | 「 | — | model_extra |
| 」 | — | — | 」 | — | model_extra |
| が | — | — | が | — | model_extra |
| ことも | — | — | ことも | — | model_extra |
| さん | — | — | さん | — | model_extra |
| できます | — | — | できる | — | model_extra |
| の | — | — | の | — | model_extra |
| ので | — | — | ので | — | model_extra |
| は | — | — | は | — | model_extra |
| カモシカ | — | — | かもし 'か', 'し', 'か' | — | model_extra |
| 中 | なか | なか | — | なか | coverage_diff |
| 保護 | — | — | — | ほご | model_missing |
| 公園 | — | — | — | こうえん | model_missing |
| 動物 | どうぶつ | どうぶつ | — | どうぶつ, どうぶつ | coverage_diff |
| 台原森林 | — | — | — | だいのはらしんりん | model_missing |
| 台原森林公園 | だいのはらしんりんこうえん | だいのはらしんりんこうえん | だいげんじしんこうえん | — | model_extra |
| 小野田 | — | — | おのだ | おのだ | coverage_diff |
| 小野田泰士 | おのだたいじ | おのだやすし | — | — | model_extra |
| 所 | ところ | ところ | — | ところ | coverage_diff |
| 東北 | — | — | とうほく | とうほく | coverage_diff |
| 東北野生動物保護管理 | とうほくやせいどうぶつほごかんり | — | — | — | model_extra |
| 東北野生動物保護管理センター | — | とうほくやせいどうぶつほごかんりせんたー | — | — | model_extra |
| 泰士 | — | — | やすし | たいじ | reading_diff |
| 生きる | いきる | いきる | — | いきる | coverage_diff |
| 研究して | — | — | — | けんきゅうして | model_missing |
| 研究している | けんきゅうしている | けんきゅうしている | — | — | model_extra |
| 管理 | — | — | — | かんり | model_missing |
| 自然 | しぜん | しぜん | — | しぜん | coverage_diff |
| 野生 | — | — | — | やせい | model_missing |
| 野生動物保護管理センター | — | — | しんせいぶどうぼうごうかん | — | model_extra |
| （自然の中で生きる動物を研究している所） | — | — | （しぜんの中でいきるどうぶつをけんきゅうしているところ） | — | model_extra |

## Sentence 22 (kahoku)
"隣りの涌谷町から来た古川黎明中学校２年生、富樫優愛さん（１３歳）は「親も食べたいと言っていたので買いに来ました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 13 | — | — | じゅうさん | — | model_extra |
| 2年生 | — | — | にねんせい | — | model_extra |
| 、 | — | — | 、 | — | model_extra |
| 「 | — | — | 「 | — | model_extra |
| から | — | — | から | — | model_extra |
| さん | — | — | さん | — | model_extra |
| た | — | — | た | — | model_extra |
| と | — | — | と | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | no | — | model_extra |
| ので | — | — | ので | — | model_extra |
| は | — | — | は | — | model_extra |
| ま | — | — | ま | — | model_extra |
| も | — | — | も | — | model_extra |
| 中学校 | — | — | ちゅうがっこう | — | model_extra |
| 優愛 | — | ゆあ | ゆあい | ゆあ | reading_diff |
| 古川 | — | — | ふるかわ | — | model_extra |
| 古川黎明中学校 | ふるかわれいめいちゅうがっこう | ふるかわれいめいちゅうがっこう | — | ふるかわれいめいちゅうがっこう | coverage_diff |
| 富樫 | — | とがし | としだ | とがし | reading_diff |
| 富樫優愛 | とがしゆあ | — | — | — | model_extra |
| 年生 | — | — | — | ねんせい | model_missing |
| 来 | — | — | きた, きた | — | model_extra |
| 来た | きた | きた | — | きた | coverage_diff |
| 来ました | きました | きました | — | きました | coverage_diff |
| 歳 | — | — | さい | さい | coverage_diff |
| 涌谷町 | わくやちょう | わくやちょう | ゆきやちょう | わくやちょう | reading_diff |
| 親 | おや | おや | しん | おや | reading_diff |
| 言って | — | — | — | いって | model_missing |
| 言っていた | いっていた | いっていた | いっていた | — | model_extra |
| 買 | — | — | か | — | model_extra |
| 買い | — | かい | — | かい | coverage_diff |
| 買いに | かいに | — | — | — | model_extra |
| 黎明 | — | — | れいめい | — | model_extra |
| （ | — | — | （ | — | model_extra |
| ） | — | — | ） | — | model_extra |
| １３歳 | じゅうさんさい | じゅうさんさい | — | — | model_extra |
| ２年生 | にねんせい | にねんせい | — | — | model_extra |

## Sentence 23 (kahoku)
"ここで４月、国の特別天然記念物（国が決めて特に大切に守っている珍しいもの）のニホンカモシカが、何度も見られています。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| が | — | — | が, が, が | — | model_extra |
| ここ | — | — | ここ | — | model_extra |
| で | — | — | で | — | model_extra |
| の | — | — | の, の | — | model_extra |
| もの | — | — | もの | — | model_extra |
| ニホンカモシカ | — | — | にほんかもしが | — | model_extra |
| 何度 | なんど | なんど | — | なんど | coverage_diff |
| 何度も | — | — | おおいに | — | model_extra |
| 大切 | — | — | — | たいせつ | model_missing |
| 大切に | たいせつに | たいせつに | たいせつな | — | model_extra |
| 天然 | — | — | — | てんねん | model_missing |
| 天然記念物 | — | — | てんねんきねんぶつ | — | model_extra |
| 守って | — | — | — | まもって | model_missing |
| 守っている | まもっている | まもっている | まもっている | — | model_extra |
| 月 | — | — | — | がつ | model_missing |
| 特 | — | — | — | とく | model_missing |
| 特に | とくに | とくに | とくべつ | — | model_extra |
| 特別 | — | — | とくべつ | とくべつ | coverage_diff |
| 特別天然記念物 | とくべつてんねんきねんぶつ | とくべつてんねんきねんぶつ | — | — | model_extra |
| 見られて | — | — | — | みられて | model_missing |
| 見られています | みられています | みられています | みられています | — | model_extra |
| 記念物 | — | — | — | きねんぶつ | model_missing |
| （ | — | — | （ | — | model_extra |
| ） | — | — | ） | — | model_extra |
| ４月 | しがつ | しがつ | よんがつ | — | model_extra |

## Sentence 24 (kahoku)
"また、実習生たちは、日本語教室で練習した曲「もしもピアノが弾けたなら」も歌いました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| たちは | — | — | たち | — | model_extra |
| で | — | — | で | — | model_extra |
| また | — | — | また | — | model_extra |
| も | — | — | も | — | model_extra |
| もしもピアノが弾けたなら | — | — | もしもぴあのがひかれたなら | — | model_extra |
| 実習 | — | — | — | じっしゅう | model_missing |
| 実習生 | じっしゅうせい | じっしゅうせい | じっしゅうせい | — | model_extra |
| 弾けたなら | ひけたなら | ひけたなら | — | ひけたなら | coverage_diff |
| 教室 | — | — | きょうしつ | きょうしつ | coverage_diff |
| 日本語 | — | — | にほんご | にほんご | coverage_diff |
| 日本語教室 | にほんごきょうしつ | にほんごきょうしつ | — | — | model_extra |
| 生 | — | — | — | せい | model_missing |
| 練習した | れんしゅうした | れんしゅうした | ねんしゅうした | れんしゅうした | reading_diff |

## Sentence 25 (kahoku)
"太白区金剛沢コミュニティ・センターの健康マージャン教室に１０年間、毎週通いました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 10年間 | — | — | じゅうねんかん | — | model_extra |
| 、 | — | — | 、 | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の | — | model_extra |
| コミュニティ・センター | — | — | こみゅうらいと・せんたー | — | model_extra |
| マージャン | — | — | まじｬﾝ | — | model_extra |
| 区 | — | — | く | — | model_extra |
| 太白 | — | — | たいはく | — | model_extra |
| 太白区 | たいはくく | たいはくく | — | たいはくく | coverage_diff |
| 年 | — | — | — | ねん | model_missing |
| 沢 | — | — | さわ | — | model_extra |
| 通いました | かよいました | かよいました | とりました | かよいました | reading_diff |
| 金刚 | — | — | ごうかん | — | model_extra |
| 金剛沢 | こんごうざわ | こんごうざわ | — | こんごうざわ | coverage_diff |
| 間 | — | — | — | かん | model_missing |
| １０年間 | じゅうねんかん | じゅうねんかん | — | — | model_extra |

## Sentence 26 (kahoku)
"神様のために踊った小学校６年生の佐藤実織さん（１１歳）は「自然が好きなので、神社へ来るととても気持ちが良くなります。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| 「 | — | — | 「 | — | model_extra |
| が | — | — | が, が | — | model_extra |
| さん | — | — | さん | — | model_extra |
| ため | — | — | ため | — | model_extra |
| とても | — | — | とても | — | model_extra |
| なので | — | — | ので | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の | — | model_extra |
| は | — | — | は | — | model_extra |
| へ | — | — | へ | — | model_extra |
| 佐藤 | — | さとう | さとう | さとう | coverage_diff |
| 佐藤実織 | さとうみおり | — | — | — | model_extra |
| 好き | — | — | すき | — | model_extra |
| 好きな | すきな | すきな | — | すきな | coverage_diff |
| 実 | — | — | — | み | model_missing |
| 実織 | — | みおり | みおり | — | model_extra |
| 年生 | — | — | — | ねんせい | model_missing |
| 来る | くる | くる | — | くる | coverage_diff |
| 来ると | — | — | きると | — | model_extra |
| 様 | — | — | さま | — | model_extra |
| 歳 | — | — | — | さい | model_missing |
| 気持ち | きもち | きもち | 気持 | きもち | reading_diff |
| 神 | — | — | かみ | — | model_extra |
| 神様 | かみさま | かみさま | — | かみさま | coverage_diff |
| 織 | — | — | — | おり | model_missing |
| 良くなります | よくなります | よくなります | よろこびになります | よくなります | reading_diff |
| （ | — | — | （ | — | model_extra |
| ） | — | — | ） | — | model_extra |
| １１歳 | じゅういっさい | じゅういっさい | じゅういちさい | — | model_extra |
| ６年生 | ろくねんせい | ろくねんせい | ろくねんせい | — | model_extra |

## Sentence 27 (kahoku)
"仙台市青葉区の台原森林公園は、広くて緑が多い公園です。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| です | — | — | です | — | model_extra |
| の | — | — | の | — | model_extra |
| は | — | — | は | — | model_extra |
| 仙台 | — | — | せんだい | — | model_extra |
| 仙台市 | せんだいし | せんだいし | — | せんだいし | coverage_diff |
| 公園 | こうえん | こうえん | — | こうえん, こうえん | coverage_diff |
| 公園です | — | — | こうえんです | — | model_extra |
| 区 | — | — | く | — | model_extra |
| 台原 | — | — | だいげん | — | model_extra |
| 台原森林 | — | — | — | だいのはらしんりん | model_missing |
| 台原森林公園 | だいのはらしんりんこうえん | だいのはらしんりんこうえん | — | — | model_extra |
| 多い | おおい | おおい | — | おおい | coverage_diff |
| 市 | — | — | し | — | model_extra |
| 森林公園 | — | — | しんりんこうえん | — | model_extra |
| 緑 | みどり | みどり | — | みどり | coverage_diff |
| 緑が多い | — | — | みどりがおおい | — | model_extra |
| 青葉 | — | — | あおば | — | model_extra |
| 青葉区 | あおばく | あおばく | — | あおばく | coverage_diff |

## Sentence 28 (kahoku)
"高校２年生の阿部日夏さんは「ブルーベリーで有名な富谷市のことを知ってほしかったです。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 2年生 | — | — | にねんせい | — | model_extra |
| 「 | — | — | 「 | — | model_extra |
| 」 | — | — | 」 | — | model_extra |
| こと | — | — | こと | — | model_extra |
| さん | — | — | さん | — | model_extra |
| で | — | — | で | — | model_extra |
| です | — | — | です | — | model_extra |
| の | — | — | の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| ほしい | — | — | ほしがった | — | model_extra |
| を | — | — | を | — | model_extra |
| ブルーベリー | — | — | ぶるべりー | — | model_extra |
| 富谷市 | とみやし | とみやし | とあしつ | — | model_extra |
| 富谷市のこ | — | — | — | とみやしのこ | model_missing |
| 年生 | — | — | — | ねんせい | model_missing |
| 日夏 | — | — | ひか | — | model_extra |
| 知って | しって | — | — | しって | coverage_diff |
| 知っている | — | — | しっている | — | model_extra |
| 知ってほしかったです | — | しってほしかったです | — | — | model_extra |
| 阿部 | — | — | あべ | — | model_extra |
| 阿部日夏 | あべひなつ | あべひなつ | — | あべひなつ | coverage_diff |
| 高校 | こうこう | — | こうか | こうこう | reading_diff |
| 高校２年生 | — | こうこうにねんせい | — | — | model_extra |
| ２年生 | にねんせい | — | — | — | model_extra |

## Sentence 29 (kahoku)
"それで、八木山動物公園と大森山動物園は話をして、雌のアフリカゾウを取り換えてみることにしました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、, 、 | — | model_extra |
| して | — | — | して | — | model_extra |
| しました | — | — | しました | — | model_extra |
| それ | — | — | それ | — | model_extra |
| で | — | — | で | — | model_extra |
| と | — | — | と | — | model_extra |
| に | — | — | に | — | model_extra |
| は | — | — | は | — | model_extra |
| み | — | — | み | — | model_extra |
| ること | — | — | こと | — | model_extra |
| を | — | — | を, を | — | model_extra |
| アフリカゾウ | — | — | あふりかぞう | — | model_extra |
| 八木山 | — | — | はぎやま | やぎやま | reading_diff |
| 八木山動物公園 | やぎやまどうぶつこうえん | やぎやまどうぶつこうえん | — | — | model_extra |
| 動物 | — | — | — | どうぶつ | model_missing |
| 動物公園 | — | — | どうぶつこうえん | どうぶつこうえん | coverage_diff |
| 動物園 | — | — | どうぶつえん | — | model_extra |
| 取り | — | — | — | とり | model_missing |
| 取り換えて | とりかえて | — | とりかえて | — | model_extra |
| 取り換えてみる | — | とりかえてみる | — | — | model_extra |
| 園 | — | — | — | えん | model_missing |
| 大森山 | — | — | おおもりやま | おおもりやま | coverage_diff |
| 大森山動物園 | おおもりやまどうぶつえん | おおもりやまどうぶつえん | — | — | model_extra |
| 換えて | — | — | — | かえて | model_missing |
| 話 | はなし | はなし | わ | はなし | reading_diff |
| 雌 | めす | めす | — | めす | coverage_diff |
| 雌の | — | — | めの | — | model_extra |

## Sentence 30 (kahoku)
"７月１２日、初めて売った日は２０人ぐらいの人が並びました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| ぐらい | — | — | くらい | — | model_extra |
| の | — | — | の | — | model_extra |
| は | — | — | は | — | model_extra |
| 人 | ひと | ひと | — | ひと | coverage_diff |
| 人が | — | — | ひとが | — | model_extra |
| 人ぐらい | — | — | — | にんぐらい | model_missing |
| 売った | うった | うった | いた | うった | reading_diff |
| 日 | ひ | ひ | ひ | にち, ひ | reading_diff |
| 月 | — | — | — | がつ | model_missing |
| １２日 | じゅうににち | じゅうににち | じゅうにひ | — | model_extra |
| ２０人 | にじゅうにん | にじゅうにん | にん | — | model_extra |
| ７月 | しちがつ | しちがつ | なながつ | — | model_extra |

## Sentence 31 (kahoku)
"それで、仙台市の宮城野高校にあげることを決めました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| あげること | — | — | あげること | — | model_extra |
| それ | — | — | それ | — | model_extra |
| で | — | — | で | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の | — | model_extra |
| を | — | — | を | — | model_extra |
| 宮城野 | — | — | みやぎの | みやぎの | coverage_diff |
| 宮城野高校 | みやぎのこうこう | みやぎのこうこう | — | — | model_extra |
| 高校 | — | — | こうこう | こうこう | coverage_diff |

## Sentence 32 (kahoku)
"高校生たちは、ブルーベリーを使って紫色の液体（水のような物）を作りました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| たち | — | — | たち | — | model_extra |
| の | — | — | の | — | model_extra |
| のような | — | — | にごうの | — | model_extra |
| は | — | — | は | — | model_extra |
| を | — | — | を | — | model_extra |
| を作りました | — | — | をつくりました | — | model_extra |
| ブルーベリー | — | — | ぶるーべりー | — | model_extra |
| 作りました | つくりました | つくりました | — | つくりました | coverage_diff |
| 高校生 | こうこうせい | こうこうせい | こうがせい | こうこうせい | reading_diff |
| （ | — | — | （ | — | model_extra |
| ） | — | — | ） | — | model_extra |

## Sentence 33 (kahoku)
"斎藤正美市長は「新しい大人の皆さんは石巻市を元気にする、とても大切な人たちです」と、あいさつをしました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、, 、 | — | model_extra |
| 「 | — | — | 「 | — | model_extra |
| 」 | — | — | 」 | — | model_extra |
| あいさつ | — | — | あいさつ | — | model_extra |
| しました | — | — | しました | — | model_extra |
| です | — | — | です | — | model_extra |
| と | — | — | と | — | model_extra |
| とても | — | — | とても | — | model_extra |
| にする | — | — | にします | — | model_extra |
| の | — | — | の | — | model_extra |
| は | — | — | は, は | — | model_extra |
| を | — | — | を, を | — | model_extra |
| 元気 | げんき | — | げんき | げんき | coverage_diff |
| 元気にする | — | げんきにする | — | — | model_extra |
| 大人 | おとな | おとな | だいじん | おとな | reading_diff |
| 市 | — | — | し | — | model_extra |
| 斎藤 | — | — | さいとう | さいとう | coverage_diff |
| 斎藤正美 | さいとうまさみ | さいとうまさみ | — | — | model_extra |
| 正美 | — | — | まさみ | まさみ | coverage_diff |
| 皆 | みな | みな | — | みな | coverage_diff |
| 皆さん | — | — | みなさん | — | model_extra |
| 石巻 | — | — | いわさき | — | model_extra |
| 石巻市 | いしのまきし | いしのまきし | — | いしのまきし | coverage_diff |

## Sentence 34 (kahoku)
"それで、花も大きくなって、きれいに育ちました」と話しました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 大きく | — | — | — | おおきく | model_missing |
| 大きくなって | おおきくなって | おおきくなって | — | — | model_extra |
| 育ちました | そだちました | そだちました | — | そだちました | coverage_diff |
| 花 | はな | はな | — | はな | coverage_diff |
| 話しました | はなしました | はなしました | — | はなしました | coverage_diff |

## Sentence 35 (kahoku)
"授業には、富谷小学校の３年生５８人が参加しました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| が | — | — | が | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の | — | model_extra |
| は | — | — | は | — | model_extra |
| 人 | — | — | — | にん | model_missing |
| 富谷 | — | — | とごう | とみや | reading_diff |
| 富谷小学校 | とみやしょうがっこう | とみやしょうがっこう | — | — | model_extra |
| 小学校 | — | — | しょうがっこう | しょうがっこう | coverage_diff |
| 年生 | — | — | — | ねんせい | model_missing |
| ３年生 | さんねんせい | さんねんせい | さんねんせい | — | model_extra |
| ５８人 | ごじゅうはちにん | ごじゅうはちにん | ごじゅうはちにん | — | model_extra |

## Sentence 36 (kahoku)
"１１月１０日には、２０人くらいの人たちがアメリカザリガニとウシガエルを使った料理を食べました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| が | — | — | が | — | model_extra |
| くらい | — | — | くらい | — | model_extra |
| と | — | — | と | — | model_extra |
| には | — | — | には | — | model_extra |
| の人たち | — | — | のひとたち | — | model_extra |
| を | — | — | を | — | model_extra |
| を使った | — | — | はいた | — | model_extra |
| アメリカザリガニ | — | — | あめりかざりがに | — | model_extra |
| ウシガエル | — | — | うしがえる | — | model_extra |
| 人 | ひと | ひと | — | ひと | coverage_diff |
| 人くらい | — | — | — | にんくらい | model_missing |
| 使った | つかった | つかった | — | つかった | coverage_diff |
| 日 | — | — | — | か | model_missing |
| 月 | — | — | — | がつ | model_missing |
| １０日 | とおか | とおか | とおか | — | model_extra |
| １１月 | じゅういちがつ | じゅういちがつ | じゅうにがつ | — | model_extra |
| ２０人 | にじゅうにん | にじゅうにん | にん | — | model_extra |

## Sentence 37 (kahoku)
"木村さんは、１８年前、名古屋の大学に通うために、名古屋市に引っ越ししました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 前 | — | — | — | まえ | model_missing |
| 名古屋 | なごや | なごや | — | なごや | coverage_diff |
| 名古屋市 | なごやし | なごやし | — | なごやし | coverage_diff |
| 大学 | だいがく | だいがく | — | だいがく | coverage_diff |
| 年 | — | — | — | ねん | model_missing |
| 引っ | — | — | — | ひっ | model_missing |
| 引っ越しし | ひっこしし | — | — | — | model_extra |
| 引っ越ししました | — | ひっこししました | — | — | model_extra |
| 木村 | きむら | きむら | — | きむら | coverage_diff |
| 越 | — | — | — | こ | model_missing |
| 通う | かよう | かよう | — | かよう | coverage_diff |
| １８年前 | じゅうはちねんまえ | じゅうはちねんまえ | — | — | model_extra |

## Sentence 38 (kahoku)
"生徒の親たちは、卒業する３年生のためにプレゼントをしようと思いました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| しよう | — | — | しよう | — | model_extra |
| する | — | — | す | — | model_extra |
| たちは | — | — | たちは | — | model_extra |
| ために | — | — | のぞみに | — | model_extra |
| と | — | — | to | — | model_extra |
| の | — | — | no, no | — | model_extra |
| を | — | — | o | — | model_extra |
| プレゼント | — | — | ぷれすてん | — | model_extra |
| 卒業 | — | — | そつぎょう | — | model_extra |
| 卒業する | そつぎょうする | そつぎょうする | — | そつぎょうする | coverage_diff |
| 年生 | — | — | — | ねんせい | model_missing |
| 親 | おや | おや | しん | おや | reading_diff |
| ３年生 | さんねんせい | さんねんせい | さんねんせい | — | model_extra |

## Sentence 39 (kahoku)
"山形県朝日町には、空気を神様にした「空気神社」があります。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| 「 | — | — | 「 | — | model_extra |
| 」 | — | — | 」 | — | model_extra |
| あります | — | — | あります | — | model_extra |
| が | — | — | が | — | model_extra |
| した | — | — | した | — | model_extra |
| に | — | — | に | — | model_extra |
| には | — | — | には | — | model_extra |
| を | — | — | を | — | model_extra |
| 山形 | — | — | やまがた | — | model_extra |
| 山形県 | やまがたけん | やまがたけん | — | やまがたけん | coverage_diff |
| 朝日 | — | — | あさひ | — | model_extra |
| 朝日町 | あさひまち | あさひまち | — | あさひまち | coverage_diff |
| 町 | — | — | ちょう | — | model_extra |
| 県 | — | — | けん | — | model_extra |
| 神社 | — | — | — | じんじゃ | model_missing |
| 空気神社 | くうきじんじゃ | くうきじんじゃ | くうきじんじゃ | — | model_extra |

## Sentence 40 (kahoku)
"３月２４日には、９０人くらいの人が来ました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| が | — | — | が | — | model_extra |
| くらいの | — | — | くらいの | — | model_extra |
| には | — | — | には | — | model_extra |
| 人くらい | — | — | — | にんくらい | model_missing |
| 月 | — | — | — | がつ | model_missing |
| ２４日 | にじゅうよっか | — | にじゅうよっか | にじゅうよっか | coverage_diff |
| ３月 | さんがつ | — | さんがつ | — | model_extra |
| ３月２４日 | — | さんがつにじゅうよっか | — | — | model_extra |
| ９０人 | きゅうじゅうにん | きゅうじゅうにん | きゅうじゅうにん | — | model_extra |

## Sentence 41 (nhk)
"家族の1人、横田早紀江さんはトランプ大統領に会ったあと「大統領は拉致の問題をよく考えていると思いました。大統領が北朝鮮のトップに会ったら、必ずこの問題のことを話してほしいです」と話しました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 1人 | ひとり | ひとり | いちにん | ひとり | reading_diff |
| 、 | — | — | 、 | — | model_extra |
| 「 | — | — | 「 | — | model_extra |
| 」 | — | — | 」 | — | model_extra |
| あと | — | — | あと | — | model_extra |
| が | — | — | が | — | model_extra |
| こと | — | — | こと | — | model_extra |
| この | — | — | こ | — | model_extra |
| さん | — | — | さん | — | model_extra |
| です | — | — | です | — | model_extra |
| と | — | — | と, と | — | model_extra |
| に | — | — | に, に | — | model_extra |
| の | — | — | の, の, の, の | — | model_extra |
| は | — | — | は, は | — | model_extra |
| ほしい | — | — | ほしが | — | model_extra |
| よく | — | — | よく | — | model_extra |
| を | — | — | を, を | — | model_extra |
| トップ | — | — | ちょう | — | model_extra |
| トランプ | — | — | とらむぷ | — | model_extra |
| 会ったら | あったら | あったら | あったら | — | model_extra |
| 問題のこ | — | — | — | もんだいのこ | model_missing |
| 必ず | かならず | かならず | ぜったい | かならず | reading_diff |
| 早紀江 | さきえ | — | はやきえ | さきえ | reading_diff |
| 横田 | よこた | — | よこた | よこた | coverage_diff |
| 横田早紀江 | — | よこたさきえ | — | — | model_extra |
| 考えて | — | — | — | かんがえて | model_missing |
| 考えている | — | かんがえている | かんがえている | — | model_extra |
| 考えていると | かんがえていると | — | — | — | model_extra |
| 話して | はなして | — | はなして | はなして | coverage_diff |
| 話してほしい | — | はなしてほしい | — | — | model_extra |

## Sentence 42 (nhk)
"永井さんは、石川県輪島市の出身で、漫画「マジンガーＺ」などで有名です。ことし4月、永井さんは地震で被害のあった人たちを助けたいと考えて、オークションに絵を出しました。200人以上の漫画家も一緒に絵を出しました。このオークションで1億2300万円が集まりました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 1億2300万円 | いちおくにせんさんびゃくまんえん | いちおくにせんさんびゃくまんえん | いちおくにせんさんびゃくまんえん | — | model_extra |
| 200人 | — | にひゃくにん | にひゃくじん | — | model_extra |
| 200人以上 | にひゃくにんいじょう | — | — | — | model_extra |
| 4月 | しがつ | しがつ | よんがつ | — | model_extra |
| あった | — | — | あっただ | — | model_extra |
| が | — | — | が | — | model_extra |
| ことし | — | — | ことし | — | model_extra |
| この | — | — | ここの | — | model_extra |
| さん | — | — | さん, さん | — | model_extra |
| たち | — | — | たち | — | model_extra |
| て | — | — | て | — | model_extra |
| で | — | — | で, で, で, で | — | model_extra |
| です | — | — | です | — | model_extra |
| と | — | — | と | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の, の, の | — | model_extra |
| も | — | — | も | — | model_extra |
| を | — | — | を, を, を | — | model_extra |
| オークション | — | — | おーくせんと, おーくせんと | — | model_extra |
| マジンガー | — | — | まじngr | — | model_extra |
| 一緒 | いっしょ | — | — | いっしょ | coverage_diff |
| 一緒に | — | いっしょに | いっしょに | — | model_extra |
| 万 | — | — | — | まん | model_missing |
| 人 | ひと | ひと | じん | ひと, にん | reading_diff |
| 以上 | — | いじょう | いじょう | いじょう | coverage_diff |
| 億 | — | — | — | おく | model_missing |
| 円 | — | — | — | えん | model_missing |
| 出しました | だしました, だしました | だしました, だしました | だいしました, だいしました | だしました, だしました | reading_diff |
| 出身 | しゅっしん | しゅっしん | しゅっせん | しゅっしん | reading_diff |
| 月 | — | — | — | がつ | model_missing |
| 石川県 | いしかわけん | いしかわけん | せいかんけん | いしかわけん | reading_diff |
| 考え | — | — | かんがえ | — | model_extra |
| 考えて | かんがえて | かんがえて | — | かんがえて | coverage_diff |
| 被害 | ひがい | ひがい | はいば | ひがい | reading_diff |
| 集まりました | あつまりました | あつまりました | しみらめいまし | あつまりました | reading_diff |
| Ｚ | — | — | Ｚ | — | model_extra |

## Sentence 43 (nhk)
"北海道と青森県、岩手県、宮城県、福島県、茨城県、千葉県の182の市や町などに住んでいる人は、これから1週間は地震があったときの準備をチェックしてほしいと言いました。避難場所や逃げるときの荷物をもう一度みてください。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 182の市や町などに | — | — | ひゃくはちにんのいちばやまちなどに | — | model_extra |
| 1週間 | いっしゅうかん | いっしゅうかん | — | — | model_extra |
| これから1週間 | — | — | こんじゅういちしゅっかん | — | model_extra |
| は | — | — | は, は | — | model_extra |
| や | — | — | や | — | model_extra |
| チェックしてほしいと言いました | — | — | けっかしてほしみていました | — | model_extra |
| 一度 | いちど | いちど | — | — | model_extra |
| 一度みてく | — | — | — | いちどみてく | model_missing |
| 人 | ひと | ひと | — | ひと | coverage_diff |
| 住んで | — | — | — | すんで | model_missing |
| 住んでいる | すんでいる | すんでいる | — | — | model_extra |
| 住んでいる人 | — | — | すみんでいるひと | — | model_extra |
| 地震 | じしん | じしん | — | じしん | coverage_diff |
| 地震があったときの準備を | — | — | じしんがあったときのじゅんびを | — | model_extra |
| 場所 | — | — | — | ばしょ | model_missing |
| 市 | し | し | — | し | coverage_diff |
| 準備 | じゅんび | じゅんび | — | じゅんび | coverage_diff |
| 町 | まち | まち | — | まち | coverage_diff |
| 茨城県 | いばらきけん | いばらきけん | ちばけん | いばらきけん | reading_diff |
| 荷物 | にもつ | にもつ | — | にもつ | coverage_diff |
| 言いました | いいました | いいました | — | いいました | coverage_diff |
| 逃げる | にげる | にげる | — | にげる | coverage_diff |
| 逃げるときの荷物を | — | — | にげるときのたもとを | — | model_extra |
| 週間 | — | — | — | しゅうかん | model_missing |
| 避難 | — | — | — | ひなん | model_missing |
| 避難場所 | ひなんばしょ | ひなんばしょ | ひなんばしょ | — | model_extra |

## Sentence 44 (nhk)
"沖縄県でビールをつくっている会社の「オリオンビール」が、25日、東京証券取引所で株を上場しました。上場すると、株を売ったり、買ったりすることができます。午前は買いたい人が多くて、値段が決まりませんでした。午後になって決まって、25日の最後の値段は1950円でした。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 1950円 | せんきゅうひゃくごじゅうえん | せんきゅうひゃくごじゅうえん | せんきゅうひゃくえん | — | model_extra |
| 25日 | にじゅうごにち, にじゅうごにち | にじゅうごにち, にじゅうごにち | にちじ | — | model_extra |
| 25日の | — | — | にちの | — | model_extra |
| 、 | — | — | 、, 、, 、, 、, 、, 、 | — | model_extra |
| 。 | — | — | 。, 。 | — | model_extra |
| 「オリオンビール」 | — | — | 「おりょんびえる」 | — | model_extra |
| が | — | — | が, が | — | model_extra |
| することができます | — | — | できることができます | — | model_extra |
| つくっている | — | — | つくりつている | — | model_extra |
| で | — | — | で, で | — | model_extra |
| でした | — | — | でいました | — | model_extra |
| の | — | — | の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| を | — | — | を, を | — | model_extra |
| ビール | — | — | びえる | — | model_extra |
| 上場しました | じょうじょうしました | じょうじょうしました | じょうじました | じょうじょうしました | reading_diff |
| 上場する | じょうじょうする | じょうじょうする | — | じょうじょうする | coverage_diff |
| 上場すると | — | — | じょうじると | — | model_extra |
| 人 | ひと | ひと | — | ひと | coverage_diff |
| 人が | — | — | ひとが | — | model_extra |
| 円 | — | — | — | えん | model_missing |
| 午前 | ごぜん | ごぜん | — | ごぜん | coverage_diff |
| 午前は | — | — | ごぜんは | — | model_extra |
| 午後 | ごご | ごご | — | ごご | coverage_diff |
| 午後になって | — | — | ごごになって | — | model_extra |
| 売った | — | — | — | うった | model_missing |
| 売ったり | うったり | うったり | うりたり | — | model_extra |
| 多くて | おおくて | おおくて | おおいて | おおくて | reading_diff |
| 日 | — | — | — | にち, にち | model_missing |
| 東京証券取引所 | とうきょうしょうけんとりひきじょ | とうきょうしょうけんとりひきじょ | とうきょうしょうけんとひんしょく | とうきょうしょうけんとりひきじょ | reading_diff |
| 株を | — | — | かぶを | — | model_extra |
| 決まって | きまって | きまって | きめられて | きまって | reading_diff |
| 決まりませんで | — | — | — | きまりませんで | model_missing |
| 決まりませんでした | きまりませんでした | きまりませんでした | きまりませんでした | — | model_extra |
| 買った | — | — | — | かった | model_missing |
| 買ったり | かったり | かったり | かいたり | — | model_extra |

## Sentence 45 (nhk)
"社長などは、正しくない調べ方をされたと言って、東京都と国を訴えました。裁判所は、5月、警察と検察は法律に違反していたと言いました。そして、東京都と国が1億6600万円を社長などに払うように命令しました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 1億6600万円 | いちおくろくせんろっぴゃくまんえん | いちおくろくせんろっぴゃくまんえん | いちおくろっぴゃくなもん | — | model_extra |
| 5月 | ごがつ | ごがつ | ごがつ | — | model_extra |
| 、 | — | — | 、 | — | model_extra |
| が | — | — | が | — | model_extra |
| された | — | — | された | — | model_extra |
| していた | — | — | ていた | — | model_extra |
| そして | — | — | そして | — | model_extra |
| と | — | — | と, と, と, と, と | — | model_extra |
| など | — | — | など | — | model_extra |
| などに | — | — | などに | — | model_extra |
| に | — | — | に | — | model_extra |
| は | — | — | は, は, は | — | model_extra |
| を | — | — | を, を, を | — | model_extra |
| 万 | — | — | — | まん | model_missing |
| 億 | — | — | — | おく | model_missing |
| 円 | — | — | — | えん | model_missing |
| 国 | くに, くに | くに, くに | こく, こく | くに, くに | reading_diff |
| 払う | はらう | はらう | — | はらう | coverage_diff |
| 払うように | — | — | はらうように | — | model_extra |
| 方 | — | — | — | かた | model_missing |
| 月 | — | — | — | がつ | model_missing |
| 正しく | — | — | — | ただしく | model_missing |
| 正しくない | ただしくない | ただしくない | ただしくない | — | model_extra |
| 訴えました | うったえました | うったえました | potrà | うったえました | reading_diff |
| 調べ | — | — | — | しらべ | model_missing |
| 調べ方 | しらべかた | しらべかた | しじかた | — | model_extra |
| 違反 | — | — | いんがい | — | model_extra |
| 違反して | — | — | — | いはんして | model_missing |
| 違反していた | いはんしていた | いはんしていた | — | — | model_extra |

## Sentence 46 (nhk)
"片岡仁左衛門さんや尾上菊五郎さんなどが旗で飾った船に乗りました。そして、大阪のまちの中の川を2.5kmぐらい進みました。舞台の近くに着くとたくさんの人たちが拍手をして迎えました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 2.5km | — | — | にっかいご | — | model_extra |
| が | — | — | が, が | — | model_extra |
| ぐらい | — | — | ぐあい | — | model_extra |
| さん | — | — | さん, さん | — | model_extra |
| して | — | — | して | — | model_extra |
| そして | — | — | それとて | — | model_extra |
| たくさんの | — | — | たっかんさの | — | model_extra |
| で | — | — | で | — | model_extra |
| と | — | — | と | — | model_extra |
| に | — | — | に, に | — | model_extra |
| の | — | — | の, の, の | — | model_extra |
| の中 | — | — | なか | — | model_extra |
| まち | — | — | まち | — | model_extra |
| や | — | — | や | — | model_extra |
| を | — | — | を, を | — | model_extra |
| 中 | なか | なか | — | なか | coverage_diff |
| 乗りました | のりました | のりました | の乘りました | のりました | reading_diff |
| 仁左衛門 | にざえもん | — | じざえもん | にざえもん | reading_diff |
| 大阪 | おおさか | おおさか | おおさか | — | model_extra |
| 大阪のまち | — | — | — | おおさかのまち | model_missing |
| 尾上 | おのえ | — | おのうえ | おのえ | reading_diff |
| 尾上菊五郎 | — | おのえきくごろう | — | — | model_extra |
| 旗 | はた | はた | ひるがえり | はた | reading_diff |
| 片岡 | かたおか | — | かたおか | かたおか | coverage_diff |
| 片岡仁左衛門 | — | かたおかにざえもん | — | — | model_extra |
| 着く | — | つく | つくる | つく | reading_diff |
| 着くと | つくと | — | — | — | model_extra |
| 船 | ふね | ふね | ふな | ふね | reading_diff |
| 菊五郎 | きくごろう | — | きくごろう | きくごろう | coverage_diff |

## Sentence 47 (nhk)
"今年4月からアメリカが関税を上げたので自動車の輸出が減りました。住宅への投資も大きく減りました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 4月 | しがつ | しがつ | よんがつ | — | model_extra |
| 。 | — | — | 。 | — | model_extra |
| から | — | — | から | — | model_extra |
| が | — | — | が, が | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の, の | — | model_extra |
| ので | — | — | ので | — | model_extra |
| も | — | — | も | — | model_extra |
| を | — | — | を | — | model_extra |
| アメリカ | — | — | あめりか | — | model_extra |
| 大いに | — | — | だいに | — | model_extra |
| 大きく | おおきく | おおきく | — | おおきく | coverage_diff |
| 月 | — | — | — | がつ | model_missing |
| 減りました | へりました, へりました | へりました, へりました | へんだりました, へんだりました | へりました, へりました | reading_diff |

## Sentence 48 (nhk)
"有名な野球選手だった松井秀喜さんが、去年大きい地震があった石川県の能登地方で、ことし9月に「野球教室」を開きます。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 9月 | くがつ | くがつ | くがつ | — | model_extra |
| 、 | — | — | 、, 、 | — | model_extra |
| 「 | — | — | 「 | — | model_extra |
| 」 | — | — | 」 | — | model_extra |
| あり | — | — | あった | — | model_extra |
| い | — | — | い | — | model_extra |
| が | — | — | が, が | — | model_extra |
| ことし | — | — | このし | — | model_extra |
| さん | — | — | さん | — | model_extra |
| た | — | — | た | — | model_extra |
| だった | — | — | ではった | — | model_extra |
| で | — | — | で | — | model_extra |
| な | — | — | な | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の | — | model_extra |
| を | — | — | を | — | model_extra |
| 地方 | — | — | ちほう | — | model_extra |
| 大 | — | — | おお | — | model_extra |
| 大きい | おおきい | おおきい | — | おおきい | coverage_diff |
| 教室 | — | — | きょうしつ | きょうしつ | coverage_diff |
| 月 | — | — | — | がつ | model_missing |
| 有名 | — | — | ゆうめい | — | model_extra |
| 有名な | ゆうめいな | ゆうめいな | — | ゆうめいな | coverage_diff |
| 松井 | まつい | — | まつい | まつい | coverage_diff |
| 松井秀喜 | — | まついひでき | — | — | model_extra |
| 秀喜 | ひでき | — | ひでき | ひでき | coverage_diff |
| 能登 | — | — | のと | — | model_extra |
| 能登地方 | のとちほう | のとちほう | — | のとちほう | coverage_diff |
| 選手 | — | — | せんしゅ | — | model_extra |
| 選手だった | — | — | — | せんしゅだった | model_missing |
| 野球 | — | — | やきゅう, やきゅう | やきゅう, やきゅう | coverage_diff |
| 野球教室 | やきゅうきょうしつ | やきゅうきょうしつ | — | — | model_extra |
| 野球選手 | やきゅうせんしゅ | やきゅうせんしゅ | — | — | model_extra |

## Sentence 49 (nhk)
"今年の4月、神奈川県川崎市で20歳の女性が、殺されているのが見つかりました。前につき合っていた男の家で見つかりました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 20歳 | はたち | にじゅっさい | にんぱい | — | model_extra |
| 4月 | しがつ | しがつ | よんがつ | — | model_extra |
| 、 | — | — | 、, 、 | — | model_extra |
| 。 | — | — | 。, 。 | — | model_extra |
| が | — | — | が | — | model_extra |
| つき合っていた | — | つきあっていた | つきあっていた | — | model_extra |
| で | — | — | で, で | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の, の | — | model_extra |
| のが | — | — | が | — | model_extra |
| 合って | — | — | — | あって | model_missing |
| 合っていた | あっていた | — | — | — | model_extra |
| 女性 | じょせい | じょせい | じょし | じょせい | reading_diff |
| 川崎市 | かわさきし | — | かわさきし | — | model_extra |
| 月 | — | — | — | がつ | model_missing |
| 殺されて | — | — | — | ころされて | model_missing |
| 殺されている | ころされている | ころされている | さつされている | — | model_extra |
| 男 | おとこ | おとこ | — | おとこ | coverage_diff |
| 男の | — | — | おとこの | — | model_extra |
| 神奈川県 | かながわけん | — | かながわけん | — | model_extra |
| 神奈川県川崎市 | — | かながわけんかわさきし | — | かながわけんかわさきし | coverage_diff |

## Sentence 50 (nhk)
"フランスの政府によると、19日の午前、犯人は美術館の2階の窓から入りました。そして宝石などを盗んで逃げました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 19日 | じゅうくにち | じゅうくにち | — | — | model_extra |
| 2階 | にかい | にかい | — | — | model_extra |
| 入りました | はいりました | はいりました | — | はいりました | coverage_diff |
| 午前 | ごぜん | ごぜん | — | ごぜん | coverage_diff |
| 宝石 | ほうせき | ほうせき | — | ほうせき | coverage_diff |
| 政府 | せいふ | せいふ | — | せいふ | coverage_diff |
| 日 | — | — | — | にち | model_missing |
| 犯人 | はんにん | はんにん | — | はんにん | coverage_diff |
| 盗んで | ぬすんで | ぬすんで | — | ぬすんで | coverage_diff |
| 窓 | まど | まど | — | まど | coverage_diff |
| 美術館 | びじゅつかん | びじゅつかん | — | びじゅつかん | coverage_diff |
| 逃げました | にげました | にげました | — | にげました | coverage_diff |
| 階 | — | — | — | かい | model_missing |

## Sentence 51 (nhk)
"とても強い台風22号は9日、伊豆諸島の東の海を進みました。伊豆諸島からだんだん離れています。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 22号 | にじゅうにごう | — | にじゅうにごう | — | model_extra |
| 9日 | ここのか | ここのか | くっか | ここのか | reading_diff |
| 、 | — | — | 、 | — | model_extra |
| 。 | — | — | 。 | — | model_extra |
| から | — | — | から | — | model_extra |
| だんだん | — | — | だんだん | — | model_extra |
| とても | — | — | とても | — | model_extra |
| の | — | — | の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| を | — | — | を | — | model_extra |
| 台風 | たいふう | — | たいふう | たいふう | coverage_diff |
| 台風22号 | — | たいふうにじゅうにごう | — | — | model_extra |
| 号 | — | — | — | ごう | model_missing |
| 離れて | — | — | — | はなれて | model_missing |
| 離れています | はなれています | はなれています | はなれています | — | model_extra |

## Sentence 52 (nhk)
"気象庁は、8日のような大きい地震のあとは、もっと大きいマグニチュード8以上の地震が起こることがあると言いました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 8以上 | — | はちいじょう | はちいじょう | — | model_extra |
| 8日 | ようか | ようか | はちにち | ようか | reading_diff |
| 、 | — | — | 、 | — | model_extra |
| あとは | — | — | あとは | — | model_extra |
| ある | — | — | ある | — | model_extra |
| が | — | — | が | — | model_extra |
| ことが | — | — | ことがある | — | model_extra |
| と言いました | — | — | と言いました | — | model_extra |
| の | — | — | の, の | — | model_extra |
| のような | — | — | ような | — | model_extra |
| は | — | — | は | — | model_extra |
| もっと | — | — | もっと | — | model_extra |
| マグニチュード | — | — | まくにちとせ | — | model_extra |
| 以上 | いじょう | — | — | いじょう | coverage_diff |
| 庁 | — | — | ちょう | — | model_extra |
| 気象 | — | — | きしょう | — | model_extra |
| 気象庁 | きしょうちょう | きしょうちょう | — | きしょうちょう | coverage_diff |
| 言いました | いいました | いいました | — | いいました | coverage_diff |

## Sentence 53 (nhk)
"解散すると、衆議院の新しい議員を選ぶ選挙があります。与党は、投票する日を2月8日と考えています。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 2月 | にがつ | — | — | — | model_extra |
| 2月8日 | — | にがつようか | にっがつはちにち | — | model_extra |
| 8日 | ようか | — | — | ようか | coverage_diff |
| 、 | — | — | 、 | — | model_extra |
| あります | — | — | あります | — | model_extra |
| が | — | — | が | — | model_extra |
| する | — | — | する | — | model_extra |
| すると | — | — | としたら | — | model_extra |
| と | — | — | と | — | model_extra |
| の | — | — | の | — | model_extra |
| は | — | — | は | — | model_extra |
| を | — | — | を, を | — | model_extra |
| 投票 | — | — | ひょうとう | — | model_extra |
| 投票する | とうひょうする | とうひょうする | — | とうひょうする | coverage_diff |
| 日 | ひ | ひ | び | ひ | reading_diff |
| 月 | — | — | — | がつ | model_missing |
| 考えて | — | — | — | かんがえて | model_missing |
| 考えています | かんがえています | かんがえています | かんがえています | — | model_extra |
| 衆議院 | しゅうぎいん | しゅうぎいん | しゅぎいん | しゅうぎいん | reading_diff |
| 解散 | — | — | かいさん | — | model_extra |
| 解散する | かいさんする | かいさんする | — | かいさんする | coverage_diff |
| 選挙 | せんきょ | せんきょう | せんきょ | せんきょ | reading_diff |

## Sentence 54 (nhk)
"東京の北区で、ペットと一緒に避難する方法を勉強する会がありました。近くに住む20人ぐらいがペットと集まりました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 20人 | にじゅうにん | にじゅうにん | — | — | model_extra |
| 一緒 | いっしょ | — | — | いっしょ | coverage_diff |
| 一緒に | — | いっしょに | — | — | model_extra |
| 人ぐらい | — | — | — | にんぐらい | model_missing |
| 会 | かい | かい | — | かい | coverage_diff |
| 住む | すむ | すむ | — | すむ | coverage_diff |
| 勉強する | べんきょうする | べんきょうする | — | べんきょうする | coverage_diff |
| 北区 | きたく | きたく | — | きたく | coverage_diff |
| 方法 | ほうほう | ほうほう | — | ほうほう | coverage_diff |
| 東京 | とうきょう | とうきょう | — | とうきょう | coverage_diff |
| 近く | ちかく | ちかく | — | ちかく | coverage_diff |
| 避難する | ひなんする | ひなんする | — | ひなんする | coverage_diff |
| 集まりました | あつまりました | あつまりました | — | あつまりました | coverage_diff |

## Sentence 55 (nhk)
"国土交通省は、全日空と日本航空に、同じタイプの飛行機をしっかりチェックするように言いました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| しっかり | — | — | しっかり | — | model_extra |
| する | — | — | する | — | model_extra |
| と | — | — | と | — | model_extra |
| に、 | — | — | に、 | — | model_extra |
| の | — | — | の | — | model_extra |
| は、 | — | — | は、 | — | model_extra |
| ように | — | — | ように | — | model_extra |
| を | — | — | を | — | model_extra |
| タイプ | — | — | たいげつ | — | model_extra |
| チェック | — | — | けっか | — | model_extra |
| 交通 | — | — | つうきん | — | model_extra |
| 全 | — | — | ぜん | — | model_extra |
| 全日空 | ぜんにっくう | ぜんにっくう | — | ぜんにっくう | coverage_diff |
| 国土 | — | — | こくど | — | model_extra |
| 国土交通省 | こくどこうつうしょう | こくどこうつうしょう | — | こくどこうつうしょう | coverage_diff |
| 日本 | — | — | にほん | — | model_extra |
| 日本航空 | にほんこうくう | にほんこうくう | — | にほんこうくう | coverage_diff |
| 日空 | — | — | にっかく | — | model_extra |
| 省 | — | — | しょう | — | model_extra |
| 航空 | — | — | こうこう | — | model_extra |

## Sentence 56 (nhk)
"漫画家の永井豪さんたちが、11日、能登半島地震で被害のあった石川県に1億2300万円を贈りました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 11日 | じゅういちにち | じゅういちにち | じゅういちにち | — | model_extra |
| 1億2300万円 | いちおくにせんさんびゃくまんえん | いちおくにせんさんびゃくまんえん | いちおくにせんぜんえん | — | model_extra |
| 、 | — | — | 、 | — | model_extra |
| あった | — | — | あっただ | — | model_extra |
| が | — | — | が | — | model_extra |
| さんたち | — | — | さんたち | — | model_extra |
| で | — | — | で | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の, の | — | model_extra |
| を | — | — | を | — | model_extra |
| 万 | — | — | — | まん | model_missing |
| 億 | — | — | — | おく | model_missing |
| 円 | — | — | — | えん | model_missing |
| 日 | — | — | — | にち | model_missing |
| 永井 | — | — | — | ながい | model_missing |
| 永井豪 | ながいごう | ながいごう | ながい やすし | — | model_extra |
| 石川県 | いしかわけん | いしかわけん | せいかんけん | いしかわけん | reading_diff |
| 豪 | — | — | — | ごう | model_missing |
| 贈りました | おくりました | おくりました | さしあげました | おくりました | reading_diff |

## Sentence 57 (nhk)
"アメリカの軍は3日、南米のベネズエラのマドゥーロ大統領と妻の2人を捕まえました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 3 | — | — | さん | — | model_extra |
| 3日 | みっか | みっか | — | みっか | coverage_diff |
| 、 | — | — | 、 | — | model_extra |
| と | — | — | と | — | model_extra |
| の | — | — | の, の, の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| を | — | — | を | — | model_extra |
| アメリカ | — | — | あめりか | — | model_extra |
| ベネズエラ | — | — | べねずえら | — | model_extra |
| マドゥーロ | — | — | まどーる | — | model_extra |
| 日 | — | — | ひ | — | model_extra |

## Sentence 58 (nhk)
"票の数が同じになった場合は、くじを引きます。これは法律で決まっています。くじの結果、新しく選挙に出た人に決まりました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| が | — | — | ga | — | model_extra |
| くじ | — | — | くじ | — | model_extra |
| くじの | — | — | くじの | — | model_extra |
| これは | — | — | これは | — | model_extra |
| で | — | — | de | — | model_extra |
| に | — | — | ni | — | model_extra |
| になった | — | — | になっただけ | — | model_extra |
| に出た | — | — | でいた | — | model_extra |
| の | — | — | no | — | model_extra |
| は | — | — | wa | — | model_extra |
| を | — | — | o | — | model_extra |
| 人 | ひと | ひと | — | ひと | coverage_diff |
| 人に | — | — | にんに | — | model_extra |
| 出た | でた | でた | — | でた | coverage_diff |
| 同じ | おなじ | — | おなじ | おなじ | coverage_diff |
| 同じになった | — | おなじになった | — | — | model_extra |
| 場合 | ばあい | ばあい | ばいがい | ばあい | reading_diff |
| 引きます | ひきます | ひきます | ひくめます | ひきます | reading_diff |
| 数 | かず | かず | すう | かず | reading_diff |
| 新しく | あたらしく | あたらしく | しんしきに | あたらしく | reading_diff |
| 決まって | — | — | — | きまって | model_missing |
| 決まっています | きまっています | きまっています | きまりています | — | model_extra |

## Sentence 59 (nhk)
"尾崎さんは体が大きくて、ボールを打つと遠くまで飛びました。みんなが「ジャンボ尾崎」と呼びました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 「 | — | — | 「 | — | model_extra |
| 」 | — | — | 」 | — | model_extra |
| が | — | — | が, が | — | model_extra |
| さん | — | — | さん | — | model_extra |
| と | — | — | と, と | — | model_extra |
| まで | — | — | まで | — | model_extra |
| みんな | — | — | みな | — | model_extra |
| を | — | — | を | — | model_extra |
| ジャンボ | — | — | じゃんぼ | — | model_extra |
| ボール | — | — | ぼうら | — | model_extra |
| 呼びました | よびました | よびました | よみました | よびました | reading_diff |
| 打つ | うつ | うつ | うちつ | うつ | reading_diff |
| 遠く | とおく | とおく | えんく | とおく | reading_diff |

## Sentence 60 (nhk)
"大学の留学生と大学院の修士課程の留学生は、1年の授業料が90万円になります。日本の学生の1.7倍です。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 1.7倍 | いってんななばい | いってんななばい | いっかりばい | — | model_extra |
| 1年 | いちねん | いちねん | いねん | — | model_extra |
| 90万円 | きゅうじゅうまんえん | きゅうじゅうまんえん | くじゅうまんえん | — | model_extra |
| が | — | — | が | — | model_extra |
| です | — | — | です | — | model_extra |
| と | — | — | と | — | model_extra |
| になります | — | — | なります | — | model_extra |
| の | — | — | の, の, の, の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| 万 | — | — | — | まん | model_missing |
| 修士課程 | しゅうしかてい | しゅうしかてい | しゅくかくげい | しゅうしかてい | reading_diff |
| 倍 | — | — | — | ばい | model_missing |
| 円 | — | — | — | えん | model_missing |
| 大学院 | だいがくいん | だいがくいん | だいがいん | だいがくいん | reading_diff |
| 年 | — | — | — | ねん | model_missing |
| 授業 | — | — | — | じゅぎょう | model_missing |
| 授業料 | じゅぎょうりょう | じゅぎょうりょう | じゅぎょうりょう | — | model_extra |
| 料 | — | — | — | りょう | model_missing |
| 日本 | にほん | にほん | — | にっぽん | reading_diff |
| 日本の | — | — | にほんの | — | model_extra |

## Sentence 61 (ud_gsd)
"しかし、1995年の時点で高校生だった主人公、辰木桂はまだ神戸に引っ越す前で阪神・淡路大震災を直接経験していないという設定のため、作中での震災の話は、桂が被害の爪痕を見ることか、直接体験した桂の友人、金城和歌子とその恋人、林浩の2人が中心となって体験談を語る形で描かれている。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 1995年 | せんきゅうひゃくきゅうじゅうごねん | せんきゅうひゃくきゅうじゅうごねん | せんきゅうきゅうねん | — | model_extra |
| 2人 | ふたり | ふたり | — | ふたり | coverage_diff |
| 、 | — | — | 、, 、, 、, 、, 、 | — | model_extra |
| が | — | — | が | — | model_extra |
| しかし | — | — | しかるべく | — | model_extra |
| その恋人 | — | — | そのれんとう | — | model_extra |
| ため | — | — | ため | — | model_extra |
| だった | — | — | だった | — | model_extra |
| で | — | — | で, で | — | model_extra |
| での | — | — | での | — | model_extra |
| と | — | — | と | — | model_extra |
| という | — | — | という | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の, の, の, の | — | model_extra |
| の2人 | — | — | ふじん | — | model_extra |
| は | — | — | は, は | — | model_extra |
| まだ | — | — | まだ | — | model_extra |
| を | — | — | を, を | — | model_extra |
| 中心 | ちゅうしん | ちゅうしん | — | ちゅうしん | coverage_diff |
| 中心となって | — | — | ちゅうしんとなって | — | model_extra |
| 主人 | — | — | — | しゅじん | model_missing |
| 主人公 | しゅじんこう | しゅじんこう | しゅじんぶつ | — | model_extra |
| 体験 | — | — | — | たいけん | model_missing |
| 体験した | たいけんした | たいけんした | — | たいけんした | coverage_diff |
| 体験談 | たいけんだん | たいけんだん | — | — | model_extra |
| 体験談を語る | — | — | たいけんだんをわる | — | model_extra |
| 作中 | さくちゅう | さくちゅう | さっちゅう | さくちゅう | reading_diff |
| 公 | — | — | — | こう | model_missing |
| 和歌子 | — | わかこ | — | わかこ | coverage_diff |
| 大 | — | — | — | だい | model_missing |
| 大震災 | — | だいしんさい | — | — | model_extra |
| 年 | — | — | — | ねん | model_missing |
| 形 | かたち | かたち | — | かたち | coverage_diff |
| 形で | — | — | かたで | — | model_extra |
| 恋人 | こいびと | こいびと | — | こいびと | coverage_diff |
| 描 | — | — | — | えが | model_missing |
| 描かれている | えがかれている | えがかれている | えがかれている | — | model_extra |
| 時点 | じてん | じてん | — | じてん | coverage_diff |
| 林 | — | はやし | — | — | model_extra |
| 林浩 | はやしひろし | — | はやしこう | りんはお | reading_diff |
| 桂 | かつら, かつら | けい, けい, けい | かつら | かつら, かつら, かつら | reading_diff |
| 桂が | — | — | かつらが | — | model_extra |
| 桂の | — | — | かつらの | — | model_extra |
| 浩 | — | ひろし | — | — | model_extra |
| 淡路 | — | あわじ | — | あわじ | coverage_diff |
| 爪痕 | つめあと | つめあと | そうこん | つめあと | reading_diff |
| 生だった | — | — | — | せいだった | model_missing |
| 直接 | ちょくせつ, ちょくせつ | ちょくせつ, ちょくせつ | — | ちょくせつ, ちょくせつ | coverage_diff |
| 直接体験した | — | — | ちょくせつたいけんだ | — | model_extra |
| 直接経験していない | — | — | ちょくせつけいけいていない | — | model_extra |
| 神戸 | こうべ | こうべ | かんべ | こうべ | reading_diff |
| 経験して | — | — | — | けいけんして | model_missing |
| 経験していない | けいけんしていない | けいけんしていない | — | — | model_extra |
| 見る | みる | みる | — | みる | coverage_diff |
| 見ることか | — | — | みることか | — | model_extra |
| 語る | かたる | かたる | — | かたる | coverage_diff |
| 談 | — | — | — | だん | model_missing |
| 辰木 | — | たつき | たぎ | たつき | reading_diff |
| 辰木桂 | たつきかつら | — | — | — | model_extra |
| 金城 | — | きんじょう | — | かなぎ | reading_diff |
| 金城和歌子 | かなしろわかこ | — | きんせいかこ | — | model_extra |
| 阪神 | — | はんしん | — | はんしん | coverage_diff |
| 阪神・淡路大震災 | はんしん・あわじだいしんさい | — | はんじん・たじゅうだいしんさい | — | model_extra |
| 高校 | — | — | — | こうこう | model_missing |
| 高校生 | こうこうせい | こうこうせい | こうがせい | — | model_extra |

## Sentence 62 (ud_gsd)
"また同小説では藍染になすりつけられた罪は、元柳斎の尽力もあって藍染の謀略が認められたことから鉄裁・夜一の罪状共々取り消しとなったこと、商店も尸魂界公認となった上、破面篇で喜助の存在が広く知れ渡った為、現世駐在任務の死神が多数訪れるように手が足りなくなりつつある程忙しくなっていることが語られている。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、, 、 | — | model_extra |
| あって | — | — | あって | — | model_extra |
| から | — | — | から | — | model_extra |
| が | — | — | が, が, が | — | model_extra |
| こと | — | — | こと | — | model_extra |
| ことから | — | — | ことから | — | model_extra |
| ことが | — | — | ことが | — | model_extra |
| で | — | — | で | — | model_extra |
| では | — | — | でわ | — | model_extra |
| となった | — | — | ことになった, ことになった | — | model_extra |
| になすりつけられた | — | — | になすりつけられた | — | model_extra |
| の | — | — | の, の, の, の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| また | — | — | また | — | model_extra |
| も | — | — | も, も | — | model_extra |
| ように | — | — | ように | — | model_extra |
| ・ | — | — | ・ | — | model_extra |
| 任務 | にんむ | — | — | にんむ | coverage_diff |
| 元柳斎 | げんりゅうさい | げんりゅうさい | もとやなぎさ | げんりゅうさい | reading_diff |
| 共々 | ともども | — | ともに | ともども | reading_diff |
| 取り消 | — | — | — | とりけ | model_missing |
| 取り消し | とりけし | とりけし | とりしょう | — | model_extra |
| 同 | どう | — | — | どう | coverage_diff |
| 同小説 | — | どうしょうせつ | どうしょうせつ | — | model_extra |
| 喜助 | きすけ | きすけ | よしげ | きすけ | reading_diff |
| 多数 | たすう | たすう | すうた | たすう | reading_diff |
| 夜一 | よるいち | よるいち | よつち | よるいち | reading_diff |
| 小説 | しょうせつ | — | — | しょうせつ | coverage_diff |
| 尸魂 | — | — | — | そうる | model_missing |
| 尸魂界 | そうるそさえてぃ | しこんかい | しかいんかい | — | model_extra |
| 尽力 | じんりょく | じんりょく | げんりき | じんりょく | reading_diff |
| 忙しく | — | — | — | いそがしく | model_missing |
| 忙しくなっている | いそがしくなっている | いそがしくなっている | いそがしくなっている | — | model_extra |
| 手 | て | て | — | て | coverage_diff |
| 手が足りなくなりつつある | — | — | てがたたりなくなりつつある | — | model_extra |
| 死神 | しにがみ | しにがみ | ししん | しにがみ | reading_diff |
| 渡った | — | — | — | わたった | model_missing |
| 現世 | げんせい | — | — | げんせ | reading_diff |
| 現世駐在任務 | — | げんせちゅうざいにんむ | げんせいちざいむんじ | — | model_extra |
| 界 | — | — | — | そさえてぃ | model_missing |
| 知れ | — | — | — | しれ | model_missing |
| 知れ渡った | しれわたった | しれわたった | しれわたった | — | model_extra |
| 破面 | — | — | — | はめん | model_missing |
| 破面篇 | はめんへん | はめんへん | はめんへん | — | model_extra |
| 篇 | — | — | — | へん | model_missing |
| 罪 | つみ | つみ | ざい | つみ | reading_diff |
| 罪状 | ざいじょう | — | ざいじょう | ざいじょう | coverage_diff |
| 罪状共々 | — | ざいじょうともども | — | — | model_extra |
| 訪れる | おとずれる | おとずれる | ほうれる | おとずれる | reading_diff |
| 認められた | みとめられた | みとめられた | ことわかった | みとめられた | reading_diff |
| 語られて | — | — | — | かたられて | model_missing |
| 語られている | かたられている | かたられている | はかれられている | — | model_extra |
| 謀略 | ぼうりゃく | ぼうりゃく | ぼうろく | ぼうりゃく | reading_diff |
| 足り | — | — | — | たり | model_missing |
| 足りなくなりつつある | たりなくなりつつある | たりなくなりつつある | — | — | model_extra |
| 駐在 | ちゅうざい | — | — | ちゅうざい | coverage_diff |

## Sentence 63 (ud_gsd)
"1970年代の末に開発された本形式は、国産の高品質な軽快車に広く採用されたが、近年の自転車の低価格化圧力と、大手自転車部品メーカー、シマノ社の開発した後発製品であるローラーブレーキの普及による挟撃を受ける形となり、安売りされている自転車はバンドブレーキ、他の多くの軽快車ではローラーブレーキに市場を奪われ、新車でサーボブレーキが付く自転車は減少傾向である。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 1970年代 | せんきゅうひゃくななじゅうねんだい | せんきゅうひゃくななじゅうねんだい | じゅうきゅうなinen | — | model_extra |
| 、 | — | — | 、, 、, 、, 、, 、, 、, 、 | — | model_extra |
| が | — | — | が, が | — | model_extra |
| された | — | — | された, された | — | model_extra |
| されている | — | — | されている | — | model_extra |
| した | — | — | した | — | model_extra |
| で | — | — | で | — | model_extra |
| である | — | — | である, である | — | model_extra |
| では | — | — | では | — | model_extra |
| と | — | — | と | — | model_extra |
| となり | — | — | となり | — | model_extra |
| に | — | — | に, に, に | — | model_extra |
| による | — | — | による | — | model_extra |
| の | — | — | の, の, の, の, の, の | — | model_extra |
| は | — | — | は, は, は | — | model_extra |
| を | — | — | を, を | — | model_extra |
| サーボブレーキ | — | — | さーぼぶれき | — | model_extra |
| シマノ | — | — | しまの | — | model_extra |
| バンドブレーキ | — | — | ばんどぶれき | — | model_extra |
| メーカー | — | — | めーかー | — | model_extra |
| ローラーブレーキ | — | — | ろーらぶれき, ろーらぶれき | — | model_extra |
| 他 | ほか | ほか | — | ほか | coverage_diff |
| 他の | — | — | その他の | — | model_extra |
| 代 | — | — | — | だい | model_missing |
| 低 | — | — | — | てい | model_missing |
| 低価格化 | ていかかくか | — | ていかっか | — | model_extra |
| 低価格化圧力 | — | ていかかくかあつりょく | — | — | model_extra |
| 価格 | — | — | — | かかく | model_missing |
| 傾向 | — | — | けいこう | けいこう | coverage_diff |
| 化 | — | — | — | か | model_missing |
| 品質な | — | — | — | ひんしつな | model_missing |
| 国産 | こくさん | こくさん | こっせん | こくさん | reading_diff |
| 圧力 | あつりょく | — | あつりょく | あつりょく | coverage_diff |
| 多く | おおく | おおく | — | おおく | coverage_diff |
| 多くの | — | — | おおくの | — | model_extra |
| 大手 | おおて | おおて | だて | おおて | reading_diff |
| 安売り | — | — | やすせり | — | model_extra |
| 安売りされて | — | — | — | やすうりされて | model_missing |
| 安売りされている | やすうりされている | やすうりされている | — | — | model_extra |
| 市場 | しじょう | しじょう | じょうひか | しじょう | reading_diff |
| 年 | — | — | — | ねん | model_missing |
| 形 | かたち | かたち | かた | かたち | reading_diff |
| 形式 | けいしき | — | — | けいしき | coverage_diff |
| 後発 | — | — | — | こうはつ | model_missing |
| 後発製品 | こうはつせいひん | こうはつせいひん | こうはっせいひん | — | model_extra |
| 挟撃 | きょうげき | きょうげき | けっげき | きょうげき | reading_diff |
| 採用 | — | — | さいよう | — | model_extra |
| 採用された | さいようされた | さいようされた | — | さいようされた | coverage_diff |
| 普及 | ふきゅう | ふきゅう | ふしゅう | ふきゅう | reading_diff |
| 末 | すえ | すえ | まつ | すえ | reading_diff |
| 本 | ほん | — | — | ほん | coverage_diff |
| 本形式 | — | ほんけいしき | ほんしき | — | model_extra |
| 減少 | — | — | げんしょう | げんしょう | coverage_diff |
| 減少傾向 | げんしょうけいこう | げんしょうけいこう | — | — | model_extra |
| 自転 | — | — | — | じてん, じてん, じてん, じてん | model_missing |
| 自転車 | じてんしゃ, じてんしゃ, じてんしゃ | じてんしゃ, じてんしゃ, じてんしゃ | じてんしゃ, じてんしゃ, じてんしゃ | — | model_extra |
| 自転車部品 | じてんしゃぶひん | じてんしゃぶひん | じてんしゃぶひん | — | model_extra |
| 製品 | — | — | — | せいひん | model_missing |
| 車 | — | — | — | しゃ, しゃ, しゃ, しゃ, しゃ, しゃ | model_missing |
| 軽快 | — | — | — | けいかい, けいかい | model_missing |
| 軽快車 | けいかいしゃ, けいかいしゃ | けいかいしゃ, けいかいしゃ | かるかしゃ, かるかしゃ | — | model_extra |
| 部品 | — | — | — | ぶひん | model_missing |
| 開発 | — | — | かいはつ, かいはつ | — | model_extra |
| 開発された | かいはつされた | かいはつされた | — | かいはつされた | coverage_diff |
| 開発した | かいはつした | かいはつした | — | かいはつした | coverage_diff |
| 高 | — | — | — | こう | model_missing |
| 高品質な | こうひんしつな | こうひんしつな | こうひけいな | — | model_extra |

## Sentence 64 (ud_gsd)
"佐脇有紀裁判長は,吉田被告について“本件に果たした役割は主導的で積極的”とし,元警察官として“犯行の情状も悪い”としながらも,被告が素直に犯行を認め二度と犯罪を起こさないと反省していることや弁護士会に100万円を寄付したことなどを総合考慮し執行猶予付きの判決となったと述べた。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 100万円 | ひゃくまんえん | ひゃくまんえん | — | — | model_extra |
| “本件に果たした役割は主導的で積極的”とし | — | — | “ほんけんにかたしたやくわりはしゅどうてきでせっきょくてき”とし | — | model_extra |
| “犯行の情状も悪い”としながらも | — | — | “はんこうのじょうじょうもわるい”とはながらにも | — | model_extra |
| として | — | — | として | — | model_extra |
| に100万円を寄付したことなどを総合考慮し | — | — | にひゃくまんえんをよふつしたことなどをそうごうかんこうし | — | model_extra |
| について | — | — | おわせについて | — | model_extra |
| は | — | — | は | — | model_extra |
| 万 | — | — | — | まん | model_missing |
| 主導 | — | — | — | しゅどう | model_missing |
| 主導的 | しゅどうてき | — | — | — | model_extra |
| 主導的で | — | しゅどうてきで | — | — | model_extra |
| 二 | — | — | — | に | model_missing |
| 二度 | にど | にど | — | — | model_extra |
| 付き | — | — | — | つき | model_missing |
| 会 | — | — | — | かい | model_missing |
| 佐脇 | — | — | さわき | さわき | coverage_diff |
| 佐脇有紀 | さわきゆき | さわきゆき | — | — | model_extra |
| 元 | もと | — | — | もと | coverage_diff |
| 元警察官 | — | もとけいさつかん | もとさしこかん | — | model_extra |
| 円 | — | — | — | えん | model_missing |
| 判決 | はんけつ | はんけつ | — | はんけつ | coverage_diff |
| 反省して | — | — | — | はんせいして | model_missing |
| 反省している | はんせいしている | はんせいしている | — | — | model_extra |
| 執行 | — | — | — | しっこう | model_missing |
| 執行猶予付き | しっこうゆうよつき | しっこうゆうよつき | — | — | model_extra |
| 執行猶予付きの判決となったと述べた。 | — | — | せいこうゆよつきのはんけきとなったとしこんだ。 | — | model_extra |
| 士 | — | — | — | し | model_missing |
| 官として | — | — | — | かんとして | model_missing |
| 寄付 | — | — | — | きふ | model_missing |
| 寄付した | きふした | きふした | — | — | model_extra |
| 度 | — | — | — | ど | model_missing |
| 弁護 | — | — | — | べんご | model_missing |
| 弁護士会 | べんごしかい | べんごしかい | べんごし | — | model_extra |
| 役割 | やくわり | やくわり | — | やくわり | coverage_diff |
| 悪い | わるい | わるい | — | わるい | coverage_diff |
| 情状 | じょうじょう | じょうじょう | — | じょうじょう | coverage_diff |
| 有紀 | — | — | ゆき | ゆき | coverage_diff |
| 本件 | ほんけん | ほんけん | — | ほんけん | coverage_diff |
| 果たした | はたした | はたした | — | はたした | coverage_diff |
| 犯罪 | はんざい | はんざい | — | はんざい | coverage_diff |
| 犯行 | はんこう, はんこう | はんこう, はんこう | — | はんこう, はんこう | coverage_diff |
| 猶予 | — | — | — | ゆうよ | model_missing |
| 的 | — | — | — | てき, てき | model_missing |
| 積極 | — | — | — | せっきょく | model_missing |
| 積極的 | せっきょくてき | せっきょくてき | — | — | model_extra |
| 素直 | すなお | — | — | すなお | coverage_diff |
| 素直に | — | すなおに | — | — | model_extra |
| 総合 | そうごう | — | — | そうごう | coverage_diff |
| 総合考慮し | — | そうごうこうりょし | — | — | model_extra |
| 考慮し | こうりょし | — | — | こうりょし | coverage_diff |
| 被告 | ひこく, ひこく | ひこく, ひこく | ぼうぎょう | ひこく, ひこく | reading_diff |
| 被告が素直に犯行を認め二度と犯罪を起こさないと反省していることや | — | — | ぼうぎょうかすなおにはんこうをきんじてにどとうくざんをおこさないとしめていることや | — | model_extra |
| 裁判 | — | — | — | さいばん | model_missing |
| 裁判長 | さいばんちょう | さいばんちょう | せんばいちょう | — | model_extra |
| 認め | みとめ | みとめ | — | みとめ | coverage_diff |
| 警察 | — | — | — | けいさつ | model_missing |
| 警察官 | けいさつかん | — | — | — | model_extra |
| 起こさな | — | — | — | おこさな | model_missing |
| 起こさない | おこさない | おこさない | — | — | model_extra |
| 述べた | のべた | のべた | — | のべた | coverage_diff |
| 長 | — | — | — | ちょう | model_missing |

## Sentence 65 (ud_gsd)
"このことから、勝負事では引き分けをなるべく避けようとするのが一般的であるが、チェスのステイルメイト、将棋の千日手狙いの戦術、サッカーのリーグ戦における引き分けの勝ち点のように「引き分けも試合結果のひとつ」ととらえる文化も少数ながら存在する。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、, 、, 、, 、 | — | model_extra |
| 「引き分けも試合結果のひとつ」と | — | — | ひきわけもしじかくのひとつと | — | model_extra |
| から | — | — | から | — | model_extra |
| が | — | — | が | — | model_extra |
| こと | — | — | こと | — | model_extra |
| この | — | — | この | — | model_extra |
| では | — | — | でわ | — | model_extra |
| とらえる | — | — | とらえる | — | model_extra |
| なるべく | — | — | なるべく | — | model_extra |
| のが | — | — | のが | — | model_extra |
| のように | — | — | にようかん | — | model_extra |
| も | — | — | も | — | model_extra |
| サッカーの | — | — | さっかーの | — | model_extra |
| ステイルメイト | — | — | すているめいと | — | model_extra |
| チェスの | — | — | ちぇすの | — | model_extra |
| リーグ戦 | — | りーぐせん | — | — | model_extra |
| リーグ戦における | — | — | りーぐせんにおける | — | model_extra |
| 一般 | — | — | — | いっぱん | model_missing |
| 一般的 | いっぱんてき | いっぱんてき | — | — | model_extra |
| 一般的である | — | — | いっぱんせきである | — | model_extra |
| 事 | — | — | — | こと | model_missing |
| 勝ち点 | かちてん | かちてん | しょうちてん | かちてん | reading_diff |
| 勝負 | — | — | — | しょうぶ | model_missing |
| 勝負事 | しょうぶごと | しょうぶごと | しょうぶじ | — | model_extra |
| 千日手 | せんにちて | せんにちて | — | せんにちて | coverage_diff |
| 千日手狙いの | — | — | せんにちてねらいの | — | model_extra |
| 将棋 | しょうぎ | しょうぎ | — | しょうぎ | coverage_diff |
| 将棋の | — | — | しょうぎの | — | model_extra |
| 少数 | しょうすう | しょうすう | — | — | model_extra |
| 少数な | — | — | — | しょうすうな | model_missing |
| 少数ながら | — | — | しょうすうながら | — | model_extra |
| 引き分け | ひきわけ, ひきわけ, ひきわけ | ひきわけ, ひきわけ, ひきわけ | — | ひきわけ, ひきわけ, ひきわけ | coverage_diff |
| 引き分けの | — | — | ひきわけの | — | model_extra |
| 引き分けを | — | — | ひきわけを | — | model_extra |
| 戦 | せん | — | — | せん | coverage_diff |
| 戦術 | せんじゅつ | せんじゅつ | せんじつ | せんじゅつ | reading_diff |
| 狙い | ねらい | ねらい | — | ねらい | coverage_diff |
| 的 | — | — | — | てき | model_missing |
| 結果 | — | — | — | けっか | model_missing |
| 試合 | — | — | — | しあい | model_missing |
| 試合結果 | しあいけっか | しあいけっか | — | — | model_extra |
| 避けよう | さけよう | — | — | さける | reading_diff |
| 避けようとする | — | さけようとする | さけようとする | — | model_extra |

## Sentence 66 (ud_gsd)
"6日引け後、厚生労働省厚生科学審議会科学技術部会において、東海大学医学部による「軟骨再生シート」に関する臨床研究実施計画を了承する方向性が示され、当該臨床研究の開始が認められる見通しとなったと発表。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 6日 | むいか | むいか | — | — | model_extra |
| 了承する | りょうしょうする | りょうしょうする | — | りょうしょうする | coverage_diff |
| 会 | — | — | — | かい | model_missing |
| 再生 | さいせい | — | — | さいせい | coverage_diff |
| 労働 | — | — | — | ろうどう | model_missing |
| 医学 | — | — | — | いがく | model_missing |
| 医学部 | いがくぶ | いがくぶ | — | — | model_extra |
| 厚生 | — | — | — | こうせい, こうせい | model_missing |
| 厚生労働省 | こうせいろうどうしょう | こうせいろうどうしょう | — | — | model_extra |
| 厚生科学審議会 | こうせいかがくしんぎかい | こうせいかがくしんぎかい | — | — | model_extra |
| 大学 | — | — | — | だいがく | model_missing |
| 実施 | — | — | — | じっし | model_missing |
| 実施計画 | じっしけいかく | じっしけいかく | — | — | model_extra |
| 審議 | — | — | — | しんぎ | model_missing |
| 引け | ひけ | — | — | ひけ | coverage_diff |
| 引け後 | — | ひけご | — | — | model_extra |
| 当該 | とうがい | とうがい | — | とうがい | coverage_diff |
| 後 | ご | — | — | ご | coverage_diff |
| 性 | — | — | — | せい | model_missing |
| 技術 | — | — | — | ぎじゅつ | model_missing |
| 方向 | — | — | — | ほうこう | model_missing |
| 方向性 | ほうこうせい | ほうこうせい | — | — | model_extra |
| 日 | — | — | — | か | model_missing |
| 東海 | — | — | — | とうかい | model_missing |
| 東海大学 | とうかいだいがく | とうかいだいがく | — | — | model_extra |
| 発表 | はっぴょう | はっぴょう | — | はっぴょう | coverage_diff |
| 省 | — | — | — | しょう | model_missing |
| 研究 | — | — | — | けんきゅう, けんきゅう | model_missing |
| 示され | しめされ | しめされ | — | しめされ | coverage_diff |
| 科学 | — | — | — | かがく, かがく | model_missing |
| 科学技術部会 | かがくぎじゅつぶかい | かがくぎじゅつぶかい | — | — | model_extra |
| 臨床 | — | — | — | りんしょう, りんしょう | model_missing |
| 臨床研究 | りんしょうけんきゅう, りんしょうけんきゅう | りんしょうけんきゅう, りんしょうけんきゅう | — | — | model_extra |
| 見通 | — | — | — | みとお | model_missing |
| 見通し | みとおし | みとおし | — | — | model_extra |
| 計画 | — | — | — | けいかく | model_missing |
| 認められる | みとめられる | みとめられる | — | みとめられる | coverage_diff |
| 軟骨 | なんこつ | — | — | なんこつ | coverage_diff |
| 軟骨再生 | — | なんこつさいせい | — | — | model_extra |
| 部 | — | — | — | ぶ | model_missing |
| 部会 | — | — | — | ぶかい | model_missing |
| 開始 | かいし | かいし | — | かいし | coverage_diff |
| 関する | かんする | かんする | — | かんする | coverage_diff |

## Sentence 67 (ud_gsd)
"少林寺は、二人が帰ってから書物庫の蔵書が盗み見されたことに気付き、事情を調べるために一人の僧、渡元を華山派に派遣した。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、, 、 | — | model_extra |
| いた | — | — | いた | — | model_extra |
| から | — | — | から | — | model_extra |
| が | — | — | が, が | — | model_extra |
| こと | — | — | こと | — | model_extra |
| された | — | — | された | — | model_extra |
| した | — | — | した | — | model_extra |
| する | — | — | す | — | model_extra |
| ため | — | — | の | — | model_extra |
| に | — | — | に, に, に | — | model_extra |
| の | — | — | の, の | — | model_extra |
| は、 | — | — | は、 | — | model_extra |
| を | — | — | を, を | — | model_extra |
| 寺 | — | — | じ | じ | coverage_diff |
| 少林 | — | — | しょうりん | しょうりん | coverage_diff |
| 少林寺 | しょうりんじ | しょうりんじ | — | — | model_extra |
| 帰って | かえって | かえって | かって | かえって | reading_diff |
| 庫 | — | — | — | こ | model_missing |
| 書物 | — | — | — | しょもつ | model_missing |
| 書物庫 | しょもつこ | しょもつこ | しょぶっく | — | model_extra |
| 気付 | — | — | きづ | — | model_extra |
| 気付き | きづき | きづき | — | きずき | reading_diff |
| 派 | — | — | — | は | model_missing |
| 派遣 | — | — | はんさい | — | model_extra |
| 派遣した | はけんした | はけんした | — | はけんした | coverage_diff |
| 渡元 | とげん | とげん | ともと | とげん | reading_diff |
| 盗み見 | — | — | ぬかみみ | — | model_extra |
| 盗み見された | ぬすみみされた | ぬすみみされた | — | ぬすみみされた | coverage_diff |
| 華山 | — | — | — | かざん | model_missing |
| 華山派 | かざんは | かざんぱ | かざんぱい | — | model_extra |
| 調べる | しらべる | しらべる | — | しらべる | coverage_diff |
| 調査 | — | — | ちょうさ | — | model_extra |

## Sentence 68 (ud_gsd)
"用意できない信者は“経済舞台”が組まれ,印鑑や浄水器等を販売し,教会に貢献することが求められていた。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| “経済舞台” | — | — | けいざいだいがわ | — | model_extra |
| が組まれ | — | — | がくみまrekareba | — | model_extra |
| できない | — | — | できないうち | — | model_extra |
| や | — | — | や | — | model_extra |
| を販売し | — | — | をはんばいし | — | model_extra |
| 信者 | しんじゃ | しんじゃ | しんしゃ | しんじゃ | reading_diff |
| 器 | — | — | — | き | model_missing |
| 教会 | きょうかい | きょうかい | — | きょうかい | coverage_diff |
| 求められて | — | — | — | もとめられて | model_missing |
| 求められていた | もとめられていた | もとめられていた | — | — | model_extra |
| 浄水 | — | — | — | じょうすい | model_missing |
| 浄水器 | じょうすいき | — | じょうすいき | — | model_extra |
| 浄水器等 | — | じょうすいきとう | — | — | model_extra |
| 用意 | — | — | ようい | — | model_extra |
| 用意できない | よういできない | よういできない | — | よういできない | coverage_diff |
| 等 | とう | — | など | とう | reading_diff |
| 組まれ | くまれ | くまれ | — | くまれ | coverage_diff |
| 経済 | — | — | — | けいざい | model_missing |
| 経済舞台 | けいざいぶたい | けいざいぶたい | — | — | model_extra |
| 舞台 | — | — | — | ぶたい | model_missing |
| 貢献する | こうけんする | こうけんする | — | こうけんする | coverage_diff |
| 貢献することが求められていた | — | — | くせいせきすがもとめられていた | — | model_extra |
| 販売し | はんばいし | はんばいし | — | はんばいし | coverage_diff |

## Sentence 69 (ud_gsd)
"宇宙で無限の時間が経過すると、全てのエネルギーが均等に分布する状態に漸近的に到達すると考えられる。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| 。 | — | — | 。 | — | model_extra |
| が | — | — | が, が | — | model_extra |
| する | — | — | する, する | — | model_extra |
| すると | — | — | としたら | — | model_extra |
| で | — | — | で | — | model_extra |
| と | — | — | と | — | model_extra |
| に | — | — | に, に | — | model_extra |
| の | — | — | の, の | — | model_extra |
| エネルギー | — | — | ねんりょか | — | model_extra |
| 全て | すべて | すべて | ぜんぶ | すべて | reading_diff |
| 分布 | — | — | ふしゅつ | — | model_extra |
| 分布する | ぶんぷする | ぶんぷする | — | ぶんぷする | coverage_diff |
| 到達 | — | — | とうたつ | — | model_extra |
| 到達する | とうたつする | とうたつする | — | とうたつする | coverage_diff |
| 均等 | きんとう | — | きんとう | きんとう | coverage_diff |
| 均等に | — | きんとうに | — | — | model_extra |
| 漸近 | — | — | — | ぜんきん | model_missing |
| 漸近的 | ぜんきんてき | — | — | — | model_extra |
| 漸近的に | — | ぜんきんてきに | せんきんてきに | — | model_extra |
| 的 | — | — | — | てき | model_missing |
| 経過 | — | — | けいかい | — | model_extra |
| 経過する | けいかする | けいかする | — | けいかする | coverage_diff |

## Sentence 70 (ud_gsd)
"国際的に拘束力を持つ条約ではなく、勧告の形式で採択されたため、盛り込まれた措置の完全な実施を義務付けられることはない。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、, 、 | — | model_extra |
| された | — | — | された | — | model_extra |
| ため | — | — | ため | — | model_extra |
| で | — | — | で | — | model_extra |
| ではなく | — | — | ではなく | — | model_extra |
| ない | — | — | ない | — | model_extra |
| の | — | — | の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| ること | — | — | こと | — | model_extra |
| を | — | — | を | — | model_extra |
| を持つ | — | — | をもつ | — | model_extra |
| 付けられる | — | — | — | ずけられる | model_missing |
| 力 | — | — | — | りょく | model_missing |
| 国際 | — | — | — | こくさい | model_missing |
| 国際的 | こくさいてき | — | — | — | model_extra |
| 国際的に | — | こくさいてきに | こくさいてきに | — | model_extra |
| 形式 | けいしき | けいしき | しき | けいしき | reading_diff |
| 拘束 | — | — | — | こうそく | model_missing |
| 拘束力 | こうそくりょく | こうそくりょく | きそつりょく | — | model_extra |
| 持つ | もつ | もつ | — | もつ | coverage_diff |
| 採択 | — | — | さいせつ | — | model_extra |
| 採択された | さいたくされた | さいたくされた | — | さいたくされた | coverage_diff |
| 的 | — | — | — | てき | model_missing |
| 盛り込まれた | もりこまれた | もりこまれた | まじりこまれた | もりこまれた | reading_diff |
| 義務 | — | — | — | ぎむ | model_missing |
| 義務付けられ | — | — | ぎむつけられ | — | model_extra |
| 義務付けられる | ぎむづけられる | ぎむづけられる | — | — | model_extra |

## Sentence 71 (ud_gsd)
"なぜならば,私にその倉渕透と守谷香の関係を知られることは,二人のための大きな収入源が断たれてしまうことになるからです。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| から | — | — | から, から | — | model_extra |
| が | — | — | が | — | model_extra |
| こと | — | — | こと, こと | — | model_extra |
| その | — | — | その, その | — | model_extra |
| ため | — | — | のめい | — | model_extra |
| てしまう | — | — | てしまう | — | model_extra |
| です | — | — | です | — | model_extra |
| と | — | — | と, と | — | model_extra |
| なぜ | — | — | なにゆえ | — | model_extra |
| なら | — | — | なら | — | model_extra |
| なる | — | — | なる | — | model_extra |
| に | — | — | に, に | — | model_extra |
| になる | — | — | なる, なる | — | model_extra |
| の | — | — | の, の, の, の | — | model_extra |
| は | — | — | は, は | — | model_extra |
| られ | — | — | られる | — | model_extra |
| ること | — | — | こと, こと | — | model_extra |
| を | — | — | を, を | — | model_extra |
| 倉渕 | — | — | くらぶち, くらぶち | くらぶち | coverage_diff |
| 倉渕透 | くらぶちとおる | くらぶちとおる | — | — | model_extra |
| 収入 | — | — | — | しゅうにゅう | model_missing |
| 収入源 | しゅうにゅうげん | しゅうにゅうげん | しゅうにょんげん | — | model_extra |
| 守谷 | — | — | まもや, まもや | もりや | reading_diff |
| 守谷香 | もりやかおり | もりやかおり | — | — | model_extra |
| 断たれ | — | — | だんたれ | — | model_extra |
| 断たれて | — | — | — | たたれて | model_missing |
| 断たれてしまう | たたれてしまう | たたれてしまう | — | — | model_extra |
| 源 | — | — | — | げん | model_missing |
| 知られ | — | — | しれ, しれ | — | model_extra |
| 知られる | しられる | しられる | — | しられる | coverage_diff |
| 透 | — | — | と, と | とおる | reading_diff |
| 香 | — | — | か, か | かおり | reading_diff |

## Sentence 72 (ud_gsd)
"一人だけいた若い女性信者が手作りのミルクプリンと紅茶を出し,記者には海老澤代表が付いた。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 一人 | ひとり | ひとり | — | — | model_extra |
| 一人だけいた | — | — | — | ひとりだけいた | model_missing |
| 付いた | ついた | ついた | — | ついた | coverage_diff |
| 代表 | だいひょう | だいひょう | — | だいひょう | coverage_diff |
| 信者 | しんじゃ | しんじゃ | — | しんじゃ | coverage_diff |
| 出し | だし | だし | — | だし | coverage_diff |
| 女性 | じょせい | じょせい | — | じょせい | coverage_diff |
| 手作り | てづくり | てづくり | — | てづくり | coverage_diff |
| 海老澤 | えびさわ | えびさわ | — | えびさわ | coverage_diff |
| 紅茶 | こうちゃ | こうちゃ | — | こうちゃ | coverage_diff |
| 若い | わかい | わかい | — | わかい | coverage_diff |
| 記者 | きしゃ | きしゃ | — | きしゃ | coverage_diff |

## Sentence 73 (ud_gsd)
"同市の大久保寿夫市長は「県の責任で別途補助金を確保してくれるものと確信している」とのコメントを発表した。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 「 | — | — | 「 | — | model_extra |
| 」 | — | — | 」 | — | model_extra |
| と | — | — | と | — | model_extra |
| の | — | — | の | — | model_extra |
| の大久保寿夫市長 | — | — | のおおくぼひさおしみちょう | — | model_extra |
| は | — | — | は | — | model_extra |
| コメントを発表した | — | — | こめんとをはっぴょうした | — | model_extra |
| 別途 | べっと | べっと | — | べっと | coverage_diff |
| 別途補助金を確保してくれるものと | — | — | べっとほじきんをかくしゃするものと | — | model_extra |
| 大久保 | — | — | — | おおくぼ | model_missing |
| 大久保寿夫 | おおくぼとしお | おおくぼとしお | — | — | model_extra |
| 寿夫 | — | — | — | としお | model_missing |
| 市長 | しちょう | しちょう | — | しちょう | coverage_diff |
| 発表した | はっぴょうした | はっぴょうした | — | はっぴょうした | coverage_diff |
| 県 | けん | けん | — | けん | coverage_diff |
| 県の責任で | — | — | けんのせきにんで | — | model_extra |
| 確保して | — | — | — | かくほして | model_missing |
| 確保してくれる | かくほしてくれる | かくほしてくれる | — | — | model_extra |
| 確信して | — | — | — | かくしんして | model_missing |
| 確信している | かくしんしている | かくしんしている | かくしんでいる | — | model_extra |
| 補助 | — | — | — | ほじょ | model_missing |
| 補助金 | ほじょきん | ほじょきん | — | — | model_extra |
| 責任 | せきにん | せきにん | — | せきにん | coverage_diff |
| 金 | — | — | — | きん | model_missing |

## Sentence 74 (ud_gsd)
"2005年7月1日に浜松市に編入合併した旧三ケ日町の町役場庁舎を利用して三ヶ日総合事務所として開設された。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 1日 | ついたち | ついたち | ついたち | — | model_extra |
| 2005 | — | — | にせんごおつ | — | model_extra |
| 2005年 | にせんごねん | にせんごねん | — | — | model_extra |
| 7月 | しちがつ | しちがつ | しちがつ | — | model_extra |
| 。 | — | — | 。 | — | model_extra |
| された | — | — | された | — | model_extra |
| した | — | — | した | — | model_extra |
| て | — | — | て | — | model_extra |
| として | — | — | とおして | — | model_extra |
| に | — | — | に, に | — | model_extra |
| の | — | — | の | — | model_extra |
| を | — | — | を | — | model_extra |
| 三ケ日 | — | — | — | みっかび | model_missing |
| 三ケ日町 | みっかびちょう | みっかびちょう | — | — | model_extra |
| 三ヶ日 | — | — | — | みっかび | model_missing |
| 三ヶ日総合事務所 | みっかびそうごうじむしょ | みっかびそうごうじむしょ | みかじまそうごうじむしょ | — | model_extra |
| 事務 | — | — | — | じむ | model_missing |
| 利用 | — | — | りよう | — | model_extra |
| 利用して | りようして | りようして | — | りようして | coverage_diff |
| 合併した | — | — | — | がっぺいした | model_missing |
| 市 | — | — | — | し | model_missing |
| 年 | — | — | ねん | ねん | coverage_diff |
| 庁舎 | ちょうしゃ | — | — | ちょうしゃ | coverage_diff |
| 役場 | — | — | — | やくば | model_missing |
| 所として | — | — | — | しょとして | model_missing |
| 日 | — | — | — | にち | model_missing |
| 旧 | きゅう | きゅう | — | きゅう | coverage_diff |
| 旧三ケ日町 | — | — | きゅうみかじちょう | — | model_extra |
| 月 | — | — | — | がつ | model_missing |
| 浜松 | — | — | — | はままつ | model_missing |
| 浜松市 | はままつし | はままつし | はまなかしせん | — | model_extra |
| 町 | — | — | — | ちょう, まち | model_missing |
| 町役場 | まちやくば | — | — | — | model_extra |
| 町役場庁舎 | — | まちやくばちょうしゃ | ちょうやばちょうしゃ | — | model_extra |
| 総合 | — | — | — | そうごう | model_missing |
| 編入 | — | — | — | へんにゅう | model_missing |
| 編入合併 | — | — | へんにゅうごうべん | — | model_extra |
| 編入合併した | へんにゅうがっぺいした | へんにゅうがっぺいした | — | — | model_extra |
| 開設 | — | — | かいせつ | — | model_extra |
| 開設された | かいせつされた | かいせつされた | — | かいせつされた | coverage_diff |

## Sentence 75 (ud_gsd)
"現に統一教会も教祖の自叙伝を信者に大量購入させ,配り歩かせている。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| , | — | — | , | — | model_extra |
| 。 | — | — | . | — | model_extra |
| させ | — | — | さし | — | model_extra |
| た | — | — | た | — | model_extra |
| ている | — | — | ていて | — | model_extra |
| に | — | — | に, に | — | model_extra |
| の | — | — | の | — | model_extra |
| も | — | — | も | — | model_extra |
| を | — | — | を | — | model_extra |
| 伝 | — | — | — | でん | model_missing |
| 信者 | しんじゃ | しんじゃ | しんしゃ | しんじゃ | reading_diff |
| 大量 | たいりょう | — | だいりょう | たいりょう | reading_diff |
| 大量購入させ | — | たいりょうこうにゅうさせ | — | — | model_extra |
| 教会 | — | — | — | きょうかい | model_missing |
| 教祖 | きょうそ | きょうそ | きょうしゅ | きょうそ | reading_diff |
| 歩かせ | — | — | あるせ | — | model_extra |
| 現 | げん | — | げん | げん | coverage_diff |
| 現に | — | げんに | — | — | model_extra |
| 統一 | — | — | — | とういつ | model_missing |
| 統一教会 | とういつきょうかい | とういつきょうかい | とういつきょうかい | — | model_extra |
| 自叙 | — | — | — | じじょ | model_missing |
| 自叙伝 | じじょでん | じじょでん | じそでん | — | model_extra |
| 購入 | — | — | こうにゅう | — | model_extra |
| 購入させ | こうにゅうさせ | — | — | こうにゅうさせ | coverage_diff |
| 配り | — | — | はり | — | model_extra |
| 配り歩かせている | くばりあるかせている | くばりあるかせている | — | くばりあるかせている | coverage_diff |

## Sentence 76 (ud_gsd)
"子どもらを世話する養育者を資金支援する国の「ファミリーホーム制度」の活用を考え、移り住めるよう空き家も用意した。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| 「ファミリーホーム制度」 | — | — | 「ふみりえほむせいどじど」 | — | model_extra |
| える | — | — | える | — | model_extra |
| した | — | — | した | — | model_extra |
| する | — | — | する, する | — | model_extra |
| と | — | — | と | — | model_extra |
| の | — | — | の, の | — | model_extra |
| も | — | — | も | — | model_extra |
| よう | — | — | ように | — | model_extra |
| らを | — | — | らを | — | model_extra |
| を | — | — | を, を | — | model_extra |
| ファミリーホーム制度 | — | ふぁみりーほーむせいど | — | — | model_extra |
| 世話 | — | — | せわ | — | model_extra |
| 世話する | せわする | せわする | — | せわする | coverage_diff |
| 制度 | せいど | — | — | せいど | coverage_diff |
| 子ど | — | — | — | こど | model_missing |
| 子ども | こども | こども | こども | — | model_extra |
| 支援 | — | — | しえん | — | model_extra |
| 支援する | しえんする | — | — | しえんする | coverage_diff |
| 用意 | — | — | ようい | — | model_extra |
| 用意した | よういした | よういした | — | よういした | coverage_diff |
| 移り住める | うつりすめる | うつりすめる | いれすみえる | うつりすめる | reading_diff |
| 空き家 | あきや | あきや | くぎや | あきや | reading_diff |
| 考 | — | — | かんが | — | model_extra |
| 者 | — | — | — | しゃ | model_missing |
| 資金 | しきん | — | かしん | しきん | reading_diff |
| 資金支援する | — | しきんしえんする | — | — | model_extra |
| 養育 | — | — | — | よういく | model_missing |
| 養育者 | よういくしゃ | よういくしゃ | よういくしゃ | — | model_extra |

## Sentence 77 (ud_gsd)
"これに対して幸福の科学の信者が講談社を非難するデモや署名活動を行いましたが,抗議活動はこれだけではありませんでした。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| が | — | — | が, が | — | model_extra |
| これ | — | — | これ | — | model_extra |
| これだけ | — | — | これだけ | — | model_extra |
| ではありませんでした | — | — | ありませんでした | — | model_extra |
| に対して | — | — | たいして | — | model_extra |
| の | — | — | の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| や | — | — | や | — | model_extra |
| を | — | — | を, を | — | model_extra |
| デモ | — | — | でも | — | model_extra |
| 信者 | しんじゃ | しんじゃ | しんしゃ | しんじゃ | reading_diff |
| 対して | たいして | たいして | — | たいして | coverage_diff |
| 幸福 | こうふく | — | ふっこう | こうふく | reading_diff |
| 幸福の科学 | — | こうふくのかがく | — | — | model_extra |
| 抗議 | — | — | こうぎ | こうぎ | coverage_diff |
| 抗議活動 | こうぎかつどう | こうぎかつどう | — | — | model_extra |
| 活動 | かつどう | — | かつどう, かつどう | かつどう, かつどう | coverage_diff |
| 社 | — | — | — | しゃ | model_missing |
| 科学 | かがく | — | かがく | かがく | coverage_diff |
| 署名 | しょめい | — | しょめい | しょめい | coverage_diff |
| 署名活動 | — | しょめいかつどう | — | — | model_extra |
| 行いました | — | おこないました | おこないました | — | model_extra |
| 行いましたが | おこないましたが | — | — | おこないましたが | coverage_diff |
| 講談 | — | — | — | こうだん | model_missing |
| 講談社 | こうだんしゃ | こうだんしゃ | こうたんしゃ | — | model_extra |

## Sentence 78 (ud_gsd)
"物質界監視員として長年地上に派遣されており、現在は神貫の協力を取り付けてゼフォンの動向を探っている。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| として | — | — | とおして | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| を | — | — | を, を | — | model_extra |
| ゼフォン | — | — | ぜふぉん | — | model_extra |
| 員として | — | — | — | いんとして | model_missing |
| 地上 | ちじょう | ちじょう | じち | ちじょう | reading_diff |
| 探って | — | — | — | さぐって | model_missing |
| 探っている | さぐっている | さぐっている | さがっている | — | model_extra |
| 派遣されて | — | — | — | はけんされて | model_missing |
| 派遣されており | はけんされており | はけんされており | はいしゅうちょうされており | — | model_extra |
| 物質 | — | — | ぶしつ | ぶっしつ | reading_diff |
| 物質界 | ぶっしつかい | — | — | — | model_extra |
| 物質界監視員 | — | ぶっしつかいかんしいん | — | — | model_extra |
| 界 | — | — | かい | かい | coverage_diff |
| 監視 | — | — | — | かんし | model_missing |
| 監視員 | かんしいん | — | かんしいん | — | model_extra |
| 神貫 | かんぬき | かみぬき | かみがね | かんぬき | reading_diff |
| 長年 | ながねん | ながねん | ちょうねん | ながねん | reading_diff |

## Sentence 79 (ud_gsd)
"この反乱によってマウリキウスは皇位を追われ、息子たちが殺されるのを見せられた上で処刑されてしまった。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| 。 | — | — | 。 | — | model_extra |
| が | — | — | が | — | model_extra |
| この | — | — | この | — | model_extra |
| によって | — | — | でよって | — | model_extra |
| の | — | — | の | — | model_extra |
| は | — | — | は | — | model_extra |
| を | — | — | を, を | — | model_extra |
| マウリキウス | — | — | まおきうす | — | model_extra |
| 上 | うえ | うえ | — | うえ | coverage_diff |
| 上で | — | — | かで | — | model_extra |
| 処刑されて | — | — | — | しょけいされて | model_missing |
| 処刑されてしまった | しょけいされてしまった | しょけいされてしまった | しょけいされてしまった | — | model_extra |
| 息子 | むすこ | むすこ | — | むすこ | coverage_diff |
| 息子たち | — | — | きしたち | — | model_extra |
| 殺される | ころされる | ころされる | ころされ | ころされる | reading_diff |
| 追われ | おわれ | おわれ | おいわ | おわれ | reading_diff |

## Sentence 80 (ud_gsd)
"伝統的仏堂建築に新様式を取り入れた、近代仏堂の代表作として、2007年に国の重要文化財に指定された。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 2007年 | にせんななねん | にせんななねん | にせんひゃくしちねん | — | model_extra |
| 、 | — | — | 、, 、 | — | model_extra |
| として | — | — | とおして | — | model_extra |
| に | — | — | に, に, に | — | model_extra |
| の | — | — | の, の | — | model_extra |
| を | — | — | を | — | model_extra |
| 仏堂 | ぶつどう, ぶつどう | — | ぶどう, ぶどう | ぶつどう, ぶつどう | reading_diff |
| 仏堂建築 | — | ぶつどうけんちく | — | — | model_extra |
| 代表 | — | — | — | だいひょう | model_missing |
| 代表作 | だいひょうさく | だいひょうさく | だいひょうさく | — | model_extra |
| 伝統 | — | — | — | でんとう | model_missing |
| 伝統的 | でんとうてき | でんとうてき | でんとうてき | — | model_extra |
| 作として | — | — | — | さくとして | model_missing |
| 国 | くに | くに | こく | くに | reading_diff |
| 年 | — | — | — | ねん | model_missing |
| 建築 | けんちく | — | けっちゅう | けんちく | reading_diff |
| 指定された | していされた | していされた | しごいてられた | していされた | reading_diff |
| 文化 | — | — | — | ぶんか | model_missing |
| 文化財 | — | — | ぶんかざい | — | model_extra |
| 新 | — | — | しん | しん | coverage_diff |
| 新様式 | しんようしき | しんようしき | — | — | model_extra |
| 様式 | — | — | ようしき | ようしき | coverage_diff |
| 的 | — | — | — | てき | model_missing |
| 財 | — | — | — | ざい | model_missing |
| 近代 | きんだい | — | きんじだい | きんだい | reading_diff |
| 近代仏堂 | — | きんだいぶつどう | — | — | model_extra |
| 重要 | — | — | じゅうよう | じゅうよう | coverage_diff |
| 重要文化財 | じゅうようぶんかざい | じゅうようぶんかざい | — | — | model_extra |

## Sentence 81 (ud_pud)
"ジョコウィは大統領に就任する前に、退任するユドヨノ大統領に、補助金をさらに減額することで燃料価格を上昇させる決定について責任をとるように求めた。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、, 、 | — | model_extra |
| さらに | — | — | さらにお | — | model_extra |
| し | — | — | し | — | model_extra |
| で | — | — | で | — | model_extra |
| と | — | — | と | — | model_extra |
| に | — | — | に, に | — | model_extra |
| について | — | — | おわせについて | — | model_extra |
| は | — | — | は | — | model_extra |
| ように | — | — | ように | — | model_extra |
| を | — | — | を, を | — | model_extra |
| コウィ | — | — | こうぃ | — | model_extra |
| ジョ | — | — | じょ | — | model_extra |
| ユドヨノ | — | — | ゆどよの | — | model_extra |
| 上昇させる | じょうしょうさせる | じょうしょうさせる | じょうしょうさす | じょうしょうさせる | reading_diff |
| 価格 | かかく | — | かがい | かかく | reading_diff |
| 前 | まえ | まえ | — | まえ | coverage_diff |
| 前に | — | — | まえに | — | model_extra |
| 求めた | もとめた | もとめた | もくした | もとめた | reading_diff |
| 減額 | — | — | げんにゃく | — | model_extra |
| 減額する | げんがくする | げんがくする | — | げんがくする | coverage_diff |
| 燃料 | ねんりょう | — | りょうりえん | ねんりょう | reading_diff |
| 燃料価格 | — | ねんりょうかかく | — | — | model_extra |
| 補助 | — | — | — | ほじょ | model_missing |
| 補助金 | ほじょきん | ほじょきん | ほじきん | — | model_extra |
| 責任 | せきにん | せきにん | — | せきにん | coverage_diff |
| 責任を | — | — | せんせいを | — | model_extra |
| 退任する | たいにんする | たいにんする | たいんする | たいにんする | reading_diff |
| 金 | — | — | — | きん | model_missing |

## Sentence 82 (ud_pud)
"一方、最良の管理慣行が機能している良好な生態系は、こうした事態の発生機会を減少させるか、それができない場合でも悪影響の度合いを軽減します。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| か | — | — | か | — | model_extra |
| が | — | — | が | — | model_extra |
| こう | — | — | こう | — | model_extra |
| させる | — | — | さす | — | model_extra |
| した | — | — | した | — | model_extra |
| している | — | — | していいる | — | model_extra |
| します | — | — | すます | — | model_extra |
| それが | — | — | それが | — | model_extra |
| できない | — | — | できな | — | model_extra |
| でも | — | — | でも | — | model_extra |
| の | — | — | の, の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| を | — | — | を, を | — | model_extra |
| 場合 | ばあい | ばあい | ばいがい | ばあい | reading_diff |
| 影響 | — | — | — | えいきょう | model_missing |
| 悪 | — | — | — | あく | model_missing |
| 悪影響 | あくえいきょう | あくえいきょう | あくえいきょう | — | model_extra |
| 慣行 | かんこう | — | かんこう | かんこう | coverage_diff |
| 最良 | さいりょう | さいりょう | すばらしい | さいりょう | reading_diff |
| 機会 | きかい | — | きかい | きかい | coverage_diff |
| 機能 | — | — | き能 | — | model_extra |
| 機能して | — | — | — | きのうして | model_missing |
| 機能している | きのうしている | きのうしている | — | — | model_extra |
| 減少 | — | — | かげん | — | model_extra |
| 減少させる | げんしょうさせる | げんしょうさせる | — | げんしょうさせる | coverage_diff |
| 生態 | — | — | — | せいたい | model_missing |
| 生態系 | せいたいけい | せいたいけい | たいせきけい | — | model_extra |
| 発生 | はっせい | — | はっせい | はっせい | coverage_diff |
| 発生機会 | — | はっせいきかい | — | — | model_extra |
| 管理 | かんり | — | かんり | かんり | coverage_diff |
| 管理慣行 | — | かんりかんこう | — | — | model_extra |
| 系 | — | — | — | けい | model_missing |
| 良好な | りょうこうな | りょうこうな | こうりょうな | りょうこうな | reading_diff |
| 軽減 | — | — | けいげん | — | model_extra |
| 軽減します | けいげんします | けいげんします | — | けいげんします | coverage_diff |

## Sentence 83 (ud_pud)
"この分野での専門家として名を知られるようになった彼女は、それらのスキルと小さな円盤状のポロニウムをラジウム研究所に持ち帰った。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| こと | — | — | こと | — | model_extra |
| この | — | — | この | — | model_extra |
| それら | — | — | それら | — | model_extra |
| で | — | — | で | — | model_extra |
| と | — | — | と | — | model_extra |
| として | — | — | として | — | model_extra |
| な | — | — | な | — | model_extra |
| に | — | — | に, に | — | model_extra |
| の | — | — | の, の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| を | — | — | を, を | — | model_extra |
| スキル | — | — | しきる | — | model_extra |
| ポロニウム | — | — | ぽろにうむ | — | model_extra |
| ラジウム | — | — | らじうむ | — | model_extra |
| 了 | — | — | りょう | — | model_extra |
| 円盤 | — | — | — | えんばん | model_missing |
| 円盤状 | えんばんじょう | えんばんじょう | えんばんじょう | — | model_extra |
| 家として | — | — | — | かとして | model_missing |
| 専門 | — | — | — | せんもん | model_missing |
| 専門家 | せんもんか | せんもんか | せんもんか | — | model_extra |
| 所 | — | — | — | しょ | model_missing |
| 持ち帰った | もちかえった | もちかえった | もぎかえた | もちかえった | reading_diff |
| 状 | — | — | — | じょう | model_missing |
| 知られる | しられる | — | しられ | しられる | reading_diff |
| 知られるようになった | — | しられるようになった | — | — | model_extra |
| 研究 | — | — | — | けんきゅう | model_missing |
| 研究所 | けんきゅうしょ | けんきゅうじょ | けんきゅうじょ | — | model_extra |

## Sentence 84 (ud_pud)
"明治天皇以後、一人の天皇について一つの年号を付け、天皇の死後は統治の時代に使っていた年号を改めることが慣習となった。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| が | — | — | が | — | model_extra |
| こと | — | — | こと | — | model_extra |
| となった | — | — | なった | — | model_extra |
| に | — | — | に | — | model_extra |
| について | — | — | について | — | model_extra |
| の | — | — | の, の, の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| を | — | — | を, を | — | model_extra |
| 一つ | ひとつ | ひとつ | いちとう | ひとつ | reading_diff |
| 以後 | いご | いご | — | いご | coverage_diff |
| 以降 | — | — | いこう | — | model_extra |
| 使って | — | — | — | つかって | model_missing |
| 使っていた | つかっていた | つかっていた | つかっていた | — | model_extra |
| 改める | あらためる | あらためる | かいめる | あらためる | reading_diff |
| 明治 | — | — | めいじ | めいじ | coverage_diff |
| 明治天皇 | めいじてんのう | めいじてんのう | — | — | model_extra |
| 統治 | とうち | とうち | とうじ | とうち | reading_diff |

## Sentence 85 (ud_pud)
"彼が平凡な人生の後に老衰で亡くなるか、あるいは戦場で若くして命を落とし、詩を通じて不死を得ることが、そこでは予言されていました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、, 、, 、 | — | model_extra |
| あるいは | — | — | もしくは | — | model_extra |
| か | — | — | か | — | model_extra |
| が | — | — | が | — | model_extra |
| ことが | — | — | ことが | — | model_extra |
| して | — | — | して | — | model_extra |
| そこ | — | — | そこ | — | model_extra |
| で | — | — | で, で, で | — | model_extra |
| な | — | — | な | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の | — | model_extra |
| を通じて | — | — | つうじて | — | model_extra |
| 不死 | ふし | ふし | — | ふし | coverage_diff |
| 不死を得る | — | — | ふしをとる | — | model_extra |
| 予言されて | — | — | — | よげんされて | model_missing |
| 予言されていました | よげんされていました | よげんされていました | よげんされていました | — | model_extra |
| 亡くなる | なくなる | なくなる | むかっていく | なくなる | reading_diff |
| 命 | いのち | いのち | — | いのち | coverage_diff |
| 命を落とす | — | — | いのちをおとす | — | model_extra |
| 平凡 | — | — | へいぼん | — | model_extra |
| 平凡な | へいぼんな | へいぼんな | — | へいぼんな | coverage_diff |
| 後 | あと | あと | ご | あと | reading_diff |
| 得る | える | える | — | える | coverage_diff |
| 若く | — | — | わかく | — | model_extra |
| 若くして | わかくして | わかくして | — | わかくして | coverage_diff |
| 落とし | おとし | おとし | — | おとし | coverage_diff |
| 通じ | — | — | — | つうずる | model_missing |
| 通じて | つうじて | つうじて | — | — | model_extra |

## Sentence 86 (ud_pud)
"国際再生可能エネルギー機関（IRENA）総裁、Z.Aminは「洋上風力発電は世界経済において石炭エネルギーに依存しない最大の発電手段となりうる」と確信している。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| Z.Amin | — | — | ぜ・あみん | — | model_extra |
| 。 | — | — | 。 | — | model_extra |
| 「 | — | — | 「 | — | model_extra |
| と | — | — | と | — | model_extra |
| となりうる | — | — | となれる | — | model_extra |
| に | — | — | に | — | model_extra |
| において | — | — | にいてい | — | model_extra |
| は | — | — | は, は | — | model_extra |
| 世界 | — | — | — | せかい | model_missing |
| 世界経済 | せかいけいざい | せかいけいざい | せかいけいざい | — | model_extra |
| 依存 | — | — | — | いぞん | model_missing |
| 依存しない | いぞんしない | いぞんしない | いしゅんしない | — | model_extra |
| 再生 | さいせい | — | — | さいせい | coverage_diff |
| 再生可能エネルギー | — | — | せいせいか능에너지 | — | model_extra |
| 可能 | かのう | — | — | かのう | coverage_diff |
| 国際 | こくさい | — | こくさい | こくさい | coverage_diff |
| 国際再生可能エネルギー機関 | — | こくさいさいせいかのうえねるぎーきかん | — | — | model_extra |
| 手段 | しゅだん | — | — | しゅだん | coverage_diff |
| 最大 | さいだい | さいだい | — | さいだい | coverage_diff |
| 最大の | — | — | さいだいの | — | model_extra |
| 機関 | きかん | — | きかん | きかん | coverage_diff |
| 洋上 | ようじょう | — | — | ようじょう | coverage_diff |
| 洋上風力発電 | — | ようじょうふうりょくはつでん | ようじょうふうりょくはつでん | — | model_extra |
| 発電 | はつでん | — | — | はつでん, はつでん | coverage_diff |
| 発電手段 | — | はつでんしゅだん | はつでんだん | — | model_extra |
| 石炭 | せきたん | — | — | せきたん | coverage_diff |
| 石炭エネルギー | — | せきたんえねるぎー | せっとうねんりょく | — | model_extra |
| 確信して | — | — | — | かくしんして | model_missing |
| 確信している | かくしんしている | かくしんしている | かくしんしている | — | model_extra |
| 経済 | — | — | — | けいざい | model_missing |
| 総裁 | そうさい | そうさい | そうざい | そうさい | reading_diff |
| 風力 | — | — | — | ふうりょく | model_missing |
| 風力発電 | ふうりょくはつでん | — | — | — | model_extra |
| （IRENA） | — | — | （あいれな） | — | model_extra |

## Sentence 87 (ud_pud)
"しかし、機内インターネットは多くの場合信頼性に欠け、旅行者の航空会社の選択に影響を及ぼす可能性は低いと、ある海外旅行の専門家は警告した。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、, 、 | — | model_extra |
| ある | — | — | ある | — | model_extra |
| しかし | — | — | しかるべく | — | model_extra |
| と | — | — | と | — | model_extra |
| に | — | — | に, に | — | model_extra |
| の | — | — | の, の, の | — | model_extra |
| は | — | — | は, は, は | — | model_extra |
| を | — | — | を | — | model_extra |
| インターネット | — | — | いんたーねっと | — | model_extra |
| 会社 | — | — | — | かいしゃ | model_missing |
| 信頼 | — | — | — | しんらい | model_missing |
| 信頼性 | しんらいせい | しんらいせい | しんらいせい | — | model_extra |
| 及ぼす | およぼす | およぼす | およぶ | およぼす | reading_diff |
| 可能 | — | — | — | かのう | model_missing |
| 可能性 | かのうせい | かのうせい | かのうせい | — | model_extra |
| 多く | おおく | おおく | — | おおく | coverage_diff |
| 多くの | — | — | おおくの | — | model_extra |
| 家 | — | — | — | か | model_missing |
| 専門 | — | — | — | せんもん | model_missing |
| 専門家 | せんもんか | せんもんか | せんもんか | — | model_extra |
| 性 | — | — | — | せい, せい | model_missing |
| 旅行 | りょこう | — | — | りょこう, りょこう | coverage_diff |
| 旅行者 | りょこうしゃ | りょこうしゃ | りょこうしゃ | — | model_extra |
| 機内 | きない | — | きない | きない | coverage_diff |
| 機内インターネット | — | きないいんたーねっと | — | — | model_extra |
| 欠け | かけ | かけ | けがなき | かけ | reading_diff |
| 海外 | かいがい | — | — | かいがい | coverage_diff |
| 海外旅行 | — | かいがいりょこう | かいがいりょこう | — | model_extra |
| 者 | — | — | — | しゃ | model_missing |
| 航空 | — | — | — | こうくう | model_missing |
| 航空会社 | こうくうがいしゃ | こうくうがいしゃ | こうくうかいしゃ | — | model_extra |
| 警告した | けいこくした | けいこくした | きょうごうした | けいこくした | reading_diff |

## Sentence 88 (ud_pud)
"さらに彼女は、機密情報を彼女に提供した数々の政府系科学者との人脈を利用しました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| さらに | — | — | さらにお | — | model_extra |
| と | — | — | と | — | model_extra |
| の | — | — | の | — | model_extra |
| は | — | — | は | — | model_extra |
| を | — | — | を, を | — | model_extra |
| 情報 | — | — | じょうほう | じょうほう | coverage_diff |
| 政府 | — | — | — | せいふ | model_missing |
| 政府系 | せいふけい | — | せいふけい | — | model_extra |
| 政府系科学者 | — | せいふけいかがくしゃ | — | — | model_extra |
| 数々 | かずかず | かずかず | — | かずかず | coverage_diff |
| 数々の | — | — | すうしゅうの | — | model_extra |
| 機密 | — | — | きひつ | きみつ | reading_diff |
| 機密情報 | きみつじょうほう | きみつじょうほう | — | — | model_extra |
| 科学 | — | — | — | かがく | model_missing |
| 科学者 | かがくしゃ | — | かがくしゃ | — | model_extra |
| 系 | — | — | — | けい | model_missing |
| 者 | — | — | — | しゃ | model_missing |

## Sentence 89 (ud_pud)
"地中海全域の商業的な前哨基地を設立することで、それまで使用されていなかった技術である「貿易」が発展した。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| 「 | — | — | 「 | — | model_extra |
| 」 | — | — | 」 | — | model_extra |
| が | — | — | が | — | model_extra |
| した | — | — | した | — | model_extra |
| することで | — | — | でこと | — | model_extra |
| それまで | — | — | それまでは | — | model_extra |
| である | — | — | である | — | model_extra |
| の | — | — | の | — | model_extra |
| を | — | — | を | — | model_extra |
| 使用されて | — | — | — | しようされて | model_missing |
| 使用されていなかった | しようされていなかった | しようされていなかった | しようされていなかった | — | model_extra |
| 全域 | ぜんいき | ぜんいき | ぜいきょ | ぜんいき | reading_diff |
| 前哨 | — | — | ぜんしゅう | ぜんしょう | reading_diff |
| 前哨基地 | ぜんしょうきち | ぜんしょうきち | — | — | model_extra |
| 商業 | — | — | — | しょうぎょう | model_missing |
| 商業的な | しょうぎょうてきな | しょうぎょうてきな | しょうぎょうてんの | — | model_extra |
| 地中 | — | — | ちじ | ちちゅう | reading_diff |
| 地中海 | ちちゅうかい | ちちゅうかい | — | — | model_extra |
| 基地 | — | — | きじ | きち | reading_diff |
| 海 | — | — | かい | かい | coverage_diff |
| 発展 | — | — | はてん | — | model_extra |
| 発展した | はってんした | はってんした | — | はってんした | coverage_diff |
| 的な | — | — | — | てきな | model_missing |
| 設立 | — | — | せつりつ | — | model_extra |
| 設立する | せつりつする | せつりつする | — | せつりつする | coverage_diff |
| 貿易 | ぼうえき | ぼうえき | まひつ | ぼうえき | reading_diff |

## Sentence 90 (ud_pud)
"中国の旧正月や、タイの華人によるその他の饗宴は、旧暦こよみに基づいて計算されるので、どちらも日付が毎年変わります。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| が | — | — | ga | — | model_extra |
| その他 | — | そのた | — | — | model_extra |
| その他の | — | — | その他の | — | model_extra |
| どちらも | — | — | どちらも | — | model_extra |
| による | — | — | にゅうりょう | — | model_extra |
| に基づいて | — | — | にじたいて | — | model_extra |
| の | — | — | no, no | — | model_extra |
| ので | — | — | node | — | model_extra |
| は | — | — | wa | — | model_extra |
| や | — | — | ya | — | model_extra |
| タイ | — | — | たい | — | model_extra |
| 他 | た | — | — | ほか | reading_diff |
| 基づ | — | — | — | もとず | model_missing |
| 基づいて | もとづいて | もとづいて | — | — | model_extra |
| 日付 | ひづけ | ひづけ | にっぷ | ひずけ | reading_diff |
| 旧 | — | — | — | きゅう | model_missing |
| 旧暦 | きゅうれき | きゅうれき | こよみ | — | model_extra |
| 旧暦こよみ | — | — | — | きゅうれきこよみ | model_missing |
| 旧正月 | きゅうしょうがつ | きゅうしょうがつ | きゅうせいげつ | — | model_extra |
| 正月 | — | — | — | しょうがつ | model_missing |
| 毎年 | まいとし | まいとし | まいねん | まいとし | reading_diff |
| 計算される | けいさんされる | けいさんされる | けいさんされ | けいさんされる | reading_diff |

## Sentence 91 (ud_pud)
"今年の初め、セガールは、首都ベオグラードで武術学校の設立を申し出た後に、セルビア国籍を与えられた。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 与えられた | あたえられた | あたえられた | — | あたえられた | coverage_diff |
| 今年 | ことし | ことし | — | ことし | coverage_diff |
| 初め | はじめ | はじめ | — | はじめ | coverage_diff |
| 国籍 | こくせき | こくせき | — | こくせき | coverage_diff |
| 学校 | — | — | — | がっこう | model_missing |
| 後 | あと | あと | — | あと | coverage_diff |
| 武術 | — | — | — | ぶじゅつ | model_missing |
| 武術学校 | ぶじゅつがっこう | ぶじゅつがっこう | — | — | model_extra |
| 申し出た | もうしでた | もうしでた | — | もうしでるた | reading_diff |
| 設立 | せつりつ | せつりつ | — | せつりつ | coverage_diff |
| 首都 | しゅと | しゅと | — | しゅと | coverage_diff |

## Sentence 92 (ud_pud)
"プラトンは、権力は教育を受けた保護者に注意して委ねる方がずっと安全だろう、と考えた。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 保護 | — | — | — | ほご | model_missing |
| 保護者 | ほごしゃ | ほごしゃ | — | — | model_extra |
| 受けた | うけた | うけた | — | うけた | coverage_diff |
| 委ねる | ゆだねる | ゆだねる | — | ゆだねる | coverage_diff |
| 安全 | — | あんぜん | — | — | model_extra |
| 安全だろう | あんぜんだろう | — | — | あんぜんだろう | coverage_diff |
| 教育 | きょういく | きょういく | — | きょういく | coverage_diff |
| 方 | ほう | ほう | — | ほう | coverage_diff |
| 権力 | けんりょく | けんりょく | — | けんりょく | coverage_diff |
| 注意して | ちゅういして | ちゅういして | — | ちゅういして | coverage_diff |
| 考えた | かんがえた | かんがえた | — | かんがえた | coverage_diff |
| 者 | — | — | — | しゃ | model_missing |

## Sentence 93 (ud_pud)
"ブリスベンが繁栄するに連れて、河川の状態は下水道やゴミ捨て場並に悪化した。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 、 | — | — | 、 | — | model_extra |
| が | — | — | が | — | model_extra |
| に | — | — | に | — | model_extra |
| の | — | — | の | — | model_extra |
| は | — | — | は | — | model_extra |
| や | — | — | や | — | model_extra |
| ゴミ捨て | — | — | — | ごみすて | model_missing |
| ゴミ捨て場 | — | ごみすてば | ごみすてじょう | — | model_extra |
| ブリスベン | — | — | ぶりすべん | — | model_extra |
| 下水 | — | — | — | げすい | model_missing |
| 下水道 | げすいどう | げすいどう | かすいどう | — | model_extra |
| 並 | なみ | — | — | なみ | coverage_diff |
| 並に | — | なみに | なりに | — | model_extra |
| 場 | — | — | — | ば | model_missing |
| 悪化した | あっかした | あっかした | あかわした | あっかした | reading_diff |
| 捨て場 | すてば | — | — | — | model_extra |
| 連れて | つれて | つれて | れんれて | つれて | reading_diff |
| 道 | — | — | — | どう | model_missing |

## Sentence 94 (ud_pud)
"沈括は、行政官および政府役人としての高いスキルと能力で、王安石を感心させました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| および | — | — | および | — | model_extra |
| で、 | — | — | で、 | — | model_extra |
| と | — | — | と | — | model_extra |
| としての | — | — | としての | — | model_extra |
| は、 | — | — | は、 | — | model_extra |
| を | — | — | を | — | model_extra |
| スキル | — | — | すきる | — | model_extra |
| 安石 | — | — | あんせき | あんせき | coverage_diff |
| 官 | — | — | — | かん | model_missing |
| 役人 | やくにん | — | やくにん | — | model_extra |
| 役人として | — | — | — | やくにんとして | model_missing |
| 感心させました | かんしんさせました | かんしんさせました | かんしんさけました | かんしんさせました | reading_diff |
| 括 | — | — | かく | — | model_extra |
| 政府 | せいふ | — | せいふ | せいふ | coverage_diff |
| 政府役人 | — | せいふやくにん | — | — | model_extra |
| 沈 | — | — | しん | — | model_extra |
| 沈括 | ちんかつ | しんかつ | — | ちんかつ | reading_diff |
| 王 | — | — | おう | おう | coverage_diff |
| 王安石 | おうあんせき | おうあんせき | — | — | model_extra |
| 行政 | — | — | — | ぎょうせい | model_missing |
| 行政官 | ぎょうせいかん | ぎょうせいかん | せいこうかん | — | model_extra |

## Sentence 95 (ud_pud)
"複数の古代文明は地中海沿岸にあり、付近の海から大きな影響を受けました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 付近 | ふきん | ふきん | — | ふきん | coverage_diff |
| 受けました | うけました | うけました | — | うけました | coverage_diff |
| 古代 | — | — | — | こだい | model_missing |
| 古代文明 | こだいぶんめい | こだいぶんめい | — | — | model_extra |
| 地中 | — | — | — | ちちゅう | model_missing |
| 地中海沿岸 | ちちゅうかいえんがん | ちちゅうかいえんがん | — | — | model_extra |
| 大きな | おおきな | おおきな | — | おおきな | coverage_diff |
| 影響 | えいきょう | えいきょう | — | えいきょう | coverage_diff |
| 文明 | — | — | — | ぶんめい | model_missing |
| 沿岸 | — | — | — | えんがん | model_missing |
| 海 | うみ | うみ | — | かい, うみ | reading_diff |
| 複数 | ふくすう | ふくすう | — | ふくすう | coverage_diff |

## Sentence 96 (ud_pud)
"「私はノーサンプトン大学で示される新しい才能を取り上げるために訪問します。」と彼は言う。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 。 | — | — | 。 | — | model_extra |
| ため | — | — | の | — | model_extra |
| で | — | — | で | — | model_extra |
| と | — | — | と | — | model_extra |
| に | — | — | に | — | model_extra |
| は | — | — | は, は | — | model_extra |
| を | — | — | を | — | model_extra |
| ノーサンプトン | — | — | のーさんぷとん | — | model_extra |
| ノーサンプトン大学 | — | のーさんぷとんだいがく | — | — | model_extra |
| 大学 | だいがく | — | だいがく | だいがく | coverage_diff |
| 才能 | さいのう | さいのう | さいがい | さいのう | reading_diff |
| 示される | しめされる | しめされる | しめられる | しめされる | reading_diff |
| 言う | いう | いう | いいます | いう | reading_diff |

## Sentence 97 (ud_pud)
"しかし、彼らの友情は二人の非公式的な協業をめぐって生じた法的紛争によってひび割れることになった。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| こと | — | — | こと | — | model_extra |
| しかし | — | — | しかるべく | — | model_extra |
| て | — | — | て | — | model_extra |
| に | — | — | に, に | — | model_extra |
| の | — | — | の, の | — | model_extra |
| は | — | — | は | — | model_extra |
| ひび割れ | — | — | ひびわり | — | model_extra |
| ひび割れる | — | ひびわれる | — | ひびわれる | coverage_diff |
| めぐって | — | — | めぐって | — | model_extra |
| を | — | — | を | — | model_extra |
| 公式 | — | — | — | こうしき | model_missing |
| 割れる | われる | — | — | — | model_extra |
| 生じ | — | — | — | しょうずる | model_missing |
| 生じた | しょうじた | しょうじた | うまれた | — | model_extra |
| 由来 | — | — | ゆらい | — | model_extra |
| 的な | — | — | — | てきな | model_missing |
| 非 | — | — | — | ひ | model_missing |
| 非公式的な | ひこうしきてきな | ひこうしきてきな | ひこうしきな | — | model_extra |

## Sentence 98 (ud_pud)
"デジタル技術の問題に関する法案を提言するフランスデジタル審議会も、それを調査することになる可能性がある。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| 会 | — | — | — | かい | model_missing |
| 可能 | — | — | — | かのう | model_missing |
| 可能性 | かのうせい | かのうせい | — | — | model_extra |
| 問題 | もんだい | もんだい | — | もんだい | coverage_diff |
| 審議 | — | — | — | しんぎ | model_missing |
| 審議会 | しんぎかい | しんぎかい | — | — | model_extra |
| 性 | — | — | — | せい | model_missing |
| 技術 | ぎじゅつ | ぎじゅつ | — | ぎじゅつ | coverage_diff |
| 提言する | ていげんする | ていげんする | — | ていげんする | coverage_diff |
| 法案 | ほうあん | ほうあん | — | ほうあん | coverage_diff |
| 調査 | — | ちょうさ | — | — | model_extra |
| 調査する | ちょうさする | — | — | ちょうさする | coverage_diff |
| 関する | かんする | かんする | — | かんする | coverage_diff |

## Sentence 99 (ud_pud)
"しかし、女性、特に出産の役割を担う女性を含む人口統計学および人口データの広範な統計的分析が行われてきた。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| および | — | — | および | — | model_extra |
| が | — | — | が | — | model_extra |
| しかし | — | — | しかるべく | — | model_extra |
| な | — | — | な | — | model_extra |
| の | — | — | の, の | — | model_extra |
| を | — | — | を, を | — | model_extra |
| データ | — | — | てきとう | — | model_extra |
| 人口統計学 | じんこうとうけいがく | じんこうとうけいがく | — | — | model_extra |
| 分析 | ぶんせき | — | ぶんせき | ぶんせき | coverage_diff |
| 女性 | じょせい, じょせい | じょせい, じょせい | じょし, じょし | じょせい, じょせい | reading_diff |
| 学 | — | — | — | がく | model_missing |
| 広範 | — | — | こうはん | — | model_extra |
| 広範な | こうはんな | こうはんな | — | こうはんな | coverage_diff |
| 担う | になう | になう | たもつ | になう | reading_diff |
| 特 | とく | — | — | とく | coverage_diff |
| 特に | — | とくに | とくに | — | model_extra |
| 的 | — | — | — | てき | model_missing |
| 統計 | — | — | — | とうけい, とうけい | model_missing |
| 統計学 | — | — | とうけいがく | — | model_extra |
| 統計的 | とうけいてき | — | とうけいてき | — | model_extra |
| 統計的分析 | — | とうけいてきぶんせき | — | — | model_extra |
| 行われて | — | — | — | おこなわれて | model_missing |
| 行われてきた | おこなわれてきた | おこなわれてきた | おこなわれてき | — | model_extra |

## Sentence 100 (ud_pud)
"後年、アウグストゥスがローマ帝国を創設した際に、ローマ人たちは地中海をマレ・ノストラム（「私たちの海」）と呼びました。"

| Surface | claude_v2 | gemini | qwen7b | v7 GT | Type |
|---------|---------|---------|---------|-------|------|
| い | — | — | い | — | model_extra |
| が | — | — | が | — | model_extra |
| した | — | — | した | — | model_extra |
| たち | — | — | たち | — | model_extra |
| と | — | — | と | — | model_extra |
| に | — | — | に | — | model_extra |
| は | — | — | は | — | model_extra |
| び | — | — | び | — | model_extra |
| ま | — | — | ま, ま | — | model_extra |
| を | — | — | を, を | — | model_extra |
| アウグストゥス | — | — | あうぐすとぅす | — | model_extra |
| マレ・ノストラム | — | — | まれ・のすとらむ | — | model_extra |
| ローマ | — | — | ろーま | — | model_extra |
| ローマ人 | — | ろーまじん | ろーまじん | — | model_extra |
| ローマ帝国 | — | ろーまていこく | — | — | model_extra |
| 人 | じん | — | — | じん | coverage_diff |
| 創設 | — | — | そうせつ | — | model_extra |
| 創設した | そうせつした | そうせつした | — | そうせつした | coverage_diff |
| 呼 | — | — | よ | — | model_extra |
| 呼びました | よびました | よびました | — | よびました | coverage_diff |
| 地中 | — | — | — | ちちゅう | model_missing |
| 地中海 | ちちゅうかい | ちちゅうかい | ちtml海 | — | model_extra |
| 帝国 | ていこく | — | ていこく | ていこく | coverage_diff |
| 年 | — | — | ねん | — | model_extra |
| 後 | — | — | ご | — | model_extra |
| 後年 | こうねん | こうねん | — | こうねん | coverage_diff |
| 海 | うみ | うみ | かい | かい, うみ | reading_diff |
| 私 | わたし | — | — | わたし | coverage_diff |
| 私たち | — | わたしたち | — | — | model_extra |
| 私たちの | — | — | わたしたちの | — | model_extra |
| 際 | さい | さい | き | さい | reading_diff |

