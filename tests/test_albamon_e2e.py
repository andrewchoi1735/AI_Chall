import os
import re
from dotenv import load_dotenv
import pytest
from playwright.sync_api import expect
import json

# ──────────────────────────────────────────────────────────────────────────────
# 공통 설정
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()
ALBAMON_ID = os.getenv("ALBAMON_ID")
ALBAMON_PW = os.getenv("ALBAMON_PW")
BASE_URL = "https://m.albamon.com"

# 모바일 디바이스 프로필 사용 (안정적 모바일 뷰 재현)
@pytest.fixture(scope="session")
def device_profile(playwright):
    return playwright.devices["iPhone 13 Pro"]

@pytest.fixture()
def mobile_context(browser, device_profile):
    # headless=False는 디버깅용. CI에서는 True 권장
    context = browser.new_context(**device_profile)
    page = context.new_page()
    yield page, context
    context.close()

# 간단한 Page Object Helper (의미론적 우선 → 폴백)
class LoginPage:
    def __init__(self, page):
        self.page = page

    def goto(self):
        self.page.goto(f"{BASE_URL}/user-account/login", wait_until="domcontentloaded")

    def fill_username(self, username: str):
        # placeholder/label 우선 + 폴백
        try:
            self.page.get_by_placeholder(re.compile("아이디|이메일|ID", re.I)).fill(username)
        except:
            self.page.locator('input[type="text"], input[name*="id" i], input[name*="email" i]').first.fill(username)

    def fill_password(self, password: str):
        try:
            self.page.get_by_placeholder(re.compile("비밀번호|password", re.I)).fill(password)
        except:
            self.page.locator('input[type="password"]').first.fill(password)

    def toggle_keep_signed_in(self, enable=True):
        """
        '로그인 상태 유지' 체크박스가 있으면 상태를 원하는대로 맞춤.
        - 접근성 Role 체크박스 시도 → 텍스트 필터 폴백
        """
        try:
            cb = self.page.get_by_role("checkbox", name=re.compile("로그인 상태 유지"))
            # 현재 상태 읽기
            is_checked = cb.is_checked()
            if enable and not is_checked:
                cb.check()
            elif not enable and is_checked:
                cb.uncheck()
            return
        except:
            # 폴백: 텍스트 영역에서 체크박스 추정 후 클릭
            root = self.page.locator("body")
            label = root.get_by_text(re.compile("로그인 상태 유지"))
            if label.count() > 0:
                label.first.click()

    def submit(self):
        # 버튼 Role 우선 → 텍스트 폴백 → 타입 폴백
        try:
            self.page.get_by_role("button", name=re.compile("^로그인$", re.I), exact=True).click()
            return
        except:
            pass
        try:
            self.page.get_by_text(re.compile("^로그인$", re.I)).first.click()
            return
        except:
            pass
        self.page.locator('button, input[type="submit"]').filter(has_text=re.compile("로그인")).first.click()

    def expect_error(self):
        """
        로그인 실패 시 나타나는 에러 메시지 영역을 탐지.
        사이트마다 문구가 조금씩 달라질 수 있으므로 정규식으로 느슨하게 검사.
        """
        # 일반적인 실패 문구 후보
        candidates = [
            re.compile("아이디|이메일|비밀번호.*일치하지 않", re.I),
            re.compile("로그인.*실패", re.I),
            re.compile("다시 시도", re.I),
        ]
        # 화면 어디든 텍스트로 확인
        page_text = self.page.locator("body").inner_text()
        assert any(p.search(page_text) for p in candidates), "로그인 실패 메시지를 찾지 못했습니다."


def open_mypage(page):
    # 이미 마이페이지면 스킵
    if re.search(r"(personal/)?mypage", page.url, re.I):
        return
    # 클릭 시도
    for fn in (
        lambda: page.get_by_role("link", name=re.compile("마이페이지")).click(),
        lambda: page.get_by_text(re.compile("마이페이지")).first.click(),
        lambda: (page.get_by_role("button", name=re.compile("메뉴|열기|더보기")).click(),
                 page.get_by_text(re.compile("마이페이지")).first.click()),
    ):
        try:
            fn()
            return
        except:
            pass
    # 마지막 폴백: 직접 진입
    page.goto("https://m.albamon.com/personal/mypage", wait_until="domcontentloaded")


def expect_on_mypage(page):
    """
    마이페이지 진입 확인: URL + 화면에만 존재하는 지표 텍스트로 판별
    """
    # URL 패턴: /personal/mypage 를 포함하거나 my/mypage/account/user 유사 키워드
    expect(page).to_have_url(re.compile(r"(personal/)?mypage|/my\b|account|user", re.I))

    # 화면에서만 보이는 마커(실제 페이지 텍스트 기반)
    markers = [
        "회원정보",     # 사이드/상단 메뉴
        "이력서",       # 이력서관리, 이력서 열람 등
        "지원현황",
        "스크랩",
        "최근본알바"
    ]
    body_text = page.locator("body").inner_text()
    assert any(m in body_text for m in markers), "마이페이지 지표 텍스트 미검출"

# ──────────────────────────────────────────────────────────────────────────────
# 보조 함수: 컨텍스트의 모든 쿠키/스토리지를 새 컨텍스트로 복제 주입
# ──────────────────────────────────────────────────────────────────────────────
def _extract_local_storage(page):
    """
    현재 페이지 origin의 localStorage를 {k:v} dict로 추출
    - 주의: origin 별로 다르므로 albamon 관련 origin에서 호출해야 함.
    """
    items = page.evaluate("Object.entries(window.localStorage)")
    return {k: v for (k, v) in items}

def _inject_tokens_to_new_context(browser, device_profile, cookies, local_storage_map):
    """
    새 컨텍스트를 만들고:
    1) cookies 전부 add_cookies
    2) add_init_script로 albamon 도메인 접근 시 localStorage를 주입
    """
    context2 = browser.new_context(**device_profile)

    # 1) 쿠키 그대로 주입
    if cookies:
        context2.add_cookies(cookies)

    # 2) localStorage 주입 (dict → JSON 직렬화 후 JS 내에서 복원)
    if local_storage_map:
        local_storage_json = json.dumps(local_storage_map)
        context2.add_init_script(f"""
            (() => {{
                if (!location.hostname.endsWith('albamon.com')) return;
                try {{
                    const data = JSON.parse('{local_storage_json}');
                    for (const [k, v] of Object.entries(data || {{}})) {{
                        window.localStorage.setItem(k, v);
                    }}
                }} catch(e) {{}}
            }})();
        """)

    return context2


# ──────────────────────────────────────────────────────────────────────────────
# 주요 시나리오 1: 정상 로그인 → 마이페이지 진입 (Happy Path)
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.albamon_e2e
def test_login_success_then_open_mypage(mobile_context):
    """
    Given 로그인 페이지에 접속했고
    When 올바른 ID/비밀번호를 입력하고 로그인 버튼을 클릭하면
    Then 로그인 성공 후 마이페이지로 진입할 수 있다
    """
    page, _ = mobile_context
    login = LoginPage(page)

    # Given
    login.goto()

    # When
    login.fill_username(ALBAMON_ID)
    login.fill_password(ALBAMON_PW)
    login.submit()

    # 로그인 후 약간 대기(리다이렉션/토스트 처리)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(700)

    # Then
    open_mypage(page)
    expect_on_mypage(page)

    # 증적 스크린샷
    page.screenshot(path="01_mypage_after_login.png")


# ──────────────────────────────────────────────────────────────────────────────
# 주요 시나리오 2: 잘못된 비밀번호로 로그인 실패 (에러 메시지 확인)
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.albamon_e2e
def test_login_failure_with_wrong_password(mobile_context):
    """
    Given 로그인 페이지에 접속했고
    When 틀린 비밀번호로 로그인하면
    Then 의미있는 에러 메시지가 노출된다(보안상 과도한 정보 노출 금지)
    """
    page, _ = mobile_context
    login = LoginPage(page)

    # Given
    login.goto()

    # When
    login.fill_username(ALBAMON_ID)
    login.fill_password("WRONG_PASSWORD_!!!")
    login.submit()

    # Then
    # 에러 메시지가 나타나는지 느슨한 정규식 기반 확인
    page.wait_for_timeout(500)
    login.expect_error()

    page.screenshot(path="02_login_failure.png")


# ──────────────────────────────────────────────────────────────────────────────
# 주요 시나리오 3(대체): '로그인 상태 유지' 확인을 토큰/쿠키 주입 방식으로
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.albamon_e2e
def test_keep_signed_in_persists_session(playwright, browser, device_profile, tmp_path):
    """
    Given 정상 로그인 후 (쿠키/스토리지 확보)
    When 새 컨텍스트를 만들고 쿠키 + localStorage를 '직접 주입'해서 마이페이지에 접근하면
    Then 추가 로그인 없이 마이페이지에 진입할 수 있다
    """
    # 1) 최초 컨텍스트에서 로그인하고 토큰/쿠키/스토리지 확보
    context1 = browser.new_context(**device_profile)
    page1 = context1.new_page()

    login = LoginPage(page1)
    login.goto()
    login.fill_username(ALBAMON_ID)
    login.fill_password(ALBAMON_PW)
    login.toggle_keep_signed_in(True)  # 사이트에 이 옵션이 있다면 ON
    login.submit()

    # 로그인/리다이렉트 안정화
    page1.wait_for_load_state("domcontentloaded")
    page1.wait_for_timeout(1200)

    # 로그인 성공 지표 확인 + 마이페이지 열어놓기
    open_mypage(page1)
    expect_on_mypage(page1)

    # (중요) 토큰/쿠키 반영 시간 살짝 더 대기
    page1.wait_for_timeout(1500)

    # 컨텍스트1의 모든 쿠키 수집
    cookies = context1.cookies()  # 모든 도메인의 쿠키가 dict로 반환됨
    # localStorage는 origin 단위라, 마이페이지에서 한 번 추출
    local_storage_map = _extract_local_storage(page1)

    # 참고: 디버깅이 필요하면 아래 주석을 풀어 내용 확인
    # import json
    # print("== cookies ==")
    # print(json.dumps(cookies, indent=2, ensure_ascii=False))
    # print("== localStorage ==")
    # print(json.dumps(local_storage_map, indent=2, ensure_ascii=False))

    context1.close()

    # 2) 새 컨텍스트 생성 + 토큰/스토리지 '주입'
    context2 = _inject_tokens_to_new_context(browser, device_profile, cookies, local_storage_map)
    page2 = context2.new_page()

    # 3) 곧장 마이페이지 접근
    #    - localStorage 주입은 add_init_script로 되어 있으므로, 해당 도메인 문서 로드 시 자동 적용됨
    page2.goto(f"{BASE_URL}/personal/mypage", wait_until="domcontentloaded")

    # Ajax 렌더링/지연 대비
    page2.wait_for_timeout(800)

    # 4) 검증
    #    - 텍스트가 늦게 도착할 수 있으므로 selector 기반 대기도 함께 사용(안정성 ↑)
    try:
        page2.wait_for_selector("text=회원정보", timeout=2000)
    except:
        # 텍스트 마커가 다른 케이스를 위해 보조 마커도 확인
        # (사이트 개편/AB테스트에 대비한 완충)
        for marker in ("이력서", "지원현황", "스크랩", "최근본알바"):
            if page2.locator(f"text={marker}").count() > 0:
                break
        else:
            # 마지막으로 기존 휴리스틱으로도 한 번 더 판별
            expect_on_mypage(page2)

    # 최종 스냅샷
    page2.screenshot(path="03_mypage_persisted_token_injection.png")
    context2.close()
