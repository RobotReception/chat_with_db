# أمثلة سريعة لاستخدام API

## ⚠️ مهم: يجب إضافة Header في كل طلب

```
X-API-Key: your-api-key-here
```

---

## 1️⃣ إنشاء جلسة (Session)

```bash
curl -X POST "http://localhost:3300/api/v1/chat/session" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"user_name": "أحمد"}'
```

**النتيجة:**
```json
{
  "success": true,
  "session_id": "1306cad3-e59f-4c68-9511-05ca40ccce5d",
  "message": "Session created successfully"
}
```

---

## 2️⃣ الحصول على معلومات الجلسة

```bash
curl -X GET "http://localhost:3300/api/v1/chat/session/1306cad3-e59f-4c68-9511-05ca40ccce5d" \
  -H "X-API-Key: your-api-key-here"
```

---

## 3️⃣ إرسال سؤال

```bash
curl -X POST "http://localhost:3300/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "question": "ما هو عدد العملاء؟",
    "session_id": "1306cad3-e59f-4c68-9511-05ca40ccce5d"
  }'
```

---

## 4️⃣ الحصول على سجل المحادثات

```bash
curl -X GET "http://localhost:3300/api/v1/chat/history?session_id=1306cad3-e59f-4c68-9511-05ca40ccce5d" \
  -H "X-API-Key: your-api-key-here"
```

---

## 📝 JavaScript Example

```javascript
const API_KEY = 'your-api-key-here';
const BASE_URL = 'http://localhost:3300/api/v1/chat';

// إنشاء جلسة
async function createSession() {
  const response = await fetch(`${BASE_URL}/session`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    },
    body: JSON.stringify({
      user_name: 'أحمد',
      user_email: 'ahmed@example.com'
    })
  });
  return await response.json();
}

// إرسال سؤال
async function askQuestion(sessionId, question) {
  const response = await fetch(`${BASE_URL}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    },
    body: JSON.stringify({
      question: question,
      session_id: sessionId
    })
  });
  return await response.json();
}

// استخدام
(async () => {
  const session = await createSession();
  console.log('Session ID:', session.session_id);
  
  const answer = await askQuestion(session.session_id, 'ما هو عدد العملاء؟');
  console.log('Answer:', answer.answer);
})();
```

---

## 🐍 Python Example

```python
import requests

API_KEY = 'your-api-key-here'
BASE_URL = 'http://localhost:3300/api/v1/chat'

headers = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
}

# إنشاء جلسة
def create_session():
    response = requests.post(
        f'{BASE_URL}/session',
        headers=headers,
        json={'user_name': 'أحمد'}
    )
    return response.json()

# إرسال سؤال
def ask_question(session_id, question):
    response = requests.post(
        f'{BASE_URL}',
        headers=headers,
        json={
            'question': question,
            'session_id': session_id
        }
    )
    return response.json()

# استخدام
session = create_session()
print(f'Session ID: {session["session_id"]}')

answer = ask_question(session['session_id'], 'ما هو عدد العملاء؟')
print(f'Answer: {answer["answer"]}')
```

---

## 🔧 Postman Collection

### Environment Variables:
- `base_url`: `http://localhost:3300`
- `api_key`: `your-api-key-here`

### Headers (لجميع الطلبات):
```
X-API-Key: {{api_key}}
Content-Type: application/json
```

### Endpoints:

1. **Create Session**
   - Method: `POST`
   - URL: `{{base_url}}/api/v1/chat/session`
   - Body:
   ```json
   {
     "user_name": "أحمد",
     "user_email": "ahmed@example.com"
   }
   ```

2. **Get Session**
   - Method: `GET`
   - URL: `{{base_url}}/api/v1/chat/session/{{session_id}}`

3. **Chat**
   - Method: `POST`
   - URL: `{{base_url}}/api/v1/chat`
   - Body:
   ```json
   {
     "question": "ما هو عدد العملاء؟",
     "session_id": "{{session_id}}"
   }
   ```

---

## ⚡ Quick Test

```bash
# اختبار سريع
API_KEY="your-api-key-here"
BASE_URL="http://localhost:3300/api/v1/chat"

# 1. إنشاء جلسة
SESSION=$(curl -s -X POST "$BASE_URL/session" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"user_name":"Test"}' | jq -r '.session_id')

echo "Session ID: $SESSION"

# 2. إرسال سؤال
curl -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{\"question\":\"ما هو عدد العملاء؟\",\"session_id\":\"$SESSION\"}"
```

---

## 🚨 حل مشكلة 401

إذا حصلت على `401 Unauthorized`:

1. ✅ تأكد من إرسال `X-API-Key` header
2. ✅ القيمة: `your-api-key-here` (من ملف `.env`)
3. ✅ الاسم صحيح: `X-API-Key` (حساس لحالة الأحرف)
4. ✅ لا مسافات إضافية

**صحيح:**
```
X-API-Key: your-api-key-here
```

**خاطئ:**
```
x-api-key: your-api-key-here
X-API-KEY: your-api-key-here
X-API-Key : your-api-key-here
```
