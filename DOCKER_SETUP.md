# 🐳 Docker Setup Guide - PostgreSQL Chat API

## 📋 نظرة عامة

هذا الدليل يشرح كيفية تشغيل الخدمة باستخدام Docker Compose.

---

## 🚀 البدء السريع

### 1. إعداد ملف البيئة

```bash
# نسخ ملف المثال
cp .env.example .env

# تعديل الملف بالقيم الخاصة بك
nano .env
```

### 2. تشغيل الخدمة

```bash
# Production Mode
docker-compose up -d

# Development Mode (with hot reload)
docker-compose -f docker-compose.dev.yml up -d
```

### 3. التحقق من حالة الخدمة

```bash
# عرض حالة جميع الحاويات
docker-compose ps

# عرض السجلات
docker-compose logs -f api

# فحص الصحة
curl http://localhost:3300/health
```

---

## 📦 الخدمات (Services)

### 1. **API Service** (FastAPI Application)
- **Port**: 3300
- **Container**: `postgresql_chat_api`
- **Health Check**: `http://localhost:3300/health`

### 2. **PostgreSQL** (Main Database)
- **Port**: 5432
- **Container**: `postgres_chat_db`
- **Default User**: postgres
- **Default Password**: postgres

### 3. **MongoDB** (Conversations & Sessions)
- **Port**: 27017
- **Container**: `mongodb_chat_db`
- **Default User**: admin
- **Default Password**: Strong#Mongo!123
- **Database**: chat_db

---

## 🔧 الأوامر الأساسية

### إدارة الحاويات

```bash
# تشغيل الخدمات
docker-compose up -d

# إيقاف الخدمات
docker-compose down

# إعادة تشغيل خدمة محددة
docker-compose restart api

# عرض السجلات
docker-compose logs -f api

# عرض السجلات لجميع الخدمات
docker-compose logs -f
```

### إدارة البيانات

```bash
# عرض Volumes
docker volume ls

# حذف Volumes (⚠️ يحذف جميع البيانات)
docker-compose down -v

# Backup PostgreSQL
docker-compose exec postgres pg_dump -U postgres postgres > backup.sql

# Restore PostgreSQL
docker-compose exec -T postgres psql -U postgres postgres < backup.sql

# Backup MongoDB
docker-compose exec mongodb mongodump --archive=/data/db/backup.archive
docker-compose cp mongodb:/data/db/backup.archive ./mongodb-backup.archive

# Restore MongoDB
docker-compose cp ./mongodb-backup.archive mongodb:/data/db/backup.archive
docker-compose exec mongodb mongorestore --archive=/data/db/backup.archive
```

### الوصول إلى الحاويات

```bash
# الوصول إلى PostgreSQL
docker-compose exec postgres psql -U postgres -d postgres

# الوصول إلى MongoDB
docker-compose exec mongodb mongosh -u admin -p 'Strong#Mongo!123' --authenticationDatabase admin

# الوصول إلى API Container
docker-compose exec api bash

# تنفيذ أمر في API Container
docker-compose exec api python -c "from app.config import settings; print(settings.API_VERSION)"
```

---

## 🔐 متغيرات البيئة

### إعدادات أساسية

```env
# API
API_PORT=3300
DEBUG=false
LOG_LEVEL=INFO

# Security
API_KEY=your-secret-api-key
```

### PostgreSQL

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
POSTGRES_PORT=5432
```

### MongoDB

```env
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=Strong#Mongo!123
MONGO_DB_NAME=chat_db
MONGO_PORT=27017
```

### LLM Keys

```env
# Required
GEMINI_API_KEY=your-gemini-api-key

# Optional
OPENAI_API_KEY=your-openai-api-key
```

---

## 🛠 Build & Deploy

### بناء الصورة

```bash
# بناء الصورة
docker-compose build

# إعادة بناء بدون cache
docker-compose build --no-cache

# بناء خدمة محددة
docker-compose build api
```

### تحديث الخدمة

```bash
# إيقاف الخدمات
docker-compose down

# سحب آخر التحديثات
git pull

# بناء الصور الجديدة
docker-compose build

# تشغيل الخدمات
docker-compose up -d
```

---

## 📊 المراقبة والصحة

### Health Checks

```bash
# فحص صحة API
curl http://localhost:3300/health

# فحص صحة PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# فحص صحة MongoDB
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### عرض المقاييس

```bash
# استخدام الموارد
docker stats

# عرض معلومات الحاويات
docker-compose ps

# عرض السجلات المباشرة
docker-compose logs -f --tail=100
```

---

## 🔍 استكشاف الأخطاء

### المشاكل الشائعة

#### 1. الخدمة لا تبدأ

```bash
# عرض السجلات
docker-compose logs api

# فحص حالة الحاويات
docker-compose ps

# فحص اتصال الشبكة
docker network ls
docker network inspect new_version_chat_network
```

#### 2. خطأ في الاتصال بقاعدة البيانات

```bash
# فحص اتصال PostgreSQL
docker-compose exec api python -c "from app.db.postgres import engine; print(engine)"

# فحص اتصال MongoDB
docker-compose exec api python -c "from app.db.mongodb import mongodb_manager; import asyncio; asyncio.run(mongodb_manager.connect())"
```

#### 3. خطأ في متغيرات البيئة

```bash
# عرض متغيرات البيئة في الحاوية
docker-compose exec api env | grep -E "(DB_|MONGO_|GEMINI_|API_)"
```

#### 4. مشكلة في Volumes

```bash
# عرض Volumes
docker volume ls

# فحص محتوى Volume
docker volume inspect new_version_exports_data
```

---

## 🚀 Production Deployment

### تحسينات للإنتاج

1. **استخدام .env محمي**
   ```bash
   chmod 600 .env
   ```

2. **إزالة hot reload**
   ```bash
   # استخدام docker-compose.yml (بدون reload)
   docker-compose up -d
   ```

3. **تفعيل Health Checks**
   - Health checks مفعلة تلقائياً في docker-compose.yml

4. **مراقبة السجلات**
   ```bash
   # استخدام log driver
   docker-compose logs -f --tail=1000 api > api.log
   ```

5. **Backup دوري**
   ```bash
   # إنشاء سكريبت backup
   # backup.sh
   #!/bin/bash
   docker-compose exec -T postgres pg_dump -U postgres postgres | gzip > backup_$(date +%Y%m%d).sql.gz
   ```

---

## 📝 ملاحظات مهمة

### Volumes
- **postgres_data**: بيانات PostgreSQL (مهمة!)
- **mongodb_data**: بيانات MongoDB (مهمة!)
- **exports_data**: ملفات Excel المصدرة
- **charts_data**: الرسوم البيانية المولدة
- **cache_data**: Cache للاستعلامات

### Ports
- **3300**: API Service
- **5432**: PostgreSQL
- **27017**: MongoDB

### Networks
- جميع الخدمات في نفس الشبكة (`chat_network`)
- يمكن الوصول إلى الخدمات عبر اسم الحاوية (postgres, mongodb)

---

## 🔄 Development vs Production

### Development Mode
```bash
docker-compose -f docker-compose.dev.yml up -d
```
- ✅ Hot reload مفعل
- ✅ DEBUG=true
- ✅ LOG_LEVEL=DEBUG
- ✅ Volume mount للكود

### Production Mode
```bash
docker-compose up -d
```
- ✅ بدون hot reload
- ✅ DEBUG=false
- ✅ LOG_LEVEL=INFO
- ✅ Read-only code mount
- ✅ Health checks
- ✅ Restart policies

---

## 📚 مراجع إضافية

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [MongoDB Docker](https://hub.docker.com/_/mongo)

---

**جاهز للاستخدام! 🎉**
