#!/usr/bin/env python3
"""
GEE Connection Verification Script
Kiểm tra và xác thực kết nối Google Earth Engine
"""

import json
import sys
import os
from pathlib import Path

def check_gee_connection(key_path: str, service_account_email: str) -> bool:
    """
    Kiểm tra kết nối GEE
    
    Args:
        key_path: Đường dẫn tới file khóa JSON
        service_account_email: Email của service account
        
    Returns:
        bool: True nếu kết nối thành công
    """
    try:
        import ee
        import google.auth
        
        print("🔍 Kiểm tra kết nối Google Earth Engine...")
        print(f"📁 File khóa: {key_path}")
        print(f"📧 Service Account: {service_account_email}")
        
        # Kiểm tra file khóa tồn tại
        key_file = Path(key_path)
        if not key_file.exists():
            print(f"❌ Lỗi: File khóa không tìm thấy tại {key_path}")
            return False
        
        print(f"✓ File khóa tồn tại")
        
        # Kiểm tra nội dung JSON
        try:
            with open(key_file, 'r') as f:
                key_data = json.load(f)
            print(f"✓ File JSON hợp lệ")
            print(f"  - Project ID: {key_data.get('project_id')}")
            print(f"  - Client Email: {key_data.get('client_email')}")
        except json.JSONDecodeError:
            print(f"❌ Lỗi: File JSON không hợp lệ")
            return False
        
        # Khởi tạo GEE
        print(f"\n🔐 Khởi tạo GEE...")
        credentials = ee.ServiceAccountCredentials(service_account_email, str(key_path))
        ee.Initialize(credentials)
        print(f"✓ GEE khởi tạo thành công")
        
        # Test API call
        print(f"\n🧪 Test gọi API...")
        try:
            # Lấy danh sách các bộ sưu tập
            image_collection = ee.ImageCollection('COPERNICUS/S1_GRD')
            size = image_collection.size().getInfo()
            print(f"✓ Lấy dữ liệu Sentinel-1 thành công ({size} images)")
            
            # Test lấy hình ảnh cụ thể
            first_image = image_collection.first()
            image_id = first_image.id().getInfo()
            print(f"✓ Hình ảnh đầu tiên: {image_id}")
            
        except Exception as e:
            print(f"⚠️  Cảnh báo khi gọi API: {e}")
            return False
        
        print(f"\n✅ Kết nối GEE thành công!")
        return True
        
    except ImportError as e:
        print(f"❌ Lỗi: Thư viện không cài đặt: {e}")
        print(f"   Cài đặt bằng: pip install earthengine-api google-auth")
        return False
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return False

def setup_gee_environment() -> bool:
    """
    Thiết lập môi trường GEE từ file .env
    
    Returns:
        bool: True nếu thiết lập thành công
    """
    try:
        from dotenv import load_dotenv
        
        # Tải biến từ .env - tìm từ project root
        script_dir = Path(__file__).parent
        # Đi lên từ app/gee -> app -> fastapi -> root
        project_root = script_dir.parent.parent.parent
        env_path = project_root / "fastapi" / ".env"
        
        if not env_path.exists():
            print(f"⚠️  File .env không tìm thấy tại {env_path}")
            return False
        
        load_dotenv(env_path)
        
        # Lấy cấu hình
        service_account = os.getenv("GEE_SERVICE_ACCOUNT")
        private_key_path = os.getenv("GEE_PRIVATE_KEY_PATH")
        
        if not service_account or not private_key_path:
            print(f"❌ Lỗi: Chưa cấu hình GEE_SERVICE_ACCOUNT hoặc GEE_PRIVATE_KEY_PATH trong .env")
            return False
        
        print(f"📋 Cấu hình từ .env:")
        print(f"  - GEE_SERVICE_ACCOUNT: {service_account}")
        print(f"  - GEE_PRIVATE_KEY_PATH: {private_key_path}")
        
        return check_gee_connection(private_key_path, service_account)
        
    except ImportError:
        print(f"⚠️  Thư viện python-dotenv chưa cài đặt")
        print(f"   Cài đặt bằng: pip install python-dotenv")
        return False
    except Exception as e:
        print(f"❌ Lỗi thiết lập: {e}")
        return False

def manual_setup() -> bool:
    """
    Thiết lập thủ công bằng cách nhập thông tin
    
    Returns:
        bool: True nếu thiết lập thành công
    """
    print("\n📝 Thiết lập thủ công:")
    
    service_account = input("Nhập Service Account Email: ").strip()
    key_path = input("Nhập đường dẫn tới file khóa JSON: ").strip()
    
    if not service_account or not key_path:
        print("❌ Thông tin không hợp lệ")
        return False
    
    return check_gee_connection(key_path, service_account)

if __name__ == "__main__":
    print("=" * 60)
    print("🌍 GOOGLE EARTH ENGINE - XÁC THỰC KẾT NỐI")
    print("=" * 60)
    
    # Cố gắng thiết lập từ .env
    success = setup_gee_environment()
    
    if not success:
        print(f"\n💡 Bạn có muốn thiết lập thủ công không? (y/n)")
        choice = input().strip().lower()
        if choice == 'y':
            success = manual_setup()
    
    sys.exit(0 if success else 1)
