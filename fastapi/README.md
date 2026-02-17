# FloodGuard-AI Backend

🌊 Hệ thống backend cho ứng dụng giám sát và cảnh báo ngập lụt thông minh sử dụng AI

## Tính năng chính

### 🛰️ Giám sát từ vệ tinh
- Phân tích ảnh SAR từ Sentinel-1 để phát hiện vùng ngập
- Thu thập dữ liệu mưa từ GPM/TRMM
- Tích hợp dữ liệu độ cao (DEM) và dân cư

### 🤖 Phân tích AI
- Sử dụng Google Gemini AI để đánh giá rủi ro
- Đưa ra khuyến nghị hành động thông minh
- Dự báo xu hướng ngập lụt

### 📊 API RESTful
- Dữ liệu vùng ngập theo thời gian thực
- Thông tin thời tiết chi tiết
- Phân tích và báo cáo tự động

### 📧 Thông báo thông minh
- Email tự động với HTML đẹp mắt
- Tích hợp Telegram Bot
- Tùy chỉnh tần suất và nội dung

## Kiến trúc hệ thống

```
fastapi/
├── app/
│   ├── main.py              # Entry point
│   ├── core/
│   │   └── config.py        # Configuration
│   ├── models/              # Pydantic schemas
│   │   ├── region.py
│   │   ├── weather.py
│   │   ├── analysis.py
│   │   ├── subscribe.py
│   │   └── maptiles.py
│   ├── api/                 # API endpoints
│   │   ├── regions.py
│   │   ├── weather.py
│   │   ├── analysis.py
│   │   └── subscribe.py
│   ├── services/            # Business logic
│   │   ├── gee_service.py   # Google Earth Engine
│   │   ├── ai_service.py    # AI analysis
│   │   └── mail_service.py  # Email/Telegram
│   └── utils/               # Utilities
├── requirements.txt
├── .env.example
└── README.md
```

## Cài đặt

### 1. Yêu cầu hệ thống
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Google Earth Engine account
- Google Gemini API key

### 2. Clone và cài đặt dependencies

```bash
# Clone repository
git clone https://github.com/your-org/floodguard-ai-backend.git
cd floodguard-ai-backend

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows

# Cài đặt dependencies
pip install -r requirements.txt
```

### 3. Cấu hình môi trường

```bash
# Copy file .env.example
cp .env.example .env

# Chỉnh sửa file .env với thông tin của bạn
nano .env
```

**Các biến môi trường quan trọng:**

```env
# Google Earth Engine
GEE_SERVICE_ACCOUNT=your-service-account@project.iam.gserviceaccount.com
GEE_PRIVATE_KEY_PATH=./credentials/gee-key.json

# Google Gemini AI
GEMINI_API_KEY=your-gemini-api-key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/floodguard_db

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your-bot-token
```

### 4. Thiết lập Google Earth Engine

```bash
# Đăng nhập GEE
earthengine authenticate

# Tạo service account key
# 1. Truy cập: https://console.cloud.google.com
# 2. Tạo Service Account
# 3. Tải xuống JSON key
# 4. Đặt vào ./credentials/gee-key.json
```

### 5. Khởi chạy server

```bash
# Development mode (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server sẽ chạy tại: http://localhost:8000

## API Documentation

### Swagger UI
Truy cập: http://localhost:8000/docs

### ReDoc
Truy cập: http://localhost:8000/redoc

## Endpoints chính

### 1. Regions API

#### GET /api/regions
Lấy danh sách các vùng giám sát

**Query Parameters:**
- `date_filter`: Lọc theo ngày (YYYY-MM-DD)
- `severity`: Lọc theo mức độ (Low/Moderate/High/Critical)
- `min_area`: Diện tích ngập tối thiểu (km²)

**Response:**
```json
{
  "total": 6,
  "regions": [
    {
      "id": "1",
      "name": "Quảng Trị",
      "submergedArea": 450.5,
      "rainfall": 320.0,
      "avgDepth": 1.2,
      "severity": "High",
      "affectedPopulation": 12500,
      "estimatedLoss": 125.5
    }
  ],
  "timestamp": "2024-01-15T10:30:00"
}
```

#### GET /api/regions/{region_id}
Lấy thông tin chi tiết một vùng

#### GET /api/regions/statistics/summary
Lấy thống kê tổng quan

### 2. Weather API

#### GET /api/weather
Lấy dữ liệu thời tiết

**Query Parameters:**
- `region_id`: ID vùng
- `from_date`: Ngày bắt đầu
- `to_date`: Ngày kết thúc

#### GET /api/weather/statistics
Thống kê thời tiết theo khoảng thời gian

### 3. AI Analysis API

#### POST /api/ai-analysis
Phân tích tình hình ngập lụt bằng AI

**Request Body:**
```json
{
  "regions": [...],
  "weather": [...],
  "analysis_type": "comprehensive",
  "include_forecast": true
}
```

**Response:**
```json
{
  "summary": "Tình trạng ngập lụt nghiêm trọng...",
  "risk_assessment": "Rủi ro cực cao...",
  "risk_level": "Critical",
  "recommendations": [...],
  "confidence_score": 0.94,
  "estimated_total_loss": 450.8
}
```

#### POST /api/ai-analysis/quick
Phân tích nhanh với dữ liệu hiện tại

#### GET /api/ai-analysis/report/text
Tạo báo cáo văn bản

### 4. Subscription API

#### POST /api/subscribe
Đăng ký nhận thông báo

**Request Body:**
```json
{
  "contact": "user@example.com",
  "frequency": "daily",
  "channel": "email",
  "regions": ["Quảng Trị"],
  "min_severity": "Moderate"
}
```

#### DELETE /api/subscribe
Hủy đăng ký

## Testing

```bash
# Chạy tests
pytest

# Với coverage
pytest --cov=app tests/

# Chỉ test một module
pytest tests/test_regions.py
```

## Deployment

### Docker

```bash
# Build image
docker build -t floodguard-backend .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name floodguard-backend \
  floodguard-backend
```

### Docker Compose

```bash
# Khởi động tất cả services
docker-compose up -d

# Xem logs
docker-compose logs -f

# Dừng services
docker-compose down
```

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
```bash
# Xem logs realtime
tail -f logs/app.log

# Tìm kiếm errors
grep "ERROR" logs/app.log
```

## Troubleshooting

### Lỗi Google Earth Engine
```
Error: Earth Engine not initialized
```
**Giải pháp:** Kiểm tra service account và key file

### Lỗi Gemini API
```
Error: Failed to initialize Gemini AI
```
**Giải pháp:** Kiểm tra API key và quota

### Lỗi Email
```
Error: Failed to send email
```
**Giải pháp:** Kiểm tra SMTP settings và app password

## Contributing

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## License

MIT License - xem file [LICENSE](LICENSE) để biết thêm chi tiết

## Contact

- Email: support@floodguard-ai.com
- Website: https://floodguard-ai.com
- GitHub: https://github.com/your-org/floodguard-ai

## Acknowledgments

- Google Earth Engine
- Google Gemini AI
- FastAPI Framework
- Copernicus Sentinel Data
