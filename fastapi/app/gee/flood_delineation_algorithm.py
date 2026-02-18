#!/usr/bin/env python3
"""
Thuật Toán Khoanh Vùng Ngập Lụt (Flood Area Delineation)
Sử dụng Google Earth Engine & Sentinel-1 SAR Data

Cải tiến:
- Refactor thành class FloodDetector
- Sửa lỗi double-convert dB
- Thêm permanent water mask (JRC)
- So sánh pre-flood vs flood để giảm false positive
- Tích hợp NDVI vào phân loại
- Loại bỏ hardcode project ID
"""

import ee
import json
import os
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Config ────────────────────────────────────────────────────────────────────
class FloodConfig:
    """Tập trung toàn bộ tham số cấu hình."""

    # Vùng & thời gian
    COUNTRY: str = "Viet Nam"
    ANALYZE_WHOLE_COUNTRY: bool = True
    PROVINCES: list[str] = ["Thua Thien - Hue", "Da Nang City"]

    # Khoảng thời gian ngập lụt
    FLOOD_START: str = "2024-08-15"
    FLOOD_END: str = "2024-11-15"

    # Khoảng thời gian trước lũ (baseline) — 1 tháng trước
    PRE_FLOOD_START: str = "2024-06-01"
    PRE_FLOOD_END: str = "2024-08-14"

    # Thuật toán
    VV_THRESHOLD_DB: float = -15.0      # ngưỡng phát hiện nước (dB)
    CHANGE_THRESHOLD_DB: float = -3.0   # ngưỡng thay đổi pre→flood (dB)
    MORPHOLOGY_RADIUS_M: int = 30       # bán kính morphological (m)
    COMPUTE_SCALE_WHOLE: int = 100      # scale toàn quốc (m)
    COMPUTE_SCALE_PROVINCE: int = 30    # scale tỉnh (m)
    MAX_PIXELS: float = 1e13
    USE_VH: bool = True                 # sử dụng VH hoặc ratio khi có
    RATIO_THRESHOLD_DB: float = -2.0    # ngưỡng VV-VH (dB) để phát hiện nước
    ADAPTIVE_STD_FACTOR: float = 0.5    # hệ số cho ngưỡng adaptive = mean - k*std
    LOSS_BILLION_PER_HA: float = 0.005  # ước tính thiệt hại (tỷ VND) trên mỗi ha
    POP_DENSITY_PER_HA: int = 10        # mặc định dân số (người/ha) nếu không có raster

    # Permanent water mask
    JRC_OCCURRENCE_THRESHOLD: int = 80  # % xuất hiện nước tối thiểu → thường trực

    # Output
    OUTPUT_DIR: str = "flood_analysis_results"


# ── GEE Initializer ───────────────────────────────────────────────────────────
def init_gee(env_path: Path) -> None:
    """Load credentials từ .env và khởi tạo Earth Engine."""
    load_dotenv(env_path)

    service_account = os.getenv("GEE_SERVICE_ACCOUNT")
    key_path_str = os.getenv("GEE_PRIVATE_KEY_PATH")

    if not service_account:
        raise EnvironmentError("GEE_SERVICE_ACCOUNT not set in .env")
    if not key_path_str:
        raise EnvironmentError("GEE_PRIVATE_KEY_PATH not set in .env")

    key_file = Path(key_path_str)
    if not key_file.is_absolute():
        key_file = env_path.parent.parent / key_path_str  # root / key_path

    if not key_file.exists():
        raise FileNotFoundError(f"GEE key file not found: {key_file}")

    credentials = ee.ServiceAccountCredentials(service_account, str(key_file))
    ee.Initialize(credentials)
    log.info("GEE initialized — account: %s", service_account)

    return service_account  # trả về để lưu metadata (không hardcode)


# ── Flood Detector ────────────────────────────────────────────────────────────
class FloodDetector:
    """
    Phát hiện & định lượng vùng ngập lụt bằng Sentinel-1 SAR.

    Quy trình:
    1. Lấy hình học vùng nghiên cứu (FAO GAUL)
    2. Tải Sentinel-1 GRD IW VV (flood & pre-flood)
    3. Tạo composite median
    4. Phát hiện nước bằng ngưỡng VV (đơn vị dB — không convert)
    5. Tích hợp NDVI để loại pixel thực vật bị nhầm là nước
    6. Loại bỏ mặt nước thường trực (JRC permanent water)
    7. Morphological opening để khử noise
    8. Tính diện tích & xuất kết quả
    """

    def __init__(self, config: FloodConfig, service_account: str):
        self.cfg = config
        self.service_account = service_account
        self.geometry: ee.Geometry | None = None
        self.region_name: str = ""
        self.flood_map: ee.Image | None = None
        self.stats: dict = {}

    # ── 1. Region ──────────────────────────────────────────────────────────
    def define_region(self) -> None:
        adm0 = ee.FeatureCollection("FAO/GAUL/2015/level0")
        adm1 = ee.FeatureCollection("FAO/GAUL/2015/level1")

        if self.cfg.ANALYZE_WHOLE_COUNTRY:
            self.geometry = (
                adm0.filter(ee.Filter.eq("ADM0_NAME", self.cfg.COUNTRY))
                .geometry()
            )
            self.region_name = self.cfg.COUNTRY
        else:
            country_adm1 = adm1.filter(
                ee.Filter.eq("ADM0_NAME", self.cfg.COUNTRY)
            )
            features = [
                country_adm1.filter(ee.Filter.eq("ADM1_NAME", p)).first()
                for p in self.cfg.PROVINCES
            ]
            self.geometry = (
                ee.FeatureCollection(features).union().geometry()
            )
            self.region_name = ", ".join(self.cfg.PROVINCES)

        log.info("Region: %s", self.region_name)

    # ── 2. Sentinel-1 loader ───────────────────────────────────────────────
    def _load_s1(self, start: str, end: str) -> ee.ImageCollection:
        col = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(self.geometry)
            .filterDate(start, end)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
        )
        # Prefer selecting both VV and VH when available
        if self.cfg.USE_VH:
            col = col.filter(
                ee.Filter.listContains("transmitterReceiverPolarisation", "VV")
            ).filter(
                ee.Filter.listContains("transmitterReceiverPolarisation", "VH")
            ).select(["VV", "VH"])
        else:
            col = col.filter(
                ee.Filter.listContains("transmitterReceiverPolarisation", "VV")
            ).select(["VV"])

        return col

    def _speckle_filter(self, image: ee.Image, radius_m: int = 50) -> ee.Image:
        # Approximate speckle reduction with a focal median
        return image.focal_median(radius=radius_m, kernelType="circle", units="meters")

    # ── 3. Water detection ────────────────────────────────────────────────
    def _detect_water(self, s1_composite: ee.Image) -> ee.Image:
        """
        Sentinel-1 GRD VV đã ở đơn vị dB — KHÔNG log10 thêm lần nữa.
        Ngưỡng < VV_THRESHOLD_DB → nước.
        """
        vv = s1_composite.select("VV")
        # optional speckle reduction
        vv = self._speckle_filter(vv, radius_m=20)

        masks = []
        # simple fixed threshold
        masks.append(vv.lt(self.cfg.VV_THRESHOLD_DB))

        # if VH available, use VV-VH ratio test in dB
        if "VH" in s1_composite.bandNames().getInfo():
            vh = s1_composite.select("VH")
            vh = self._speckle_filter(vh, radius_m=20)
            ratio = vv.subtract(vh)  # in dB: VV - VH
            masks.append(ratio.lt(self.cfg.RATIO_THRESHOLD_DB))

        # adaptive global threshold (mean - k * std)
        stats = vv.reduceRegion(ee.Reducer.mean().combine(ee.Reducer.stdDev(), None, True), geometry=self.geometry, scale=50, maxPixels=self.cfg.MAX_PIXELS)
        mean = ee.Number(stats.get("VV_mean"))
        std = ee.Number(stats.get("VV_stdDev"))
        adaptive_thr = mean.subtract(std.multiply(self.cfg.ADAPTIVE_STD_FACTOR))
        masks.append(vv.lt(adaptive_thr))

        combined = ee.Image(masks[0])
        for m in masks[1:]:
            combined = combined.Or(m)

        return combined.rename("water")

    # ── 4. NDVI mask ──────────────────────────────────────────────────────
    def _get_ndvi_mask(self) -> ee.Image:
        """
        Pixel có NDVI > 0.3 khó là nước → loại khỏi flood map.
        Dùng Sentinel-2 SR cùng khoảng thời gian lũ.
        """
        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(self.geometry)
            .filterDate(self.cfg.FLOOD_START, self.cfg.FLOOD_END)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
            .select(["B4", "B8"])
            .median()
        )
        ndvi = s2.normalizedDifference(["B8", "B4"]).rename("ndvi")
        # Giữ lại pixel có NDVI thấp (có thể là nước hoặc đất trần)
        return ndvi.lt(0.3).rename("ndvi_water_mask")

    # ── 5. Permanent water mask ────────────────────────────────────────────
    def _get_permanent_water_mask(self) -> ee.Image:
        """
        Dùng JRC Global Surface Water để loại mặt nước thường trực.
        Chỉ giữ các pixel ngập lũ MỚI (không phải sông/hồ cố định).
        """
        jrc = ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
        permanent = (
            jrc.select("occurrence")
            .gte(self.cfg.JRC_OCCURRENCE_THRESHOLD)
            .rename("permanent_water")
        )
        # Mask pixel thường trực → trả về: 1 = không thường trực
        return permanent.Not().rename("non_permanent")

    # ── 6. Change detection (pre-flood vs flood) ──────────────────────────
    def _get_change_mask(
        self,
        pre_composite: ee.Image,
        flood_composite: ee.Image,
    ) -> ee.Image:
        """
        So sánh trước/sau lũ: nếu VV giảm đáng kể → vùng mới ngập.
        Giúp loại bỏ false positive từ vùng nước thường trực bị bỏ sót.
        """
        change = flood_composite.subtract(pre_composite).rename("vv_change")
        return change.lt(self.cfg.CHANGE_THRESHOLD_DB).rename("change_mask")

    # ── 7. Main run ────────────────────────────────────────────────────────
    def run(self) -> dict:
        self.define_region()

        # Load ảnh
        s1_flood = self._load_s1(self.cfg.FLOOD_START, self.cfg.FLOOD_END)
        s1_pre = self._load_s1(self.cfg.PRE_FLOOD_START, self.cfg.PRE_FLOOD_END)

        flood_count = s1_flood.size().getInfo()
        pre_count = s1_pre.size().getInfo()
        log.info(
            "Sentinel-1: flood=%d imgs, pre-flood=%d imgs",
            flood_count,
            pre_count,
        )

        if flood_count == 0:
            raise ValueError("Không tìm thấy ảnh Sentinel-1 trong khoảng thời gian lũ.")

        # Composite
        flood_composite = s1_flood.median().clip(self.geometry)
        pre_composite = (
            s1_pre.median().clip(self.geometry)
            if pre_count > 0
            else None
        )

        # ── Các lớp mask ──
        water_mask = self._detect_water(flood_composite)          # ngưỡng VV
        ndvi_mask = self._get_ndvi_mask()                         # loại thực vật
        perm_mask = self._get_permanent_water_mask()              # loại nước thường trực

        # Kết hợp: nước & không phải thực vật & không phải nước thường trực
        flood_map = water_mask.And(ndvi_mask).And(perm_mask)

        # Thêm change detection nếu có ảnh pre-flood
        if pre_composite is not None:
            change_mask = self._get_change_mask(pre_composite, flood_composite)
            flood_map = flood_map.And(change_mask)
            log.info("Change detection: enabled")
        else:
            log.warning("Không có ảnh pre-flood — bỏ qua change detection")

        # ── Morphological closing: dilation → erosion (lấp lỗ hổng) ──
        flood_map = (
            flood_map
            .focal_max(radius=self.cfg.MORPHOLOGY_RADIUS_M, kernelType="circle", units="meters")
            .focal_min(radius=self.cfg.MORPHOLOGY_RADIUS_M, kernelType="circle", units="meters")
            .rename("flood")
        )
        self.flood_map = flood_map

        # ── Tính diện tích ──
        scale = (
            self.cfg.COMPUTE_SCALE_WHOLE
            if self.cfg.ANALYZE_WHOLE_COUNTRY
            else self.cfg.COMPUTE_SCALE_PROVINCE
        )
        self.stats = self._compute_stats(flood_map, scale, flood_count)
        # thêm tổng hợp theo hành chính (admin1) để trả về cho UI
        try:
            admin_summary = self._aggregate_by_admin(flood_map, scale)
            self.stats["admin_summary"] = admin_summary
        except Exception as e:
            log.warning("Không thể tổng hợp theo hành chính: %s", e)

        # xuất polygon GeoJSON (giới hạn để tránh quá lớn)
        try:
            vectors = (
                flood_map.selfMask()
                .reduceToVectors(
                    geometry=self.geometry,
                    scale=scale,
                    geometryType="polygon",
                    eightConnected=False,
                    maxPixels=self.cfg.MAX_PIXELS,
                )
            )
            # attempt to materialize small vector set
            self.stats["flood_polygons_geojson"] = vectors.getInfo()
        except Exception as e:
            log.warning("Không thể xuất polygon vector (có thể quá lớn): %s", e)

        return self.stats

    # ── 8. Statistics ──────────────────────────────────────────────────────
    def _compute_stats(
        self, flood_map: ee.Image, scale: int, image_count: int
    ) -> dict:
        pixel_area = ee.Image.pixelArea()

        flooded_m2 = (
            flood_map.multiply(pixel_area)
            .reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=self.geometry,
                scale=scale,
                maxPixels=self.cfg.MAX_PIXELS,
                bestEffort=True,
            )
            .get("flood")
        )
        total_m2 = (
            pixel_area.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=self.geometry,
                scale=scale,
                maxPixels=self.cfg.MAX_PIXELS,
                bestEffort=True,
            )
            .get("area")
        )

        # Materialize
        flooded_km2 = (flooded_m2.getInfo() or 0) / 1e6
        total_km2 = (total_m2.getInfo() or 0) / 1e6
        pct = (flooded_km2 / total_km2 * 100) if total_km2 > 0 else 0.0

        log.info("Tổng diện tích   : %,.1f km²", total_km2)
        log.info("Diện tích ngập   : %,.1f km²", flooded_km2)
        log.info("Tỉ lệ ngập lụt   : %.2f%%", pct)

        return {
            "total_area_km2": round(total_km2, 2),
            "flooded_area_km2": round(flooded_km2, 2),
            "flood_percentage": round(pct, 2),
            "sentinel1_images_used": image_count,
            "scale_m": scale,
        }

    def _aggregate_by_admin(self, flood_map: ee.Image, scale: int) -> list:
        """
        Trả về danh sách thống kê theo đơn vị hành chính cấp 1 (ADM1):
        - name, flooded_area_ha, flooded_pct, severity, estimated_loss_billion, affected_population
        """
        adm1 = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq("ADM0_NAME", self.cfg.COUNTRY))
        pixel_area = ee.Image.pixelArea()

        flooded = flood_map.multiply(pixel_area)

        reduced = flooded.reduceRegions(collection=adm1, reducer=ee.Reducer.sum(), scale=scale, maxPixels=self.cfg.MAX_PIXELS)

        # Materialize small result set
        try:
            features = reduced.getInfo()["features"]
        except Exception:
            return []

        # prepare DEM
        dem = ee.Image("USGS/SRTMGL1_003").select([0]).rename("elevation")

        summary = []
        for f in features:
            props = f.get("properties", {})
            name = props.get("ADM1_NAME") or props.get("NAME_1") or "Unknown"
            flooded_m2 = props.get("sum") or 0
            flooded_ha = flooded_m2 / 10000.0

            # rough total admin area from geometry
            geom = f.get("geometry")
            # compute geometry area client-side if possible
            total_m2 = 0
            try:
                # create temporary feature to compute area
                feat = ee.Feature(ee.Geometry(geom))
                total_m2 = feat.geometry().area().getInfo()
            except Exception:
                total_m2 = 1

            total_ha = total_m2 / 10000.0 if total_m2 else 1
            pct = (flooded_ha / total_ha * 100) if total_ha > 0 else 0

            # severity heuristic
            if pct > 20:
                severity = "Critical"
            elif pct > 10:
                severity = "High"
            elif pct > 2:
                severity = "Medium"
            else:
                severity = "Low"

            est_loss = flooded_ha * self.cfg.LOSS_BILLION_PER_HA
            affected_pop = int(flooded_ha * self.cfg.POP_DENSITY_PER_HA)

            # Estimate average depth proxy using DEM: surrounding median DEM - flooded mean DEM
            avg_depth_m = 0.0
            try:
                geom_ee = ee.Geometry(geom)
                # mean elevation inside flooded pixels within this admin
                flooded_dem_mean = dem.updateMask(flood_map).reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=geom_ee,
                    scale=scale,
                    maxPixels=self.cfg.MAX_PIXELS,
                ).get("elevation")

                # median elevation of non-flooded area within admin (surrounding reference)
                surrounding_median = dem.updateMask(flood_map.Not()).reduceRegion(
                    reducer=ee.Reducer.median(),
                    geometry=geom_ee,
                    scale=scale,
                    maxPixels=self.cfg.MAX_PIXELS,
                ).get("elevation")

                flooded_dem_mean_val = flooded_dem_mean.getInfo() if flooded_dem_mean is not None else None
                surrounding_median_val = surrounding_median.getInfo() if surrounding_median is not None else None

                if flooded_dem_mean_val is not None and surrounding_median_val is not None:
                    depth = surrounding_median_val - flooded_dem_mean_val
                    avg_depth_m = round(depth if depth > 0 else 0.0, 2)
                else:
                    avg_depth_m = 0.0
            except Exception:
                avg_depth_m = 0.0

            summary.append(
                {
                    "name": name,
                    "flooded_area_ha": round(flooded_ha, 2),
                    "flooded_pct": round(pct, 2),
                    "severity": severity,
                    "avgDepth_m": avg_depth_m,
                    "estimated_loss_billion_vnd": round(est_loss, 3),
                    "affected_population": affected_pop,
                }
            )

        return summary

    # ── 9. Export ──────────────────────────────────────────────────────────
    def export_results(self) -> Path:
        cfg = self.cfg
        output_dir = Path(__file__).parent / cfg.OUTPUT_DIR
        output_dir.mkdir(exist_ok=True)

        payload = {
            "timestamp": datetime.now().isoformat(),
            "region": self.region_name,
            "country": cfg.COUNTRY,
            "date_range": {
                "flood": {"start": cfg.FLOOD_START, "end": cfg.FLOOD_END},
                "pre_flood": {
                    "start": cfg.PRE_FLOOD_START,
                    "end": cfg.PRE_FLOOD_END,
                },
            },
            "algorithm": {
                "method": "Sentinel-1 SAR + Change Detection + NDVI + JRC Permanent Water Mask",
                "vv_threshold_db": cfg.VV_THRESHOLD_DB,
                "change_threshold_db": cfg.CHANGE_THRESHOLD_DB,
                "jrc_occurrence_threshold": cfg.JRC_OCCURRENCE_THRESHOLD,
                "composite_type": "median",
                "morphological_ops": "closing (dilation → erosion)",
            },
            "results": self.stats,
            # Không lưu service_account hay project_id vào output file
        }

        out_file = output_dir / (
            f"flood_{self.region_name.replace(', ', '_').replace(' ', '_')}"
            f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        log.info("Kết quả lưu tại: %s", out_file)
        return out_file


# ── Entry Point ───────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 70)
    print("🌊  THUẬT TOÁN KHOANH VÙNG NGẬP LỤT — GEE")
    print("=" * 70)

    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    env_path = project_root / "fastapi" / ".env"

    service_account = init_gee(env_path)

    cfg = FloodConfig()
    detector = FloodDetector(cfg, service_account)

    stats = detector.run()
    out_file = detector.export_results()

    print("\n📊  KẾT QUẢ CUỐI CÙNG")
    print("-" * 70)
    print(f"🌍  Vùng        : {detector.region_name}")
    print(f"📅  Lũ lụt      : {cfg.FLOOD_START} → {cfg.FLOOD_END}")
    print(f"📅  Baseline    : {cfg.PRE_FLOOD_START} → {cfg.PRE_FLOOD_END}")
    print(f"📡  Ảnh S1      : {stats['sentinel1_images_used']}")
    print(f"📏  Scale       : {stats['scale_m']} m")
    print("-" * 70)
    print(f"🌊  Diện tích ngập  : {stats['flooded_area_km2']:,.1f} km²")
    print(f"📐  Tổng diện tích  : {stats['total_area_km2']:,.1f} km²")
    print(f"📊  Tỉ lệ ngập      : {stats['flood_percentage']:.2f}%")
    print("-" * 70)
    print(f"💾  File kết quả    : {out_file}")
    print("\n✅  Hoàn tất!")
    print("=" * 70)


if __name__ == "__main__":
    main()