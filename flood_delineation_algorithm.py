#!/usr/bin/env python3
"""
Thuật Toán Khoanh Vùng Ngập Lụt (Flood Area Delineation)
Sử dụng Google Earth Engine & Sentinel-1 SAR Data
"""

import ee
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
from dotenv import load_dotenv

print("=" * 70)
print("🌊 THUẬT TOÁN KHOANH VÙNG NGẬP LỤT - GEE")
print("=" * 70)

# ============ SETUP ============
print("\n1️⃣  Thiết lập GEE...")

# Load environment
project_root = Path(__file__).parent
env_path = project_root / "fastapi" / ".env"
load_dotenv(env_path)

service_account = os.getenv("GEE_SERVICE_ACCOUNT")
key_path = os.getenv("GEE_PRIVATE_KEY_PATH")

# Initialize GEE
credentials = ee.ServiceAccountCredentials(service_account, str(key_path))
ee.Initialize(credentials)
print(f"✓ GEE initialized")
print(f"  Service Account: {service_account}")

# ============ DEFINE REGION ============
print("\n2️⃣  Định nghĩa vùng nghiên cứu...")

country = "Viet Nam"
provinces = ["Thua Thien - Hue", "Da Nang City"]

adm1 = ee.FeatureCollection("FAO/GAUL/2015/level1")

def get_region(country_name, province_list):
    """Lấy hình học của các tỉnh"""
    fc_country = adm1.filter(ee.Filter.eq("ADM0_NAME", country_name))
    features = []
    for p in province_list:
        f = fc_country.filter(ee.Filter.eq("ADM1_NAME", p)).first()
        features.append(f)
    return ee.FeatureCollection(features).union().geometry()

geometry = get_region(country, provinces)
print(f"✓ Vùng: {', '.join(provinces)}")
print(f"✓ Quốc gia: {country}")

# ============ DEFINE TIME RANGE ============
print("\n3️⃣  Định nghĩa khoảng thời gian...")

# Mùa lũ lụt thường là tháng 9-11 ở miền Trung Việt Nam
start_date = "2024-08-15"
end_date = "2024-11-15"

print(f"✓ Thời gian: {start_date} -> {end_date}")

# ============ LOAD SENTINEL-1 DATA ============
print("\n4️⃣  Tải dữ liệu Sentinel-1 SAR...")

# Sentinel-1 GRD (Ground Range Detected)
s1 = ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(geometry).filterDate(start_date, end_date).filter(
    ee.Filter.eq('instrumentMode', 'IW')
).filter(
    ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')
).select('VV')

count = s1.size().getInfo()
print(f"✓ Tìm thấy {count} ảnh Sentinel-1")

# ============ CREATE COMPOSITE ============
print("\n5️⃣  Tạo composite từ ảnh...")

# Median composite từ các ảnh VV
s1_composite = s1.median().clip(geometry)
print(f"✓ Tạo composite median thành công")

# ============ WATER DETECTION ============
print("\n6️⃣  Phát hiện vùng nước (Water Detection)...")

# VV threshold cho water detection (dB)
# Nước phản xạ ít hơn mặt đất => giá trị thấp hơn
vv_threshold = -15.0

# Water mask: pixels với VV < threshold => nước
water_mask = s1_composite.lt(vv_threshold).rename('water')
print(f"✓ Water Threshold: {vv_threshold} dB")

# Apply morphological operations để loại bỏi noise
print(f"✓ Áp dụng phép toán morphological...")
water_mask = water_mask.focal_median(radius=30, kernelType='circle', units='meters')
water_mask = water_mask.focal_mode(radius=60, kernelType='circle', units='meters')

# ============ FLOOD CLASSIFICATION ============
print("\n7️⃣  Phân loại ngập lụt...")

# Thêm NDVI (Normalized Difference Vegetation Index)
b4 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(
    geometry
).filterDate(start_date, end_date).select('B4', 'B8').median()

# NDVI = (NIR - RED) / (NIR + RED)
ndvi = b4.normalizedDifference(['B8', 'B4']).rename('ndvi')
print(f"✓ Tính NDVI")

# Tạo classification
# 0 = Non-flooded, 1 = Water/Flooded
flood_map = water_mask.select('water').rename('flood')

# ============ POST-PROCESSING ============
print("\n8️⃣  Xử lý sau để cải thiện chất lượng...")

# Sử dụng neighborhood analysis để cải thiện ranh giới
flood_map = flood_map.focal_mode(radius=30, kernelType='circle', units='meters')

# Loại bỏ các vùng nhỏ bằng morphological operations
flood_map = flood_map.focal_min(radius=30, kernelType='circle', units='meters')
flood_map = flood_map.focal_max(radius=30, kernelType='circle', units='meters')

print(f"✓ Post-processing hoàn thành")

# ============ COMPUTE STATISTICS ============
print("\n9️⃣  Tính toán thống kê...")

# Diện tích ngập lụt
stats = flood_map.reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=geometry,
    scale=30,
    maxPixels=1e8
).getInfo()

total_pixels = ee.Image.pixelArea().select('area').reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=geometry,
    scale=30,
    maxPixels=1e8
).getInfo()

flooded_pixels = stats.get('flood', 0)
flooded_area_km2 = flooded_pixels * 30 * 30 / 1e6  # Tính từ pixels (30mx30m) sang km²
total_area_km2 = total_pixels['area'] / 1e6

flood_percentage = (flooded_area_km2 / total_area_km2) * 100

print(f"✓ Tổng diện tích nghiên cứu: {total_area_km2:,.1f} km²")
print(f"✓ Diện tích ngập lụt: {flooded_area_km2:,.1f} km²")
print(f"✓ Tỉ lệ ngập lụt: {flood_percentage:.2f}%")

# ============ EXPORT RESULTS ============
print("\n🔟 Xuất kết quả...")

output_dir = Path(__file__).parent / "flood_analysis_results"
output_dir.mkdir(exist_ok=True)

# Kết quả dưới dạng GeoJSON
result = {
    "timestamp": datetime.now().isoformat(),
    "region": provinces,
    "country": country,
    "date_range": {
        "start": start_date,
        "end": end_date
    },
    "algorithm": {
        "method": "Sentinel-1 SAR with VV Threshold",
        "vv_threshold_db": vv_threshold,
        "composite_type": "median",
        "morphological_ops": "median + mode"
    },
    "results": {
        "total_area_km2": round(total_area_km2, 2),
        "flooded_area_km2": round(flooded_area_km2, 2),
        "flood_percentage": round(flood_percentage, 2),
        "sentinel1_images_used": count
    },
    "gee_info": {
        "service_account": service_account,
        "project_id": "driven-torus-431807-u3"
    }
}

# Lưu JSON
result_file = output_dir / f"flood_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(result_file, 'w') as f:
    json.dump(result, f, indent=2)

print(f"✓ Lưu kết quả: {result_file}")

# ============ VISUALIZATION ============
print("\n📊 Kết quả cuối cùng:")
print("-" * 70)
print(f"🌍 Vùng: {', '.join(provinces)}, {country}")
print(f"📅 Thời gian: {start_date} to {end_date}")
print(f"📡 Dữ liệu: Sentinel-1 SAR ({count} ảnh)")
print(f"📏 Độ phân giải: 30m")
print("-" * 70)
print(f"🌊 KHOẢNG VÙNG NGẬP LỤT:")
print(f"   • Tổng diện tích: {total_area_km2:,.1f} km²")
print(f"   • Diện tích ngập: {flooded_area_km2:,.1f} km²")
print(f"   • Tỉ lệ: {flood_percentage:.2f}%")
print("-" * 70)

# ============ NEXT STEPS ============
print("\n✨ Bước tiếp theo:")
print("  1. Xem kết quả chi tiết: cat flood_analysis_results/*.json")
print("  2. Export GeoTIFF: Sử dụng fastapi/app/api/analysis.py")
print("  3. Trực quan hóa bản đồ: Sử dụng folium hoặc geemap")
print()

print("✅ Thuật toán khoanh vùng ngập lụt hoàn tất!")
print("=" * 70)
