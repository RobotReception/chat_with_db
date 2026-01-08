# 💬 Chat with Database - PostgreSQL Chat API

<div dir="rtl">

# 💬 دردشة مع قاعدة البيانات - PostgreSQL Chat API

نظام ذكي للتفاعل مع قواعد بيانات PostgreSQL باستخدام الذكاء الاصطناعي. يتيح للمستخدمين طرح الأسئلة باللغة الطبيعية والحصول على إجابات دقيقة مع إمكانية تصور البيانات وتحليلها إحصائياً.

</div>

## 📋 Table of Contents / جدول المحتويات

- [Overview / نظرة عامة](#overview)
- [Features / المميزات](#features)
- [Architecture / البنية المعمارية](#architecture)
- [Project Structure / هيكلية المشروع](#project-structure)
- [Installation / التثبيت](#installation)
- [Configuration / الإعدادات](#configuration)
- [Usage / الاستخدام](#usage)
- [API Documentation / توثيق API](#api-documentation)
- [Docker Deployment / النشر باستخدام Docker](#docker-deployment)
- [Development / التطوير](#development)

---

## 🎯 Overview / نظرة عامة

<div dir="rtl">

**Chat with Database** هو نظام متقدم يسمح للمستخدمين بالتفاعل مع قواعد بيانات PostgreSQL باستخدام اللغة الطبيعية. يستخدم النظام الذكاء الاصطناعي (LLM) لفهم الأسئلة، توليد استعلامات SQL، تنفيذها، وتقديم الإجابات بشكل احترافي مع إمكانية تصور البيانات وتحليلها إحصائياً.

### المشكلة التي يحلها المشروع:
- صعوبة كتابة استعلامات SQL للمستخدمين غير التقنيين
- الحاجة لفهم بنية قاعدة البيانات قبل كتابة الاستعلامات
- صعوبة تحليل البيانات وتصورها
- الحاجة لنظام آمن يمنع الاستعلامات الضارة

### الحل:
- واجهة محادثة طبيعية باللغة العربية والإنجليزية
- توليد تلقائي لاستعلامات SQL آمنة
- تحليل إحصائي تلقائي للبيانات
- تصور البيانات برسوم بيانية
- نظام أمان متقدم لمنع الاستعلامات الضارة

</div>

**Chat with Database** is an advanced system that allows users to interact with PostgreSQL databases using natural language. The system uses AI (LLM) to understand questions, generate SQL queries, execute them, and provide professional answers with data visualization and statistical analysis capabilities.

### Problem it solves:
- Difficulty writing SQL queries for non-technical users
- Need to understand database schema before writing queries
- Difficulty analyzing and visualizing data
- Need for a secure system that prevents malicious queries

### Solution:
- Natural language chat interface in Arabic and English
- Automatic generation of secure SQL queries
- Automatic statistical analysis of data
- Data visualization with charts
- Advanced security system to prevent malicious queries

---

## ✨ Features / المميزات

### 🌐 Multi-Language Support / دعم متعدد اللغات
- **Arabic & English** support for questions and answers
- Automatic language detection
- Natural language processing

### 🤖 AI-Powered SQL Generation / توليد SQL بالذكاء الاصطناعي
- Uses **OpenAI GPT-4** or **Google Gemini** for SQL generation
- Context-aware query generation using RAG (Retrieval Augmented Generation)
- Automatic schema understanding and retrieval

### 🔒 Security Features / ميزات الأمان
- SQL injection prevention
- Query validation and sanitization
- Sensitive data detection
- Allowed operations restriction (SELECT only by default)
- Query timeout protection

### 📊 Data Analysis & Visualization / تحليل وتصور البيانات
- **Statistical Analysis**: Automatic statistical summaries
- **Data Visualization**: Generate charts and graphs using PandasAI
- **Excel Export**: Export query results to Excel files
- **Smart Data Preview**: Preview data with pagination

### 💾 Database Support / دعم قواعد البيانات
- **PostgreSQL**: Main database for queries
- **MongoDB**: Store conversations, sessions, and metadata
- Connection pooling and optimization
- Support for external databases

### 🔄 Session Management / إدارة الجلسات
- Conversation history tracking
- Session-based context
- User metadata support
- Thread-based conversations (like ChatGPT)

### 📈 Observability / المراقبة
- Structured logging (JSON format)
- Health checks
- Error tracking
- Performance monitoring

---

## 🏗️ Architecture / البنية المعمارية

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│                    (Web/Mobile App)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Chat API    │  │  Health API  │  │  Static Files│      │
│  │  Endpoints   │  │  Endpoints   │  │  (Exports)   │      │
│  └──────┬───────┘  └──────────────┘  └──────────────┘      │
└─────────┼──────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ┌──────────────────┐  ┌──────────────────┐                  │
│  │  Chat Service   │  │  Visualization  │                  │
│  │  (Orchestrator) │  │     Service     │                  │
│  └────────┬────────┘  └──────────────────┘                  │
│           │                                                    │
│  ┌────────▼──────────────────────────────────────┐           │
│  │  Statistical Analysis Service                │           │
│  └──────────────────────────────────────────────┘           │
└─────────┬──────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Question     │  │ SQL         │  │ Response     │      │
│  │ Classifier   │  │ Generator   │  │ Formatter    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Question     │  │ Sensitive   │  │ Query Intent │      │
│  │ Refiner      │  │ Detector     │  │ Detector     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────┬──────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Schema       │  │ Semantic     │  │ Schema       │      │
│  │ Store        │  │ Keywords     │  │ Retriever    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────┬──────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PostgreSQL   │  │ MongoDB      │  │ Query Cache  │      │
│  │ Executor     │  │ Manager      │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────┬──────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                             │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ PostgreSQL   │  │ MongoDB      │                        │
│  │ (Main DB)    │  │ (Sessions)    │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### Flow Diagram / مخطط التدفق

```
User Question
     │
     ▼
┌─────────────────┐
│ Question        │
│ Classification  │ ──→ Is it database-related?
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Sensitive       │ ──→ Is it safe?
│ Detection       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Question        │ ──→ Refine question with context
│ Refinement      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Schema          │ ──→ Get relevant schema parts
│ Retrieval (RAG) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SQL Generation  │ ──→ Generate SQL query
│ (LLM Chain)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SQL Validation  │ ──→ Security check
│ & Sanitization  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SQL Execution   │ ──→ Execute query
│ (PostgreSQL)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Processing │ ──→ Analyze & visualize
│ & Analysis      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Response        │ ──→ Format answer
│ Formatting      │
└────────┬────────┘
         │
         ▼
   User Answer
```

---

## 📁 Project Structure / هيكلية المشروع

```
new_version/
│
├── app/                          # Application code
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── config.py                 # Configuration management
│   │
│   ├── api/                      # API endpoints
│   │   ├── __init__.py
│   │   └── chat.py               # Chat API endpoints
│   │
│   ├── db/                       # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py         # PostgreSQL connection
│   │   ├── executor.py           # SQL execution
│   │   ├── security.py           # SQL security & validation
│   │   └── mongodb.py            # MongoDB connection & operations
│   │
│   ├── llm/                      # LLM services
│   │   ├── __init__.py
│   │   ├── client.py             # OpenAI client
│   │   ├── gemini_client.py      # Google Gemini client
│   │   ├── chains.py             # LangChain chains (SQL generation, summarization)
│   │   ├── prompts.py            # LLM prompts templates
│   │   ├── question_classifier.py      # Classify question type
│   │   ├── question_refiner.py          # Refine questions with context
│   │   ├── query_intent.py              # Detect query intent
│   │   ├── sensitive_question_detector.py  # Detect sensitive questions
│   │   ├── sensitive_question_checker.py  # Check sensitive data access
│   │   ├── general_question_handler.py    # Handle non-DB questions
│   │   └── gemini_response_formatter.py   # Format responses professionally
│   │
│   ├── rag/                      # RAG (Retrieval Augmented Generation)
│   │   ├── __init__.py
│   │   ├── schema_store.py       # Store database schema
│   │   ├── retriever.py          # Retrieve relevant schema parts
│   │   └── semantic_keywords.py  # Semantic keyword extraction
│   │
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── chat_service.py       # Main chat orchestration service
│   │   ├── statistical_analysis.py  # Statistical analysis service
│   │   └── visualization_service.py # Data visualization service
│   │
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── excel_export.py       # Excel export functionality
│   │   ├── query_cache.py        # Query result caching
│   │   ├── json_sanitizer.py     # JSON sanitization
│   │   ├── data_summarizer.py    # Data summarization
│   │   └── error_messages.py     # Error message handling
│   │
│   ├── visualization/            # Visualization
│   │   ├── __init__.py
│   │   ├── pandasai_engine.py    # PandasAI integration
│   │   └── prompts.py            # Visualization prompts
│   │
│   └── observability/            # Logging & monitoring
│       ├── __init__.py
│       └── logging.py            # Logging configuration
│
├── requirements/                 # Python dependencies
│   ├── base.txt                  # Core dependencies
│   ├── ai.txt                    # AI/LLM dependencies
│   └── analytics.txt             # Analytics & visualization dependencies
│
├── exports/                      # Generated Excel files (gitignored)
├── charts/                       # Generated charts (gitignored)
│   └── generated/
├── cache/                        # Query cache (gitignored)
│
├── docker-compose.yml            # Docker Compose configuration
├── docker-compose.dev.yml        # Development Docker Compose
├── Dockerfile                    # Docker image definition
├── .dockerignore                 # Docker ignore file
├── .env.example                  # Environment variables example
├── .gitignore                    # Git ignore file
│
├── DOCKER_SETUP.md               # Docker setup guide
├── QUICK_START_DOCKER.md         # Quick start guide
├── SERVICE_REPORT.md             # Service documentation
│
└── README.md                     # This file
```

---

## 🚀 Installation / التثبيت

### Prerequisites / المتطلبات

- Python 3.11+
- PostgreSQL database (local or remote)
- MongoDB (optional, for session management)
- OpenAI API key OR Google Gemini API key

### Option 1: Docker (Recommended) / الخيار 1: Docker (موصى به)

```bash
# Clone the repository
git clone https://github.com/RobotReception/chat_with_db.git
cd chat_with_db

# Copy environment file
cp .env.example .env

# Edit .env file with your configuration
nano .env

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f api
```

### Option 2: Local Installation / الخيار 2: التثبيت المحلي

```bash
# Clone the repository
git clone https://github.com/RobotReception/chat_with_db.git
cd chat_with_db

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/base.txt
pip install -r requirements/ai.txt
pip install -r requirements/analytics.txt

# Copy environment file
cp .env.example .env

# Edit .env file
nano .env

# Run the application
python -m app.main
```

---

## ⚙️ Configuration / الإعدادات

### Environment Variables / متغيرات البيئة

Create a `.env` file based on `.env.example`:

```env
# API Configuration
API_TITLE=PostgreSQL Chat API
API_VERSION=1.0.0
API_PREFIX=/api/v1
DEBUG=false
LOG_LEVEL=INFO

# Security
API_KEY=your-secret-api-key
JWT_SECRET=your-jwt-secret

# PostgreSQL Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=postgres
DB_PASSWORD=your_password
# OR use full connection string:
POSTGRESQL_URL=postgresql://user:password@host:port/database

# MongoDB (Optional - for sessions)
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=chat_db

# LLM Configuration
# Option 1: OpenAI
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.0

# Option 2: Google Gemini (for question refinement and response formatting)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.3

# SQL Settings
SQL_TIMEOUT_SECONDS=30
SQL_MAX_ROWS=1000
SHOW_SQL_TO_USER=true  # Set false in production

# RAG Settings
EMBEDDING_MODEL=text-embedding-ada-002
RAG_TOP_K=5
```

### Database Setup / إعداد قاعدة البيانات

1. **PostgreSQL**: Ensure your database is accessible and contains the data you want to query
2. **MongoDB** (Optional): For session management and conversation history

---

## 📖 Usage / الاستخدام

### Starting the Service / بدء الخدمة

```bash
# Using Docker
docker-compose up -d

# Or locally
python -m app.main
```

The API will be available at: `http://localhost:3300`

### API Documentation / توثيق API

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:3300/docs
- **ReDoc**: http://localhost:3300/redoc

### Example Request / مثال على الطلب

```bash
curl -X POST "http://localhost:3300/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "كم عدد العملاء في قاعدة البيانات؟",
    "session_id": "optional-session-id",
    "export_to_excel": false,
    "include_data": true
  }'
```

### Example Response / مثال على الاستجابة

```json
{
  "success": true,
  "answer": "يوجد 1,234 عميل في قاعدة البيانات.",
  "sql_query": "SELECT COUNT(*) FROM customers;",
  "data": {
    "columns": ["count"],
    "rows": [[1234]],
    "row_count": 1
  },
  "has_data": true,
  "data_preview_rows": 1,
  "needs_visualization": false,
  "visualization_type": "none",
  "is_database_related": true,
  "metadata": {
    "question": "كم عدد العملاء في قاعدة البيانات؟",
    "execution_time_ms": 45,
    "steps": ["question_classified", "sql_generated", "sql_executed"]
  }
}
```

---

## 📚 API Documentation / توثيق API

### Endpoints / النقاط الطرفية

#### `POST /api/v1/chat`

Send a question to the chat API.

**Request Body:**
```json
{
  "question": "string (required)",
  "session_id": "string (optional)",
  "conversation_id": "string (optional)",
  "export_to_excel": "boolean (default: false)",
  "include_data": "boolean (default: false)",
  "preview_rows": "integer (default: 10, max: 100)"
}
```

**Response:**
```json
{
  "success": "boolean",
  "answer": "string",
  "sql_query": "string (optional)",
  "data": "object (optional)",
  "has_data": "boolean",
  "has_chart": "boolean",
  "chart_id": "string (optional)",
  "has_excel": "boolean",
  "excel_url": "string (optional)",
  "needs_visualization": "boolean",
  "visualization_type": "string",
  "is_database_related": "boolean",
  "error": "string (optional)",
  "metadata": "object"
}
```

#### `POST /api/v1/chat/session`

Create a new session.

#### `GET /health`

Health check endpoint.

#### `GET /`

Root endpoint with API information.

---

## 🐳 Docker Deployment / النشر باستخدام Docker

See [DOCKER_SETUP.md](./DOCKER_SETUP.md) for detailed Docker setup instructions.

### Quick Start / البدء السريع

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## 🛠️ Development / التطوير

### Project Components / مكونات المشروع

#### 1. **API Layer** (`app/api/`)
- FastAPI endpoints
- Request/response models
- Error handling

#### 2. **Service Layer** (`app/services/`)
- Business logic
- Orchestration of LLM, RAG, and database operations

#### 3. **LLM Layer** (`app/llm/`)
- Question processing
- SQL generation
- Response formatting
- Security checks

#### 4. **RAG Layer** (`app/rag/`)
- Schema storage and retrieval
- Semantic search
- Context building

#### 5. **Data Access Layer** (`app/db/`)
- Database connections
- SQL execution
- Security validation
- Caching

#### 6. **Utilities** (`app/utils/`)
- Excel export
- Data summarization
- Error handling
- JSON sanitization

### Adding New Features / إضافة ميزات جديدة

1. **New LLM Chain**: Add to `app/llm/chains.py`
2. **New Service**: Add to `app/services/`
3. **New Endpoint**: Add to `app/api/`
4. **New Utility**: Add to `app/utils/`

### Testing / الاختبار

```bash
# Run tests (if available)
pytest

# Test API endpoint
curl http://localhost:3300/health
```

---

## 🔒 Security / الأمان

### Security Features / ميزات الأمان

1. **SQL Injection Prevention**
   - Query validation
   - Allowed operations restriction
   - Parameter sanitization

2. **Sensitive Data Detection**
   - Automatic detection of sensitive questions
   - Privacy protection

3. **Query Timeout**
   - Prevents long-running queries
   - Configurable timeout

4. **Row Limit**
   - Maximum rows per query
   - Prevents excessive data retrieval

---

## 📊 Features in Detail / المميزات بالتفصيل

### 1. Question Classification / تصنيف الأسئلة
- Classifies questions as database-related or general
- Routes to appropriate handler

### 2. SQL Generation / توليد SQL
- Uses LLM with RAG context
- Generates optimized SQL queries
- Handles complex queries with joins

### 3. Statistical Analysis / التحليل الإحصائي
- Automatic statistical summaries
- Mean, median, mode calculations
- Distribution analysis

### 4. Data Visualization / تصور البيانات
- Automatic chart generation
- Supports multiple chart types
- PandasAI integration

### 5. Excel Export / تصدير Excel
- Export query results to Excel
- Formatted Excel files
- Download links

---

## 🤝 Contributing / المساهمة

Contributions are welcome! Please feel free to submit a Pull Request.

<div dir="rtl">

المساهمات مرحب بها! يرجى إرسال Pull Request.

</div>

---

## 📝 License / الترخيص

This project is licensed under the MIT License.

---

## 📞 Support / الدعم

For issues and questions, please open an issue on GitHub.

<div dir="rtl">

للأسئلة والمشاكل، يرجى فتح issue على GitHub.

</div>

---

## 🙏 Acknowledgments / شكر وتقدير

- **FastAPI** - Modern web framework
- **LangChain** - LLM framework
- **OpenAI** - GPT models
- **Google Gemini** - Gemini models
- **PostgreSQL** - Database
- **MongoDB** - Session storage
- **PandasAI** - Data visualization

---

<div dir="rtl">

## 🎉 جاهز للاستخدام!

ابدأ الآن وتمتع بالتفاعل مع قاعدة البيانات باستخدام اللغة الطبيعية!

</div>

## 🎉 Ready to Use!

Start now and enjoy interacting with your database using natural language!

---

**Made with ❤️ by RobotReception**
