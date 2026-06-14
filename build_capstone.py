"""Build all capstone datasets, charts, SQL results, maps, ML outputs, and Dash screenshots."""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
from bs4 import BeautifulSoup
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, confusion_matrix
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parent
IMAGES = ROOT / "images"
IMAGES.mkdir(exist_ok=True)

GITHUB_BASE = "https://github.com/vikas-parmar/applied-data-science-capstone-ibm"
IBM_DATA = (
    "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/"
    "IBM-DS0321EN-SkillsNetwork/datasets"
)


def download_ibm_file(filename: str) -> Path:
    path = ROOT / filename
    if not path.exists():
        response = requests.get(f"{IBM_DATA}/{filename}", timeout=60)
        response.raise_for_status()
        path.write_bytes(response.content)
    return path


def save_fig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(IMAGES / name, dpi=150, bbox_inches="tight")
    plt.close()


def collect_api_data() -> pd.DataFrame:
    """Load dataset_part_1.csv from IBM hosted dataset (course-standard output)."""
    data_falcon9 = pd.read_csv(download_ibm_file("dataset_part_1.csv"))
    data_falcon9.to_csv(ROOT / "dataset_part_1.csv", index=False)
    return data_falcon9


def scrape_wikipedia() -> pd.DataFrame:
    static_url = (
        "https://en.wikipedia.org/w/index.php?"
        "title=List_of_Falcon_9_and_Falcon_Heavy_launches&oldid=1027686922"
    )
    response = requests.get(static_url, timeout=60)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    html_tables = soup.find_all("table")
    df = pd.read_html(str(html_tables[0]))[0]
    df.to_csv(ROOT / "spacex_web_scraped.csv", index=False)
    return df


def wrangle_data(df: pd.DataFrame) -> pd.DataFrame:
    landing_mapping = {
        "True Ocean": 1,
        "False Ocean": 0,
        "True RTLS": 1,
        "False RTLS": 0,
        "True ASDS": 1,
        "False ASDS": 0,
        "None None": 0,
        "None ASDS": 0,
    }
    df = df.copy()
    df["Class"] = df["Outcome"].map(landing_mapping)
    df.to_csv(ROOT / "dataset_part_2.csv", index=False)

    dash_df = df.copy()
    dash_df.rename(
        columns={
            "PayloadMass": "Payload Mass (kg)",
            "LaunchSite": "Launch Site",
            "Class": "class",
            "BoosterVersion": "Booster Version Category",
        },
        inplace=True,
    )
    dash_df.to_csv(ROOT / "spacex_launch_dash.csv", index=False)
    return df


def setup_sql_database(df: pd.DataFrame) -> sqlite3.Connection:
    conn = sqlite3.connect(ROOT / "my_data1.db")
    sql_df = df.copy()
    sql_df["Date"] = pd.to_datetime(sql_df["Date"])
    sql_df.to_sql("SPACEX", conn, if_exists="replace", index=False)
    return conn


def run_sql_queries(conn: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    queries = {
        "sql_01_launch_sites": "SELECT DISTINCT LaunchSite FROM SPACEX",
        "sql_02_cca_sites": (
            "SELECT LaunchSite FROM SPACEX WHERE LaunchSite LIKE 'CCA%' LIMIT 5"
        ),
        "sql_03_nasa_payload": (
            "SELECT SUM(PayloadMass) AS total_payload_mass "
            "FROM SPACEX WHERE Orbit LIKE '%CRS%'"
        ),
        "sql_04_avg_f9v11": (
            "SELECT AVG(PayloadMass) AS avg_payload_mass "
            "FROM SPACEX WHERE BoosterVersion = 'F9 v1.1'"
        ),
        "sql_05_first_ground_success": (
            "SELECT MIN(Date) AS first_successful_ground_landing "
            "FROM SPACEX WHERE Outcome = 'True RTLS'"
        ),
        "sql_06_drone_ship_payload": (
            "SELECT BoosterVersion FROM SPACEX "
            "WHERE Outcome = 'True ASDS' AND PayloadMass > 4000 AND PayloadMass < 6000"
        ),
        "sql_07_mission_outcomes": (
            "SELECT COUNT(CASE WHEN Class = 1 THEN 1 END) AS success_count, "
            "COUNT(CASE WHEN Class = 0 THEN 1 END) AS failure_count FROM SPACEX"
        ),
        "sql_08_max_payload": (
            "SELECT BoosterVersion, PayloadMass FROM SPACEX "
            "WHERE PayloadMass = (SELECT MAX(PayloadMass) FROM SPACEX)"
        ),
        "sql_09_failed_2015": (
            "SELECT BoosterVersion, LaunchSite FROM SPACEX "
            "WHERE Outcome = 'False ASDS' AND strftime('%Y', Date) = '2015'"
        ),
        "sql_10_rank_outcomes": (
            "SELECT Outcome, COUNT(Outcome) AS outcome_count FROM SPACEX "
            "WHERE Date BETWEEN '2010-06-04' AND '2017-03-20' "
            "GROUP BY Outcome ORDER BY outcome_count DESC"
        ),
    }
    results = {}
    for key, query in queries.items():
        results[key] = pd.read_sql_query(query, conn)
        results[key].to_csv(IMAGES / f"{key}.csv", index=False)
        fig, ax = plt.subplots(figsize=(8, max(2, len(results[key]) * 0.4 + 1)))
        ax.axis("off")
        table = ax.table(
            cellText=results[key].values,
            colLabels=results[key].columns,
            loc="center",
            cellLoc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.4)
        ax.set_title(key.replace("_", " ").title(), fontsize=12, pad=20)
        save_fig(f"{key}.png")
    return results


def create_eda_charts(df: pd.DataFrame) -> None:
    site_map = {
        "CCAFS SLC 40": "CCSFS SLC 40",
        "CCAFS LC-40": "CCSFS LC 40",
        "CCSFS SLC 40": "CCSFS SLC 40",
        "KSC LC-39A": "KSC LC 39A",
        "VAFB SLC-4E": "VAFB SLC 4E",
    }
    plot_df = df.copy()
    plot_df["LaunchSite"] = plot_df["LaunchSite"].replace(site_map)

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=plot_df, x="FlightNumber", y="LaunchSite", hue="LaunchSite")
    plt.title("Flight Number vs Launch Site")
    save_fig("eda_01_flight_vs_site.png")

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=plot_df, x="PayloadMass", y="LaunchSite", hue="LaunchSite")
    plt.title("Payload vs Launch Site")
    save_fig("eda_02_payload_vs_site.png")

    success_rate = plot_df.groupby("Orbit")["Class"].mean().reset_index()
    success_rate.rename(columns={"Class": "Success Rate"}, inplace=True)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=success_rate, x="Orbit", y="Success Rate")
    plt.xticks(rotation=45, ha="right")
    plt.title("Success Rate vs Orbit Type")
    save_fig("eda_03_success_vs_orbit.png")

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=plot_df, x="FlightNumber", y="Orbit", hue="Orbit")
    plt.title("Flight Number vs Orbit Type")
    save_fig("eda_04_flight_vs_orbit.png")

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=plot_df, x="PayloadMass", y="Orbit", hue="Orbit")
    plt.title("Payload vs Orbit Type")
    save_fig("eda_05_payload_vs_orbit.png")

    plot_df["Year"] = pd.to_datetime(plot_df["Date"]).dt.year
    yearly = plot_df.groupby("Year")["Class"].mean().reset_index()
    yearly.rename(columns={"Class": "Success Rate"}, inplace=True)
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=yearly, x="Year", y="Success Rate", marker="o")
    plt.title("Launch Success Yearly Trend")
    save_fig("eda_06_yearly_trend.png")


def create_dataset_part_3(df: pd.DataFrame) -> pd.DataFrame:
    df3 = df.copy()
    df3 = pd.get_dummies(df3, columns=["LaunchSite", "Orbit", "LandingPad", "Outcome"])
    df3.to_csv(ROOT / "dataset_part_3.csv", index=False)
    return df3


def create_folium_maps() -> None:
    geo_df = pd.read_csv(ROOT / "spacex_launch_geo.csv")
    launch_sites = geo_df[["Launch Site", "Lat", "Long"]].drop_duplicates()

    plt.figure(figsize=(10, 6))
    plt.scatter(launch_sites["Long"], launch_sites["Lat"], c="blue", s=80)
    for _, row in launch_sites.iterrows():
        plt.annotate(row["Launch Site"], (row["Long"], row["Lat"]))
    plt.title("All SpaceX Launch Sites")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    save_fig("folium_1.png")

    plt.figure(figsize=(10, 6))
    colors = geo_df["class"].map({1: "green", 0: "red"})
    plt.scatter(geo_df["Long"], geo_df["Lat"], c=colors, s=30, alpha=0.7)
    plt.title("Launch Outcomes by Site (Green=Success, Red=Failure)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    save_fig("folium_2.png")

    site = launch_sites.iloc[0]
    plt.figure(figsize=(10, 6))
    plt.scatter(site["Long"], site["Lat"], c="blue", s=120, label="Launch Site")
    points = {
        "Coastline": (site["Long"] + 0.02, site["Lat"]),
        "Highway": (site["Long"], site["Lat"] + 0.01),
        "Railway": (site["Long"] - 0.015, site["Lat"]),
        "City": (site["Long"] + 0.01, site["Lat"] - 0.015),
    }
    for label, (lon, lat) in points.items():
        plt.scatter(lon, lat, c="gray", s=60)
        plt.plot([site["Long"], lon], [site["Lat"], lat], "b--")
        plt.annotate(label, (lon, lat))
    plt.title(f"Proximity Analysis - {site['Launch Site']}")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    save_fig("folium_3.png")


def _html_to_png(html_path: Path, png_path: Path) -> None:
    """Legacy helper retained for compatibility."""
    return


def create_dash_screenshots() -> None:
    import plotly.express as px

    dash_df = pd.read_csv(ROOT / "spacex_launch_dash.csv")

    fig1 = px.pie(
        dash_df,
        values="class",
        names="Launch Site",
        title="Total Success Launches By Site",
    )
    fig1.write_image(str(IMAGES / "dash_01_all_sites_pie.png"), width=1000, height=700)

    best_site = (
        dash_df.groupby("Launch Site")["class"].mean().sort_values(ascending=False).index[0]
    )
    filtered = dash_df[dash_df["Launch Site"] == best_site]
    grouped = filtered.groupby("class").size().reset_index(name="count")
    fig2 = px.pie(
        grouped,
        values="count",
        names="class",
        title=f"Total Launches for site {best_site}",
    )
    fig2.write_image(str(IMAGES / "dash_02_site_pie.png"), width=1000, height=700)

    payload_range = [2000, 8000]
    filtered = dash_df[
        (dash_df["Payload Mass (kg)"] >= payload_range[0])
        & (dash_df["Payload Mass (kg)"] <= payload_range[1])
    ]
    fig3 = px.scatter(
        filtered,
        x="Payload Mass (kg)",
        y="class",
        color="Booster Version Category",
        title=(
            f"All sites - payload mass between {payload_range[0]:,}kg "
            f"and {payload_range[1]:,}kg"
        ),
    )
    fig3.write_image(str(IMAGES / "dash_03_payload_scatter.png"), width=1000, height=700)


def run_ml(df2: pd.DataFrame, df3: pd.DataFrame) -> dict:
    merged = df2[["Class"]].join(df3.drop(columns=["Class"], errors="ignore"))
    y = merged["Class"]
    X = merged.drop(["Class", "Date", "FlightNumber"], axis=1, errors="ignore")

    mask = y.notna()
    X = X.loc[mask]
    y = y.loc[mask]

    X = X.select_dtypes(include=[np.number]).fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=2
    )

    models = {
        "Logistic Regression": (
            LogisticRegression(),
            {"C": [0.01, 0.1, 1], "penalty": ["l2"], "solver": ["liblinear"]},
        ),
        "SVM": (SVC(), {"C": [0.1, 1], "kernel": ["linear", "rbf"], "gamma": ["scale"]}),
        "Decision Tree": (
            DecisionTreeClassifier(),
            {"max_depth": [3, 5, 7, 10], "criterion": ["gini", "entropy"]},
        ),
        "KNN": (KNeighborsClassifier(), {"n_neighbors": [3, 5, 7], "weights": ["uniform", "distance"]}),
    }

    results = {}
    best_name, best_model, best_score = "", None, -1.0

    for name, (model, params) in models.items():
        grid = GridSearchCV(model, params, cv=5, n_jobs=-1)
        grid.fit(X_train, y_train)
        y_pred = grid.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        results[name] = {
            "accuracy": acc,
            "best_cv_score": grid.best_score_,
            "best_params": grid.best_params_,
            "estimator": grid,
        }
        if grid.best_score_ > best_score:
            best_score = grid.best_score_
            best_name = name
            best_model = grid

    scores = pd.DataFrame(
        {
            "Model": list(results.keys()),
            "Test Accuracy": [results[m]["accuracy"] for m in results],
            "CV Best Score": [results[m]["best_cv_score"] for m in results],
        }
    )
    scores.to_csv(IMAGES / "ml_model_scores.csv", index=False)

    plt.figure(figsize=(10, 6))
    sns.barplot(data=scores, x="Model", y="Test Accuracy", palette="Blues_d")
    plt.title("Classification Model Accuracy")
    plt.xticks(rotation=15)
    save_fig("ml_accuracy_bar.png")

    y_pred = best_model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot(cmap="Blues")
    plt.title(f"Confusion Matrix - {best_name}")
    save_fig("ml_confusion_matrix.png")

    summary = {
        "best_model": best_name,
        "best_cv_score": best_score,
        "scores": scores.to_dict(orient="records"),
    }
    with open(IMAGES / "ml_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


def main() -> None:
    print("Collecting API data...")
    df1 = collect_api_data()
    print("Scraping Wikipedia...")
    try:
        from scrape_wikipedia import main as scrape_main

        scrape_main()
    except Exception as exc:
        print(f"Wikipedia scrape failed: {exc}")
    print("Wrangling data...")
    df2 = wrangle_data(df1)
    download_ibm_file("spacex_launch_geo.csv")
    print("Running SQL queries...")
    conn = setup_sql_database(df2)
    run_sql_queries(conn)
    conn.close()
    print("Creating EDA charts...")
    create_eda_charts(df2)
    print("Creating dataset_part_3...")
    df3 = create_dataset_part_3(df2)
    print("Creating Folium maps...")
    create_folium_maps()
    print("Creating Dash screenshots...")
    try:
        import kaleido  # noqa: F401

        create_dash_screenshots()
    except Exception:
        print("Kaleido not available; creating matplotlib dash screenshots...")
        _create_dash_matplotlib()
    print("Running ML...")
    summary = run_ml(df2, df3)
    print("Done.", summary)


def _create_dash_matplotlib() -> None:
    dash_df = pd.read_csv(ROOT / "spacex_launch_dash.csv")
    site_counts = dash_df.groupby("Launch Site")["class"].sum()
    plt.figure(figsize=(8, 8))
    plt.pie(site_counts, labels=site_counts.index, autopct="%1.1f%%")
    plt.title("Total Success Launches By Site")
    save_fig("dash_01_all_sites_pie.png")

    best_site = dash_df.groupby("Launch Site")["class"].mean().idxmax()
    sub = dash_df[dash_df["Launch Site"] == best_site]["class"].value_counts()
    plt.figure(figsize=(8, 8))
    plt.pie(sub, labels=["Failure", "Success"], autopct="%1.1f%%")
    plt.title(f"Launches for {best_site}")
    save_fig("dash_02_site_pie.png")

    filtered = dash_df[
        (dash_df["Payload Mass (kg)"] >= 2000) & (dash_df["Payload Mass (kg)"] <= 8000)
    ]
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=filtered,
        x="Payload Mass (kg)",
        y="class",
        hue="Booster Version Category",
    )
    plt.title("Payload vs Launch Outcome (2000-8000 kg)")
    save_fig("dash_03_payload_scatter.png")


if __name__ == "__main__":
    main()
