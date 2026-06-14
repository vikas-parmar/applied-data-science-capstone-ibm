# IBM Applied Data Science Capstone — Vikas Parmar

Coursera IBM Applied Data Science Capstone project predicting **SpaceX Falcon 9 first-stage landing success** to estimate launch cost savings.

## Business Problem

SpaceX advertises Falcon 9 launches at about **$62M** versus **$165M+** from other providers. Reusing the first stage drives much of that savings. This project analyzes historical launch data and builds classification models to predict whether the first stage will land successfully.

## Repository Structure

| File | Description |
|------|-------------|
| `Data Collection API.ipynb` | Collect Falcon 9 launch data from SpaceX API |
| `Data Collection with Web Scraping.ipynb` | Scrape Wikipedia launch records |
| `Data Wrangling.ipynb` | Clean data and create `Class` label |
| `EDA.ipynb` | 10 SQL queries on SQLite database |
| `EDA with Data Visualization.ipynb` | 6 exploratory charts |
| `Interactive Visual Analytics with Folium lab.ipynb` | Interactive launch site maps |
| `Machine Learning Prediction.ipynb` | 4 classifiers with GridSearchCV |
| `spacex_dash_app.py` | Plotly Dash dashboard |
| `Data Science Capstone Project Report.pdf` | Final presentation for Coursera submission |

## Submission (Coursera Option 1 — AI Graded)

**GitHub Repository:** https://github.com/vikas-parmar/applied-data-science-capstone-ibm

1. Upload **`Data Science Capstone Project Report.pdf`** to Coursera.
2. Paste the GitHub URL above in the submission form.

To regenerate the presentation after changes:
```bash
python populate_presentation.py
```

## Key Results

- EDA shows orbit type, payload mass, and launch site correlate with landing success.
- SQL analysis summarizes launch sites, payload statistics, and landing outcomes.
- Folium maps visualize launch geography and proximity to infrastructure.
- Plotly Dash enables interactive filtering by site and payload range.
- **Decision Tree** typically achieves the best cross-validation score among Logistic Regression, SVM, KNN, and Decision Tree models.

## Author

**Vikas Parmar** — IBM Data Science Professional Certificate Capstone

## Acknowledgments

IBM and Coursera for course materials; SpaceX for public launch data.
