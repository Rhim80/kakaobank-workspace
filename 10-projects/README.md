# 10-projects

> **시한부 프로젝트.** 시작일과 종료일이 있음. 완료되면 `90-archive/`로 이동.

## 네이밍

```
[숫자]-[설명적-이름]

✅ 11-website-redesign
✅ 12-product-launch-q2
❌ my-project (숫자 없음)
```

- 11~19 사이 숫자 사용
- 더 많은 프로젝트가 있으면 `11.01-subA`, `11.02-subB` 식으로 2단계 확장

## 프로젝트 폴더 구조 예시

```
10-projects/
├── 11-website-redesign/
│   ├── README.md         # 프로젝트 개요
│   ├── requirements.md   # 요구사항
│   ├── progress.md       # 진행 로그
│   └── artifacts/        # 산출물
├── 12-product-launch/
└── 13-marketing-campaign/
```

## Do Better Drive 진행

Do Better Drive(`do-better-drive` 스킬)로 진행하는 프로젝트는 폴더 안 `progress.md`가 **진행의 단일 기준**이다. ① 프레임 단계가 이 파일을 만들며, 형식은 고정이다. (처음이면 초심자 안내: `00-system/03-guides/do-better-drive-사용법.md`)

- frontmatter `status`: `프레임 → 범위 → 계획 → 생산 → 리뷰 → 발행 → 완료` (막히면 `보류`) — 지금 어느 단계인지의 기준
- 섹션: `목표`(1단계) · `실현성 점검`(2단계) · `계획`+`합격 기준`(3단계) · `생산`(4단계) · `검토`(5단계) · `지금 상태` · `다음 한 걸음` · `로그`

각 단계 스킬이 자기 섹션만 채우고 다음 단계로 넘긴다. 아래 `project-template.md`(프로젝트 개요용)와 별개다 — Drive 프로젝트는 이 progress.md를 기준으로 쓴다.

## 완료 처리

프로젝트가 끝나면:
1. 산출물 정리
2. 회고를 `40-personal/44-reflections/`에 작성
3. 재사용 가능한 지식을 `30-knowledge/` 또는 `00-wiki/`로 승격
4. 폴더 통째로 `90-archive/YYYY-QX/`로 이동
