# Selected-image assessment — 100 IDs

**Run:** A-001 / 22/11/2026, existing-output review only. Every query/image label below is **AI preliminary**, not independent human ground truth. All 100 IDs assessed; 99 selected images viewed through newly generated contact sheets, with seven full-resolution follow-ups. No inference, download or new audio listening. Current primary selected assets (including staged replacements for 004/009) are distinct from old production assets. Historical labels are retained in the JSON matrix; new labels do not rewrite them. License is context only, excluded from quality scores.

## Rubric

Relevance concerns the intended referent/action/context, not license. Visual quality concerns clarity, distracting clutter and text/preview contamination at vocabulary-card scale. Learning suitability combines these observations with whether a simple visual can teach the term. Text is not automatically a failure: incidental package labels/signage can remain NEEDS_REVIEW, while dense slide text/preview overlays obstruct the intended use. Review is at contact-sheet scale; full file links remain available for the owner. This is not an exhaustive pixel-level review of every original.

| Metric | PASS | FAIL | NEEDS_REVIEW | UNKNOWN | P+F denominator | PASS/(P+F) |
| --- | --- | --- | --- | --- | --- | --- |
| image_relevance | 44 | 27 | 28 | 1 | 71 | 61.97% |
| image_visual_quality | 39 | 47 | 13 | 1 | 86 | 45.35% |
| image_learning_suitability | 27 | 55 | 17 | 1 | 82 | 32.93% |
| image_technical | 99 | 0 | 0 | 1 | 99 | 100.0% |

N=100 IDs, 99 actual selected images and one absent (038). Relevance definitive subset is 71, visual 86, learning suitability 82. PASS/(P+F) is respectively 61.97%, 45.35%, 32.93%; these exclude uncertain/missing items. Reviewed images with any visual judgment: 99. AI visual assessment is not owner approval. All 99 decoded, matched saved hashes/dimensions/word/query metadata. This does not make them semantically suitable.

Rice/chicken primary images now depict the approved food senses, but source queries are human/curated replacements; old production images still depict the wrong senses. Correct replacements must not inflate original Qwen performance. ID038 has no chosen image because the existing semantic input gate lacks approved image intent; it is UNKNOWN/MISSING_EVIDENCE, not an image FAIL.

| ID | Relevance | Visual | Learning | Contamination | Scene/object observation |
| --- | --- | --- | --- | --- | --- |
| vocab-000001 | PASS | PASS | PASS | none | One red apple clearly fills the frame. |
| vocab-000002 | PASS | PASS | PASS | none | Bunches of bananas on the plant; referent is clear. |
| vocab-000003 | PASS | PASS | PASS | none | Single strawberry against a plain background. |
| vocab-000004 | PASS | PASS | PASS | none | Selected replacement shows cooked white rice; old production grain image is a different hash. |
| vocab-000005 | PASS | NEEDS_REVIEW | NEEDS_REVIEW | none | Bread is present among many pastries; competing foods reduce specificity. |
| vocab-000006 | PASS | PASS | PASS | none | Eggs in shells and cooked forms are clearly depicted. |
| vocab-000007 | NEEDS_REVIEW | FAIL | FAIL | dominant_text | Milk and plant ingredients appear under a milk-based beverages headline; cow-milk specificity is uncertain. |
| vocab-000008 | PASS | NEEDS_REVIEW | NEEDS_REVIEW | minor_brand | Water bottles dominate but labels and brand presentation are distracting. |
| vocab-000009 | PASS | PASS | PASS | none | Selected curated replacement depicts chicken meat; original live-chicken production image is separate. |
| vocab-000010 | PASS | NEEDS_REVIEW | NEEDS_REVIEW | none | A table of many breakfast dishes; target is plausible but composition is busy. |
| vocab-000011 | PASS | PASS | PASS | none | Single cat clearly visible. |
| vocab-000012 | PASS | PASS | PASS | none | Dog portrait has a clear animal referent. |
| vocab-000013 | PASS | PASS | PASS | none | Elephant visible almost full body. |
| vocab-000014 | PASS | PASS | PASS | none | A sapling being planted; recognizable tree though not a mature one. |
| vocab-000015 | NEEDS_REVIEW | PASS | NEEDS_REVIEW | none | Colorful bromeliad plants; distinguishing flower from ornamental bracts needs review. |
| vocab-000016 | PASS | PASS | PASS | none | Mountain peaks dominate above a village. |
| vocab-000017 | PASS | PASS | PASS | none | Flowing river in a forest is clear. |
| vocab-000018 | FAIL | FAIL | FAIL | dominant_text | A sunlight spectrum chart rather than the visible sun. |
| vocab-000019 | FAIL | NEEDS_REVIEW | FAIL | minor_signature | Nighttime resort buildings; no clear rain event. |
| vocab-000020 | PASS | PASS | PASS | none | Storm clouds and a rainbow provide an understandable weather example. |
| vocab-000021 | NEEDS_REVIEW | PASS | NEEDS_REVIEW | none | An unfinished building frame; may teach construction more than an inhabited house. |
| vocab-000022 | PASS | PASS | PASS | none | Kitchen counters, stove and cabinets clearly shown. |
| vocab-000023 | NEEDS_REVIEW | FAIL | FAIL | watermark_and_text | A labeled collage of educational institutions with an Alamy preview footer; no single school focus. |
| vocab-000024 | NEEDS_REVIEW | PASS | NEEDS_REVIEW | none | Bookshelves and seating; library vs bookstore/lounge context is not decisive. |
| vocab-000025 | PASS | FAIL | FAIL | watermark | Hospital-like building with medical cross; repeated preview marks seen at full resolution. |
| vocab-000026 | PASS | PASS | PASS | none | Airport terminal exterior with drop-off road; recognizable location. |
| vocab-000027 | PASS | PASS | PASS | none | Restaurant tables and place settings clearly shown. |
| vocab-000028 | PASS | PASS | PASS | none | One car is the dominant object. |
| vocab-000029 | PASS | PASS | PASS | none | Bicycle beside a bench, clearly identifiable. |
| vocab-000030 | PASS | FAIL | FAIL | dominant_text | Two structural bridge diagrams; labels dominate a small vocabulary image. |
| vocab-000031 | PASS | NEEDS_REVIEW | NEEDS_REVIEW | minor_title | Physical book visible, but large OBJECT cover text encourages the wrong association. |
| vocab-000032 | NEEDS_REVIEW | NEEDS_REVIEW | NEEDS_REVIEW | none | A mixed collage of phone, laptop, console, tablet and watch; phone is not isolated. |
| vocab-000033 | PASS | FAIL | FAIL | dominant_text | Computer input/output classification chart with many labels and components. |
| vocab-000034 | PASS | FAIL | FAIL | watermark | Umbrella is clear, but repeated stock preview marks cover the image. |
| vocab-000035 | FAIL | FAIL | FAIL | dominant_text | Anatomical nasal-cavity diagram, no shirt; selected metadata title also says nasal anatomy. |
| vocab-000036 | PASS | FAIL | FAIL | dominant_text | Family cartoon embedded in a dense classroom slide. |
| vocab-000037 | NEEDS_REVIEW | PASS | NEEDS_REVIEW | none | Woman embracing a child suggests motherhood; relationship cannot be established visually alone. |
| vocab-000038 | UNKNOWN | UNKNOWN | UNKNOWN | MISSING_EVIDENCE | No selected image: approved target lacks approved image_search_intent. |
| vocab-000039 | PASS | PASS | PASS | none | Adult standing in a classroom with children; teaching context is visible. |
| vocab-000040 | NEEDS_REVIEW | FAIL | FAIL | watermark | Worker with plans and hardhat is plausible; repeated Dreamstime marks and occupation ambiguity remain. |
| vocab-000041 | FAIL | PASS | FAIL | none | Luxury wristwatch, with no indication of today. |
| vocab-000042 | FAIL | FAIL | FAIL | dominant_text | Watch-show/video graphic about timepieces; does not depict tomorrow. |
| vocab-000043 | FAIL | FAIL | FAIL | dominant_text | Television-drama poster titled Yesterday; wrong referent. |
| vocab-000044 | PASS | PASS | PASS | none | Snow-covered landscape is a recognizable winter example. |
| vocab-000045 | PASS | PASS | PASS | none | Smiling happy face communicates positive emotion. |
| vocab-000046 | NEEDS_REVIEW | FAIL | FAIL | dominant_text | Hunger-versus-appetite infographic; meaning relies on reading English paragraphs. |
| vocab-000047 | FAIL | FAIL | FAIL | dominant_text | Easy drawing tutorial about objects rather than an unambiguous easy-task scene. |
| vocab-000048 | FAIL | FAIL | FAIL | dominant_text | Drawing tutorial thumbnail for difficult objects, mostly title text. |
| vocab-000049 | NEEDS_REVIEW | PASS | NEEDS_REVIEW | none | Decorative reflective object may be beautiful subjectively; no contrast or clear teaching cue. |
| vocab-000050 | NEEDS_REVIEW | FAIL | FAIL | dominant_text | Materials-strength infographic; could teach strength with instruction, but too text-dependent for this flashcard. |
| vocab-000051 | FAIL | PASS | FAIL | none | Static portrait; no visible going/walking action. |
| vocab-000052 | PASS | PASS | PASS | none | Person holds an open book in a reading pose. |
| vocab-000053 | FAIL | FAIL | FAIL | dominant_text | How-to-write-an-action-plan infographic rather than a person writing. |
| vocab-000054 | FAIL | FAIL | FAIL | watermark_and_text | Diwali greeting/rangoli with text, not studying. |
| vocab-000055 | FAIL | FAIL | FAIL | dominant_text | Advertisement for Work Objects with gift boxes, not a person working. |
| vocab-000056 | FAIL | FAIL | FAIL | watermark | Stock collage of bedtime accessories; no one sleeping. |
| vocab-000057 | PASS | PASS | PASS | none | Person eating a meal, food and utensil visible. |
| vocab-000058 | FAIL | PASS | FAIL | none | Glasses of beverages; no drinking action. |
| vocab-000059 | FAIL | NEEDS_REVIEW | FAIL | minor_brand | Action retail storefront; brand match is not a depiction of buying. |
| vocab-000060 | PASS | PASS | PASS | none | One person pulls another up a rock, visible assistance. |
| vocab-000061 | FAIL | FAIL | FAIL | dominant_text | English grammar lecture thumbnail mentioning understand/action verbs. |
| vocab-000062 | NEEDS_REVIEW | FAIL | FAIL | dominant_text | Remember the Objects memory-game title; related task but meaning relies on text. |
| vocab-000063 | NEEDS_REVIEW | FAIL | FAIL | dominant_text | Give-versus-receive action flowchart, no simple transfer scene. |
| vocab-000064 | PASS | FAIL | FAIL | watermark | Choice illustrations are relevant but multiple panels and VectorStock footer dominate. |
| vocab-000065 | FAIL | PASS | FAIL | none | Static headshot; no swimming, pool or water action. |
| vocab-000066 | NEEDS_REVIEW | FAIL | FAIL | watermark | Electronics/technology collage with repeated preview marks, software not isolated. |
| vocab-000067 | PASS | FAIL | FAIL | dominant_text | Object-oriented database diagram is related but densely labeled and too specialized. |
| vocab-000068 | NEEDS_REVIEW | FAIL | FAIL | dominant_text | HTML DOM password-object article graphic; computing subtopic rather than simple password concept. |
| vocab-000069 | PASS | FAIL | FAIL | watermark | Musical instruments/equipment collage is related but heavily marked and crowded. |
| vocab-000070 | NEEDS_REVIEW | FAIL | FAIL | dominant_text | Language-as-object/organism teaching slide; not a simple language depiction. |
| vocab-000071 | FAIL | FAIL | FAIL | dominant_text | Object-oriented problem-solving programming chart; wrong lesson context. |
| vocab-000072 | FAIL | FAIL | FAIL | watermark_and_text | College of Business building with stock footer; not a business transaction/activity. |
| vocab-000073 | PASS | PASS | PASS | none | Large campus/buildings provide a plausible university scene. |
| vocab-000074 | NEEDS_REVIEW | FAIL | FAIL | dominant_text | Object-management workbench software screenshot; only a narrow project-tool association. |
| vocab-000075 | FAIL | FAIL | FAIL | dominant_text | Object-oriented user-experience technology poster, not life/work experience. |
| vocab-000076 | PASS | PASS | PASS | none | Vegetable garden with leafy produce visible. |
| vocab-000077 | FAIL | NEEDS_REVIEW | FAIL | minor_labels | Grid of stone fragments; importance cannot be inferred. |
| vocab-000078 | NEEDS_REVIEW | FAIL | FAIL | watermark | Collage of unrelated objects; potential difference lesson but no clear comparison and stock footer. |
| vocab-000079 | PASS | FAIL | FAIL | dominant_text | Labeled sharp tools/poison/weapons communicate danger, but small dense teaching chart. |
| vocab-000080 | NEEDS_REVIEW | PASS | NEEDS_REVIEW | none | Impossible-triangle illusion is a possible metaphor, not literal general impossibility. |
| vocab-000081 | NEEDS_REVIEW | FAIL | FAIL | dominant_text | Because-sentence grammar slide; related teaching material but text-heavy. |
| vocab-000082 | FAIL | FAIL | FAIL | dominant_text | Mechanics exam question; no always/frequency depiction. |
| vocab-000083 | NEEDS_REVIEW | FAIL | FAIL | dominant_text | Person with sometime/sometimes word bubbles, no visible intermittent-event cue. |
| vocab-000084 | NEEDS_REVIEW | FAIL | FAIL | dominant_text | Matching-pairs worksheet; association rather than clear togetherness. |
| vocab-000085 | FAIL | FAIL | FAIL | dominant_text | A Place Where I Belong film poster; title lure, not where concept. |
| vocab-000086 | NEEDS_REVIEW | NEEDS_REVIEW | NEEDS_REVIEW | dominant_text | WHY word badge; readable but relies entirely on English text. |
| vocab-000087 | FAIL | FAIL | FAIL | dominant_text | Hello Objects game/media screen; title match, not greeting. |
| vocab-000088 | FAIL | FAIL | FAIL | watermark_and_text | PLEASE ACTION banner with iStock overlay; no request scene. |
| vocab-000089 | NEEDS_REVIEW | FAIL | FAIL | dominant_text | List of English gratitude phrases; no clear interaction without reading text. |
| vocab-000090 | NEEDS_REVIEW | NEEDS_REVIEW | NEEDS_REVIEW | dominant_text | Crying face holding SORRY sign; apology vs sadness remains ambiguous. |
| vocab-000091 | PASS | FAIL | FAIL | watermark | Apartment building is relevant but repeated Vecteezy marks cover it. |
| vocab-000092 | FAIL | FAIL | FAIL | dominant_text | Programming key/value dictionary diagram, not a vocabulary dictionary. |
| vocab-000093 | PASS | PASS | PASS | minor_packaging | Store aisles and stocked shelves clearly depict supermarket; normal packaging is incidental. |
| vocab-000094 | PASS | NEEDS_REVIEW | NEEDS_REVIEW | minor_signage | Pharmacist/customer scene is plausible, but prominent PHARMACY signage carries part of the meaning. |
| vocab-000095 | FAIL | NEEDS_REVIEW | FAIL | minor_brand | Museum Place facade/sign; the label alone does not establish a museum or exhibition scene. |
| vocab-000096 | NEEDS_REVIEW | NEEDS_REVIEW | NEEDS_REVIEW | minor_signature | Decorative miniature waterfall/fountain; correct water cascade association but natural-scene suitability uncertain. |
| vocab-000097 | PASS | FAIL | FAIL | watermark | Firefighter in fire scene is relevant, with visible Adobe Stock preview mark. |
| vocab-000098 | PASS | FAIL | FAIL | watermark | People talking across a fence suggest neighbors; preview marks visible at full resolution. |
| vocab-000099 | NEEDS_REVIEW | PASS | NEEDS_REVIEW | none | Woman and girl suggest mother/daughter, but relationship is not established by appearance alone. |
| vocab-000100 | NEEDS_REVIEW | PASS | NEEDS_REVIEW | none | Older woman with child suggests grandmother; relation still needs human/context confirmation. |
