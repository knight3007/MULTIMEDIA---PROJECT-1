# A-004R frozen routing preview

100 unique IDs; strategy {'NORMAL': 62, 'ICON': 10, 'SPECIAL_REVIEW': 28}; execution source {'NEW_RETRIEVAL': 9, 'OWNER_REFERENCE': 6, 'NO_SUITABLE_IMAGE': 1, 'INTERNAL_OVERRIDE': 1, 'BLOCKED_QUERY': 26, 'A004_REUSE': 57}.

Initial 10 IDs (frozen order):

- vocab-000001 apple: NORMAL / NEW_RETRIEVAL / `apple fruit`
- vocab-000028 car: NORMAL / NEW_RETRIEVAL / `car vehicle`
- vocab-000056 sleep: ICON / NEW_RETRIEVAL / `sleep icon`
- vocab-000053 write: ICON / NEW_RETRIEVAL / `write icon`
- vocab-000065 swim: ICON / NEW_RETRIEVAL / `swim icon`
- vocab-000046 hungry: ICON / OWNER_REFERENCE / ``
- vocab-000057 eat: NORMAL / OWNER_REFERENCE / ``
- vocab-000083 sometimes: SPECIAL_REVIEW / NO_SUITABLE_IMAGE / ``
- vocab-000081 because: SPECIAL_REVIEW / INTERNAL_OVERRIDE / ``
- vocab-000041 today: SPECIAL_REVIEW / BLOCKED_QUERY / ``

ICON queries to execute:

- vocab-000056: `sleep icon`
- vocab-000053: `write icon`
- vocab-000065: `swim icon`
- vocab-000019: `rain icon`
- vocab-000061: `understand icon`
- vocab-000062: `remember icon`

All other results are explicitly reused from A-004, bound to owner references, or blocked with rationale in the matrix. No owner reference is counted as a new retrieval. No production asset is written.
