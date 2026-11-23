# Pipeline v2 validation (prompt v2 word-type routing)

Frozen expectations: `expected_routes.csv` SHA `62d436771cc203f6…`, derived from the owner-approved final selection before any inference. Counts: {'PHOTO': 44, 'NON_PHOTO': 35, 'CURATE': 1, 'ANY': 20}. Criteria: PHOTO kept ≥ 90%, NON_PHOTO routed away ≥ 85%, CURATE exact, 100% valid queries. Budget: 3 prompt iterations. Model Qwen3-1.7B, greedy, local.

| Iteration | PHOTO kept | NON_PHOTO away | CURATE | Valid | Passed | Prompt SHA |
|---|---|---|---|---|---|---|
| 1 | 33/44 | 34/35 | 1/1 | 98/100 | False | `0dc99f3058b6` |
| 2 | 44/44 | 27/35 | 1/1 | 95/100 | False | `77c09b6df3ea` |
| 3 | 44/44 | 34/35 | 1/1 | 99/100 | False | `f905ac5d39bd` |

Final iteration misses — PHOTO: none; NON_PHOTO: ['rain'].
Invalid outputs: ['rain'].

Changes between iterations: (1→2) prompt states that persons, places, institutions, meals and drinks are CONCRETE; replaced examples that Qwen copied (idea light bulb, night sky); TIME uses calendar/clock; collision tokens are stripped instead of fatal. (2→3) code rejects CONCRETE answers with a non-physical class (action, activity, abstract, organization…) so the corrective retry reroutes them; digits, apostrophes and meta words are stripped; question-word, action and frequency examples added; 'a verb is never CONCRETE'.

## Final iteration, all 100 words

| Word | Expected | Type | Route | Query | Owner-approved query |
|---|---|---|---|---|---|
| apple | PHOTO | CONCRETE | PHOTO | apple fruit | apple fruit |
| banana | PHOTO | CONCRETE | PHOTO | banana fruit | banana fruit |
| strawberry | PHOTO | CONCRETE | PHOTO | strawberry fruit | strawberry fruit |
| rice | PHOTO | CONCRETE | PHOTO | rice food | cooked rice |
| bread | PHOTO | CONCRETE | PHOTO | bread food | bread food |
| egg | PHOTO | CONCRETE | PHOTO | egg food | egg food |
| milk | PHOTO | CONCRETE | PHOTO | milk drink | milk beverage |
| water | PHOTO | CONCRETE | PHOTO | water drink | water beverage |
| chicken | PHOTO | CONCRETE | PHOTO | chicken animal | chicken meat |
| breakfast | PHOTO | CONCRETE | PHOTO | breakfast meal | breakfast meal |
| cat | PHOTO | CONCRETE | PHOTO | cat animal | cat animal |
| dog | PHOTO | CONCRETE | PHOTO | dog animal | dog animal |
| elephant | PHOTO | CONCRETE | PHOTO | elephant animal | elephant animal |
| tree | PHOTO | CONCRETE | PHOTO | tree plant | tree plant |
| flower | PHOTO | CONCRETE | PHOTO | flower plant | flower plant |
| mountain | PHOTO | CONCRETE | PHOTO | mountain natural feature | mountain place |
| river | PHOTO | CONCRETE | PHOTO | river natural feature | river water |
| sun | ANY | CONCRETE | PHOTO | sun celestial body | sun in blue sky illustration |
| rain | NON_PHOTO | — | ERROR | typed query for 'rain' failed after one retry: unknown word type 'RAIN ABSTRACT' | rain icon |
| weather | ANY | ABSTRACT | SCENE | sky with clouds and sun illustration | weather phenomenon |
| house | PHOTO | CONCRETE | PHOTO | house building | house building |
| kitchen | PHOTO | CONCRETE | PHOTO | kitchen place | kitchen place |
| school | PHOTO | CONCRETE | PHOTO | school building | school institution |
| library | PHOTO | CONCRETE | PHOTO | library building | library place |
| hospital | PHOTO | CONCRETE | PHOTO | hospital building | hospital institution |
| airport | PHOTO | CONCRETE | PHOTO | airport place | airport place |
| restaurant | PHOTO | CONCRETE | PHOTO | restaurant place | restaurant place |
| car | PHOTO | CONCRETE | PHOTO | car vehicle | car vehicle |
| bicycle | PHOTO | CONCRETE | PHOTO | bicycle vehicle | bicycle vehicle |
| bridge | PHOTO | CONCRETE | PHOTO | bridge place | bridge structure |
| book | ANY | CONCRETE | PHOTO | book object | book icon |
| phone | PHOTO | CONCRETE | PHOTO | phone device | phone device |
| computer | ANY | CONCRETE | PHOTO | computer device | desktop computer monitor keyboard icon |
| umbrella | PHOTO | CONCRETE | PHOTO | umbrella object | umbrella object |
| shirt | PHOTO | CONCRETE | PHOTO | shirt clothing | shirt clothing |
| family | ANY | CONCRETE | PHOTO | family person | family parents children portrait illustration |
| mother | PHOTO | CONCRETE | PHOTO | mother person | mother person |
| friend | ANY | CONCRETE | PHOTO | friend person | two friends together illustration |
| teacher | PHOTO | CONCRETE | PHOTO | teacher person | teacher person |
| engineer | PHOTO | CONCRETE | PHOTO | engineer person | engineer profession |
| today | NON_PHOTO | TIME | SCENE | calendar with today marked illustration | today calendar current day highlighted illustration |
| tomorrow | NON_PHOTO | TIME | SCENE | calendar with tomorrow marked illustration | tomorrow next day calendar illustration |
| yesterday | NON_PHOTO | TIME | SCENE | calendar with yesterday marked illustration | yesterday previous day calendar illustration |
| winter | ANY | TIME | SCENE | calendar with winter season marked illustration | winter season |
| happy | ANY | STATE | ICON | smile face happy icon | happy emotion |
| hungry | NON_PHOTO | STATE | ICON | mouth open hungry icon | hungry icon |
| easy | NON_PHOTO | STATE | ICON | finger pointing upward easy icon | easy task simple puzzle illustration |
| difficult | NON_PHOTO | STATE | ICON | person struggling hard icon | difficult task challenging puzzle illustration |
| beautiful | ANY | ABSTRACT | SCENE | family on beach vacation illustration | beautiful object |
| strong | NON_PHOTO | STATE | ICON | hand gripping tightly icon | strong arm muscle icon |
| go | NON_PHOTO | ACTION | ICON | person walking forward icon | person walking away icon |
| read | NON_PHOTO | ACTION | ICON | person reading book icon | person reading book icon |
| write | NON_PHOTO | ACTION | ICON | person writing icon | write icon |
| study | NON_PHOTO | STATE | ICON | book open study icon | student studying at desk icon |
| work | NON_PHOTO | ABSTRACT | SCENE | person working on a computer illustration | person working at desk icon |
| sleep | NON_PHOTO | STATE | ICON | head nodding sleep icon | sleep icon |
| eat | ANY | ACTION | ICON | person eating food icon | person eating |
| drink | ANY | CONCRETE | PHOTO | drink beverage | drink beverage |
| buy | NON_PHOTO | ACTION | ICON | person buying item icon | buy icon |
| help | NON_PHOTO | SOCIAL | ICON | person giving help icon | person helping another person icon |
| understand | NON_PHOTO | STATE | ICON | person looking confused icon | understand icon |
| remember | NON_PHOTO | STATE | ICON | person looking back memory icon | remember icon |
| receive | NON_PHOTO | ACTION | ICON | person receiving gift icon | receive icon |
| choose | NON_PHOTO | ACTION | ICON | person selecting item icon | choosing between options icon |
| swim | NON_PHOTO | ACTION | ICON | person swimming water icon | swim icon |
| software | ANY | ABSTRACT | SCENE | computer screen with icons and illustration | software device |
| database | ANY | ABSTRACT | SCENE | computer screen data organization illustration | database object |
| password | ANY | ABSTRACT | SCENE | family on beach vacation illustration | password object |
| music | ANY | ABSTRACT | SCENE | people listening to music illustration | music object |
| language | NON_PHOTO | STATE | ICON | tongue speaking icon | language speech bubbles icon |
| problem | ANY | ABSTRACT | SCENE | person solving a puzzle illustration | problem object |
| business | NON_PHOTO | ABSTRACT | SCENE | business activity illustration | business meeting icon |
| university | PHOTO | CONCRETE | PHOTO | university building | university institution |
| project | NON_PHOTO | ABSTRACT | SCENE | project plan illustration | project plan teamwork illustration |
| experience | NON_PHOTO | ABSTRACT | SCENE | people enjoying a vacation illustration | learning from experience illustration |
| vegetable | PHOTO | CONCRETE | PHOTO | vegetable plant | vegetable plant |
| important | NON_PHOTO | STATE | ICON | person holding sign with important icon | important exclamation mark icon |
| different | ANY | STATE | ICON | finger pointing different icon | different object |
| dangerous | NON_PHOTO | STATE | ICON | person holding a knife dangerous icon | danger warning triangle sign icon |
| impossible | NON_PHOTO | ABSTRACT | SCENE | family on beach vacation illustration | impossible task icon |
| because | CURATE | CONNECTOR | CURATE |  | cause effect visual sequence illustration |
| always | NON_PHOTO | TIME | SCENE | clock with repeating arrows illustration | always repeating arrow icon |
| sometimes | ANY | TIME | SCENE | clock with repeating arrows illustration | sometimes event |
| together | NON_PHOTO | SOCIAL | ICON | person holding hands together icon | people together icon |
| where | NON_PHOTO | SOCIAL | ICON | person holding question mark icon | where location question mark icon |
| why | NON_PHOTO | SOCIAL | ICON | person holding question mark icon | thinking why question mark icon |
| hello | NON_PHOTO | SOCIAL | ICON | person raising hand in greeting icon | person waving hello icon |
| please | NON_PHOTO | SOCIAL | ICON | person giving polite bow icon | person asking politely icon |
| thanks | NON_PHOTO | SOCIAL | ICON | person giving thanks icon | person thanking another icon |
| sorry | ANY | SOCIAL | ICON | person bowing head with expression of apology icon | sorry emotion |
| apartment | PHOTO | CONCRETE | PHOTO | apartment place | apartment place |
| dictionary | ANY | CONCRETE | PHOTO | dictionary book | dictionary book icon |
| supermarket | PHOTO | CONCRETE | PHOTO | supermarket place | supermarket place |
| pharmacy | PHOTO | CONCRETE | PHOTO | pharmacy building | pharmacy institution |
| museum | PHOTO | CONCRETE | PHOTO | museum building | museum place |
| waterfall | PHOTO | CONCRETE | PHOTO | waterfall natural feature | waterfall object |
| firefighter | PHOTO | CONCRETE | PHOTO | firefighter person | firefighter person |
| neighbor | PHOTO | CONCRETE | PHOTO | neighbor person | neighbor person |
| daughter | PHOTO | CONCRETE | PHOTO | daughter person | daughter person |
| grandmother | PHOTO | CONCRETE | PHOTO | grandmother person | grandmother person |

## Verdict and known query-quality issues (not measured by the route criteria)

**NOT PASSED.** Iteration 3 meets the PHOTO (44/44), NON_PHOTO (34/35) and CURATE criteria, but not the 100% valid-query criterion: `rain` produced the type `RAIN ABSTRACT` and failed after one retry. The 3-iteration budget is exhausted, so pipeline v2 is recorded as a **validated candidate, not frozen**. Freezing it as is, or allowing more iterations, is an owner decision.

Manual review of the iteration-3 queries (agent desk review, not owner-verified):
- **Example copying:** beautiful, password and impossible all got `family on beach vacation illustration` (the holiday example); always and sometimes both got `clock with repeating arrows illustration` (the often example); where and why both got `person holding question mark icon`.
- **Weak or wrong sense:** sleep `head nodding sleep icon`; understand `person looking confused icon` (the opposite meaning); dangerous `person holding a knife dangerous icon` (safety concern); important `person holding sign with important icon` (likely printed text).
- **Good matches with the owner-approved style:** today, tomorrow and yesterday as calendar scenes; read, write, buy, receive, swim, together, thanks and please as person icons; every concrete noun kept as `<word> <class>`.
- These defects would reach the reviewer as `needs_review` proposals. They are not auto-approved.

## Owner decision (2026-11-23)

The owner chose to **freeze v2 as is** ("Chốt như hiện tại"), decision D-021, accepting the limitations above. Freeze hashes are in `freeze_manifest.json`, and `test_image_pipeline_v2.FreezeTests` guards them.
