# Phase H vocabulary alignment audit

> Historical audit snapshot before the authorized Phase H1 cleanup. English row 91's three trailing spaces were subsequently removed without changing the word or row order; the current structural validator now reports zero issues. The CSV retains the original pre-cleanup source value for audit traceability. Semantic decisions remain pending in [the owner decision package](phase_h_owner_decisions.md).

## 1. Executive summary

- Desk-reviewed all 100 aligned source-line triples. No source vocabulary, query, image, audio, or metadata was changed.
- Each source has 100 physical rows, no blanks, and no normalized duplicates. The confirmed structural issue is three trailing spaces in English row 91.
- 23 rows need an owner decision about sense, spelling, register, or usage. The remaining 77 have no specific issue from this desk review but lack independent bilingual sign-off. No row is automatically marked semantically correct.
- All 10 existing queries, images, and image metadata files were checked. Rows 4 and 9 have confirmed query/image drift from the meaning indicated by Japanese and Vietnamese.
- No Japanese MP3 is present in the normal dataset directory. Three valid MP3s exist only in the isolated smoke directory.
- The owner reports good pronunciation after listening and reasonably accurate downloaded images. This positive sample feedback does not independently verify all 100 entries.

## 2. Vocabulary source inventory

| Source | Physical rows | Empty rows | Duplicate normalized entries | Note |
|---|---:|---:|---:|---|
| data/vocabulary/en.txt | 100 | 0 | 0 | Row 91 has three trailing spaces |
| data/vocabulary/jp.txt | 100 | 0 | 0 | Kana text is the current display and reading; no separate kanji field |
| data/vocabulary/vn.txt | 100 | 0 | 0 | Original translations preserved |

Supporting sources: data/query/generated_qwen.json, data/query/generated_qwen_water_beverage.json, data/image/en/, data/audio/jp/, and baseline/gtts-smoke-2026-10-28/. The two query-cache files are byte-identical in the current working tree. The historical water substance snapshot is outdated.

## 3. Structural validation

Command: .\.venv\Scripts\python.exe "collect data script/validate_vocabulary.py". Observed: Physical rows: 100; en: line 91: surrounding whitespace; Structural issues: 1; exit code 1, as expected for a finding. The read-only validator checks UTF-8, physical row count, blanks, normalized duplicates, and surrounding whitespace. Equal row counts alone cannot establish translation or semantic order.

## 4. Complete 100-row alignment table

Status meanings: present_valid means the JPEG opens and word/query metadata matches the current cache. present_valid_semantic_drift means file and metadata are valid but image meaning differs. smoke_only_valid is outside the normal dataset. review_required is a human decision queue. not_independently_verified means the desk review found no specific issue but independent sign-off has not occurred.

| Row | English | Japanese | Vietnamese | Qwen query | Image | Audio | Semantic status | Issue type |
|---:|---|---|---|---|---|---|---|---|
| 1 | apple | りんご | quả táo | apple fruit | present_valid | smoke_only_valid | not_independently_verified | - |
| 2 | banana | バナナ | quả chuối | banana fruit | present_valid | smoke_only_valid | not_independently_verified | - |
| 3 | strawberry | いちご | dâu tây | strawberry fruit | present_valid | smoke_only_valid | not_independently_verified | - |
| 4 | rice | ごはん | cơm | rice grain | present_valid_semantic_drift | missing | review_required | target_sense;query_image_drift |
| 5 | bread | パン | bánh mì | bread food | present_valid | missing | not_independently_verified | - |
| 6 | egg | たまご | trứng | egg food | present_valid | missing | not_independently_verified | - |
| 7 | milk | ぎゅうにゅう | sữa | milk beverage | present_valid | missing | review_required | specificity |
| 8 | water | みず | nước | water beverage | present_valid | missing | not_independently_verified | - |
| 9 | chicken | とりにく | thịt gà | chicken animal | present_valid_semantic_drift | missing | review_required | target_sense;query_image_drift |
| 10 | breakfast | あさごはん | bữa sáng | breakfast meal | present_valid | missing | not_independently_verified | - |
| 11 | cat | ねこ | mèo | - | missing | missing | not_independently_verified | - |
| 12 | dog | いぬ | chó | - | missing | missing | not_independently_verified | - |
| 13 | elephant | ぞう | voi | - | missing | missing | not_independently_verified | - |
| 14 | tree | き | cây | - | missing | missing | not_independently_verified | - |
| 15 | flower | はな | hoa | - | missing | missing | review_required | kana_homophone |
| 16 | mountain | やま | núi | - | missing | missing | not_independently_verified | - |
| 17 | river | かわ | sông | - | missing | missing | not_independently_verified | - |
| 18 | sun | たいよう | mặt trời | - | missing | missing | not_independently_verified | - |
| 19 | rain | あめ | mưa | - | missing | missing | review_required | kana_homophone |
| 20 | weather | てんき | thời tiết | - | missing | missing | not_independently_verified | - |
| 21 | house | いえ | ngôi nhà | - | missing | missing | not_independently_verified | - |
| 22 | kitchen | だいどころ | nhà bếp | - | missing | missing | not_independently_verified | - |
| 23 | school | がっこう | trường học | - | missing | missing | not_independently_verified | - |
| 24 | library | としょかん | thư viện | - | missing | missing | not_independently_verified | - |
| 25 | hospital | びょういん | bệnh viện | - | missing | missing | not_independently_verified | - |
| 26 | airport | くうこう | sân bay | - | missing | missing | not_independently_verified | - |
| 27 | restaurant | レストラン | nhà hàng | - | missing | missing | not_independently_verified | - |
| 28 | car | くるま | ô tô | - | missing | missing | not_independently_verified | - |
| 29 | bicycle | じてんしゃ | xe đạp | - | missing | missing | not_independently_verified | - |
| 30 | bridge | はし | cây cầu | - | missing | missing | review_required | kana_homophone |
| 31 | book | ほん | sách | - | missing | missing | not_independently_verified | - |
| 32 | phone | でんわ | điện thoại | - | missing | missing | not_independently_verified | - |
| 33 | computer | コンピューター | máy tính | - | missing | missing | not_independently_verified | - |
| 34 | umbrella | かさ | ô/dù | - | missing | missing | not_independently_verified | - |
| 35 | shirt | シャツ | áo sơ mi | - | missing | missing | review_required | specificity |
| 36 | family | かぞく | gia đình | - | missing | missing | not_independently_verified | - |
| 37 | mother | はは | mẹ | - | missing | missing | review_required | register |
| 38 | friend | ともだち | bạn bè | - | missing | missing | review_required | number |
| 39 | teacher | せんせい | giáo viên | - | missing | missing | not_independently_verified | - |
| 40 | engineer | エンジニア | kỹ sư | - | missing | missing | not_independently_verified | - |
| 41 | today | きょう | hôm nay | - | missing | missing | not_independently_verified | - |
| 42 | tomorrow | あした | ngày mai | - | missing | missing | not_independently_verified | - |
| 43 | yesterday | きのう | hôm qua | - | missing | missing | not_independently_verified | - |
| 44 | winter | ふゆ | mùa đông | - | missing | missing | not_independently_verified | - |
| 45 | happy | うれしい | vui | - | missing | missing | review_required | nuance |
| 46 | hungry | おなかがすいた | đói | - | missing | missing | not_independently_verified | - |
| 47 | easy | やさしい | dễ | - | missing | missing | review_required | kana_homophone |
| 48 | difficult | むずかしい | khó | - | missing | missing | not_independently_verified | - |
| 49 | beautiful | きれい | đẹp | - | missing | missing | review_required | polysemy |
| 50 | strong | つよい | mạnh | - | missing | missing | not_independently_verified | - |
| 51 | go | いく | đi | - | missing | missing | not_independently_verified | - |
| 52 | read | よむ | đọc | - | missing | missing | not_independently_verified | - |
| 53 | write | かく | viết | - | missing | missing | review_required | kana_homophone |
| 54 | study | べんきょうする | học tập | - | missing | missing | not_independently_verified | - |
| 55 | work | はたらく | làm việc | - | missing | missing | not_independently_verified | - |
| 56 | sleep | ねる | ngủ | - | missing | missing | not_independently_verified | - |
| 57 | eat | たべる | ăn | - | missing | missing | not_independently_verified | - |
| 58 | drink | のむ | uống | - | missing | missing | not_independently_verified | - |
| 59 | buy | かう | mua | - | missing | missing | not_independently_verified | - |
| 60 | help | たすける | giúp đỡ | - | missing | missing | review_required | nuance |
| 61 | understand | わかる | hiểu | - | missing | missing | not_independently_verified | - |
| 62 | remember | おぼえる | nhớ | - | missing | missing | not_independently_verified | - |
| 63 | receive | うけとる | nhận | - | missing | missing | not_independently_verified | - |
| 64 | choose | えらぶ | chọn | - | missing | missing | not_independently_verified | - |
| 65 | swim | およぐ | bơi | - | missing | missing | not_independently_verified | - |
| 66 | software | ソフトウェア | phần mềm | - | missing | missing | not_independently_verified | - |
| 67 | database | データベース | cơ sở dữ liệu | - | missing | missing | not_independently_verified | - |
| 68 | password | パスワード | mật khẩu | - | missing | missing | not_independently_verified | - |
| 69 | music | おんがく | âm nhạc | - | missing | missing | not_independently_verified | - |
| 70 | language | ことば | ngôn ngữ | - | missing | missing | review_required | polysemy |
| 71 | problem | もんだい | vấn đề | - | missing | missing | not_independently_verified | - |
| 72 | business | ビジネス | kinh doanh | - | missing | missing | not_independently_verified | - |
| 73 | university | だいがく | trường đại học | - | missing | missing | not_independently_verified | - |
| 74 | project | プロジェクト | dự án | - | missing | missing | not_independently_verified | - |
| 75 | experience | けいけん | kinh nghiệm | - | missing | missing | not_independently_verified | - |
| 76 | vegetable | やさい | rau | - | missing | missing | not_independently_verified | - |
| 77 | important | たいせつ | quan trọng | - | missing | missing | not_independently_verified | - |
| 78 | different | ちがう | khác | - | missing | missing | review_required | grammar |
| 79 | dangerous | あぶない | nguy hiểm | - | missing | missing | not_independently_verified | - |
| 80 | impossible | ふかのう | không thể | - | missing | missing | not_independently_verified | - |
| 81 | because | なぜなら | bởi vì | - | missing | missing | review_required | grammar |
| 82 | always | いつも | luôn luôn | - | missing | missing | not_independently_verified | - |
| 83 | sometimes | ときどき | thỉnh thoảng | - | missing | missing | not_independently_verified | - |
| 84 | together | いっしょに | cùng nhau | - | missing | missing | not_independently_verified | - |
| 85 | where | どこ | ở đâu | - | missing | missing | not_independently_verified | - |
| 86 | why | なぜ | tại sao | - | missing | missing | not_independently_verified | - |
| 87 | hello | こんにちは | xin chào | - | missing | missing | review_required | usage |
| 88 | please | おねがいします | làm ơn/xin vui lòng | - | missing | missing | review_required | usage |
| 89 | thanks | ありがとう | cảm ơn | - | missing | missing | not_independently_verified | - |
| 90 | sorry | すみません | xin lỗi | - | missing | missing | review_required | usage |
| 91 | apartment [3 trailing spaces] | アパート | căn hộ | - | missing | missing | review_required | structural_whitespace;specificity |
| 92 | dictionary | じしょ | từ điển | - | missing | missing | not_independently_verified | - |
| 93 | supermarket | スーパーマーケット | siêu thị | - | missing | missing | not_independently_verified | - |
| 94 | pharmacy | やっきょく | nhà thuốc | - | missing | missing | not_independently_verified | - |
| 95 | museum | はくぶつかん | bảo tàng | - | missing | missing | not_independently_verified | - |
| 96 | waterfall | たき | thác nước | - | missing | missing | not_independently_verified | - |
| 97 | firefighter | しょうぼうし | lính cứu hỏa | - | missing | missing | not_independently_verified | - |
| 98 | neighbor | となりのひと | hàng xóm | - | missing | missing | review_required | specificity |
| 99 | daughter | むすめ | con gái | - | missing | missing | not_independently_verified | - |
| 100 | grandmother | そぼ | bà | - | missing | missing | review_required | register |

## 5. Semantic issues requiring review

The 23 flagged rows are suspected semantic/usage issues, not 23 confirmed translation errors. Rows 4 and 9 additionally have confirmed query/image drift. Categories overlap:
- grammar: 2 row(s).
- kana_homophone: 5 row(s).
- nuance: 2 row(s).
- number: 1 row(s).
- polysemy: 2 row(s).
- query_image_drift: 2 row(s).
- register: 2 row(s).
- specificity: 4 row(s).
- structural_whitespace: 1 row(s).
- target_sense: 2 row(s).
- usage: 3 row(s).

| Row | Triple | Review note | Proposed correction for approval |
|---:|---|---|---|
| 4 | rice / ごはん / cơm | Japanese/Vietnamese refer to cooked rice; the query and image show grain. | Decide cooked rice: clarify English as cooked rice and use a cooked-rice query/image. If grain is intended, revise Japanese and Vietnamese instead. |
| 7 | milk / ぎゅうにゅう / sữa | Japanese gyuunyuu specifies cow's milk; English/Vietnamese can be broader. | Confirm cow's milk as the intended sense or choose a broader Japanese term with a definition. |
| 9 | chicken / とりにく / thịt gà | Japanese/Vietnamese refer to chicken meat; the query and image show a live bird. | Decide chicken meat: clarify English and use a meat query/image. If the bird is intended, consider niwatori and Vietnamese con ga. |
| 15 | flower / はな / hoa | Japanese hana in kana can represent flower or nose. | Record the flower sense, optionally with kanji, after review. |
| 19 | rain / あめ / mưa | Japanese ame in kana can represent rain or candy. | Record the rain sense, optionally with kanji, after review. |
| 30 | bridge / はし / cây cầu | Japanese hashi in kana can represent bridge or chopsticks. | Record the bridge sense, optionally with kanji, after review. |
| 35 | shirt / シャツ / áo sơ mi | Vietnamese ao so mi is narrower than generic shirt. | Use a generic Vietnamese shirt label or clarify English as a button-up shirt. |
| 37 | mother / はは / mẹ | Japanese haha usually refers to one's own mother in conversation. | Confirm own-mother context or choose the appropriate form for addressing/referencing another mother. |
| 38 | friend / ともだち / bạn bè | English friend is singular; Vietnamese ban be is usually collective/plural. | Use a singular Vietnamese friend label or change English to friends. |
| 45 | happy / うれしい / vui | Japanese ureshii is closer to glad/pleased than every sense of happy. | Specify glad/pleased or select a Japanese term for the intended longer-term happiness sense. |
| 47 | easy / やさしい / dễ | Japanese yasashii in kana can mean easy or kind depending on kanji. | Record the easy sense, optionally with kanji, or consider kantan. |
| 49 | beautiful / きれい / đẹp | Japanese kirei can mean beautiful or clean. | Specify the beautiful sense or use a less ambiguous Japanese expression. |
| 53 | write / かく / viết | Japanese kaku in kana can mean write or draw depending on kanji. | Record the write sense, optionally with kanji, after review. |
| 60 | help / たすける / giúp đỡ | Japanese tasukeru often means rescue/help in difficulty; help is broader. | Choose the rescue/aid context or consider tetsudau for ordinary assistance. |
| 70 | language / ことば / ngôn ngữ | Japanese kotoba can mean language, word, or speech. | Select language system or words/speech; consider gengo for a language system. |
| 78 | different / ちがう / khác | Japanese chigau is verbal, while different is adjectival. | Document usage in an example; decide whether part of speech matters for the game. |
| 81 | because / なぜなら / bởi vì | Japanese nazenara commonly introduces an explanation and is not interchangeable with because in every position. | Specify a sentence pattern or revise the Japanese for the intended clause use. |
| 87 | hello / こんにちは / xin chào | Japanese konnichiwa is normally a daytime greeting; hello is broader. | Specify daytime greeting context or choose a greeting suitable for the lesson. |
| 88 | please / おねがいします / làm ơn/xin vui lòng | Japanese onegaishimasu is a request formula rather than a universal please particle. | Specify the request context in a usage example. |
| 90 | sorry / すみません / xin lỗi | Japanese sumimasen can mean sorry, excuse me, or an attention-getter. | Specify the apology context in an example. |
| 91 | apartment / アパート / căn hộ | English has three trailing spaces; Japanese apaato can imply a narrower housing type than apartment. | After approval, remove three trailing spaces and clarify the housing sense if needed. |
| 98 | neighbor / となりのひと / hàng xóm | Japanese tonari no hito means the person next door, narrower than neighborhood neighbor. | Specify next-door neighbor or use a broader Japanese term for someone nearby. |
| 100 | grandmother / そぼ / bà | Japanese sobo usually refers to one's own grandmother, unlike a direct address. | Specify own-grandmother context and note the address form if needed. |

Selected dictionary checks support the highest-risk distinctions: [chicken as bird or meat](https://dictionary.cambridge.org/dictionary/english-japanese/chicken), [cooked rice/meal](https://dictionary.cambridge.org/dictionary/japanese-english/%E5%BE%A1-), [easy](https://dictionary.cambridge.org/dictionary/japanese-english/%E6%98%93%E3%81%97%E3%81%84) versus [kind](https://dictionary.cambridge.org/dictionary/japanese-english/%E5%84%AA%E3%81%97%E3%81%84), [beautiful versus clean](https://dictionary.cambridge.org/dictionary/japanese-english/%E7%B6%BA%E9%BA%97), and [language versus word](https://dictionary.cambridge.org/dictionary/japanese-english/%E8%A8%80%E8%91%89). Dictionary verification was selective, not a 100-entry independent linguistic review.

## 6. Query and image alignment

- Both query JSON files have the same 10 ordered records, signature, and bytes; 90 rows have no query. Missing queries are an asset-coverage gap, not translation failures.
- All 10 image metadata records have a word and search_query matching the cache, with duckduckgo provider. All 10 JPEGs opened with Pillow and have dimensions at or below 1024 by 1024. No missing or stale word/query metadata was found. The metadata does not store a final output image path; the filename is inferred from the English word.
- Row 4 uses rice grain and displays unprocessed grain, while the Japanese/Vietnamese point to cooked rice. Row 9 uses chicken animal and displays a live hen, while the Japanese/Vietnamese point to meat.
- The other eight images appear conceptually aligned on direct visual inspection. This is not a full independent visual or image-license review. Water is depicted as bottled water, a narrower presentation consistent with water beverage.

## 7. Audio mapping

- data/audio/jp/ has no dataset MP3/WAV or audio metadata: all 100 expected normal audio paths are missing. No stale audio reference was found there.
- The isolated baseline/gtts-smoke-2026-10-28/ has three MP3s and matching metadata: row 1 Japanese text (7,488 bytes, 0.936 s), row 2 (7,104 bytes, 0.888 s), row 3 (7,488 bytes, 0.936 s). All passed the current MP3 parser. Filename, word, reading, relative path, size, duration, source google_translate_gtts, locale ja, voice com/slow=false, and format mp3 match metadata. The 100 Japanese source strings have no duplicates.
- Smoke metadata keys 1-3 currently match physical row indices, but those keys are order-dependent. Phase I should address stable identifiers. Smoke assets are not counted as normal dataset coverage.

## 8. Missing assets

| Asset | Present in normal dataset | Missing of 100 | Note |
|---|---:|---:|---|
| Qwen query | 10 | 90 | No new query generated in this audit |
| English JPEG and metadata | 10 | 90 | Two present images drift from target sense |
| Japanese MP3 and metadata | 0 | 100 | Three valid MP3s exist only in isolated smoke |

Missing media is separate from semantic translation quality.

## 9. Recommended corrections, not applied

Decide the target sense for rows 4 and 9 before collecting more images. Review the other 21 flagged rows, especially kana homophones, semantic scope, and usage context. Approve cleanup of row 91's three trailing spaces. The CSV lists each proposed change. No source vocabulary, query, or media was altered in Phase H.

## 10. Readiness for the next phase

The Phase H audit is complete for all 100 rows, reproducible structural checks, and every existing query/image/audio mapping. Semantic approval remains open for 23 flagged rows; independent bilingual sign-off remains open for all 100. Do not freeze a unified dataset or publish semantic correctness yet. Recommended next step: owner decisions for rows 4 and 9 and the review queue, followed by Phase I schema and asset-contract design. No unified dataset was created.
