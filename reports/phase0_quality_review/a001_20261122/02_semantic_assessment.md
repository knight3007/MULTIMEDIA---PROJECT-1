# Semantic assessment — 100 queries

**Run:** A-001 / 22/11/2026, existing-output review only. Every query/image label below is **AI preliminary**, not independent human ground truth. All 100 IDs assessed; 99 selected images viewed through newly generated contact sheets, with seven full-resolution follow-ups. No inference, download or new audio listening. Current primary selected assets (including staged replacements for 004/009) are distinct from old production assets. Historical labels are retained in the JSON matrix; new labels do not rewrite them. License is context only, excluded from quality scores.

## Rubric and denominators

PASS: meaning/context preserved and sufficiently specific for visual search. FAIL: clear mismatch or inadequate visual-search representation under the stated flashcard rubric. NEEDS_REVIEW: ambiguity, register, chosen sense, visual metaphor or specificity needs human decision. UNKNOWN: evidence cannot support assessment. Query overall is FAIL if any of six dimensions FAIL; otherwise UNKNOWN if any unknown, then NEEDS_REVIEW if any such flag, else PASS. It is stricter than correct_meaning alone. These are per-ID judgments with rationale, not regex classifications. Human approval of a target sense does not approve a raw query.

| Metric | PASS | FAIL | NEEDS_REVIEW | UNKNOWN | P+F denominator | PASS/(P+F) |
| --- | --- | --- | --- | --- | --- | --- |
| query_overall | 37 | 22 | 41 | 0 | 59 | 62.71% |
| query_correct_meaning | 75 | 16 | 9 | 0 | 91 | 82.42% |
| query_specificity | 54 | 0 | 46 | 0 | 54 | 100.0% |
| query_context_appropriateness | 37 | 16 | 47 | 0 | 53 | 69.81% |
| query_ambiguity | 37 | 8 | 55 | 0 | 45 | 82.22% |
| query_translation_consistency | 78 | 3 | 19 | 0 | 81 | 96.3% |
| query_visual_search_suitability | 49 | 20 | 31 | 0 | 69 | 71.01% |

All rows use N=100; counts are also percentages of the complete set. PASS/(P+F) excludes NEEDS_REVIEW/UNKNOWN and must not be read as accuracy on all 100. For query overall it is 37/59=62.71%; meaning alone is 75/91=82.42%. No human semantic accuracy estimate is certified.

The underlying 100 queries are a heterogeneous historical cache/staging collection: six corrected-verb raw outputs, original prompt signature evidence, human overrides for 004/009. They are not a controlled fresh 100-item run of one immutable prompt/revision. Accepted raw decoded text is missing for 94 IDs. Every parsed query was rechecked against its referenced cache file (100 matches). Exact historical model revisions remain MISSING_EVIDENCE; do not substitute the revision of a later 25-row A/B experiment.

## Per-ID preliminary judgment

Detailed six-dimensional labels and original/effective query are in evaluation_matrix.csv/JSON. Reasons below are preliminary linguistic/visual-search judgments; pending semantic decisions remain unchanged.

| ID | EN / JP / VN | Original parsed query | Overall | Reason |
| --- | --- | --- | --- | --- |
| vocab-000001 | apple / りんご / quả táo | apple fruit | PASS | Fruit sense is explicit and matches the trilingual term. |
| vocab-000002 | banana / バナナ / quả chuối | banana fruit | PASS | Fruit category preserves banana meaning. |
| vocab-000003 | strawberry / いちご / dâu tây | strawberry fruit | PASS | Fruit category disambiguates strawberry appropriately. |
| vocab-000004 | rice / ごはん / cơm | rice grain | FAIL | Grain conflicts with owner-approved cooked rice; human override is separate. |
| vocab-000005 | bread / パン / bánh mì | bread food | PASS | Bread as food matches pan/bánh mì broadly. |
| vocab-000006 | egg / たまご / trứng | egg food | PASS | Egg as food matches tamago/trứng. |
| vocab-000007 | milk / ぎゅうにゅう / sữa | milk beverage | NEEDS_REVIEW | Milk beverage is plausible but cow-milk scope needs human decision. |
| vocab-000008 | water / みず / nước | water beverage | PASS | Beverage avoids substance/chemical sense; drinking water is intended. |
| vocab-000009 | chicken / とりにく / thịt gà | chicken animal | FAIL | Animal contradicts toriniku/thịt gà and approved meat sense. |
| vocab-000010 | breakfast / あさごはん / bữa sáng | breakfast meal | PASS | Breakfast meal preserves morning-meal meaning. |
| vocab-000011 | cat / ねこ / mèo | cat animal | PASS | Animal category names cat unambiguously. |
| vocab-000012 | dog / いぬ / chó | dog animal | PASS | Animal category names dog unambiguously. |
| vocab-000013 | elephant / ぞう / voi | elephant animal | PASS | Animal category matches elephant. |
| vocab-000014 | tree / き / cây | tree plant | PASS | Plant category preserves tree meaning. |
| vocab-000015 | flower / はな / hoa | flower plant | NEEDS_REVIEW | Flower is a valid sense of hana but kana ambiguity remains for human review. |
| vocab-000016 | mountain / やま / núi | mountain place | PASS | Mountain as place keeps the geographic referent. |
| vocab-000017 | river / かわ / sông | river water | PASS | River water keeps river referent, though wording is slightly broad. |
| vocab-000018 | sun / たいよう / mặt trời | sun illumination | NEEDS_REVIEW | Illumination is associated with the sun but can retrieve light/spectrum instead of the sun. |
| vocab-000019 | rain / あめ / mưa | rain illumination | FAIL | Illumination misclassifies rain; rain/weather context is lost, with kana sense pending. |
| vocab-000020 | weather / てんき / thời tiết | weather phenomenon | NEEDS_REVIEW | Weather phenomenon is valid but needs a particular teaching scene. |
| vocab-000021 | house / いえ / ngôi nhà | house building | PASS | House building preserves the intended dwelling. |
| vocab-000022 | kitchen / だいどころ / nhà bếp | kitchen place | PASS | Kitchen place preserves room meaning. |
| vocab-000023 | school / がっこう / trường học | school institution | PASS | School institution is semantically appropriate. |
| vocab-000024 | library / としょかん / thư viện | library place | PASS | Library place is an appropriate intended location. |
| vocab-000025 | hospital / びょういん / bệnh viện | hospital institution | PASS | Hospital institution preserves hospital meaning. |
| vocab-000026 | airport / くうこう / sân bay | airport place | PASS | Airport place retains travel facility meaning. |
| vocab-000027 | restaurant / レストラン / nhà hàng | restaurant place | PASS | Restaurant place retains dining venue meaning. |
| vocab-000028 | car / くるま / ô tô | car vehicle | PASS | Vehicle disambiguates car correctly. |
| vocab-000029 | bicycle / じてんしゃ / xe đạp | bicycle vehicle | PASS | Vehicle disambiguates bicycle correctly. |
| vocab-000030 | bridge / はし / cây cầu | bridge structure | NEEDS_REVIEW | Bridge structure matches EN/VN but kana hashi needs sense confirmation. |
| vocab-000031 | book / ほん / sách | book object | NEEDS_REVIEW | Book is retained but object does not exclude programming/object titles. |
| vocab-000032 | phone / でんわ / điện thoại | phone device | PASS | Phone device retains telephone meaning. |
| vocab-000033 | computer / コンピューター / máy tính | computer device | PASS | Computer device is a clear query for the intended term. |
| vocab-000034 | umbrella / かさ / ô/dù | umbrella object | PASS | Umbrella remains a specific physical noun despite generic object suffix. |
| vocab-000035 | shirt / シャツ / áo sơ mi | shirt clothing | NEEDS_REVIEW | Shirt clothing is plausible but Vietnamese specifies button-up shirt; scope awaits review. |
| vocab-000036 | family / かぞく / gia đình | family institution | NEEDS_REVIEW | Family as institution is abstract/social rather than a concrete family scene. |
| vocab-000037 | mother / はは / mẹ | mother person | NEEDS_REVIEW | Mother person is plausible but own-mother register in haha needs context. |
| vocab-000038 | friend / ともだち / bạn | friend person | NEEDS_REVIEW | Friend person matches approved singular friend but lacks a usable specific scene. |
| vocab-000039 | teacher / せんせい / giáo viên | teacher person | PASS | Teacher person matches the profession. |
| vocab-000040 | engineer / エンジニア / kỹ sư | engineer profession | NEEDS_REVIEW | Engineer profession is valid but engineering discipline is unspecified. |
| vocab-000041 | today / きょう / hôm nay | today timepiece | FAIL | Today is a time relation, not a timepiece object. |
| vocab-000042 | tomorrow / あした / ngày mai | tomorrow timepiece | FAIL | Tomorrow is a future day, not a timepiece category. |
| vocab-000043 | yesterday / きのう / hôm qua | yesterday place | FAIL | Yesterday is past time, not a place. |
| vocab-000044 | winter / ふゆ / mùa đông | winter season | PASS | Winter season preserves seasonal meaning. |
| vocab-000045 | happy / うれしい / vui | happy emotion | NEEDS_REVIEW | Happy emotion is broadly compatible; ureshii/glad nuance needs context. |
| vocab-000046 | hungry / おなかがすいた / đói | hungry appetite | NEEDS_REVIEW | Hungry is a bodily state; appetite is related but not identical to hunger. |
| vocab-000047 | easy / やさしい / dễ | easy object | FAIL | Easy object does not specify what task is easy or contrast difficulty; yasashii sense pending. |
| vocab-000048 | difficult / むずかしい / khó | difficult object | FAIL | Difficult object is underspecified; need a difficult task or comparison. |
| vocab-000049 | beautiful / きれい / đẹp | beautiful object | FAIL | Beautiful object is arbitrary and kirei may mean clean; no chosen visual context. |
| vocab-000050 | strong / つよい / mạnh | strong object | FAIL | Strong object lacks person/material context or a visible strength comparison. |
| vocab-000051 | go / いく / đi | person going | NEEDS_REVIEW | Person going preserves action but lacks destination or visible movement cue. |
| vocab-000052 | read / よむ / đọc | person reading | PASS | Person reading specifies an observable action matching yomu. |
| vocab-000053 | write / かく / viết | write action | NEEDS_REVIEW | Write action preserves verb but needs actual writing scene and kana/kaku sense review. |
| vocab-000054 | study / べんきょうする / học tập | study object | FAIL | Study object converts benkyou-suru action into an unspecified object. |
| vocab-000055 | work / はたらく / làm việc | work object | FAIL | Work object loses hataraku action and invites product-name matches. |
| vocab-000056 | sleep / ねる / ngủ | sleep object | FAIL | Sleep object loses neru action and invites related accessories. |
| vocab-000057 | eat / たべる / ăn | person eating | PASS | Person eating specifies observable eating action. |
| vocab-000058 | drink / のむ / uống | drink beverage | FAIL | Drink beverage selects a noun while nomu/uống are the drinking action. |
| vocab-000059 | buy / かう / mua | buy action | NEEDS_REVIEW | Buy action retains verb but does not specify visible transaction and invites Action brand. |
| vocab-000060 | help / たすける / giúp đỡ | person helping | NEEDS_REVIEW | Person helping is plausible; tasukeru aid/rescue scope needs human context. |
| vocab-000061 | understand / わかる / hiểu | understand action | NEEDS_REVIEW | Understand action retains concept but needs a scenario showing comprehension. |
| vocab-000062 | remember / おぼえる / nhớ | remember object | FAIL | Remember object turns memory action into an object phrase; need a recall scenario. |
| vocab-000063 | receive / うけとる / nhận | receive action | NEEDS_REVIEW | Receive action retains verb but needs a recipient/transfer scene. |
| vocab-000064 | choose / えらぶ / chọn | person choosing | PASS | Person choosing depicts the intended choice action. |
| vocab-000065 | swim / およぐ / bơi | person swimming | PASS | Person swimming is a direct observable action query. |
| vocab-000066 | software / ソフトウェア / phần mềm | software device | FAIL | Software is not a physical device; classifier misleads toward electronics. |
| vocab-000067 | database / データベース / cơ sở dữ liệu | database object | NEEDS_REVIEW | Database object can drift to programming subtypes; intended example unspecified. |
| vocab-000068 | password / パスワード / mật khẩu | password object | NEEDS_REVIEW | Password object invites DOM/API object meaning rather than a familiar password example. |
| vocab-000069 | music / おんがく / âm nhạc | music object | NEEDS_REVIEW | Music is not a single physical object; instruments are associated examples, not music itself. |
| vocab-000070 | language / ことば / ngôn ngữ | language object | NEEDS_REVIEW | Language object is abstract and kotoba scope includes words/speech; context needed. |
| vocab-000071 | problem / もんだい / vấn đề | problem object | NEEDS_REVIEW | Problem object can drift into object-oriented programming; no everyday problem context. |
| vocab-000072 | business / ビジネス / kinh doanh | business institution | NEEDS_REVIEW | Business institution may select a school/institution rather than kinh-doanh activity. |
| vocab-000073 | university / だいがく / trường đại học | university institution | PASS | University institution is appropriate to daigaku. |
| vocab-000074 | project / プロジェクト / dự án | project object | NEEDS_REVIEW | Project object is vague and can select software-specific objects; context unspecified. |
| vocab-000075 | experience / けいけん / kinh nghiệm | experience object | FAIL | Experience object converts experiential knowledge to an object phrase; user-experience drift. |
| vocab-000076 | vegetable / やさい / rau | vegetable plant | PASS | Vegetable plant preserves edible-plant meaning. |
| vocab-000077 | important / たいせつ / quan trọng | important object | FAIL | Important object supplies no cue why something is important; adjective remains underspecified. |
| vocab-000078 | different / ちがう / khác | different object | FAIL | Different object has no explicit comparison relation; chigau is relational. |
| vocab-000079 | dangerous / あぶない / nguy hiểm | dangerous object | NEEDS_REVIEW | Dangerous object is plausible but needs chosen hazard/context. |
| vocab-000080 | impossible / ふかのう / không thể | impossible object | NEEDS_REVIEW | Impossible object may be an optical-illusion example; metaphor needs lesson context. |
| vocab-000081 | because / なぜなら / bởi vì | because cause | NEEDS_REVIEW | Because cause is conceptually related but needs causal example and Japanese clause context. |
| vocab-000082 | always / いつも / luôn luôn | always object | FAIL | Always is frequency, not an object; missing repeated-time representation. |
| vocab-000083 | sometimes / ときどき / thỉnh thoảng | sometimes event | NEEDS_REVIEW | Sometimes event retains intermittent sense but lacks time/frequency contrast. |
| vocab-000084 | together / いっしょに / cùng nhau | together object | FAIL | Together is a relation/adverb, not an object category; needs people/things acting together. |
| vocab-000085 | where / どこ / ở đâu | where place | NEEDS_REVIEW | Where place preserves location relation but needs a locating/question scenario. |
| vocab-000086 | why / なぜ / tại sao | why icon | NEEDS_REVIEW | Why icon is a possible symbol but does not explain cause/question context. |
| vocab-000087 | hello / こんにちは / xin chào | hello object | FAIL | Hello is a greeting, not an object; daytime Japanese greeting context also pending. |
| vocab-000088 | please / おねがいします / làm ơn/xin vui lòng | please action | NEEDS_REVIEW | Please action is underspecified; onegaishimasu requires a polite-request situation. |
| vocab-000089 | thanks / ありがとう / cảm ơn | thanks expression | NEEDS_REVIEW | Thanks expression preserves gratitude but needs a recognizable thanking scene. |
| vocab-000090 | sorry / すみません / xin lỗi | sorry emotion | NEEDS_REVIEW | Sorry emotion can mean sadness rather than apology; sumimasen scope needs context. |
| vocab-000091 | apartment / アパート / căn hộ | apartment place | NEEDS_REVIEW | Apartment place is plausible; Japanese housing-type scope is pending. |
| vocab-000092 | dictionary / じしょ / từ điển | dictionary object | NEEDS_REVIEW | Dictionary object preserves generic term but fails to exclude programming dictionary. |
| vocab-000093 | supermarket / スーパーマーケット / siêu thị | supermarket place | PASS | Supermarket place preserves retail-store meaning. |
| vocab-000094 | pharmacy / やっきょく / nhà thuốc | pharmacy institution | PASS | Pharmacy institution correctly identifies the intended venue. |
| vocab-000095 | museum / はくぶつかん / bảo tàng | museum place | PASS | Museum place is semantically appropriate. |
| vocab-000096 | waterfall / たき / thác nước | waterfall object | NEEDS_REVIEW | Waterfall is retained but object invites a decorative model rather than natural place. |
| vocab-000097 | firefighter / しょうぼうし / lính cứu hỏa | firefighter person | PASS | Firefighter person identifies the profession clearly. |
| vocab-000098 | neighbor / となりのひと / hàng xóm | neighbor person | NEEDS_REVIEW | Neighbor person is plausible; next-door vs broader neighbor scope pending. |
| vocab-000099 | daughter / むすめ / con gái | daughter person | NEEDS_REVIEW | Daughter person cannot specify relational identity without parent context. |
| vocab-000100 | grandmother / そぼ / bà | grandmother person | NEEDS_REVIEW | Grandmother person is plausible; sobo own-family register needs context. |
