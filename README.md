# Universal Learning Engine v0.1

Universal Learning Engine의 최초 공개 MVP입니다.

목표는 하나입니다.

> 학습할 주제를 입력하면 동일한 학습 엔진이 해당 주제에 맞게 동작한다.

## 포함 기능

- 주제 입력
- 튜토리얼
- 예제
- 직접 구현 / 직접 작성
- 실습
- CBT 5문제
- 오답노트
- 해설
- 학습 종료 메시지

## 제외 기능

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

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

## OpenAI API 설정

앱은 아래 순서로 API 키를 읽습니다.

1. 로컬 `.env`
2. 환경 변수 `OPENAI_API_KEY`
3. Streamlit Cloud Secrets

### 로컬 실행

`.env.example` 파일을 복사해서 `.env` 파일을 만듭니다.

```bash
copy .env.example .env
```

`.env` 파일 안의 값을 본인 키로 바꿉니다.

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

## 배포 파일

Streamlit Cloud의 Main file path:

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
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

## v0.1 원칙

- MVP만 구현
- 확장 기능 구현 금지
- 디자인보다 동작 우선
- 하나의 엔진으로 모든 학습 주제 처리
- 주제별 하드코딩 금지
