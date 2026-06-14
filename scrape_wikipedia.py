"""Generate spacex_web_scraped.csv from Wikipedia using course lab logic."""

import re
import unicodedata

import pandas as pd
import requests
from bs4 import BeautifulSoup

URL = (
    "https://en.wikipedia.org/w/index.php?"
    "title=List_of_Falcon_9_and_Falcon_Heavy_launches&oldid=1027686922"
)


def extract_column_from_header(header):
    column_name = " ".join(header.strings)
    if column_name:
        column_name = column_name.strip()
        column_name = re.sub(r"\[.*\]", "", column_name)
    return column_name


def date_time(table_cells):
    return [data_time.strip() for data_time in list(table_cells.strings)][0:2]


def booster_version(table_cells):
    return "".join(
        [bv for i, bv in enumerate(table_cells.strings) if i % 2 == 0][0:-1]
    )


def landing_status(table_cells):
    return [i for i in table_cells.strings][0]


def get_mass(table_cells):
    mass = unicodedata.normalize("NFKD", table_cells.text).strip()
    if mass:
        mass = re.findall(r"\d+", mass.replace(",", ""))
        return mass[0] if mass else None
    return None


def main() -> None:
    response = requests.get(URL, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    html_tables = soup.find_all("table")
    first_launch_table = html_tables[2]
    column_names = []
    for th in first_launch_table.find_all("th"):
        name = extract_column_from_header(th)
        if name:
            column_names.append(name)

    launch_dict = dict.fromkeys(column_names)
    if "Date and time ( )" in launch_dict:
        del launch_dict["Date and time ( )"]
    launch_dict["Flight No."] = []
    launch_dict["Launch site"] = []
    launch_dict["Payload"] = []
    launch_dict["Payload mass"] = []
    launch_dict["Orbit"] = []
    launch_dict["Customer"] = []
    launch_dict["Launch outcome"] = []
    launch_dict["Version Booster"] = []
    launch_dict["Booster landing"] = []
    launch_dict["Date"] = []
    launch_dict["Time"] = []

    for table in soup.find_all("table", "wikitable plainrowheaders collapsible"):
        for rows in table.find_all("tr"):
            if rows.th and rows.th.string:
                flight_number = rows.th.string.strip()
                flag = flight_number.isdigit()
            else:
                flag = False
            row = rows.find_all("td")
            if not flag:
                continue
            launch_dict["Flight No."].append(flight_number)
            datatimelist = date_time(row[0])
            launch_dict["Date"].append(datatimelist[0].strip(","))
            launch_dict["Time"].append(datatimelist[1])
            launch_dict["Version Booster"].append(booster_version(row[1]))
            launch_dict["Launch site"].append(row[2].text.strip())
            launch_dict["Payload"].append(row[3].text.strip())
            launch_dict["Payload mass"].append(get_mass(row[4]))
            launch_dict["Orbit"].append(row[5].text.strip())
            launch_dict["Customer"].append(row[6].text.strip())
            launch_dict["Launch outcome"].append(row[7].text.strip())
            launch_dict["Booster landing"].append(landing_status(row[8]))

    df = pd.DataFrame(launch_dict)
    df.to_csv("spacex_web_scraped.csv", index=False)
    print(f"Saved spacex_web_scraped.csv with shape {df.shape}")


if __name__ == "__main__":
    main()
