# 🚀 البدء السريع - Docker Compose

## خطوات التشغيل السريعة

### 1️⃣ إعداد ملف البيئة

```bash
# نسخ ملف المثال
cp .env.example .env

# تعديل الملف بإضافة API Keys وإعدادات قواعد البيانات
nano .env
```

**المتغيرات المطلوبة:**
- `GEMINI_API_KEY`: **مطلوب** - Google Gemini API Key
- `MONGO_URI`: **مطلوب** - MongoDB Connection URI
- `DB_HOST` أو `POSTGRESQL_URL`: **مطلوب** - PostgreSQL connection
- `OPENAI_API_KEY`: اختياري - OpenAI API Key

### 2️⃣ التأكد من اتصال قواعد البيانات

**PostgreSQL:**
```bash
# اختبار الاتصال
psql -h your-db-host -U postgres -d postgres
```

**MongoDB:**
```bash
# اختبار الاتصال
mongosh "mongodb://admin:password@host:port/admin"
```

### 3️⃣ تشغيل الخدمة

```bash
# Production Mode
docker-compose up -d

# أو Development Mode (مع hot reload)
docker-compose -f docker-compose.dev.yml up -d
```

### 4️⃣ التحقق من التشغيل

```bash
# فحص الحالة
docker-compose ps

# فحص السجلات
docker-compose logs -f api

# اختبار الصحة
curl http://localhost:3300/health
```

---

## 🌐 الوصول للخدمات

- **API**: http://localhost:3300
- **API Docs**: http://localhost:3300/docs
- **Health Check**: http://localhost:3300/health

**ملاحظة:** الخدمة تستخدم قواعد البيانات الخارجية (PostgreSQL و MongoDB) المحددة في ملف `.env`

---

## 📝 أوامر مفيدة

```bash
# إيقاف الخدمات
docker-compose down

# إعادة تشغيل
docker-compose restart api

# عرض السجلات
docker-compose logs -f api

# الوصول إلى Container
docker-compose exec api bash

# عرض متغيرات البيئة
docker-compose exec api env | grep -E "(DB_|MONGO_|GEMINI_|API_)"
```

---

## 📚 للمزيد من التفاصيل

راجع ملف `DOCKER_SETUP.md` للدليل الكامل.

---

**جاهز للاستخدام! 🎉**
