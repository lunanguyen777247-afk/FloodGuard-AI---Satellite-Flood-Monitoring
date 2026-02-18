import pytest
from fastapi.testclient import TestClient
from app.main import app

# Create a stubbed gee_service to avoid real GEE calls
class StubGEE:
    def get_region_geometry(self, name):
        return f"geom-{name}"

    def get_sentinel1_flood_mask(self, region_geom, start, end):
        return {"mock": "mask"}

    def calculate_flood_statistics(self, region_geom, flood_mask):
        return {"flood_area_km2": 50}

    def get_rainfall_data(self, region_geom, start, end):
        return {"precipitation_mean": 1.2}

    def estimate_affected_population(self, region_geom, flood_mask):
        return 1200

    def export_to_geojson(self, region_geom, flood_mask):
        return {"type": "FeatureCollection", "features": []}

    def generate_flood_map(self, region_name, start_date, end_date):
        return {
            "region": region_name,
            "date_range": {"start": start_date, "end": end_date},
            "flood_statistics": {"flood_area_km2": 50},
            "rainfall_statistics": {},
            "map_url": "https://tiles.example/{z}/{x}/{y}.png",
            "map_id": "mock-map"
        }

    def aggregate_admin_summary(self, country_name, start_date, end_date, scale=100):
        return [
            {
                "name": "Test Province",
                "flooded_area_ha": 120.5,
                "flooded_pct": 5.2,
                "severity": "Medium",
                "avgDepth_m": 0.8,
                "estimated_loss_billion_vnd": 0.6,
                "affected_population": 1200
            }
        ]


@pytest.fixture(autouse=True)
def mock_gee_service(monkeypatch):
    import app.api.regions as regions_mod
    import app.services.gee_service as gee_mod

    stub = StubGEE()
    # monkeypatch the gee_service used by regions router
    monkeypatch.setattr(regions_mod, 'gee_service', stub)
    # also patch the module-level gee_service if other imports use it
    monkeypatch.setattr(gee_mod, 'gee_service', stub)
    yield


client = TestClient(app)


def test_get_region_geojson():
    resp = client.get('/api/regions/Quang%20Tri/geojson')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('type') == 'FeatureCollection'


def test_get_region_map():
    resp = client.get('/api/regions/Quang%20Tri/map')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('map_url')


def test_admin_summary():
    resp = client.get('/api/regions/statistics/admin_summary')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('country') == 'Viet Nam'
    assert isinstance(data.get('admin_summary'), list)