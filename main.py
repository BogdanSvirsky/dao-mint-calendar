import requests
from datetime import datetime
from dateutil import tz
import sqlite3

def get_todays_time() -> int:
    today = datetime.utcnow()
    today = int(datetime.timestamp(datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=tz.tzutc())))
    return today

def mint_responce(startTime: int, endTime: int) -> dict:
    params = {
            "calendar": "true",
            "startDate": str(startTime * 1000),
            "endDate": str(endTime * 1000)
    }
    responce = requests.get("https://www.alphabot.app/api/projectData", params=params)
    json_resp = responce.json()
    return json_resp["projects"]

def insert_data_in_db(data: dict) -> None:
    conn = sqlite3.connect('mints.db', isolation_level=None)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS mint_collects(
            name TEXT, 
            discordUrl TEXT,
            twitterUrl TEXT,
            twitterProfileImage TEXT,
            mintTime INTEGER,
            wlPrice TEXT,
            pubPrice TEXT
        );
    """)
    conn.commit()

    cursor = conn.cursor()
    cursor.execute("""SELECT name FROM mint_collects""")
    collects_in_db = [name[0] for name in cursor.fetchall()]

    keys = ["name", "discordUrl", "twitterUrl", "twitterProfileImage", "mintDate", "wlPrice", "pubPrice"]
    for collect in data:
        if collect["name"] in collects_in_db:
            continue
        collect_keys = [x[0] for x in collect.items()]
        result = {}

        for key in keys:
            if key in collect_keys:
                if key == "mintDate":
                    result[key] = int(collect[key])
                else:
                    result[key] = collect[key]
            else:
                result[key] = ""
        try:    
            cursor.execute("""
                INSERT INTO mint_collects(name, discordUrl, twitterUrl, twitterProfileImage, mintTime, wlPrice, pubPrice) VALUES(?, ?, ?, ?, ?, ?, ?)
            """, (result["name"], result["discordUrl"], result["twitterUrl"], result["twitterProfileImage"], result["mintDate"], result["wlPrice"], result["pubPrice"]))
        except Exception as e:
            print(result, e)

    conn.commit()
    conn.close()

def clear_db() -> None:
    today = get_todays_time()
    conn = sqlite3.connect('mints.db', isolation_level=None)
    cursor = conn.cursor()

    cursor.execute(f"""DELETE FROM mint_collects WHERE mintTime < {today - 86400}""")
    conn.commit()
    conn.close()

    
class MintCalendar:
    def __init__(self) -> None:
        today = get_todays_time()
        insert_data_in_db(mint_responce(today - 86400, today + 2 * 86400))


    def update(self) -> None:
        today = get_todays_time()
        insert_data_in_db(mint_responce(today + 86400, today + 2 * 86400))
        clear_db()
    

    def get_todays_collects(self, userTimeSet: int) -> list:
        today = get_todays_time() - userTimeSet * 3600

        conn = sqlite3.connect('mints.db')
        cursor = conn.cursor()
        cursor.execute(f"""SELECT * FROM mint_collects WHERE mintTime >= {today * 1000} AND mintTime <= {(today + 86400) * 1000}""")
        todaysCollects = []
        for collectData in cursor.fetchall():
            resultCollect = {
                "name": collectData[0],
                "discordUrl": collectData[1],
                "twitterUrl": collectData[2],
                "twitterProfileImage": collectData[3],
                "mintTime": datetime.utcfromtimestamp(int(collectData[4]) / 1000 + userTimeSet * 3600).strftime("%H:%M"),
                "wlPrice": collectData[5],
                "pubPrice": collectData[6],
            }
            todaysCollects.append(resultCollect)
        return todaysCollects


if __name__ == "__main__":
    mint_calendar = MintCalendar()
    print(mint_calendar.get_todays_collects(7))
    mint_calendar.update()