# دليل استخدام API - PostgreSQL Chat API

## المصادقة (Authentication)

جميع الطلبات (ما عدا `/health` و `/`) تتطلب **API Key** في الـ header.

### Header المطلوب:
```
X-API-Key: your-api-key-here
```

**ملاحظة:** القيمة الحالية في `.env` هي `your-api-key-here`. يجب تغييرها في الإنتاج.

---

## أمثلة على الطلبات

### 1. إنشاء جلسة جديدة (Session)

**POST** `/api/v1/chat/session`

**Headers:**
```json
{
  "Content-Type": "application/json",
  "X-API-Key": "your-api-key-here"
}
```

**Body:**
```json
{
  "user_name": "أحمد محمد",
  "user_email": "ahmed@example.com",
  "user_metadata": {
    "department": "IT",
    "role": "admin"
  }
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "1306cad3-e59f-4c68-9511-05ca40ccce5d",
  "message": "Session created successfully"
}
```

---

### 2. الحصول على معلومات الجلسة

**GET** `/api/v1/chat/session/{session_id}`

**Headers:**
```
X-API-Key: your-api-key-here
```

**مثال:**
```
GET /api/v1/chat/session/1306cad3-e59f-4c68-9511-05ca40ccce5d
```

---

### 3. إرسال سؤال (Chat)

**POST** `/api/v1/chat`

**Headers:**
```json
{
  "Content-Type": "application/json",
  "X-API-Key": "your-api-key-here"
}
```

**Body:**
```json
{
  "question": "ما هو عدد العملاء في قاعدة البيانات؟",
  "session_id": "1306cad3-e59f-4c68-9511-05ca40ccce5d",
  "conversation_id": null,
  "export_to_excel": false,
  "include_data": false,
  "preview_rows": 10
}
```

**Response:**
```json
{
  "success": true,
  "answer": "يوجد 599 عميل في قاعدة البيانات.",
  "data": [...],
  "has_data": true,
  "data_preview_rows": 10,
  "data_total_rows": 599,
  "has_more_data": true,
  "has_chart": false,
  "chart_id": null,
  "chart_url": null,
  "chart_type": null,
  "needs_visualization": false,
  "visualization_type": "none",
  "has_excel": false,
  "excel_url": null,
  "query_id": "abc123...",
  "conversation_id": "xyz789...",
  "error": null
}
```

---

### 4. إنشاء محادثة جديدة (Conversation Thread)

**POST** `/api/v1/chat/conversation`

**Headers:**
```json
{
  "Content-Type": "application/json",
  "X-API-Key": "your-api-key-here"
}
```

**Body:**
```json
{
  "session_id": "1306cad3-e59f-4c68-9511-05ca40ccce5d",
  "title": "محادثة حول المبيعات",
  "user_metadata": {}
}
```

---

### 5. الحصول على سجل المحادثات

**GET** `/api/v1/chat/history`

**Headers:**
```
X-API-Key: your-api-key-here
```

**Query Parameters:**
- `session_id` (اختياري): تصفية حسب الجلسة
- `limit` (افتراضي: 50): عدد النتائج
- `skip` (افتراضي: 0): عدد النتائج للتخطي (للصفحات)

**مثال:**
```
GET /api/v1/chat/history?session_id=1306cad3-e59f-4c68-9511-05ca40ccce5d&limit=20
```

---

## أمثلة باستخدام cURL

### إنشاء جلسة:
```bash
curl -X POST "http://localhost:3300/api/v1/chat/session" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "user_name": "أحمد",
    "user_email": "ahmed@example.com"
  }'
```

### إرسال سؤال:
```bash
curl -X POST "http://localhost:3300/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "question": "ما هو عدد العملاء؟",
    "session_id": "1306cad3-e59f-4c68-9511-05ca40ccce5d"
  }'
```

### الحصول على معلومات الجلسة:
```bash
curl -X GET "http://localhost:3300/api/v1/chat/session/1306cad3-e59f-4c68-9511-05ca40ccce5d" \
  -H "X-API-Key: your-api-key-here"
```

---

## أمثلة باستخدام JavaScript (Fetch API)

### إنشاء جلسة:
```javascript
const response = await fetch('http://localhost:3300/api/v1/chat/session', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key-here'
  },
  body: JSON.stringify({
    user_name: 'أحمد',
    user_email: 'ahmed@example.com'
  })
});

const data = await response.json();
console.log(data.session_id);
```

### إرسال سؤال:
```javascript
const response = await fetch('http://localhost:3300/api/v1/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key-here'
  },
  body: JSON.stringify({
    question: 'ما هو عدد العملاء؟',
    session_id: '1306cad3-e59f-4c68-9511-05ca40ccce5d'
  })
});

const data = await response.json();
console.log(data.answer);
```

---

## أمثلة باستخدام Python (requests)

```python
import requests

BASE_URL = "http://localhost:3300/api/v1/chat"
API_KEY = "your-api-key-here"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# إنشاء جلسة
response = requests.post(
    f"{BASE_URL}/session",
    headers=headers,
    json={
        "user_name": "أحمد",
        "user_email": "ahmed@example.com"
    }
)
session_data = response.json()
session_id = session_data["session_id"]

# إرسال سؤال
response = requests.post(
    f"{BASE_URL}",
    headers=headers,
    json={
        "question": "ما هو عدد العملاء؟",
        "session_id": session_id
    }
)
chat_data = response.json()
print(chat_data["answer"])
```

---

## Endpoints المتاحة

| Method | Endpoint | الوصف |
|--------|----------|-------|
| POST | `/api/v1/chat/session` | إنشاء جلسة جديدة |
| GET | `/api/v1/chat/session/{session_id}` | الحصول على معلومات الجلسة |
| GET | `/api/v1/chat/sessions` | الحصول على جميع الجلسات |
| POST | `/api/v1/chat/session/{session_id}/end` | إنهاء جلسة |
| POST | `/api/v1/chat` | إرسال سؤال |
| POST | `/api/v1/chat/conversation` | إنشاء محادثة جديدة |
| GET | `/api/v1/chat/conversations` | قائمة المحادثات |
| GET | `/api/v1/chat/conversation/{conversation_id}/messages` | رسائل المحادثة |
| GET | `/api/v1/chat/history` | سجل المحادثات |
| GET | `/api/v1/chat/history/{conversation_id}` | تفاصيل محادثة محددة |
| GET | `/api/v1/chat/search?q={query}` | البحث في المحادثات |
| GET | `/api/v1/chat/data/{query_id}` | الحصول على البيانات الكاملة |
| GET | `/api/v1/chat/export/{query_id}` | تصدير إلى Excel |
| GET | `/api/v1/chat/health` | فحص الحالة (لا يحتاج API Key) |

---

## ملاحظات مهمة

1. **جميع الطلبات تحتاج `X-API-Key` header** (ما عدا `/health` و `/`)
2. **القيمة الحالية:** `your-api-key-here` (يجب تغييرها في الإنتاج)
3. **Base URL:** `http://localhost:3300` (أو عنوان الخادم الخاص بك)
4. **API Prefix:** `/api/v1`
5. **Content-Type:** يجب أن يكون `application/json` للطلبات التي تحتوي على body

---

## حل مشكلة 401 Unauthorized

إذا كنت تحصل على `401 Unauthorized`، تأكد من:

1. ✅ إرسال header `X-API-Key` في كل طلب
2. ✅ القيمة مطابقة تماماً للقيمة في ملف `.env` (`API_KEY`)
3. ✅ الاسم صحيح: `X-API-Key` (حساس لحالة الأحرف)
4. ✅ لا توجد مسافات إضافية في القيمة

**مثال صحيح:**
```
X-API-Key: your-api-key-here
```

**أمثلة خاطئة:**
```
X-API-Key: your-api-key-here   (مسافة في النهاية)
x-api-key: your-api-key-here  (أحرف صغيرة)
X-API-KEY: your-api-key-here  (أحرف كبيرة)
```
