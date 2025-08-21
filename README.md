1. 자체제작 화면.png
    - 혼자 만들던 서비스를 사용하여 테스트 케이스를 자동적으로 만들어서 일정한 폼의 형태로 뽑아냅니다.
    - 이때 생성된 파일들에 대해 xml 형태로 다운로드 가능합니다.(자체제작 결과물.xml)
    - 사용한 모델은 [gemini-2.5-flash]
    - 요청 프롬프트는 아래에 해당하는 형태로 보내집니다. (요청 내용 + 백그라운드 프롬프트)
**(요청 내용) **
알바몬 모바일 웹에 대해서 테스트 케이스를 작성해줘
- 개인회원 로그인 이고, [아이디]/ [비밀번호] 입력 후, 1로그인] 버튼을 클릭 하면 로 그인 과정이 진행 돼
- 로그인 과정에 성공하면 [마이페이지] 진입
- 로그인 과정에 값에 대한 누락이 있으면 토스트 팝업이 나타날꺼야
> 아이디 누락, 비밀번호 누락 처럼
Jo
아이디 + 비밀번호 입력 로그인 유효성 검증 (입력 값 누락 등)
로그인 실패 시 오류 메시지 출력
로그인 성공 시 마이페이지VpersonaVmypage) 이동 SNS 로그인 (카카오, 네이버)- 선택 사항
*
적어도 10개의 테스트 케이스를 만들어줘


-- (백그라운드 프롬프트) --
const userPrompt = `
        기능 이름: "${featureName}"
        요구사항: "${featureDescription}"
        
        위 기능에 대해 ${caseCount}개의 고유하고 품질 높은 테스트 케이스를 생성해줘. 반드시 ${caseCount}개를 생성해야 한다.
    `;

    try {
        const response = await ai.models.generateContent({
            model: 'gemini-2.5-flash',
            contents: userPrompt,
            config: {
                systemInstruction: "당신은 전문 QA 엔지니어입니다. 주어진 기능 설명에 따라 테스트 케이스를 생성해야 합니다. 모든 내용은 반드시 한국어로 작성해야 하며, 응답은 요구된 JSON 스키마를 엄격히 준수해야 합니다. 사용자가 요청한 개수만큼 정확히 테스트 케이스를 생성해야 합니다. 응답에는 JSON 객체 외에 다른 텍스트, 설명, 마크다운 서식이 포함되어서는 안 됩니다.",
                responseMimeType: "application/json",
                responseSchema: testCaseSchema
            }
        });
        
        const jsonString = response.text.trim();
        const result = JSON.parse(jsonString);
        
-- (케이스 스키마) --
const testCaseSchema = {
    type: Type.OBJECT,
    properties: {
        cases: {
            type: Type.ARRAY,
            items: {
                type: Type.OBJECT,
                properties: {
                    title: { type: Type.STRING, description: '테스트 케이스의 구체적이고 고유한 제목' },
                    description: { type: Type.STRING, description: '테스트 케이스의 목적과 범위에 대한 상세 설명' },
                    preConditions: { type: Type.STRING, description: '테스트를 수행하기 위한 명확한 사전 조건' },
                    postConditions: { type: Type.STRING, description: '테스트 완료 후 예상되는 시스템 상태 (선택 사항)' },
                    priority: { type: Type.STRING, enum: ['Critical', 'High', 'Medium', 'Low'] },
                    severity: { type: Type.STRING, enum: ['Critical', 'Major', 'Minor', 'Low'] },
                    testType: { type: Type.STRING, enum: ['Functional', 'Security', 'Performance', 'Usability', 'Compatibility'] },
                    behavior: { type: Type.STRING, enum: ['Positive', 'Negative', 'Destructive'] },
                    automationStatus: { type: Type.STRING, enum: ['Manual', 'Automated', 'Semi-automated'] },
                    layer: { type: Type.STRING, enum: ['E2E', 'API', 'Unit'] },
                    tags: { type: Type.ARRAY, items: { type: Type.STRING }, description: '검색을 위한 관련 키워드 배열' },
                    steps: {
                        type: Type.ARRAY,
                        items: {
                            type: Type.OBJECT,
                            properties: {
                                step: { type: Type.STRING, description: '수행할 구체적인 액션' },
                                inputData: { type: Type.STRING, description: '해당 단계를 위한 예시 입력 데이터 (선택 사항)' },
                                expectedResult: { type: Type.STRING, description: '해당 단계의 예상 결과' },
                            },
                             required: ['step', 'expectedResult']
                        }
                    }
                },
                required: ['title', 'description', 'preConditions', 'priority', 'severity', 'testType', 'behavior', 'automationStatus', 'layer', 'tags', 'steps']
            }
        }
    },
    required: ['cases']
};


2. GPT만 사용 했을 시.md
    - GPT 만 사용해서 통째로 보내보면 어떻게 나올까 생각이 들어서 한번 진행해보았습니다.
    - 이때, 생성되는 파일은 생각보다 내용이 좋았지만 코드 적인 부분에서 문제가 계속 발생하는 부분이 있어 한번에 요청하면 안된다는 것을 확인 하였습니다.


3. 자동화 케이스 코드
    - playwright + python 을 사용 하였습니다.
    - codegen 을 통해서 레코드 방식으로 먼저 요소를 찾은 후, 요소에 맞게 동작하게끔 설정
    - 일부 항목에 대해서는 gpt를 통해 수정 진행

4. 테스트 케이스.md 
    - 내용 추가

5. 자동화 케이스.md
    - 내용 추가

6. 결과물 검토.md
    - 내용 추가
