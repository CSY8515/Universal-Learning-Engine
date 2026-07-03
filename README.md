# Universal Learning Engine v0.2

Universal Learning Engine v0.2는 학습할 주제를 입력하면 동일한 학습 엔진이 해당 주제에 맞게 학습 흐름을 생성하는 Streamlit MVP입니다.

## 현재 구현된 기능

- 학습 주제 입력
- 입력 검증
  - 빈 입력 차단
  - 공백 입력 차단
  - 80자 초과 입력 차단
- OpenAI API를 통한 학습 내용 생성
- 튜토리얼
- 예제
- 직접 구현 / 직접 작성
- 실습
- CBT 5문제
- 오답노트
- 해설
- 학습 종료 메시지
- JSON 응답 형식 오류 안내
- OpenAI API 호출 오류 안내
- 응답 데이터 구조 오류 안내

## 구현하지 않은 기능

- Adaptive Difficulty
- Learning Analytics
- Learning Report
- Weakness Score
- Recovery Priority
- Learning Decision Engine
- Dashboard
- Expansion Pack
- AI 추천
- 난이도 조절
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

앱은 아래 순서로 API 키를 읽습니다.

1. 로컬 `.env`
2. 환경 변수 `OPENAI_API_KEY`
3. Streamlit Cloud Secrets

### 로컬 실행

`.env.example` 파일을 복사해서 `.env` 파일을 만듭니다.

```bash
copy .env.example .env
```

`.env` 파일에 실제 API 키를 입력합니다.

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

`.env` 파일은 `.gitignore`에 포함되어 있으므로 GitHub에 올리지 않습니다.

### Streamlit Cloud 실행

Streamlit Cloud의 App Settings → Secrets에 아래 값을 추가합니다.

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
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

## v0.2 원칙

- MVP 범위 유지
- 기존 Learning Flow 유지
- CBT 5문제 구조 유지
- Expansion Pack 미구현
- 데이터 저장 미구현
- 로그인 미구현
- 실행 안정성 우선
