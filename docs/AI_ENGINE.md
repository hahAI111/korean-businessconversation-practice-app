# 🧠 AI Engine Deep-Dive / AI 엔진 심층 분석

> How the AI teaching system works — GPT Agent, MCP tools, voice pipeline, and instruction design.
>
> AI 교육 시스템의 작동 방식 — GPT 에이전트, MCP 도구, 음성 파이프라인, 지시문 설계.

---

## Table of Contents / 목차

1. [Architecture Overview / 아키텍처 개요](#1-architecture-overview--아키텍처-개요)
2. [Azure AI Foundry Agent / Azure AI Foundry 에이전트](#2-azure-ai-foundry-agent--azure-ai-foundry-에이전트)
3. [Instruction Design / 지시문 설계](#3-instruction-design--지시문-설계)
4. [MCP Tools System / MCP 도구 시스템](#4-mcp-tools-system--mcp-도구-시스템)
5. [Voice Pipeline / 음성 파이프라인](#5-voice-pipeline--음성-파이프라인)
6. [Thread & Context Management / 스레드 & 컨텍스트 관리](#6-thread--context-management--스레드--컨텍스트-관리)
7. [Agent Fallback Strategy / 에이전트 대체 전략](#7-agent-fallback-strategy--에이전트-대체-전략)

---

## 1. Architecture Overview / 아키텍처 개요

The AI engine has two modes: **text** and **voice**, each with different instruction sets and processing pipelines.

AI 엔진에는 **텍스트**와 **음성** 두 가지 모드가 있으며, 각각 다른 지시문과 처리 파이프라인을 사용합니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                       AI Engine / AI 엔진                        │
│                                                                  │
│   ┌──────────────────────┐    ┌──────────────────────┐          │
│   │   Text Mode          │    │   Voice Mode         │          │
│   │   텍스트 모드         │    │   음성 모드           │          │
│   │                      │    │                      │          │
│   │  TEXT_INSTRUCTIONS   │    │  VOICE_INSTRUCTIONS  │          │
│   │  (600+ lines)        │    │  (150+ lines)        │          │
│   │  Comprehensive       │    │  수진 (Sujin)        │          │
│   │  teaching doctrine   │    │  Short, warm voice   │          │
│   │  종합 교육 교리       │    │  짧고 따뜻한 음성     │          │
│   │                      │    │                      │          │
│   │  → Long, detailed    │    │  → Short, 1-3        │          │
│   │    responses with    │    │    sentences in       │          │
│   │    dialogues,        │    │    Korean + English   │          │
│   │    grammar notes     │    │    translation        │          │
│   │  → 대화, 문법 포함    │    │  → 한국어 1-3문장 +   │          │
│   │    긴 상세 응답       │    │    영어 번역           │          │
│   └──────────┬───────────┘    └──────────┬───────────┘          │
│              │                           │                       │
│              └─────────┬─────────────────┘                       │
│                        │                                         │
│              ┌─────────▼─────────┐                               │
│              │  Azure AI Foundry │                               │
│              │  Responses API    │                               │
│              │  (GPT model)      │                               │
│              │                   │                               │
│              │  + 9 MCP Tools    │                               │
│              │  + Thread Context │                               │
│              └───────────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Azure AI Foundry Agent / Azure AI Foundry 에이전트

### 2.1 How It Works / 작동 방식

The agent uses **Azure AI Foundry's Responses API** — a newer API that replaces the older Assistants API. It provides:
- Agent-level instructions (system prompt) / 에이전트 수준 지시문
- Thread-based conversation continuity via `previous_response_id` / 스레드 기반 대화 연속성
- Tool integration (MCP tools) / 도구 통합

에이전트는 **Azure AI Foundry의 Responses API**를 사용합니다 — 이전 Assistants API를 대체하는 최신 API입니다.

### 2.2 AgentService Class / AgentService 클래스

```python
class AgentService:
    """Singleton service for Azure AI Foundry agent interaction
       Azure AI Foundry 에이전트 상호작용을 위한 싱글턴 서비스"""
    
    def __init__(self):
        self._client = None           # AzureOpenAI client
        self._responses = {}          # {thread_id: previous_response_id}
    
    async def _ensure_client(self):
        """Lazily create AzureOpenAI client with Managed Identity
           관리 ID로 AzureOpenAI 클라이언트를 지연 생성"""
        # DefaultAzureCredential → get_bearer_token_provider
        # Scope: "https://cognitiveservices.azure.com/.default"
    
    def create_thread(self) -> str:
        """Generate unique thread ID / 고유 스레드 ID 생성"""
        return f"thread_{uuid.uuid4().hex[:16]}"
    
    async def _call_agent(self, thread_id, user_msg, agent_name, instructions):
        """Core method — calls GPT with agent_reference or instructions
           핵심 메서드 — agent_reference 또는 instructions로 GPT 호출"""
        # 1. Try: agent_reference mode (Portal-configured agent)
        #    시도: agent_reference 모드 (포털 설정 에이전트)
        # 2. Fallback: instructions mode (inline system prompt)
        #    대체: instructions 모드 (인라인 시스템 프롬프트)
        # 3. Pass previous_response_id for context continuity
        #    컨텍스트 연속성을 위해 previous_response_id 전달
    
    async def chat(self, thread_id, user_msg) -> str:
        """Text mode — uses TEXT_INSTRUCTIONS / 텍스트 모드"""
    
    async def voice_chat(self, thread_id, user_msg) -> str:
        """Voice mode — uses VOICE_INSTRUCTIONS / 음성 모드"""
```

### 2.3 API Call Flow / API 호출 흐름

```
_call_agent(thread_id, user_msg, agent_name, instructions)
    │
    ├─ Build kwargs: / 매개변수 구성:
    │   model = settings.MODEL_DEPLOYMENT
    │   input = user_msg
    │   previous_response_id = self._responses.get(thread_id)
    │
    ├─ Try agent_reference mode: / agent_reference 모드 시도:
    │   kwargs["agent"] = {"agent_reference": {"id": agent_name}}
    │   response = client.responses.create(**kwargs)
    │   │
    │   └─ If works → save response.id to self._responses[thread_id]
    │      성공 → response.id를 self._responses[thread_id]에 저장
    │
    ├─ If agent_reference fails → Fallback to instructions mode:
    │   agent_reference 실패 → instructions 모드로 대체:
    │   kwargs["instructions"] = instructions  (TEXT or VOICE)
    │   response = client.responses.create(**kwargs)
    │
    └─ Return response.output_text
        응답 텍스트 반환
```

### 2.4 Authentication / 인증

```python
# Production (Azure App Service) / 프로덕션:
credential = DefaultAzureCredential()
# → Uses Managed Identity (Principal ID: f18f4864-...)
#   관리 ID 사용

# Local development / 로컬 개발:
credential = DefaultAzureCredential()  
# → Falls back to AzureCliCredential (requires: az login)
#   AzureCliCredential로 대체 (필요: az login)

token_provider = get_bearer_token_provider(
    credential, 
    "https://cognitiveservices.azure.com/.default"
)

client = AzureOpenAI(
    azure_endpoint=settings.AZURE_AI_ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version="2025-03-01-preview"
)
```

---

## 3. Instruction Design / 지시문 설계

### 3.1 TEXT_INSTRUCTIONS — Comprehensive Teaching Doctrine / 종합 교육 교리

The text mode instruction is a **600+ line comprehensive teaching document** that defines the agent's entire behavior, personality, and teaching methodology.

텍스트 모드 지시문은 에이전트의 전체 행동, 성격, 교육 방법론을 정의하는 **600줄 이상의 종합 교육 문서**입니다.

**Key principles / 핵심 원칙**:

#### Identity / 정체성
```
You are a Korean business communication coach.
당신은 한국어 비즈니스 커뮤니케이션 코치입니다.

NOT a textbook teacher. You teach NATURAL Korean as spoken in real Korean 
offices and K-dramas.
교과서 선생님이 아닙니다. 실제 한국 사무실과 한국 드라마에서 쓰는 
자연스러운 한국어를 가르칩니다.
```

#### Teaching Philosophy — Natural Endings / 교육 철학 — 자연스러운 어미
```
NEVER teach only -습니다/-요 forms. Real Koreans combine:
-습니다/-요 형태만 가르치지 마세요. 실제 한국인은 조합합니다:

Reason / 이유:        -거든요     ("because..." context)
Shared knowledge:     -잖아요     ("as you know...")
Experience:           -더라고요   ("I noticed that...")
Discovery:            -네요       ("oh, I see!")
Agreement:            -죠         ("right?")
Softening:            -는데요     ("well, the thing is...")
```

#### Output Requirements / 출력 요구사항
```
EVERY response MUST include:
모든 응답은 반드시 포함해야 합니다:

1. A complete 8-12 turn Korean dialogue 
   OR a 200+ character business email
   8-12턴 완전한 한국어 대화 또는 200자 이상 비즈니스 이메일

2. Romanization for all Korean text
   모든 한국어 텍스트에 로마자 표기

3. Chinese/English translation
   중국어/영어 번역

4. Grammar/vocabulary notes
   문법/어휘 설명
```

#### K-Drama References / 한국 드라마 참조
```
Draw examples from real K-dramas:
실제 한국 드라마에서 예시를 가져옵니다:

- 미생 (Misaeng) — Office hierarchies, first day at work
- 스타트업 (Start-Up) — Tech industry, investor meetings  
- 이태원클라쓰 (Itaewon Class) — Business founding, negotiations
- 눈물의여왕 (Queen of Tears) — Corporate culture, chaebol dynamics
- 김과장 (Chief Kim) — Office politics, accounting terminology
```

### 3.2 VOICE_INSTRUCTIONS — 수진 (Sujin) Persona / 수진 페르소나

The voice mode uses a **completely different instruction set** optimized for spoken conversation.

음성 모드는 음성 대화에 최적화된 **완전히 다른 지시문**을 사용합니다.

**Key differences from text mode / 텍스트 모드와의 핵심 차이**:

| Aspect / 측면 | Text Mode / 텍스트 | Voice Mode / 음성 |
|---|---|---|
| **Identity / 정체성** | Korean Business Coach / 비즈니스 코치 | 수진 (Sujin), warm Korean woman manager / 따뜻한 한국 여성 매니저 |
| **Response length / 응답 길이** | Long (8-12 turn dialogues) / 긴 대화 | Short (1-3 sentences) / 짧은 응답 |
| **Language / 언어** | Korean + romanization + translation | Korean first + "(English: ...)" |
| **Input accepted / 입력 허용** | Any language / 모든 언어 | Any language (auto-detect ko/en/zh) / 자동 감지 |
| **Formatting / 서식** | Markdown, structured / 구조화 | No markdown, clean text / 깔끔한 텍스트 |
| **Emojis / 이모지** | Allowed / 허용 | Not allowed (TTS reads them) / 불허 (TTS가 읽음) |

**Sujin's personality / 수진의 성격**:
```
- Warm and encouraging / 따뜻하고 격려하는
- Uses natural Korean speech patterns / 자연스러운 한국어 화법 사용
- Responds AS IF in a real conversation / 실제 대화처럼 응답
- Gently corrects mistakes / 부드럽게 실수 교정
- Speaks like a friendly senior colleague / 친근한 선배처럼 말함

Natural patterns used by Sujin / 수진이 사용하는 자연스러운 패턴:
- Gentle confirmations / 부드러운 확인: -는데요, -거든요, -잖아요
- Impressions / 인상: -네요, -더라고요, -구나
- Agreement seeking / 동의 구하기: -죠?, 그쵸?
- Proposals / 제안: -ㄹ까요?, -는 게 어때요?
- Explanations / 설명: -거든요, -는데, -기는 한데
```

---

## 4. MCP Tools System / MCP 도구 시스템

### 4.1 What is MCP? / MCP란?

**MCP (Model Context Protocol)** is a standard that lets AI agents call external tools during conversations. Instead of the agent guessing or hallucinating, it can look up real data.

**MCP (Model Context Protocol)**는 AI 에이전트가 대화 중 외부 도구를 호출할 수 있게 하는 표준입니다. 에이전트가 추측하거나 환각하는 대신 실제 데이터를 조회할 수 있습니다.

### 4.2 How MCP Works in This Project / 이 프로젝트에서의 MCP 작동 방식

```
┌───────────────────────────────────────────────────────────────┐
│  User: "What does 보고서 mean?"                               │
│  사용자: "보고서가 무슨 뜻이에요?"                              │
└───────────────────────┬───────────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────────┐
│  GPT Agent (Azure AI Foundry)                                 │
│  GPT 에이전트 (Azure AI Foundry)                               │
│                                                               │
│  "I need to look up vocabulary. Let me call the               │
│   lookup_vocabulary tool."                                    │
│  "어휘를 조회해야 해. lookup_vocabulary 도구를 호출하자."        │
│                                                               │
│  → function_call: lookup_vocabulary(query="보고서")            │
└───────────────────────┬───────────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────────┐
│  MCP Server (mcp_server/server.py)                            │
│  Mounted at /mcp in FastAPI                                   │
│                                                               │
│  lookup_vocabulary("보고서")                                   │
│  → Searches data/business_korean.json                         │
│  → Returns: {                                                 │
│      "word": "보고서",                                        │
│      "romanization": "bogoseo",                               │
│      "meaning": "report / 报告",                              │
│      "formal": "보고서를 제출하다",                             │
│      "informal": "보고서 올릴게요",                             │
│      "example": "오늘까지 보고서 제출해야 하거든요."             │
│    }                                                          │
└───────────────────────┬───────────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────────┐
│  GPT Agent incorporates the data into its response:           │
│  GPT 에이전트가 데이터를 응답에 통합:                           │
│                                                               │
│  "보고서 (bogoseo) means 'report'! Here's how it's used       │
│   in a real office conversation: ..."                         │
│  "보고서는 'report'라는 뜻이에요! 실제 사무실 대화에서          │
│   이렇게 사용됩니다: ..."                                      │
└───────────────────────────────────────────────────────────────┘
```

### 4.3 All 9 MCP Tools / 전체 9개 MCP 도구

#### Tool 1: `lookup_vocabulary` — Vocabulary Lookup / 어휘 조회

```
Input / 입력:  query (str) — Korean, Chinese, English, or romanization
Output / 출력: Matching vocabulary entries with formal/informal forms, examples
Data / 데이터: 50+ business Korean terms from business_korean.json

Example / 예시:
  Input: "meeting"
  Output: 회의 (hoeuui) — meeting/ 会议
         Formal: 회의를 진행하겠습니다
         Informal: 회의 시작할게요
```

#### Tool 2: `get_grammar_pattern` — Grammar Explanation / 문법 설명

```
Input / 입력:  pattern (str) — Grammar pattern name or keyword
Output / 출력: Rule explanation, usage context, 3+ examples
Data / 데이터: 20+ Korean grammar patterns

Example / 예시:
  Input: "-거든요"
  Output: Usage: Providing reason (background info)
         Context: Used when explaining why something happened
         Example: 늦어서 죄송해요, 회의가 길어졌거든요.
```

#### Tool 3: `generate_business_scenario` — Scenario Framework / 시나리오 프레임워크

```
Input / 입력:  scenario_type (str) — meeting/negotiation/phone/presentation/networking/interview
Output / 출력: Complete conversation framework with roles, dialogue structure, key phrases
Data / 데이터: 6 scenario types with templates

Example / 예시:
  Input: "meeting"
  Output: [Meeting scenario with opening, agenda, discussion, action items, closing]
```

#### Tool 4: `get_email_template` — Business Email / 비즈니스 이메일

```
Input / 입력:  template_type (str) — meeting_request/thank_you/apology/inquiry/introduction/follow_up
Output / 출력: Complete email template in Korean with structure notes
Data / 데이터: 6 email templates

Example / 예시:
  Input: "apology"
  Output: [Full Korean apology email with subject, greeting, body, closing]
```

#### Tool 5: `check_formality` — Honorific Check / 경어 확인

```
Input / 입력:  text (str), context (str) — Korean text + social context
Output / 출력: Formality assessment, corrections if inappropriate
Data / 데이터: Rule-based formality checking

Example / 예시:
  Input: text="야, 이거 해" context="speaking to department head"
  Output: ❌ Too informal! Use: "부장님, 이것 좀 확인해 주시겠어요?"
```

#### Tool 6: `quiz_me` — Random Quiz / 랜덤 퀴즈

```
Input / 입력:  quiz_type (str, optional) — vocabulary/grammar/formality/email/conversation
Output / 출력: Quiz question with options and answer
Data / 데이터: Generated from all teaching data

Example / 예시:
  Output: Q: What does 결재 mean?
          A) Payment  B) Approval  C) Meeting  D) Report
          Answer: B) Approval (결재 vs 결제 — common confusion!)
```

#### Tool 7: `get_drama_dialogue` — K-Drama Scenes / 한국 드라마 장면

```
Input / 입력:  drama_name (str, optional) — 미생/스타트업/이태원클라쓰/김과장/비밀의숲
Output / 출력: Real workplace dialogue scene with vocabulary notes
Data / 데이터: K-drama scripts with business dialogue

Example / 예시:
  Input: "미생"
  Output: [Scene from 미생 Episode 3 — New employee's first team meeting]
```

#### Tool 8: `get_sentence_endings` — 어미 Reference / 어미 참조

```
Input / 입력:  ending (str, optional) — Specific ending or category
Output / 출력: 어미/연결어미 with usage rules and examples
Data / 데이터: 45+ sentence endings and connectors

Example / 예시:
  Input: "-더라고요"
  Output: Type: Experience/observation ending (경험/관찰 어미)
          Usage: Reporting personal experience
          Example: 어제 써봤는데 꽤 괜찮더라고요.
```

#### Tool 9: `practice_conversation` — Role-Play / 롤플레이

```
Input / 입력:  scenario (str) — Conversation situation description
Output / 출력: Interactive role-play setup with character, situation, starter dialogue
Data / 데이터: Generated scenario frameworks

Example / 예시:
  Input: "ordering lunch with colleagues"
  Output: [Role-play setup: You are a new employee, ordering lunch with team]
```

### 4.4 Data Source / 데이터 소스

All MCP tools read from **`data/business_korean.json`** (~27KB), a comprehensive Korean business curriculum corpus containing:

모든 MCP 도구는 **`data/business_korean.json`** (~27KB)에서 읽으며, 다음을 포함하는 종합 한국어 비즈니스 교육 코퍼스입니다:

```json
{
  "vocabulary": [{ "word": "...", "formal": "...", "informal": "...", ... }],
  "grammar_patterns": [{ "pattern": "...", "explanation": "...", "examples": [...] }],
  "scenarios": { "meeting": {...}, "negotiation": {...}, ... },
  "email_templates": { "meeting_request": {...}, "apology": {...}, ... },
  "sentence_endings": [{ "ending": "-거든요", "type": "reason", ... }],
  "drama_dialogues": [{ "drama": "미생", "scene": "...", ... }],
  "quizzes": [{ "question": "...", "options": [...], "answer": "..." }]
}
```

---

## 5. Voice Pipeline / 음성 파이프라인

### 5.1 Complete Voice Flow / 완전한 음성 흐름

```
┌──────────────────────────────────────────────────────────────────────┐
│  VOICE PIPELINE: Browser → Server → Azure → Server → Browser        │
│  음성 파이프라인: 브라우저 → 서버 → Azure → 서버 → 브라우저           │
│                                                                      │
│  ┌─────────────┐                                                     │
│  │ 1. RECORD   │  Browser: MediaRecorder API → WebM audio blob       │
│  │    녹음     │  → OfflineAudioContext resample to 16kHz WAV         │
│  │             │  → Send binary frames over WebSocket                 │
│  └──────┬──────┘  → Send {"type":"end_audio"} JSON                   │
│         │                                                            │
│  ┌──────▼──────┐                                                     │
│  │ 2. CONVERT  │  Server: Collect audio frames → Detect format       │
│  │    변환     │  → Resample to 16kHz mono WAV (ffmpeg or Python)     │
│  │             │  → Check for silence (max_amplitude < 10)           │
│  └──────┬──────┘                                                     │
│         │                                                            │
│  ┌──────▼──────┐                                                     │
│  │ 3. STT      │  Azure Speech REST API:                             │
│  │    음성인식  │  POST {endpoint}/stt/speech/recognition/...         │
│  │             │  Auth: Bearer token (Managed Identity)              │
│  │             │  관리 ID로 Bearer 토큰 인증                          │
│  │             │                                                     │
│  │             │  Auto-detect mode (language="auto"):                 │
│  │             │  자동 감지 모드:                                      │
│  │             │  ┌─────────────────────────────────────────┐        │
│  │             │  │ Parallel STT / 병렬 STT:                │        │
│  │             │  │  ├─ ko-KR (Korean / 한국어)              │        │
│  │             │  │  ├─ en-US (English / 영어)               │        │
│  │             │  │  └─ zh-CN (Chinese / 중국어)             │        │
│  │             │  │                                         │        │
│  │             │  │ → Pick highest confidence result         │        │
│  │             │  │   가장 높은 신뢰도 결과 선택              │        │
│  │             │  └─────────────────────────────────────────┘        │
│  └──────┬──────┘                                                     │
│         │ Recognized text / 인식된 텍스트                              │
│  ┌──────▼──────┐                                                     │
│  │ 4. AI AGENT │  GPT via Responses API                              │
│  │    AI 에이전트│  Instructions: VOICE_INSTRUCTIONS (Sujin persona)  │
│  │             │  Context: previous_response_id for thread continuity │
│  │             │  9 MCP tools available / 9개 MCP 도구 사용 가능      │
│  └──────┬──────┘                                                     │
│         │ AI reply text / AI 응답 텍스트                               │
│  ┌──────▼──────┐                                                     │
│  │ 5. TTS      │  Azure Speech REST API:                             │
│  │    음성합성  │  POST {endpoint}/tts/cognitiveservices/v1           │
│  │             │  Voice: ko-KR-SunHiNeural                           │
│  │             │  SSML: prosody rate=0.95, pitch=+2%, style=friendly │
│  │             │  Output: audio-16khz-128kbitrate-mono-mp3           │
│  └──────┬──────┘                                                     │
│         │ MP3 audio / MP3 오디오                                      │
│  ┌──────▼──────┐                                                     │
│  │ 6. DELIVER  │  Send to client over WebSocket:                     │
│  │    전달     │  1. JSON: {"type":"transcript", "text":"..."} (STT) │
│  │             │  2. JSON: {"type":"reply", "text":"..."} (AI)       │
│  │             │  3. Binary: MP3 audio (TTS)                         │
│  └─────────────┘                                                     │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.2 SSML Configuration / SSML 설정

The TTS uses SSML (Speech Synthesis Markup Language) to create a warm, natural-sounding business Korean voice:

TTS는 따뜻하고 자연스러운 비즈니스 한국어 목소리를 만들기 위해 SSML을 사용합니다:

```xml
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="ko-KR">
  <voice name="ko-KR-SunHiNeural">
    <mstts:express-as style="friendly">
      <prosody rate="0.95" pitch="+2%">
        안녕하세요~ 오늘 회의 준비 잘 되셨어요?
      </prosody>
    </mstts:express-as>
  </voice>
</speak>
```

| Parameter / 매개변수 | Value / 값 | Effect / 효과 |
|---|---|---|
| `voice` | `ko-KR-SunHiNeural` | Korean female voice / 한국어 여성 목소리 |
| `style` | `friendly` | Warm, approachable tone / 따뜻하고 친근한 톤 |
| `rate` | `0.95` | Slightly slower for clarity / 명확성을 위해 약간 느리게 |
| `pitch` | `+2%` | Slightly higher for warmth / 따뜻함을 위해 약간 높게 |

### 5.3 HTTP Connection Pooling / HTTP 연결 풀링

Speech API calls use connection pools to minimize latency:

음성 API 호출은 지연 시간을 최소화하기 위해 연결 풀을 사용합니다:

```python
# Module-level persistent pools (reused across requests)
# 모듈 수준 영구 풀 (요청 간 재사용)
_http_pool = httpx.Client(
    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    timeout=httpx.Timeout(30.0)
)
_tts_pool = httpx.Client(
    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    timeout=httpx.Timeout(30.0)
)
```

---

## 6. Thread & Context Management / 스레드 & 컨텍스트 관리

### 6.1 Conversation Continuity / 대화 연속성

The Responses API maintains context using `previous_response_id` — each response references the previous one, forming a chain.

Responses API는 `previous_response_id`를 사용하여 컨텍스트를 유지합니다 — 각 응답이 이전 응답을 참조하여 체인을 형성합니다.

```
Message 1: "What does 보고서 mean?" / "보고서가 무슨 뜻이에요?"
  → response_id: "resp_001"
  → self._responses["thread_abc"] = "resp_001"

Message 2: "Can you use it in a sentence?" / "문장에서 써볼 수 있어요?"
  → previous_response_id: "resp_001"  ← links to previous / 이전에 연결
  → response_id: "resp_002"
  → self._responses["thread_abc"] = "resp_002"

Message 3: "What about 결재?" / "결재는요?"
  → previous_response_id: "resp_002"  ← maintains full context / 전체 컨텍스트 유지
```

### 6.2 Thread Storage / 스레드 저장

```
Redis: thread:{user_id} → "thread_abc123"  (TTL: 24h)
         Current thread mapping / 현재 스레드 매핑

In-memory: self._responses[thread_id] → "resp_002"
           Last response ID per thread / 스레드별 마지막 응답 ID

Cosmos DB: conversations container → full message history
           전체 메시지 기록
```

---

## 7. Agent Fallback Strategy / 에이전트 대체 전략

The system has a graceful degradation strategy for the AI core:

시스템은 AI 핵심에 대한 우아한 퇴보 전략을 가지고 있습니다:

```
Priority 1: Portal Agent (agent_reference)
우선순위 1: 포털 에이전트 (agent_reference)
  ├─ Pre-configured agent in Azure AI Foundry portal
  │  Azure AI Foundry 포털에서 미리 설정된 에이전트
  ├─ Has MCP tools attached / MCP 도구 연결됨
  └─ Best experience / 최상의 경험

         │ Fails / 실패
         ▼

Priority 2: Inline Instructions
우선순위 2: 인라인 지시문
  ├─ TEXT_INSTRUCTIONS or VOICE_INSTRUCTIONS passed directly
  │  TEXT_INSTRUCTIONS 또는 VOICE_INSTRUCTIONS 직접 전달
  ├─ No MCP tools (instructions-only mode)
  │  MCP 도구 없음 (지시문 전용 모드)
  └─ Still functional but less capable / 기능하지만 능력 제한

         │ Fails / 실패
         ▼

Priority 3: Error Response
우선순위 3: 오류 응답
  ├─ Returns error message to user
  │  사용자에게 오류 메시지 반환
  └─ "AI service temporarily unavailable"
     "AI 서비스가 일시적으로 사용 불가"
```

---

## Navigation / 탐색

| Next / 다음 | Document / 문서 |
|---|---|
| Database & storage / 데이터베이스 & 저장소 | → [docs/DATABASE.md](DATABASE.md) |
| All files explained / 모든 파일 설명 | → [docs/CODEBASE.md](CODEBASE.md) |
| Network & deployment / 네트워크 & 배포 | → [docs/NETWORK.md](NETWORK.md) |
| BMAD methodology / BMAD 방법론 | → [docs/BMAD.md](BMAD.md) |
