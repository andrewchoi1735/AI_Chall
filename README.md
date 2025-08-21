# 📌 Albamon Mobile Web – 테스트 케이스 자동 생성 & 자동화

이 레포는 **Albamon 모바일 웹(개인회원 로그인)**을 대상으로  
1) AI를 활용한 **테스트 케이스 자동 생성**,  
2) Playwright + Python 기반 **자동화 코드**,  
3) 산출물 **검토/보완 기록**을 정리한 프로젝트입니다.

> 사용 모델: `gemini-2.5-flash`, `GPT`  
> 자동화: `Playwright (Python)`  
> 결과물: `JSON → XML` 변환(자체제작 도구), 여러 `.md` 문서

---

## 📁 파일/문서 개요

- `자체제작 화면.png`  
  자체 제작한 서비스의 생성 화면 (AI로 케이스 자동 생성 → XML 다운로드)
- `자체제작 결과물.xml`  
  생성된 케이스를 **XML 형태로 다운로드**한 산출물
- `테스트 케이스.md`  
  로그인/실패/유효성/SNS 등 **10개 이상** 케이스 정리 문서
- `자동화 케이스.md`  
  **Playwright + Python** 자동화 스크립트 설명과 실행 방법
- `결과물 검토.md`  
  AI 출력 한계와 보완 내역, 실무 예외 케이스 추가 제안
- `GPT만 사용 했을 시.md`  
  GPT 단독 사용 실험 기록 (장단점/한계)

> README 내에 모든 핵심 내용이 포함됩니다. 별도 문서 링크 없이도 이해 가능하도록 구성했습니다.

---

## 1) 자체제작 화면.png — 생성/다운로드 플로우

- **자체 제작 서비스**에서 테스트 케이스를 자동 생성하고 **일정한 폼(JSON 스키마 기반)**으로 출력합니다.  
- 생성된 결과는 **XML로 다운로드**가 가능합니다 → 파일명: `자체제작 결과물.xml`  
- 사용한 AI 모델: **`gemini-2.5-flash`**

### (요청 내용) — 프롬프트 예시
알바몬 모바일 웹에 대해서 테스트 케이스를 작성해줘

개인회원 로그인 이고, [아이디]/ [비밀번호] 입력 후, [로그인] 버튼을 클릭 하면 로그인 과정이 진행 돼

로그인 과정에 성공하면 [마이페이지] 진입

로그인 과정에 값에 대한 누락이 있으면 토스트 팝업이 나타날꺼야

아이디 + 비밀번호 입력 로그인 유효성 검증 (입력 값 누락 등)
로그인 실패 시 오류 메시지 출력
로그인 성공 시 마이페이지(persona/mypage) 이동
SNS 로그인 (카카오, 네이버)- 선택 사항
*
적어도 10개의 테스트 케이스를 만들어줘

### (백그라운드 프롬프트) — 코드 스니펫
```javascript
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
```


### (케이스 스키마) — 코드 스니펫
```javascript
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
```

## 2) GPT만 사용 했을 시.md — 단독 사용 결과 요약

GPT 단독으로 “통째로” 요청을 보냈을 때
- 장점: 생성된 케이스의 내용 품질은 비교적 양호

- 단점: 코드/스키마 호환성 문제와 형식 누락이 자주 발생

- 결론 → 분할 요청 + 스키마 강제가 필요
(예: 케이스만 먼저 생성 → 별도 단계에서 코드/스텁 생성)

## 3) 자동화 케이스 코드 — Playwright + Python

전략

- codegen으로 요소/흐름 레코딩

- POM/헬퍼로 정리 (LoginPage, expect_on_mypage 등)

- 토큰 주입/스토리지 복원 케이스 포함 (세션 유지 검증)

[실행 전제]

- Python 3.11+ / 3.12
- Playwright 설치 및 브라우저 준비

```bash
pip install pytest playwright pytest-playwright
playwright install
```
[실행]
```bash
pytest -s -vv -k albamon_e2e
```

## 예시 코드 (요지)
```python
# tests/test_albamon_e2e.py
import json, re, pytest
from playwright.sync_api import expect

BASE_URL = "https://m.albamon.com"
ALBAMON_ID = "YOUR_ID"
ALBAMON_PW = "YOUR_PW"

# --- Page Object ---
class LoginPage:
    def __init__(self, page):
        self.page = page
    def goto(self):
        self.page.goto(f"{BASE_URL}/user-account/login", wait_until="domcontentloaded")
    def fill_username(self, v): self.page.get_by_placeholder("아이디").fill(v)
    def fill_password(self, v): self.page.get_by_placeholder("비밀번호").fill(v)
    def toggle_keep_signed_in(self, on=True):
        # 실제 스위치 로케이터에 맞춰 조정 필요
        sw = self.page.get_by_text("로그인 상태 유지", exact=False)
        if on: sw.click()
    def submit(self):
        self.page.get_by_role("button", name=re.compile("로그인")).click()

def open_mypage(page):
    # 메뉴 경로가 바뀌면 직접 이동 폴백
    page.goto(f"{BASE_URL}/personal/mypage", wait_until="domcontentloaded")

def expect_on_mypage(page):
    expect(page).to_have_url(re.compile(r"(personal/)?mypage|/my\b|account|user", re.I))
    markers = ["회원정보","이력서","지원현황","스크랩","최근본알바"]
    body_text = page.locator("body").inner_text()
    assert any(m in body_text for m in markers), "마이페이지 지표 텍스트 미검출"

def expect_login_error(page):
    # 실제 에러 토스트/배너 텍스트에 맞춰 수정
    err = page.get_by_text(re.compile("아이디|비밀번호|오류|확인", re.I))
    expect(err).to_be_visible()

# --- 유틸: localStorage 추출 ---
def _extract_local_storage(page):
    return page.evaluate("""() => {
        const out = {};
        for (let i=0;i<localStorage.length;i++){
            const k = localStorage.key(i);
            out[k] = localStorage.getItem(k);
        }
        return out;
    }""")

# --- 유틸: 새 컨텍스트에 토큰/스토리지 주입 ---
def _inject_tokens_to_new_context(browser, device_profile, cookies, local_storage_map):
    context2 = browser.new_context(**device_profile)
    if cookies: context2.add_cookies(cookies)
    if local_storage_map:
        local_storage_json = json.dumps(local_storage_map)
        context2.add_init_script(f"""
            (() => {{
                if (!location.hostname.endsWith('albamon.com')) return;
                try {{
                    const data = JSON.parse('{local_storage_json}');
                    for (const [k,v] of Object.entries(data||{{}})) {{
                        localStorage.setItem(k, v);
                    }}
                }} catch(e) {{}}
            }})();
        """)
    return context2

# --- 디바이스 프로파일(예: iPhone 12 대략값) ---
@pytest.fixture
def device_profile():
    return dict(
        is_mobile=True, has_touch=True, device_scale_factor=3,
        viewport={"width":390,"height":844}, user_agent="Mozilla/5.0 Playwright"
    )

# --- 시나리오 1: 로그인 성공 ---
@pytest.mark.albamon_e2e
def test_login_success_then_open_mypage(playwright, browser, device_profile):
    context = browser.new_context(**device_profile)
    page = context.new_page()
    login = LoginPage(page)

    login.goto()
    login.fill_username(ALBAMON_ID)
    login.fill_password(ALBAMON_PW)
    login.submit()

    page.wait_for_load_state("domcontentloaded")
    open_mypage(page)
    expect_on_mypage(page)
    context.close()

# --- 시나리오 2: 로그인 실패 ---
@pytest.mark.albamon_e2e
def test_login_failure_with_wrong_password(playwright, browser, device_profile):
    context = browser.new_context(**device_profile)
    page = context.new_page()
    login = LoginPage(page)

    login.goto()
    login.fill_username(ALBAMON_ID)
    login.fill_password("WRONG_PASS!!")
    login.submit()

    expect_login_error(page)
    context.close()

# --- 시나리오 3: 로그인 유지 (토큰 주입) ---
@pytest.mark.albamon_e2e
def test_keep_signed_in_persists_session(playwright, browser, device_profile, tmp_path):
    context1 = browser.new_context(**device_profile)
    page1 = context1.new_page()

    login = LoginPage(page1)
    login.goto()
    login.fill_username(ALBAMON_ID)
    login.fill_password(ALBAMON_PW)
    login.toggle_keep_signed_in(True)
    login.submit()
    page1.wait_for_load_state("domcontentloaded")
    open_mypage(page1)
    expect_on_mypage(page1)

    # 토큰/쿠키 수집
    page1.wait_for_timeout(1000)
    cookies = context1.cookies()
    local_storage_map = _extract_local_storage(page1)
    context1.close()

    # 새 컨텍스트에 주입 후 접근
    context2 = _inject_tokens_to_new_context(browser, device_profile, cookies, local_storage_map)
    page2 = context2.new_page()
    page2.goto(f"{BASE_URL}/personal/mypage", wait_until="domcontentloaded")
    page2.wait_for_timeout(500)
    expect_on_mypage(page2)
    context2.close()
```

## 4) 테스트 케이스.md — 요약(10개 이상)

1. 정상 로그인 후 마이페이지 진입(해피패스)

2. 아이디 누락 → 토스트 노출

3. 비밀번호 누락 → 토스트 노출

4. 아이디/비밀번호 모두 누락 → 토스트 노출

5. 잘못된 자격증명 → 오류 메시지 노출

6. 공백/트림 처리 유효성

7. 비밀번호 대소문자/특수문자 민감도

8. 로그인 상태 유지(세션 지속)

9. 로그아웃 후 보호 리소스 접근 차단

10. 보호 리소스 직접 접근 → 로그인 후 원래 페이지로 리다이렉션

11. SNS 로그인(카카오) 시작→취소

12. SNS 로그인(네이버) 완료
→ 상세 단계/예상결과는 별도 파일 테스트 케이스.md에 정리 가능(또는 본 README 하위에 섹션 추가)

##5) 자동화 케이스.md — 요약

자동화 범위: 로그인 성공/실패/유효성/세션 유지

도구/환경: Python + Playwright + Pytest

실행 명령:
```bash
pytest -s -vv -k albamon_e2e
```

권장 사항

의미론적 로케이터(get_by_role/label/placeholder) 우선, 텍스트/CSS는 폴백

실패 시 스크린샷/트레이스 자동 수집

CI에서 브라우저 캐시/스토리지를 워크스페이스별로 분리





## 6) 결과물 검토.md — 핵심 요약
[AI 출력의 한계 또는 오류]

- 스키마 불일치(필드 누락/형식 상이)

- 형식 외 텍스트 혼입(마크다운/설명)

- 코드 호환성 문제(API 시그니처 차이, 예: add_init_script)

[수정/보완한 내용 및 이유]

- 스키마 강제/검증으로 일관성 확보

- 로케이터/대기 로직 보강(텍스트 마커 + URL 정규식 + 셀렉터 대기)

- 토큰 주입 방식으로 로그인 유지 신뢰성 향상

[실무 관점 추가 예외 케이스]

- 토큰 만료/재발급 플로우

- 캡차/2FA 개입 시 스킵 가드

- 멀티 디바이스 동시 로그인 정책

- 느린 네트워크(3G) 성능 검증(P95, TTFB 등)

- 접근성(a11y) 및 i18n 텍스트 변동 대응


## 🧪 팁 & 모범사례

- 분할 요청 전략: (케이스) → (코드 스텁) → (보강/리팩터링)

- 환경 파라미터화: 아이디/비밀번호는 환경변수/시크릿으로 관리

- 테스트 증적: 실패 시 스크린샷/trace/network HAR 자동 저장

- 디바이스 프로필: iOS/Android 주요 해상도 별 파라미터로 커버

- 로케이터 안정성: ARIA Role/Label 우선 + 폴백


## ✅ 결론

Gemini(스키마 기반) + GPT(코드 보강) 조합으로
테스트 케이스 생성 → XML 관리 → 자동화 실행의 파이프라인을 구축했습니다.

실무 적용 시 스키마 강제, 예외 케이스 보강, CI 관측성이 핵심입니다.
