#!/usr/bin/env python3
"""
Simple GEE Connection Test - Chỉ kiểm tra credentials
"""
import json
import sys
from pathlib import Path

print("=" * 70)
print("✅ GOOGLE EARTH ENGINE - KIỂM TRA KẾT NỐI ĐƠN GIẢN")
print("=" * 70)

# Cấu hình đường dẫn - từ app/gee -> app -> fastapi -> root
script_dir = Path(__file__).parent  # app/gee
project_root = script_dir.parent.parent.parent  # root

key_path = project_root / "fastapi" / "config" / "gee-key.json"
env_path = project_root / "fastapi" / ".env"

print(f"\n📂 Kiểm tra file...")
print(f"  Project Root: {project_root}")

# Kiểm tra file .env
if env_path.exists():
    print(f"  ✓ .env: {env_path}")
else:
    print(f"  ✗ .env KHÔNG TÌM THẤY: {env_path}")
    sys.exit(1)

# Kiểm tra file khóa
if key_path.exists():
    print(f"  ✓ gee-key.json: {key_path}")
else:
    print(f"  ✗ gee-key.json KHÔNG TÌM THẤY: {key_path}")
    sys.exit(1)

# Kiểm tra nội dung JSON
print(f"\n📋 Kiểm tra JSON...")
try:
    with open(key_path, 'r') as f:
        key_data = json.load(f)
    print(f"  ✓ File JSON hợp lệ")
    print(f"  ✓ Project ID: {key_data.get('project_id')}")
    print(f"  ✓ Client Email: {key_data.get('client_email')}")
    print(f"  ✓ Private Key: {'*' * 50} (ẩn)")
except Exception as e:
    print(f"  ✗ Lỗi JSON: {e}")
    sys.exit(1)

# Kiểm tra .env
print(f"\n📝 Kiểm tra .env...")
try:
    from dotenv import load_dotenv
    import os
    
    load_dotenv(env_path)
    service_account = os.getenv("GEE_SERVICE_ACCOUNT")
    gee_key_path = os.getenv("GEE_PRIVATE_KEY_PATH")
    
    print(f"  ✓ GEE_SERVICE_ACCOUNT: {service_account}")
    print(f"  ✓ GEE_PRIVATE_KEY_PATH: {gee_key_path}")
except Exception as e:
    print(f"  ✗ Lỗi .env: {e}")
    sys.exit(1)

# Kiểm tra earthengine-api
print(f"\n📦 Kiểm tra thư viện...")
try:
    import ee
    print(f"  ✓ earthengine-api: Đã cài đặt")
except ImportError:
    print(f"  ✗ earthengine-api: CHƯA CÀI")
    sys.exit(1)

# Khởi tạo GEE (không gọi API)
print(f"\n🔐 Khởi tạo GEE...")
try:
    credentials = ee.ServiceAccountCredentials(service_account, str(key_path))
    ee.Initialize(credentials)
    print(f"  ✓ GEE khởi tạo thành công")
except Exception as e:
    print(f"  ✗ Lỗi khởi tạo: {e}")
    sys.exit(1)

# Test tạo geometry (không gọi API)
print(f"\n🧪 Test tạo geometry...")
try:
    geom = ee.Geometry.Rectangle([106.0, 16.0, 108.0, 18.0])
    print(f"  ✓ Geometry tạo thành công")
except Exception as e:
    print(f"  ✗ Lỗi geometry: {e}")
    sys.exit(1)

print(f"\n" + "=" * 70)
print(f"🎉 TẤT CẢ KIỂM TRA THÀNH CÔNG!")
print(f"=" * 70)
print(f"\n📊 GEE sẵn sàng để sử dụng!")
print(f"\nCác API endpoints có sẵn:")
print(f"  • GET /api/regions - Danh sách vùng")
print(f"  • GET /api/analysis/{{region}} - Phân tích lũ lụt")
print(f"  • GET /api/flood-map/{{region}} - Bản đồ ngập nước")
print(f"  • GET /api/sentinel1/{{region}} - Dữ liệu Sentinel-1")
print(f"\nKhởi động server: uvicorn app.main:app --reload")
print()
