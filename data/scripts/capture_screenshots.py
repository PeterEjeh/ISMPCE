"""
Automated script to capture high-resolution screenshots of the live running ISMPCE system:
- Frontend Dashboard (localhost:3000)
- Geospatial Map
- Time Series Chart & Forecast
- Sectoral Breakdown
- Model Comparison
- Prediction Simulator
- Backend Swagger Documentation (127.0.0.1:8000/docs)
"""

import os
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def capture_all():
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge", headless=True)
            print("Launched Microsoft Edge...")
        except Exception:
            try:
                browser = p.chromium.launch(channel="chrome", headless=True)
                print("Launched Google Chrome...")
            except Exception:
                browser = p.chromium.launch(headless=True)
                print("Launched Chromium...")
        context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = context.new_page()

        print("Navigating to Frontend Dashboard (http://localhost:3000)...")
        page.goto("http://localhost:3000", wait_until="networkidle")
        time.sleep(3)  # Allow charts and animations to render completely

        # 1. Full Dashboard Overview
        full_path = os.path.join(OUTPUT_DIR, "figure_4_1_dashboard_overview.png")
        page.screenshot(path=full_path, full_page=True)
        print(f"  [Captured] Full Dashboard Overview -> {full_path}")

        # 2. Header and Summary Metrics + Time Series
        chart_elem = page.locator(".dashboard-grid > div:nth-child(1)")
        if chart_elem.count() > 0:
            ts_path = os.path.join(OUTPUT_DIR, "figure_4_2_timeseries_forecast.png")
            chart_elem.first.screenshot(path=ts_path)
            print(f"  [Captured] Time Series Forecast Chart -> {ts_path}")

        # 3. Geospatial Leaflet Map
        map_elem = page.locator(".dashboard-grid > div:nth-child(2)")
        if map_elem.count() > 0:
            map_path = os.path.join(OUTPUT_DIR, "figure_4_3_geospatial_map.png")
            map_elem.first.screenshot(path=map_path)
            print(f"  [Captured] Geospatial Map -> {map_path}")

        # 4. Sectoral Breakdown Charts
        sector_elem = page.locator(".dashboard-grid > div:nth-child(3)")
        if sector_elem.count() > 0:
            sector_path = os.path.join(OUTPUT_DIR, "figure_4_4_sectoral_breakdown.png")
            sector_elem.first.screenshot(path=sector_path)
            print(f"  [Captured] Sectoral Breakdown -> {sector_path}")

        # 5. Model Comparison Panel
        model_elem = page.locator(".dashboard-grid > div:nth-child(4)")
        if model_elem.count() > 0:
            model_path = os.path.join(OUTPUT_DIR, "figure_4_5_model_comparison.png")
            model_elem.first.screenshot(path=model_path)
            print(f"  [Captured] Model Comparison Panel -> {model_path}")

        # 6. Interactive Prediction Console
        pred_elem = page.locator(".dashboard-grid > div:nth-child(5)")
        if pred_elem.count() > 0:
            # Trigger a prediction to populate the table nicely
            btn = page.locator("button[type='submit']")
            if btn.count() > 0:
                btn.click()
                time.sleep(1.5)
            pred_path = os.path.join(OUTPUT_DIR, "figure_4_6_prediction_simulator.png")
            pred_elem.first.screenshot(path=pred_path)
            print(f"  [Captured] Prediction Simulator -> {pred_path}")

        # 7. Backend FastAPI Swagger Documentation
        print("Navigating to FastAPI Swagger Documentation (http://127.0.0.1:8000/docs)...")
        page.goto("http://127.0.0.1:8000/docs", wait_until="networkidle")
        time.sleep(2)
        swagger_path = os.path.join(OUTPUT_DIR, "figure_4_7_swagger_api.png")
        page.screenshot(path=swagger_path, full_page=False)
        print(f"  [Captured] FastAPI Swagger UI -> {swagger_path}")

        browser.close()
        print("\nAll high-resolution system screenshots captured successfully!")

if __name__ == "__main__":
    capture_all()
