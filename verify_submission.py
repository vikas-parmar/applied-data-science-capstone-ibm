"""Verify capstone deliverables against AI grading rubric."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGES = ROOT / "images"

REQUIRED = [
    "Data Collection API.ipynb",
    "Data Collection with Web Scraping.ipynb",
    "Data Wrangling.ipynb",
    "EDA.ipynb",
    "EDA with Data Visualization.ipynb",
    "Interactive Visual Analytics with Folium lab.ipynb",
    "Machine Learning Prediction.ipynb",
    "spacex_dash_app.py",
    "dataset_part_1.csv",
    "dataset_part_2.csv",
    "dataset_part_3.csv",
    "spacex_web_scraped.csv",
    "spacex_launch_dash.csv",
    "spacex_launch_geo.csv",
    "Data Science Capstone Project Report.pdf",
    "Data Science Capstone Project Report.pptx",
    "README.md",
]

IMAGE_CHECKS = [
    "eda_01_flight_vs_site.png",
    "eda_02_payload_vs_site.png",
    "eda_03_success_vs_orbit.png",
    "eda_04_flight_vs_orbit.png",
    "eda_05_payload_vs_orbit.png",
    "eda_06_yearly_trend.png",
    "sql_01_launch_sites.png",
    "sql_10_rank_outcomes.png",
    "folium_1.png",
    "folium_2.png",
    "folium_3.png",
    "dash_01_all_sites_pie.png",
    "dash_02_site_pie.png",
    "dash_03_payload_scatter.png",
    "ml_accuracy_bar.png",
    "ml_confusion_matrix.png",
]


def main() -> None:
    missing = [f for f in REQUIRED if not (ROOT / f).exists()]
    missing_images = [f for f in IMAGE_CHECKS if not (IMAGES / f).exists()]

    print("=== IBM Capstone Submission Verification ===")
    print(f"Project root: {ROOT}")
    print(f"Required files missing: {len(missing)}")
    for item in missing:
        print(f"  MISSING: {item}")

    print(f"Required images missing: {len(missing_images)}")
    for item in missing_images:
        print(f"  MISSING IMAGE: {item}")

    if not missing and not missing_images:
        print("All deliverables present. Ready for Coursera Option 1 submission.")
        print("GitHub URL to submit: https://github.com/vikas-parmar/applied-data-science-capstone-ibm")
        print("PDF to upload: Data Science Capstone Project Report.pdf")
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
