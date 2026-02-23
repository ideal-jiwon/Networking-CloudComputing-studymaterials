# 중간고사 준비 시스템 (Midterm Study System)

강의 자료에서 추출한 개념과 시나리오 기반 연습 문제를 활용하여 중간고사를 준비하는 대화형 학습 시스템입니다.
API 없이 사전 생성된 JSON 데이터 파일만으로 동작합니다.

## 주요 기능

- **PDF 텍스트 추출**: 강의 PDF에서 텍스트 자동 추출
- **개념 관리**: JSON 파일로 핵심 개념 구조화 및 관리
- **시나리오 기반 문제**: 실제 상황을 기반으로 한 연습 문제 제공
- **대화형 학습 인터페이스**: CLI 기반 학습 세션 (rich 라이브러리 활용)
- **키워드 기반 피드백**: 답변 키워드 매칭을 통한 자동 평가 및 한국어 피드백
- **학습 진행률 추적**: 개념별/주제별 커버리지 통계
- **주제 필터링**: 특정 주제만 선택하여 집중 학습 가능

## 설치 방법

### 사전 요구사항

- Python 3.8 이상

### 설치

1. 저장소를 클론하거나 다운로드합니다.

2. 가상환경을 생성하고 활성화합니다:
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
```

3. 의존성을 설치합니다:
```bash
pip install -r requirements.txt
```

4. 강의 PDF 파일을 `classmaterials/` 디렉토리에 넣습니다.

## 디렉토리 구조

```
midterm-study-system/
├── src/                        # 소스 코드
│   ├── models.py              # 데이터 모델 (Concept, Question, Feedback 등)
│   ├── pdf_processor.py       # PDF 텍스트 추출
│   ├── data_loader.py         # JSON 데이터 로딩 및 검증
│   ├── content_store.py       # 데이터 저장/조회 (JSON 기반)
│   ├── answer_evaluator.py    # 키워드 매칭 기반 답변 평가
│   ├── coverage_tracker.py    # 학습 진행률 추적
│   ├── study_interface.py     # CLI 학습 인터페이스
│   └── topic_validator.py     # 주제 커버리지 검증
├── data/                       # 데이터 파일
│   ├── concepts.json          # 핵심 개념 데이터
│   ├── questions.json         # 시나리오 기반 문제
│   ├── feedback_templates.json # 피드백 템플릿
│   └── extracted_text/        # PDF에서 추출한 텍스트
├── tests/                      # 테스트 파일
├── classmaterials/             # 강의 PDF 파일
├── main.py                     # 메인 진입점 (CLI)
├── prepare_data.py             # 데이터 준비 도구
└── requirements.txt            # Python 의존성
```

## 사용 방법

### 1. 데이터 로드 확인 (`load`)

개념과 질문 데이터를 로드하고 요약을 표시합니다:
```bash
python main.py load
```

출력 예시:
```
📚 데이터 로딩 결과
  개념: 61개 로드 완료
  질문: 30개 로드 완료
  피드백 템플릿: 로드 완료

주제별 데이터 분포
  Cloud Computing          4개 개념   2개 질문
  DevOps                   3개 개념   2개 질문
  Networking               6개 개념   3개 질문
  ...
```

### 2. 학습 세션 시작 (`study`)

대화형 학습 세션을 시작합니다:
```bash
python main.py study
```

학습 세션에서 사용 가능한 명령어:
- 답변 입력 후 Enter → 피드백 확인
- `다음` 또는 `n` → 다음 질문으로 이동
- `진행` 또는 `p` → 학습 진행률 확인
- `주제` 또는 `t` → 특정 주제 선택하여 필터링
- `건너뛰기` 또는 `s` → 현재 질문 건너뛰기
- `종료` 또는 `q` → 학습 세션 종료 (진행률 자동 저장)

### 3. 학습 진행률 확인 (`stats`)

학습 진행률 통계를 표시합니다:
```bash
python main.py stats
```

출력 예시:
```
📊 학습 진행률
  15/61 개념 완료 (24.6%)

주제별 진행 상황
  Cloud Computing          50%   진행 중
  DevOps                   100%  ✓ 완료
  Networking               0%    미시작
  ...
```

### 4. 데이터 검증 (`validate`)

데이터 파일의 완전성과 무결성을 검증합니다:
```bash
python main.py validate
```

검증 항목:
- 개념/질문 데이터의 필수 필드 확인
- 개념-질문 간 참조 무결성 확인
- 주제별 커버리지 확인 (classtopics.md 기준)

## 데이터 준비 도구 (`prepare_data.py`)

### PDF 텍스트 추출
```bash
python prepare_data.py extract
```

### 템플릿 파일 생성
```bash
python prepare_data.py template
```

### samplequestions.md 파싱
```bash
python prepare_data.py format-questions
```

### 데이터 검증
```bash
python prepare_data.py validate
```

## 데이터 파일 형식

### concepts.json

핵심 개념 목록입니다. 각 개념은 다음 필드를 포함합니다:

```json
[
  {
    "id": "c-cloud-001",
    "name": "클라우드 컴퓨팅 (Cloud Computing)",
    "definition": "인터넷을 통해 컴퓨팅 리소스를 온디맨드로 제공하는 서비스 모델",
    "context": "Cloud computing is the delivery of computing services over the internet.",
    "source_file": "L01_01_Fundamentals of Cloud Computing_pdf.pdf",
    "topic_area": "Fundamentals of Cloud Computing",
    "related_concepts": ["c-cloud-002", "c-cloud-003"],
    "keywords": ["cloud", "computing", "클라우드", "서비스모델"]
  }
]
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | string | 고유 식별자 (형식: `c-{주제}-{번호}`) |
| `name` | string | 개념 이름 (한국어 + 영어) |
| `definition` | string | 한국어 정의 |
| `context` | string | 영어 맥락 설명 |
| `source_file` | string | 출처 PDF 파일명 |
| `topic_area` | string | 주제 영역 (classtopics.md와 일치) |
| `related_concepts` | list[string] | 관련 개념 ID 목록 |
| `keywords` | list[string] | 검색 키워드 (한국어 + 영어) |

### questions.json

시나리오 기반 연습 문제 목록입니다:

```json
[
  {
    "id": "q001",
    "concept_ids": ["c-network-003"],
    "scenario": "Sarah is building two applications: a banking portal...",
    "question_text": "Explain the key differences between TCP and UDP...",
    "model_answer": "TCP is connection-oriented, provides reliable ordered delivery...",
    "difficulty": "medium",
    "topic_area": "Networking Fundamentals"
  }
]
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | string | 고유 식별자 (형식: `q{번호}`) |
| `concept_ids` | list[string] | 관련 개념 ID 목록 (1개 이상 필수) |
| `scenario` | string | 실제 상황 시나리오 |
| `question_text` | string | 질문 텍스트 |
| `model_answer` | string | 모범 답안 |
| `difficulty` | string | 난이도 (`basic`, `medium`, `hard`) |
| `topic_area` | string | 주제 영역 |

### feedback_templates.json

피드백 생성에 사용되는 템플릿입니다:

```json
{
  "correct": {
    "message_korean": "훌륭합니다! 정확하게 이해하고 계십니다.",
    "message_english": "Excellent! You have a correct understanding."
  },
  "partially_correct": {
    "message_korean": "좋은 시작입니다! 몇 가지 추가 사항이 있습니다.",
    "guidance_korean": "다음 개념들을 더 검토해보세요:"
  },
  "incorrect": {
    "message_korean": "다시 한번 생각해보세요.",
    "guidance_korean": "다음 개념들을 복습하는 것이 도움이 될 것입니다:"
  },
  "scoring_thresholds": {
    "correct": { "min_score": 80 },
    "partially_correct": { "min_score": 40 },
    "incorrect": { "min_score": 0 }
  }
}
```

주요 섹션:
- `correct` / `partially_correct` / `incorrect`: 점수 범위별 피드백 메시지
- `common_mistakes`: 주제별 흔한 실수와 교정 내용
- `feedback_templates_by_topic`: 주제별 핵심 학습 포인트
- `scoring_thresholds`: 점수 구간 설정 (정답: 80+, 부분 정답: 40-79, 오답: 0-39)

## 학습 세션 예시

```
=== 중간고사 준비 시스템 ===

📚 데이터 로딩 완료: 61개 개념, 30개 질문

[질문 1/30]

시나리오:
Sarah is building two applications: a banking portal where every
transaction must be reliably delivered, and a live sports score
ticker where speed matters more than perfection.

질문:
Explain the key differences between TCP and UDP that would help
Sarah make her decision. Which protocol should she choose for
each application, and why?

답변을 입력하세요 (완료하려면 빈 줄에서 Enter):
> TCP는 연결 지향적 프로토콜로 신뢰성 있는 데이터 전송을 보장합니다.
> 3-way handshake를 통해 연결을 설정하고, 패킷 손실 시 재전송합니다.
> UDP는 비연결형으로 빠르지만 전송 보장이 없습니다.
> 은행 포털은 TCP, 스포츠 티커는 UDP를 사용해야 합니다.
>

[피드백]
점수: 75/100

좋은 시작입니다! 핵심 개념은 이해하고 있지만, 몇 가지 추가 사항이 있습니다.

잘한 점:
  ✓ TCP의 연결 지향적 특성 언급
  ✓ 3-way handshake 언급
  ✓ 올바른 프로토콜 선택

보완할 점:
  • TCP의 오류 검사와 순서 보장에 대해 더 설명 필요
  • UDP의 낮은 오버헤드 장점 언급 필요

관련 개념: TCP vs UDP, 네트워킹 기초

모범 답안:
TCP is connection-oriented, provides reliable ordered delivery
with error checking and retransmission (3-way handshake: SYN,
SYN-ACK, ACK). UDP is connectionless, faster but no delivery/
ordering guarantees...

다음 질문으로 이동하시겠습니까? (y/n): y
```

## 다루는 주제

시스템은 다음 주제를 포함합니다 (classtopics.md 기준):

- Fundamentals of Cloud Computing
- The Software Development Life Cycle (SDLC)
- The Twelve-Factor App
- Introduction to DevOps
- The Linux Command Line
- Cloud Regions & Availability Zones
- Unit, Integration, Performance, and Load Testing
- Continuous Integration with GitHub Actions
- Version Control with Git
- Git Forking Workflow
- Networking Fundamentals
- Infrastructure as Code w/Terraform
- Identity & Access Management (IAM)
- Network Firewall
- Virtual Machines
- Custom Machine Images
- cloud-init
- systemd - System and Service Manager

## 개발

### 테스트 실행

전체 테스트 실행:
```bash
pytest tests/ -v
```

커버리지 포함:
```bash
pytest tests/ --cov=src -v
```

Property-based 테스트 통계:
```bash
pytest tests/ -v --hypothesis-show-statistics
```

### 테스트 전략

- **단위 테스트 (Unit Tests)**: 각 컴포넌트의 구체적 동작 검증
- **Property-based 테스트**: Hypothesis 라이브러리를 활용한 범용 속성 검증
- **통합 테스트**: 컴포넌트 간 데이터 흐름 검증

## 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다.

python main.py load — verify your data loads correctly (61 concepts, 30 questions)
python main.py stats — check your study progress anytime
python main.py validate — make sure all data files are complete