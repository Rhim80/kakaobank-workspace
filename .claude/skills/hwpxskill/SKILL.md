---
name: hwpx
description: "한글(HWPX) 문서 생성/읽기/편집 스킬. .hwpx 파일, 한글 문서, Hancom, OWPML 관련 요청 시 사용."
---

# HWPX 문서 스킬 — 레퍼런스 복원 우선(XML-first) 워크플로우

한글(Hancom Office)의 HWPX 파일을 **XML 직접 작성** 중심으로 생성, 편집, 읽기할 수 있는 스킬.
HWPX는 ZIP 기반 XML 컨테이너(OWPML 표준)이다. python-hwpx API의 서식 버그를 완전히 우회하며, 세밀한 서식 제어가 가능하다.

## 항상 지키는 것 (워크플로우·실행 방식 무관)

아래 둘은 XML을 손으로 짜든 라이브러리를 부르든 똑같이 걸린다. **실행 방식을 갈아끼워도 남는 규칙이다.**

### A. 추출 결과가 짧으면 "내용 없음"이 아니라 "표를 건너뛴 것"부터 의심한다

한글 서식·공문서는 본문이 대부분 **표 안**에 있다. 표를 건너뛰는 추출기는 내용이 가득한 문서를 몇 글자로 내놓고 **에러는 내지 않는다.**

실측(2026-09-01, 멘토일지 서식 1건): 표 제외 11자·찾는 이름 0건 / 표 포함 2,057자·2건 / markdown 2,153자·2건.

```bash
source "$VENV"
python "$SKILL_DIR/scripts/text_extract.py" document.hwpx        # 표 포함이 기본
```

`text_extract.py`는 **표 포함이 기본값**이다(2026-09-01 변경 — 그전까지는 건너뛰는 게 기본이었다). 건너뛰려면 `--no-tables`를 주며, 줄 때마다 경고가 찍힌다. 옛 명령에 남아 있는 `--include-tables`는 지금 기본과 같아 아무것도 바꾸지 않는다.

**다른 도구·다른 함수로 읽을 때는 이 기본값이 없다** — 표 포함 여부를 직접 켜고, 결과 길이를 원본과 대본다.

### B. "이 문자열이 문서에 없다"는 추출 결과로 판정하지 않는다

탭이 섞인 줄(`멘토명 :        (서명)` 같은 서식 칸)은 그 글자가 `hp:t`의 text가 아니라 **`hp:tab` 요소의 tail**에 들어간다. `.text`만 훑는 코드는 **조용히** 못 찾고 지나간다.

- 치환·검색 코드는 `el.text`와 `el.tail`을 **둘 다** 본다.
- 없다고 결론 내리기 전에 원본 XML을 직접 본다:
  ```bash
  python "$SKILL_DIR/scripts/office/unpack.py" document.hwpx ./unpacked
  grep -c "찾는말" ./unpacked/Contents/section0.xml
  ```
- **같은 라이브러리 안에서도 부르는 함수마다 갈린다** (`python-hwpx 6.3.0` 실측, 같은 파일 1건): `doc.text.plain()`·`doc.text.markdown()`·`doc.text.html()`·`doc.text.runs()` 넷은 **못 잡는다**. `TextExtractor.extract_text()`(= `text_extract.py`가 감싼 것)는 **잡는다**. 라이브러리 이름으로 믿지 말고 **부르는 함수**로 판단한다.

**이 스킬 스크립트 쪽 상태(2026-09-01 확인)**: 글자를 읽어 판정하는 셋은 전부 tail을 본다 — `page_guard.py`·`analyze_template.py`는 `itertext()`, `text_extract.py`는 tail을 잡는 `TextExtractor`. (`analyze_template.py`는 이날 `.text`만 보다가 고친 것 — 같은 파일에서 834자·미검출이 985자·검출로 바뀌었다.) 나머지 다섯은 글자로 판정하지 않는다.

이 규칙이 덮는 범위: 파일 1건 · tab tail 1종. `hp:lineBreak` 등 다른 tail 요소는 아직 안 재봤다.

## 기본 동작 모드 (필수): 첨부 HWPX 분석 → 고유 XML 복원(99% 근접) → 요청 반영 재작성

사용자가 `.hwpx`를 첨부한 경우, 이 스킬은 아래 순서를 **기본값**으로 따른다.

1. **레퍼런스 확보**: 첨부된 HWPX를 기준 문서로 사용
2. **심층 분석/추출**: `analyze_template.py`로 `header.xml`, `section0.xml` 추출
3. **구조 복원**: header 스타일 ID/표 구조/셀 병합/여백/문단 흐름을 최대한 동일하게 유지
4. **요청 반영 재작성**: 사용자가 요구한 텍스트/데이터만 교체하고 구조는 보존
5. **빌드/검증**: `build_hwpx.py` + `validate.py`로 결과 산출 및 무결성 확인
6. **쪽수 가드(필수)**: `page_guard.py`로 레퍼런스 대비 페이지 드리프트 위험 검사

### 99% 근접 복원 기준 (실무 체크리스트)

- `charPrIDRef`, `paraPrIDRef`, `borderFillIDRef` 참조 체계 동일
- 표의 `rowCnt`, `colCnt`, `colSpan`, `rowSpan`, `cellSz`, `cellMargin` 동일
- 문단 순서, 문단 수, 주요 빈 줄/구획 위치 동일
- 페이지/여백/섹션(secPr) 동일
- 변경은 사용자 요청 범위(본문 텍스트, 값, 항목명 등)로 제한

### 쪽수 동일(100%) 필수 기준

- 사용자가 레퍼런스를 제공한 경우 **결과 문서의 최종 쪽수는 레퍼런스와 동일해야 한다**
- 쪽수가 늘어날 가능성이 보이면 먼저 텍스트를 압축/요약해서 기존 레이아웃에 맞춘다
- 사용자 명시 요청 없이 `hp:p`, `hp:tbl`, `rowCnt`, `colCnt`, `pageBreak`, `secPr`를 변경하지 않는다
- `validate.py` 통과만으로 완료 처리하지 않는다. 반드시 `page_guard.py`도 통과해야 한다
- `page_guard.py` 실패 시 결과를 완료로 제출하지 않고, 원인(길이 과다/구조 변경)을 수정 후 재빌드한다
- 가능하면 한글(또는 사용자의 확인) 기준 최종 쪽수 값을 확인하고 레퍼런스와 일치 여부를 재확인한다

### 기본 실행 명령 (첨부 레퍼런스가 있을 때)

```bash
source "$VENV"

# 1) 레퍼런스 분석 + XML 추출
python "$SKILL_DIR/scripts/analyze_template.py" reference.hwpx \
  --extract-header /tmp/ref_header.xml \
  --extract-section /tmp/ref_section.xml

# 2) /tmp/ref_section.xml을 복제해 /tmp/new_section0.xml 작성
#    (구조 유지, 텍스트/데이터만 요청에 맞게 수정)

# 3) 복원 빌드
python "$SKILL_DIR/scripts/build_hwpx.py" \
  --header /tmp/ref_header.xml \
  --section /tmp/new_section0.xml \
  --output result.hwpx

# 4) 검증
python "$SKILL_DIR/scripts/validate.py" result.hwpx

# 5) 쪽수 드리프트 가드 (필수)
python "$SKILL_DIR/scripts/page_guard.py" \
  --reference reference.hwpx \
  --output result.hwpx
```

## 환경

```
# SKILL_DIR는 이 SKILL.md가 위치한 디렉토리의 절대 경로로 설정
SKILL_DIR="$(cd "$(dirname "${0}")/.." && pwd)"   # 스크립트 내에서
# 또는 Claude Code가 자동으로 주입하는 base directory 경로를 사용

# Python 가상환경 — 경로는 .claude/venv.sh 가 OS별로 알아서 고른다
# (Mac·Linux는 .venv/bin, 윈도우 Git Bash는 .venv/Scripts)
VENV=".claude/venv.sh"
```

모든 Python 실행 시:
```bash
# 워크스페이스의 .venv를 활성화
source "$VENV"
```

활성화 뒤에는 `python3`가 아니라 **`python`**으로 부른다 — 윈도우 가상환경에는 `python3`라는 이름이 없다.

### 설치 (처음 한 번, 기계마다)

이 스킬의 스크립트는 `python-hwpx`를 import 한다. **워크스페이스 기본 세팅(`setup-workspace`)에는 이 패키지가 없다** — 여기서 따로 깐다.

```bash
source "$VENV"
python -m pip install -r .claude/skills/hwpxskill/scripts/requirements.txt
```

확인:
```bash
source "$VENV" && python -c "import hwpx; print('OK', hwpx.__version__)"
```

`pip`가 아니라 **`python -m pip`**로 부른다 — 워크스페이스 폴더 이름이 바뀐 적이 있으면 `pip` 실행 파일이 옛 경로를 가리켜 `bad interpreter`로 죽는다(2026-09-01 이 맥에서 실제로 그랬다). `python -m pip`는 그 영향을 안 받는다.

**`ModuleNotFoundError: No module named 'hwpx'` 또는 `python: command not found`가 뜨면** 위 설치를 안 했거나 `.venv`가 다른 경로에서 만들어진 것이다. 후자면 `.venv`를 지우고 다시 만든다(`python3 -m venv .venv` → 위 설치). `venv.sh`가 활성화 직후 이 상태를 잡아 메시지로 알려준다.

## 디렉토리 구조

```
.claude/skills/hwpxskill/
├── SKILL.md                              # 이 파일
├── scripts/
│   ├── office/
│   │   ├── unpack.py                     # HWPX → 디렉토리 (XML pretty-print)
│   │   └── pack.py                       # 디렉토리 → HWPX
│   ├── build_hwpx.py                     # 템플릿 + XML → .hwpx 조립 (핵심)
│   ├── analyze_template.py               # HWPX 심층 분석 (레퍼런스 기반 생성용)
│   ├── validate.py                       # HWPX 구조 검증
│   ├── page_guard.py                     # 레퍼런스 대비 페이지 드리프트 위험 검사
│   └── text_extract.py                   # 텍스트 추출
├── templates/
│   ├── base/                             # 베이스 템플릿 (Skeleton 기반)
│   │   ├── mimetype, META-INF/*, version.xml, settings.xml, Preview/*
│   │   └── Contents/ (header.xml, section0.xml, content.hpf)
│   ├── gonmun/                           # 공문 오버레이 (header.xml, section0.xml)
│   ├── report/                           # 보고서 오버레이
│   ├── minutes/                          # 회의록 오버레이
│   └── proposal/                         # 제안서/사업개요 오버레이 (색상 헤더바, 번호 배지)
└── references/
    └── hwpx-format.md                    # OWPML XML 요소 레퍼런스
```

---

## 워크플로우 0: `.hwp`(바이너리)가 들어왔을 때

이 스킬의 나머지 전부는 `.hwpx`를 다룬다. `.hwp`는 다른 물건이고, 둘을 잇는 문은 **한글이 깔린 윈도우 기계**뿐이다 — 순수 파이썬으로 `.hwp`를 쓰는 길은 2026-09-01 조사 시점에 없다. 그러니 **`.hwp`를 만나면 먼저 `.hwpx`로 바꾸고 들어온다.**

**어느 기계인지부터 본다.**

```bash
uname -s    # Darwin=맥 / MINGW*·MSYS*=윈도우 Git Bash / Linux
```

### 맥·리눅스 — 사람에게 넘긴다

여기서는 변환할 방법이 없다. 사용자에게 안내한다:

> 한글에서 파일 → 다른 이름으로 저장 → 파일 형식 **HWPX** 로 저장해 주세요.

### 윈도우 + 한글 설치 — `pyhwpx`로 연다  ⚠️ 미검증

```bash
source "$VENV"
python -m pip install -r .claude/skills/hwpxskill/scripts/requirements-windows.txt
```

```python
from pyhwpx import Hwp

hwp = Hwp(visible=False)              # 한글 창을 띄우지 않고 백그라운드로
hwp.open("input.hwp")                 # format 생략 = 자동 인식
hwp.save_as("output.hwpx", format="HWPX")
hwp.quit()
```

그다음은 평소대로 `.hwpx` 워크플로우로 들어간다.

**⚠️ 이 절은 아직 한 번도 돌려보지 않았다.** 위 함수 이름·인자·`"HWPX"` 포맷 문자열은 `pyhwpx 1.7.2` 패키지 소스에서 확인한 것이고(2026-09-01), **실행 결과는 확인하지 않았다** — 이 자리를 쓸 수 있는 기계가 없었다. 처음 돌리는 세션이 **서식이 지켜지는지(칸 넘침·줄 겹침·이미지·쪽수) 눈으로 확인하고, 결과를 이 절에 적어 「미검증」 표시를 지운다.** 되돌아오는 길(`.hwpx` → `.hwp`)도 같이 재본다.

---

## 워크플로우 1: XML-first 문서 생성 (보조 워크플로우, 레퍼런스 파일이 없을 때만)

### 흐름

1. **템플릿 선택** (base/gonmun/report/minutes/proposal)
2. **section0.xml 작성** (본문 내용)
3. **(선택) header.xml 수정** (새 스타일 추가 필요 시)
4. **build_hwpx.py로 빌드**
5. **validate.py로 검증**

> 원칙: 사용자가 레퍼런스 HWPX를 제공한 경우에는 이 워크플로우 대신 상단의 "기본 동작 모드(레퍼런스 복원 우선)"를 사용한다.

### 기본 사용법

```bash
source "$VENV"

# 빈 문서 (base 템플릿)
python "$SKILL_DIR/scripts/build_hwpx.py" --output result.hwpx

# 템플릿 사용
python "$SKILL_DIR/scripts/build_hwpx.py" --template gonmun --output result.hwpx

# 커스텀 section0.xml 오버라이드
python "$SKILL_DIR/scripts/build_hwpx.py" --template gonmun --section my_section0.xml --output result.hwpx

# header도 오버라이드
python "$SKILL_DIR/scripts/build_hwpx.py" --header my_header.xml --section my_section0.xml --output result.hwpx

# 메타데이터 설정
python "$SKILL_DIR/scripts/build_hwpx.py" --template report --section my.xml \
  --title "제목" --creator "작성자" --output result.hwpx
```

### 실전 패턴: section0.xml을 인라인 작성 → 빌드

```bash
# 1. section0.xml을 임시파일로 작성
SECTION=$(mktemp /tmp/section0_XXXX.xml)
cat > "$SECTION" << 'XMLEOF'
<?xml version='1.0' encoding='UTF-8'?>
<hs:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"
        xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section">
  <!-- secPr 포함 첫 문단 (base/section0.xml에서 복사) -->
  <!-- ... -->
  <hp:p id="1000000002" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="0">
      <hp:t>본문 내용</hp:t>
    </hp:run>
  </hp:p>
</hs:sec>
XMLEOF

# 2. 빌드
python "$SKILL_DIR/scripts/build_hwpx.py" --section "$SECTION" --output result.hwpx

# 3. 정리
rm -f "$SECTION"
```

---

## section0.xml 작성 가이드

### 필수 구조

section0.xml의 첫 문단(`<hp:p>`)의 첫 런(`<hp:run>`)에 반드시 `<hp:secPr>`과 `<hp:colPr>` 포함:

```xml
<hp:p id="1000000001" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="0">
    <hp:secPr ...>
      <!-- 페이지 크기, 여백, 각주/미주 설정 등 -->
    </hp:secPr>
    <hp:ctrl>
      <hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/>
    </hp:ctrl>
  </hp:run>
  <hp:run charPrIDRef="0"><hp:t/></hp:run>
</hp:p>
```

**Tip**: `templates/base/Contents/section0.xml` 의 첫 문단을 그대로 복사하면 된다.

### 문단

```xml
<hp:p id="고유ID" paraPrIDRef="문단스타일ID" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="글자스타일ID">
    <hp:t>텍스트 내용</hp:t>
  </hp:run>
</hp:p>
```

### 빈 줄

```xml
<hp:p id="고유ID" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="0"><hp:t/></hp:run>
</hp:p>
```

### 서식 혼합 런 (한 문단에 여러 스타일)

```xml
<hp:p id="고유ID" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="0"><hp:t>일반 텍스트 </hp:t></hp:run>
  <hp:run charPrIDRef="7"><hp:t>볼드 텍스트</hp:t></hp:run>
  <hp:run charPrIDRef="0"><hp:t> 다시 일반</hp:t></hp:run>
</hp:p>
```

### 표 작성법

```xml
<hp:p id="고유ID" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="0">
    <hp:tbl id="고유ID" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM"
            textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL"
            repeatHeader="0" rowCnt="행수" colCnt="열수" cellSpacing="0"
            borderFillIDRef="3" noAdjust="0">
      <hp:sz width="42520" widthRelTo="ABSOLUTE" height="전체높이" heightRelTo="ABSOLUTE" protect="0"/>
      <hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0"
              holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP"
              horzAlign="LEFT" vertOffset="0" horzOffset="0"/>
      <hp:outMargin left="0" right="0" top="0" bottom="0"/>
      <hp:inMargin left="0" right="0" top="0" bottom="0"/>
      <hp:tr>
        <hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="1" borderFillIDRef="4">
          <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER"
                     linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0"
                     hasTextRef="0" hasNumRef="0">
            <hp:p paraPrIDRef="21" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0" id="고유ID">
              <hp:run charPrIDRef="9"><hp:t>헤더 셀</hp:t></hp:run>
            </hp:p>
          </hp:subList>
          <hp:cellAddr colAddr="0" rowAddr="0"/>
          <hp:cellSpan colSpan="1" rowSpan="1"/>
          <hp:cellSz width="열너비" height="행높이"/>
          <hp:cellMargin left="0" right="0" top="0" bottom="0"/>
        </hp:tc>
        <!-- 나머지 셀... -->
      </hp:tr>
    </hp:tbl>
  </hp:run>
</hp:p>
```

### 표 크기 계산

- **A4 본문폭**: 42520 HWPUNIT = 59528(용지) - 8504×2(좌우여백)
- **열 너비 합 = 본문폭** (42520)
- 예: 3열 균등 → 14173 + 14173 + 14174 = 42520
- 예: 2열 (라벨:내용 = 1:4) → 8504 + 34016 = 42520
- **행 높이**: 셀당 보통 2400~3600 HWPUNIT

### ID 규칙

- 문단 id: `1000000001`부터 순차 증가
- 표 id: `1000000099` 등 별도 범위 사용 권장
- 모든 id는 문서 내 고유해야 함

---

## header.xml 수정 가이드

### 커스텀 스타일 추가 방법

1. `templates/base/Contents/header.xml` 복사
2. 필요한 charPr/paraPr/borderFill 추가
3. 각 그룹의 `itemCnt` 속성 업데이트

### charPr 추가 예시 (볼드 14pt)

```xml
<hh:charPr id="8" height="1400" textColor="#000000" shadeColor="none"
           useFontSpace="0" useKerning="0" symMark="NONE" borderFillIDRef="2">
  <hh:fontRef hangul="1" latin="1" hanja="1" japanese="1" other="1" symbol="1" user="1"/>
  <hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>
  <hh:spacing hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>
  <hh:relSz hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>
  <hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>
  <hh:bold/>
  <hh:underline type="NONE" shape="SOLID" color="#000000"/>
  <hh:strikeout shape="NONE" color="#000000"/>
  <hh:outline type="NONE"/>
  <hh:shadow type="NONE" color="#C0C0C0" offsetX="10" offsetY="10"/>
</hh:charPr>
```

### 폰트 참조 체계

- `fontRef` 값은 `fontfaces`에 정의된 font id
- `hangul="0"` → 함초롬돋움 (고딕)
- `hangul="1"` → 함초롬바탕 (명조)
- 7개 언어 모두 동일하게 설정

### paraPr 추가 시 주의

- 반드시 `hp:switch` 구조 포함 (`hp:case` + `hp:default`)
- `hp:case`와 `hp:default`의 값은 보통 동일 (또는 default가 2배)
- `borderFillIDRef="2"` 유지

---

## 템플릿별 스타일 ID 맵

### base (기본)

| ID | 유형 | 설명 |
|----|------|------|
| charPr 0 | 글자 | 10pt 함초롬바탕, 기본 |
| charPr 1 | 글자 | 10pt 함초롬돋움 |
| charPr 2~6 | 글자 | Skeleton 기본 스타일 |
| paraPr 0 | 문단 | JUSTIFY, 160% 줄간격 |
| paraPr 1~19 | 문단 | Skeleton 기본 (개요, 각주 등) |
| borderFill 1 | 테두리 | 없음 (페이지 보더) |
| borderFill 2 | 테두리 | 없음 + 투명배경 (참조용) |

### gonmun (공문) — base + 추가

| ID | 유형 | 설명 |
|----|------|------|
| charPr 7 | 글자 | 22pt 볼드 함초롬바탕 (기관명/제목) |
| charPr 8 | 글자 | 16pt 볼드 함초롬바탕 (서명자) |
| charPr 9 | 글자 | 8pt 함초롬바탕 (하단 연락처) |
| charPr 10 | 글자 | 10pt 볼드 함초롬바탕 (표 헤더) |
| paraPr 20 | 문단 | CENTER, 160% 줄간격 |
| paraPr 21 | 문단 | CENTER, 130% (표 셀) |
| paraPr 22 | 문단 | JUSTIFY, 130% (표 셀) |
| borderFill 3 | 테두리 | SOLID 0.12mm 4면 |
| borderFill 4 | 테두리 | SOLID 0.12mm + #D6DCE4 배경 |

### report (보고서) — base + 추가

| ID | 유형 | 설명 |
|----|------|------|
| charPr 7 | 글자 | 20pt 볼드 (문서 제목) |
| charPr 8 | 글자 | 14pt 볼드 (소제목) |
| charPr 9 | 글자 | 10pt 볼드 (표 헤더) |
| charPr 10 | 글자 | 10pt 볼드+밑줄 (강조 텍스트) |
| charPr 11 | 글자 | 9pt 함초롬바탕 (소형/각주) |
| charPr 12 | 글자 | 16pt 볼드 함초롬바탕 (1줄 제목) |
| charPr 13 | 글자 | 12pt 볼드 함초롬돋움 (섹션 헤더) |
| paraPr 20~22 | 문단 | CENTER/JUSTIFY 변형 |
| paraPr 23 | 문단 | RIGHT 정렬, 160% 줄간격 |
| paraPr 24 | 문단 | JUSTIFY, left 600 (□ 체크항목 들여쓰기) |
| paraPr 25 | 문단 | JUSTIFY, left 1200 (하위항목 ①②③ 들여쓰기) |
| paraPr 26 | 문단 | JUSTIFY, left 1800 (깊은 하위항목 - 들여쓰기) |
| paraPr 27 | 문단 | LEFT, 상하단 테두리선 (섹션 헤더용), prev 400 |
| borderFill 3 | 테두리 | SOLID 0.12mm 4면 |
| borderFill 4 | 테두리 | SOLID 0.12mm + #DAEEF3 배경 |
| borderFill 5 | 테두리 | 상단 0.4mm 굵은선 + 하단 0.12mm 얇은선 (섹션 헤더) |

**들여쓰기 규칙**: 공백 문자가 아닌 반드시 paraPr의 left margin 사용. □ 항목은 paraPr 24, 하위 ①②③ 는 paraPr 25, 깊은 - 항목은 paraPr 26.

**섹션 헤더 규칙**: paraPr 27 + charPr 13 조합. 문단 테두리(borderFillIDRef="5")로 상단 굵은선 + 하단 얇은선 자동 표시.

### minutes (회의록) — base + 추가

| ID | 유형 | 설명 |
|----|------|------|
| charPr 7 | 글자 | 18pt 볼드 (제목) |
| charPr 8 | 글자 | 12pt 볼드 (섹션 라벨) |
| charPr 9 | 글자 | 10pt 볼드 (표 헤더) |
| paraPr 20~22 | 문단 | CENTER/JUSTIFY 변형 |
| borderFill 3 | 테두리 | SOLID 0.12mm 4면 |
| borderFill 4 | 테두리 | SOLID 0.12mm + #E2EFDA 배경 |

### proposal (제안서/사업개요) — base + 추가

시각적 구분이 필요한 공식 문서용. 색상 배경 헤더바와 번호 배지를 표(table) 기반 레이아웃으로 구현.

| ID | 유형 | 설명 |
|----|------|------|
| charPr 7 | 글자 | 20pt 볼드 함초롬바탕 (문서 제목) |
| charPr 8 | 글자 | 14pt 볼드 함초롬바탕 (소제목) |
| charPr 9 | 글자 | 10pt 볼드 함초롬바탕 (표 헤더) |
| charPr 10 | 글자 | 14pt 볼드 흰색 함초롬돋움 (대항목 번호, 녹색 배경) |
| charPr 11 | 글자 | 11pt 볼드 흰색 함초롬돋움 (소항목 번호, 파란 배경) |
| paraPr 20 | 문단 | CENTER, 160% 줄간격 |
| paraPr 21 | 문단 | CENTER, 130% (표 셀) |
| paraPr 22 | 문단 | JUSTIFY, 130% (표 셀) |
| borderFill 3 | 테두리 | SOLID 0.12mm 4면 |
| borderFill 4 | 테두리 | SOLID 0.12mm + #DAEEF3 배경 |
| borderFill 5 | 테두리 | 올리브녹색 배경 #7B8B3D (대항목 번호 셀) |
| borderFill 6 | 테두리 | 연한 회색 배경 #F2F2F2 + 회색 테두리 (대항목 제목 셀) |
| borderFill 7 | 테두리 | 파란색 배경 #4472C4 (소항목 번호 배지) |
| borderFill 8 | 테두리 | 하단 테두리만 #D0D0D0 (소항목 제목 영역) |

#### proposal 레이아웃 패턴

**대항목 헤더** (2셀 표: 번호 + 제목):
```xml
<!-- borderFillIDRef="5" + charPrIDRef="10" → 녹색배경 흰색 로마숫자 -->
<!-- borderFillIDRef="6" + charPrIDRef="8"  → 회색배경 검정 볼드 제목 -->
```

**소항목 헤더** (2셀 표: 번호배지 + 제목):
```xml
<!-- borderFillIDRef="7" + charPrIDRef="11" → 파란배경 흰색 아라비아숫자 -->
<!-- borderFillIDRef="8" + charPrIDRef="8"  → 하단선만 검정 볼드 제목 -->
```

---

## 워크플로우 2: 기존 문서 편집 (unpack → Edit → pack)

```bash
source "$VENV"

# 1. HWPX → 디렉토리 (XML pretty-print)
python "$SKILL_DIR/scripts/office/unpack.py" document.hwpx ./unpacked/

# 2. XML 직접 편집 (Claude가 Read/Edit 도구로)
#    본문: ./unpacked/Contents/section0.xml
#    스타일: ./unpacked/Contents/header.xml

# 3. 다시 HWPX로 패키징
python "$SKILL_DIR/scripts/office/pack.py" ./unpacked/ edited.hwpx

# 4. 검증
python "$SKILL_DIR/scripts/validate.py" edited.hwpx
```

### 빈 서식(표)을 채울 때 — 실측 함정 3가지

`validate.py`가 통과해도 화면에서 깨진다. 아래 셋은 XML만 봐서는 안 보인다.

1. **`hp:linesegarray`는 줄 수만큼 있어야 한다.** 문단 하나에 `hp:lineseg`를 한 개만 넣고 긴 텍스트를 담으면, 한글이 여러 줄을 **같은 자리에 겹쳐 그린다**(글자가 뭉개진 한 줄로 보임). 가장 안전한 대응은 **한 문단 = 한 줄이 되게 텍스트를 끊는 것**이다. 줄 수만큼 lineseg를 만들려면 각 줄의 시작 문자 위치(`textpos`)까지 맞아야 하는데, 그 계산이 틀리면 같은 증상이 다시 난다.
2. **칸 높이는 고정이다.** `hp:cellSz height`를 넘기면 칸이 자라 페이지가 밀린다. 넣기 전에 칸마다 용량을 계산한다 — 줄 수 = `(height - 위아래여백) / 줄간격(보통 1760)`, 한 줄 글자 폭 = `cellSz width - cellMargin 좌우`, 한글 한 자 ≈ `charPr height`, 라틴·숫자 ≈ 0.55배, 공백 ≈ 0.35배. `page_guard.py`는 이걸 못 본다(문단 수·전체 글자 수만 비교하므로 빈 서식을 채우면 무조건 FAIL이 뜬다 — 이 경우 FAIL은 무시하고 칸 계산으로 판정한다).
3. **찾는 문자열이 `hp:t`의 `text`에 없을 수 있다** — 원본은 위 「항상 지키는 것 B」. 이 함정은 XML 직접 편집만의 것이 아니라서 그리로 올렸다.

**이미지 삽입**은 세 곳을 같이 손봐야 한다 — `BinData/`에 파일 넣기 + `Contents/content.hpf` 매니페스트에 `opf:item` 추가 + 문단에 `hp:pic`(`hc:img binaryItemIDRef`가 매니페스트 id와 일치) 삽입. 사진 방향은 EXIF가 없으면 눈으로 봐야 한다 — **네 방향을 한 장에 붙여 한 번에 비교**하면 확실하다(작은 미리보기 하나만 보고 판정하면 180도를 놓친다).

---

## 워크플로우 3: 읽기/텍스트 추출

```bash
source "$VENV"

# 순수 텍스트 (표 포함이 기본)
python "$SKILL_DIR/scripts/text_extract.py" document.hwpx

# 마크다운 형식
python "$SKILL_DIR/scripts/text_extract.py" document.hwpx --format markdown

# 표를 일부러 뺄 때만 (경고가 찍힌다)
python "$SKILL_DIR/scripts/text_extract.py" document.hwpx --no-tables
```

읽은 결과로 "이 말이 문서에 없다"를 판정하기 전에 위 「항상 지키는 것 A·B」를 먼저 본다.

### Python API

`TextExtractor` 경로를 쓴다 — `doc.text.plain()` 계열은 탭 뒤 글자를 놓친다(「항상 지키는 것 B」).

```python
from hwpx import TextExtractor
with TextExtractor("document.hwpx") as ext:
    text = ext.extract_text(include_nested=True, object_behavior="nested")
    print(text)
```

---

## 워크플로우 4: 검증

```bash
source "$VENV"
python "$SKILL_DIR/scripts/validate.py" document.hwpx
```

검증 항목: ZIP 유효성, 필수 파일 존재, mimetype 내용/위치/압축방식, XML well-formedness

---

## 워크플로우 5: 레퍼런스 기반 문서 생성 (첨부 HWPX가 있을 때 기본 적용)

사용자가 제공한 HWPX 파일을 분석하여 동일한 레이아웃의 문서를 생성하는 워크플로우.
이 스킬에서는 첨부 레퍼런스가 존재하면 본 워크플로우를 기본으로 사용한다.

### 흐름

1. **분석** — `analyze_template.py`로 레퍼런스 문서 심층 분석
2. **header.xml 추출** — 레퍼런스의 스타일 정의를 그대로 사용
3. **section0.xml 작성** — 분석 결과의 구조를 따라 새 내용으로 작성
4. **빌드** — 추출한 header.xml + 새 section0.xml로 빌드
5. **검증** — `validate.py`
6. **쪽수 가드** — `page_guard.py` (실패 시 재수정)

### 사용법

```bash
source "$VENV"

# 1. 심층 분석 (구조 청사진 출력)
python "$SKILL_DIR/scripts/analyze_template.py" reference.hwpx

# 2. header.xml과 section0.xml을 추출하여 참고용으로 보관
python "$SKILL_DIR/scripts/analyze_template.py" reference.hwpx \
  --extract-header /tmp/ref_header.xml \
  --extract-section /tmp/ref_section.xml

# 3. 분석 결과를 보고 새 section0.xml 작성
#    - 동일한 charPrIDRef, paraPrIDRef 사용
#    - 동일한 테이블 구조 (열 수, 열 너비, 행 수, rowSpan/colSpan)
#    - 동일한 borderFillIDRef, cellMargin

# 4. 추출한 header.xml + 새 section0.xml로 빌드
python "$SKILL_DIR/scripts/build_hwpx.py" \
  --header /tmp/ref_header.xml \
  --section /tmp/new_section0.xml \
  --output result.hwpx

# 5. 검증
python "$SKILL_DIR/scripts/validate.py" result.hwpx

# 6. 쪽수 드리프트 가드 (필수)
python "$SKILL_DIR/scripts/page_guard.py" \
  --reference reference.hwpx \
  --output result.hwpx
```

### 분석 출력 항목

| 항목 | 설명 |
|------|------|
| 폰트 정의 | hangul/latin 폰트 매핑 |
| borderFill | 테두리 타입/두께 + 배경색 (각 면별 상세) |
| charPr | 글꼴 크기(pt), 폰트명, 색상, 볼드/이탤릭/밑줄/취소선, fontRef |
| paraPr | 정렬, 줄간격, 여백(left/right/prev/next/intent), heading, borderFillIDRef |
| 문서 구조 | 페이지 크기, 여백, 페이지 테두리, 본문폭 |
| 본문 상세 | 모든 문단의 id/paraPr/charPr + 텍스트 내용 |
| 표 상세 | 행×열, 열너비 배열, 셀별 span/margin/borderFill/vertAlign + 내용 |

### 핵심 원칙

- **charPrIDRef/paraPrIDRef를 그대로 사용**: 추출한 header.xml의 스타일 ID를 변경하지 말 것
- **열 너비 합계 = 본문폭**: 분석 결과의 열너비 배열을 그대로 복제
- **rowSpan/colSpan 패턴 유지**: 분석된 셀 병합 구조를 정확히 재현
- **cellMargin 보존**: 분석된 셀 여백 값을 동일하게 적용
- **페이지 증가 금지**: 사용자 명시 승인 없이 결과 쪽수를 늘리지 말 것
- **치환 우선 편집**: 새 문단/표 추가보다 기존 텍스트 노드 치환을 우선할 것

---

## 스크립트 요약

| 스크립트 | 용도 |
|----------|------|
| `scripts/build_hwpx.py` | **핵심** — 템플릿 + XML → HWPX 조립 |
| `scripts/analyze_template.py` | HWPX 심층 분석 (레퍼런스 기반 생성의 청사진) |
| `scripts/office/unpack.py` | HWPX → 디렉토리 (XML pretty-print) |
| `scripts/office/pack.py` | 디렉토리 → HWPX (mimetype first) |
| `scripts/validate.py` | HWPX 파일 구조 검증 |
| `scripts/page_guard.py` | 레퍼런스 대비 페이지 드리프트 위험 검사 (필수 게이트) |
| `scripts/text_extract.py` | HWPX 텍스트 추출 |

## 단위 변환

| 값 | HWPUNIT | 의미 |
|----|---------|------|
| 1pt | 100 | 기본 단위 |
| 10pt | 1000 | 기본 글자크기 |
| 1mm | 283.5 | 밀리미터 |
| 1cm | 2835 | 센티미터 |
| A4 폭 | 59528 | 210mm |
| A4 높이 | 84186 | 297mm |
| 좌우여백 | 8504 | 30mm |
| 본문폭 | 42520 | 150mm (A4-좌우여백) |

## Critical Rules

1. **`.hwp`가 오면 먼저 `.hwpx`로 바꾼다** — 절차는 「워크플로우 0」(맥은 사용자에게 안내, 윈도우+한글은 `pyhwpx`). 이 스킬의 나머지는 전부 `.hwpx` 기준이다.
2. **secPr 필수**: section0.xml 첫 문단의 첫 run에 반드시 secPr + colPr 포함
3. **mimetype 순서**: HWPX 패키징 시 mimetype은 첫 번째 ZIP 엔트리, ZIP_STORED
4. **네임스페이스 보존**: XML 편집 시 `hp:`, `hs:`, `hh:`, `hc:` 접두사 유지
5. **itemCnt 정합성**: header.xml의 charProperties/paraProperties/borderFills itemCnt가 실제 자식 수와 일치
6. **ID 참조 정합성**: section0.xml의 charPrIDRef/paraPrIDRef가 header.xml 정의와 일치
7. **venv 사용**: `source .claude/venv.sh`로 활성화한 뒤 `python`. 필요한 패키지는 `scripts/requirements.txt`가 원본이고, 설치 방법은 위 「환경 › 설치」. 가상환경 경로는 OS마다 다르므로 직접 적지 않는다
8. **검증**: 생성 후 반드시 `validate.py`로 무결성 확인
9. **레퍼런스**: 상세 XML 구조는 `$SKILL_DIR/references/hwpx-format.md` 참조
10. **build_hwpx.py 우선**: 새 문서 생성은 build_hwpx.py 사용 (python-hwpx API 직접 호출 지양)
11. **빈 줄**: `<hp:t/>` 사용 (self-closing tag)
12. **레퍼런스 우선 강제**: 사용자가 HWPX를 첨부하면 반드시 `analyze_template.py` + 추출 XML 기반으로 복원/재작성할 것
13. **examples 폴더 미사용**: 작업 중 `.claude/skills/hwpxskill/examples/*` 파일은 읽기/참조/복사에 사용하지 말 것
14. **쪽수 동일 필수**: 레퍼런스 기반 작업에서는 최종 결과의 쪽수를 레퍼런스와 동일하게 유지할 것
15. **무단 페이지 증가 금지**: 사용자 명시 요청/승인 없이 쪽수 증가를 유발하는 구조 변경 금지
16. **구조 변경 제한**: 사용자 요청이 없는 한 문단/표의 추가·삭제·분할·병합 금지 (치환 중심 편집)
17. **page_guard 필수 통과**: `validate.py`와 별개로 `page_guard.py`를 반드시 통과해야 완료 처리

---

Made by Do Better Things
