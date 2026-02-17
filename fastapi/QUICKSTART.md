# FloodGuard-AI Backend - Quick Start Guide

## 🚀 Bắt đầu nhanh trong 5 phút

### Bước 1: Clone và Setup (1 phút)
```bash
cd floodguard-ai-backend
cp .env.example .env
```

### Bước 2: Cấu hình API Keys (2 phút)
Mở file `.env` và điền các thông tin:
```env
# Bắt buộc
GEMINI_API_KEY=your-key-here          # Lấy từ: https://makersuite.google.com/app/apikey
GEE_SERVICE_ACCOUNT=your-account      # Google Earth Engine service account
GEE_PRIVATE_KEY_PATH=./credentials/gee-key.json

# Email (tùy chọn)
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password        # App password từ Gmail
```

### Bước 3: Chạy với Docker (2 phút)
```bash
# Build và start
docker-compose up -d

# Xem logs
docker-compose logs -f backend
```

**Hoặc chạy trực tiếp (không Docker):**
```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

### Bước 4: Test API
```bash
# Health check
curl http://localhost:8000/health

# Get regions data
curl http://localhost:8000/api/regions

# Open API docs
open http://localhost:8000/docs
```

---

## 📚 Tài liệu chi tiết

- **README.md**: Tổng quan và cài đặt đầy đủ
- **ARCHITECTURE.md**: Kiến trúc hệ thống và data flow
- **DEPLOYMENT_GUIDE.md**: Hướng dẫn triển khai production

---

## 🔑 API Endpoints chính

### 1. Regions (Vùng ngập)
```bash
GET /api/regions                    # Danh sách vùng
GET /api/regions/{id}               # Chi tiết vùng
GET /api/regions/statistics/summary # Thống kê tổng quan
```

### 2. Weather (Thời tiết)
```bash
GET /api/weather                    # Dữ liệu thời tiết
GET /api/weather/statistics         # Thống kê thời tiết
```

### 3. AI Analysis (Phân tích AI)
```bash
POST /api/ai-analysis               # Phân tích chi tiết
POST /api/ai-analysis/quick         # Phân tích nhanh
GET  /api/ai-analysis/report/text   # Báo cáo văn bản
```

### 4. Subscriptions (Đăng ký)
```bash
POST   /api/subscribe               # Đăng ký nhận tin
DELETE /api/subscribe               # Hủy đăng ký
GET    /api/subscribe/statistics    # Thống kê đăng ký
```

---

## 🧪 Test nhanh

### Test phân tích AI
```bash
curl -X POST http://localhost:8000/api/ai-analysis/quick
```

### Test gửi email
```bash
curl -X POST "http://localhost:8000/api/subscribe" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "your-email@example.com",
    "frequency": "daily",
    "channel": "email"
  }'
```

---

## ❗ Troubleshooting

**Lỗi: "Earth Engine not initialized"**
```bash
# Kiểm tra service account key
ls -la credentials/gee-key.json

# Test GEE connection
python -c "import ee; ee.Initialize(); print('OK')"
```

**Lỗi: "Failed to initialize Gemini AI"**
```bash
# Kiểm tra API key
echo $GEMINI_API_KEY

# Test Gemini
python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print('OK')"
```

**Port đã được sử dụng**
```bash
# Đổi port trong docker-compose.yml hoặc chạy:
uvicorn app.main:app --port 8001
```

---

## 🎯 Next Steps

1. **Tích hợp Frontend**: Kết nối với React app
2. **Cấu hình Production**: Theo DEPLOYMENT_GUIDE.md
3. **Setup Monitoring**: Prometheus + Grafana
4. **Tối ưu Performance**: Redis caching, database indexing

---

## 📞 Support

- 📧 Email: support@floodguard-ai.com
- 📚 Docs: http://localhost:8000/docs
- 🐛 Issues: GitHub Issues

**Chúc bạn triển khai thành công! 🎉**
