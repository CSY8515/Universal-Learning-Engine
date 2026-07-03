# Universal Learning Engine v0.2

Universal Learning Engine v0.2는 학습 주제를 입력하면 같은 학습 흐름으로 튜토리얼, 예제, 실습, CBT를 생성하는 Streamlit 기반 학습 MVP입니다.

이번 버전의 목표는 완성형 학습 서비스가 아니라, 범용 학습 엔진이 실제로 동작하는 흐름을 검증하는 것입니다.

## 현재 구현된 기능

- 학습 주제 입력
- 입력 검증
  - 빈 입력 차단
  - 공백 입력 차단
  - 너무 긴 입력 차단
- 문제 수 선택
  - 5문제
  - 10문제
  - 15문제
  - 20문제
- 난이도 선택
  - 입문
  - 초급
  - 중급
- OpenAI API를 통한 학습 내용 생성
- JSON 응답 파싱
- 튜토리얼
- 예제
- 직접 구현 / 직접 작성
- 실습
- CBT 진행
  - 한 문제씩 표시
  - 답안 선택
  - 정답 확인
  - 정답 / 오답 표시
  - 해설 표시
  - 다음 문제 이동
  - 마지막 문제 후 결과 보기
- 학습 진행률 표시
  - 현재 문제 / 전체 문제
  - Progress Bar
- 결과 화면
  - 총 문제 수
  - 정답 수
  - 오답 수
  - 정답률
  - 다시 학습
  - 처음으로
- OpenAI 응답 오류 안내
- JSON 파싱 오류 안내
- 문제 수 불일치 처리
  - 부족하면 안내 후 생성된 문제로 진행
  - 많으면 요청한 문제 수만 사용
  - 0개면 학습 시작 중단

## 향후 예정

아래 기능은 v0.2에 구현되어 있지 않습니다. 향후 버전에서 검토할 예정입니다.

- Recovery Engine
- Learning Analytics
- Learning Report
- Weakness Score
- Recovery Priority
- Learning Decision Engine
- Dashboard
- Expansion Pack
- AI 추천
- 난이도 자동 조절
- 사용자 맞춤 학습
- 복습 스케줄
- 데이터 저장
- 로그인

## 설치 방법

```bash
pip install -r requirements.txt
```

## 실행 방법

```bash
streamlit run app.py
```

## OpenAI API Key 설정

API Key는 코드에 직접 넣지 않습니다.

앱은 아래 순서로 API Key를 읽습니다.

1. 로컬 `.env`
2. 환경 변수 `OPENAI_API_KEY`
3. Streamlit Cloud Secrets

### 로컬 실행

`.env.example` 파일을 복사해서 `.env` 파일을 만듭니다.

```bash
copy .env.example .env
```

`.env` 파일에 실제 API Key를 입력합니다.

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

`.env` 파일은 `.gitignore`에 포함되어 있으므로 GitHub에 올리지 않습니다.

### Streamlit Cloud 실행

Streamlit Cloud의 App Settings > Secrets에 아래 값을 추가합니다.

```toml
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_MODEL = "gpt-4.1-mini"
```

참고용 예시는 `.streamlit/secrets.toml.example` 파일에 있습니다.

## Streamlit Cloud 배포 설정

Main file path:

```text
app.py
```

## 프로젝트 구조

```text
Universal_Learning_Engine/
├─ app.py
├─ requirements.txt
├─ README.md
├─ .env.example
├─ .gitignore
└─ .streamlit/
   ├─ config.toml
   └─ secrets.toml.example
```

## v0.2 Release Candidate 기준

- 기존 단일 `app.py` 중심 구조 유지
- Streamlit Cloud 배포 가능
- OpenAI API Key 하드코딩 없음
- CBT 흐름 안정화
- Recovery / Analytics / Dashboard / Expansion Pack 미구현
- 배포 전 실제 API Key 환경에서 최종 수동 테스트 권장
