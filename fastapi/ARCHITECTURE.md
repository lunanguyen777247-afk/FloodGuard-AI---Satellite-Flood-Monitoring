# FloodGuard-AI Backend Architecture

## Tổng quan kiến trúc

FloodGuard-AI Backend được thiết kế theo kiến trúc **layered architecture** với các tầng rõ ràng:

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
│  (React Frontend, Mobile App, External Integrations)         │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
┌──────────────────────┴──────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Regions  │ │ Weather  │ │ Analysis │ │Subscribe │       │
│  │   API    │ │   API    │ │   API    │ │   API    │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                   Service Layer                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │   GEE    │ │    AI    │ │   Mail   │                    │
│  │ Service  │ │ Service  │ │ Service  │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                  External Services                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Google  │ │  Google  │ │   SMTP   │ │ Telegram │       │
│  │   Earth  │ │  Gemini  │ │  Server  │ │   Bot    │       │
│  │  Engine  │ │    AI    │ │          │ │          │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Các thành phần chính

### 1. API Layer (`app/api/`)

Xử lý HTTP requests và responses, validation, error handling.

**Modules:**
- `regions.py`: Quản lý dữ liệu vùng ngập
- `weather.py`: Dữ liệu thời tiết và khí tượng
- `analysis.py`: Phân tích AI và báo cáo
- `subscribe.py`: Quản lý đăng ký thông báo
- `maptiles.py`: Xuất bản đồ và tiles

### 2. Service Layer (`app/services/`)

Business logic và tích hợp với external services.

**GEE Service (`gee_service.py`)**
```python
class GEEService:
    - get_sentinel1_flood_mask()  # Phát hiện vùng ngập từ SAR
    - get_rainfall_data()          # Lượng mưa từ GPM
    - get_dem_data()               # Dữ liệu độ cao
    - calculate_flood_statistics() # Tính toán thống kê
    - estimate_affected_population() # Ước tính dân số ảnh hưởng
```

**AI Service (`ai_service.py`)**
```python
class AIService:
    - analyze_flood_situation()    # Phân tích tổng thể
    - generate_summary_report()    # Tạo báo cáo
    - _build_analysis_prompt()     # Xây dựng prompt cho AI
```

**Mail Service (`mail_service.py`)**
```python
class MailService:
    - send_email()                 # Gửi email chung
    - send_flood_alert()           # Cảnh báo ngập lụt
    - send_daily_report()          # Báo cáo hàng ngày
    - send_telegram_message()      # Thông báo Telegram
```

### 3. Model Layer (`app/models/`)

Pydantic models cho data validation và serialization.

**Hierarchy:**
```
BaseModel (Pydantic)
├── RegionBase → RegionCreate, Region, RegionDetail
├── WeatherBase → WeatherCreate, Weather
├── AnalysisRequest → AnalysisResult
├── SubscriptionBase → SubscriptionCreate, Subscription
└── TileRequest → TileResponse
```

### 4. Core Layer (`app/core/`)

Configuration, settings, utilities.

```python
class Settings(BaseSettings):
    # Application config
    # Database URLs
    # API keys
    # Service configurations
```

## Data Flow

### Luồng dữ liệu phân tích ngập lụt

```
1. Client Request
   │
   ├─> GET /api/regions
   │   ├─> regions.get_regions()
   │   │   ├─> gee_service.get_region_geometry()
   │   │   ├─> gee_service.get_sentinel1_flood_mask()
   │   │   ├─> gee_service.calculate_flood_statistics()
   │   │   └─> gee_service.estimate_affected_population()
   │   └─> Return: RegionListResponse
   │
   ├─> POST /api/ai-analysis
   │   ├─> analysis.analyze_flood_situation()
   │   │   ├─> ai_service.analyze_flood_situation()
   │   │   │   ├─> Build prompt from data
   │   │   │   ├─> Call Gemini API
   │   │   │   └─> Parse response
   │   │   └─> Return: AnalysisResult
   │   │
   │   └─> Background: Send notifications
   │       ├─> mail_service.send_flood_alert()
   │       └─> mail_service.send_telegram_message()
   │
   └─> POST /api/subscribe
       ├─> subscribe.create_subscription()
       │   ├─> Validate contact
       │   ├─> Store in database
       │   └─> Send confirmation email
       └─> Return: SubscriptionResponse
```

### Luồng xử lý dữ liệu vệ tinh

```
Google Earth Engine
    │
    ├─> Sentinel-1 SAR (Flood Detection)
    │   ├─> Filter by date & region
    │   ├─> Create median composite
    │   ├─> Apply water detection threshold
    │   └─> Morphological operations
    │
    ├─> GPM IMERG (Rainfall)
    │   ├─> Filter precipitation data
    │   ├─> Calculate total rainfall
    │   └─> Extract statistics
    │
    ├─> SRTM DEM (Elevation)
    │   ├─> Extract elevation data
    │   └─> Calculate slope
    │
    └─> WorldPop (Population)
        ├─> Get population density
        └─> Calculate affected population
```

## Database Schema

### Regions Table
```sql
CREATE TABLE regions (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    submerged_area FLOAT,
    rainfall FLOAT,
    avg_depth FLOAT,
    severity VARCHAR,
    affected_population INT,
    estimated_loss FLOAT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Weather Table
```sql
CREATE TABLE weather (
    id VARCHAR PRIMARY KEY,
    region_id VARCHAR REFERENCES regions(id),
    date DATE NOT NULL,
    rainfall FLOAT,
    temperature FLOAT,
    humidity FLOAT,
    wind_speed FLOAT,
    pressure FLOAT,
    created_at TIMESTAMP
);
```

### Subscriptions Table
```sql
CREATE TABLE subscriptions (
    id VARCHAR PRIMARY KEY,
    contact VARCHAR NOT NULL,
    frequency VARCHAR,
    channel VARCHAR,
    regions TEXT[],
    min_severity VARCHAR,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_notification_at TIMESTAMP
);
```

## Security

### Authentication & Authorization
- API Key authentication cho external integrations
- JWT tokens cho user sessions (future)
- Rate limiting per endpoint
- CORS policy configuration

### Data Protection
- HTTPS only in production
- Environment variables for secrets
- Service account keys in secure storage
- Database connection encryption

### Input Validation
- Pydantic models cho tất cả inputs
- Query parameter validation
- File upload restrictions
- SQL injection prevention

## Performance Optimization

### Caching Strategy
```python
Redis Cache:
    - Region data: 1 hour TTL
    - Weather data: 30 minutes TTL
    - AI analysis: 2 hours TTL
    - Map tiles: 24 hours TTL
```

### Background Tasks
```python
Celery Tasks:
    - Update region data: Every 6 hours
    - Fetch weather data: Every 1 hour
    - Send notifications: Based on subscription frequency
    - Generate reports: Daily at 8 AM
```

### Database Optimization
- Indexes on frequently queried fields
- Connection pooling
- Query result caching
- Batch operations for bulk updates

## Monitoring & Logging

### Logging Levels
```python
DEBUG: Development debugging
INFO: Normal operations
WARNING: Non-critical issues
ERROR: Error conditions
CRITICAL: System failures
```

### Metrics to Monitor
- API response times
- Error rates by endpoint
- GEE API usage
- Gemini AI API calls
- Email delivery rate
- Active subscriptions
- Cache hit rates

### Health Checks
```python
/health endpoint returns:
{
    "status": "healthy",
    "services": {
        "api": "operational",
        "database": "operational",
        "redis": "operational",
        "gee": "operational",
        "ai": "operational"
    }
}
```

## Deployment Architecture

### Production Setup
```
Load Balancer (Nginx)
    │
    ├─> App Server 1 (Uvicorn)
    ├─> App Server 2 (Uvicorn)
    └─> App Server 3 (Uvicorn)
         │
         ├─> PostgreSQL (Primary + Replica)
         ├─> Redis Cluster
         ├─> Celery Workers
         └─> Celery Beat
```

### Scaling Strategy
- Horizontal scaling: Multiple app instances
- Database replication: Read replicas
- Redis clustering: Distributed cache
- CDN: Static assets and map tiles
- Background workers: Multiple Celery instances

## Error Handling

### Error Response Format
```json
{
    "error": "Error type",
    "message": "Detailed error message",
    "timestamp": "2024-01-15T10:30:00Z",
    "path": "/api/endpoint"
}
```

### Retry Logic
- External API calls: 3 retries with exponential backoff
- Email sending: 2 retries
- Database operations: Automatic reconnection

## Future Enhancements

1. **Real-time Updates**: WebSocket support for live data
2. **Machine Learning**: Custom ML models for prediction
3. **Multi-language**: i18n support
4. **Mobile API**: Optimized endpoints for mobile apps
5. **GraphQL**: Alternative API interface
6. **Advanced Analytics**: Time-series analysis and trends
7. **Integration Hub**: Webhook support for third-party integrations
