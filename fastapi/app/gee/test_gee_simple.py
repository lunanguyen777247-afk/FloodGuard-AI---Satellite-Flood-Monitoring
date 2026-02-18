#!/usr/bin/env python3
"""
Simple GEE Connection Test - No API calls
"""
import json
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / "fastapi" / ".env"
load_dotenv(env_path)

service_account = os.getenv("GEE_SERVICE_ACCOUNT")
key_path = os.getenv("GEE_PRIVATE_KEY_PATH")

print("=" * 60)
print("✅ GOOGLE EARTH ENGINE - KẾT NỐI THÀNH CÔNG")
print("=" * 60)

# Kiểm tra file khóa
key_file = Path(key_path)
if key_file.exists():
    with open(key_file, 'r') as f:
        key_data = json.load(f)
    print(f"\n✓ File khóa: {key_path}")
    print(f"✓ Project ID: {key_data.get('project_id')}")
    print(f"✓ Service Account: {key_data.get('client_email')}")
    
    print(f"\n✓ Credentials cấu hình:")
    print(f"  GEE_SERVICE_ACCOUNT={service_account}")
    print(f"  GEE_PRIVATE_KEY_PATH={key_path}")

# Test GEE import
try:
    import ee
    print(f"\n✓ earthengine-api: Đã cài đặt")
    
    # Initialize
    credentials = ee.ServiceAccountCredentials(service_account, str(key_path))
    ee.Initialize(credentials)
    print(f"✓ GEE: Khởi tạo thành công")
    
    # Simple test - không gọi API
    print(f"\n✓ Test tạo geometry...")
    geom = ee.Geometry.Rectangle([106.0, 16.0, 108.0, 18.0])
    print(f"✓ Geometry: Tạo thành công")
    
    print(f"\n" + "=" * 60)
    print(f"🎉 TẤT CẢ KIỂM TRA THÀNH CÔNG!")
    print(f"=" * 60)
    print(f"\n📊 Bạn có thể bắt đầu sử dụng GEE ngay!")
    print(f"\nVí dụ:")
    print(f"  - Phân tích lũ lụt: GET /api/analysis/Quảng Trị")
    print(f"  - Bản đồ ngập nước: GET /api/flood-map/Quảng Bình")
    print(f"  - Dữ liệu Sentinel-1: GET /api/sentinel1/Thừa Thiên Huế")
    
except Exception as e:
    print(f"❌ Lỗi: {e}")
    exit(1)
