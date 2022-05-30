from dotenv import load_dotenv
import os
import requests
import json
from datetime import date
from config import create_api

load_dotenv()
api_key = os.getenv("NASA_API_KEY")
api = create_api()


def get_today():
    return date.today().strftime("%Y-%m-%d")


def get_today_as_text():
    return date.today().strftime("%B %d, %Y")


def get_data(url):
    response_API = requests.get(f"{url}")
    data = response_API.text
    return json.loads(data)


def get_media_of_the_day(api_key):
    url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}"
    return get_data(url)


def get_neos_by_approach_date(date, api_key):
    # retrieve Near Earth Objects by approach date
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={date}&end_date={date}&api_key={api_key}"
    return get_data(url)


def get_number_of_neos(data):
    return data["element_count"]


def get_number_of_potentially_hazardous_neos(data, today):
    count = 0
    for item in data["near_earth_objects"][today]:
        if (item["is_potentially_hazardous_asteroid"]):
            count += 1
    return count


def get_closest_neo(data, today):
    distances_km = {}
    distances_miles = {}
    for item in data["near_earth_objects"][today]:
        distances_km.update(
            {item["name"]: float(item["close_approach_data"][0]["miss_distance"]["kilometers"])})
        distances_miles.update(
            {item["name"]: float(item["close_approach_data"][0]["miss_distance"]["miles"])})
    min_km = min(distances_km.values())
    min_miles = min(distances_miles.values())
    min_name = [k for k, v in distances_km.items() if v == min_km][0]

    return(f"{min_name} - {'{:.2f}'.format(min_km)}km / {'{:.2f}'.format(min_miles)}mi")


def create_daily_tweet_content():
    today = get_today()
    content = f"Beep beep, here's {get_today_as_text()} update:\n\n"

    # get data
    data = get_neos_by_approach_date(today, api_key)

    # total NEOs
    total = get_number_of_neos(data)
    content += f"  ☄️ Approaching near earth objects: {total}\n"

    # potentially hazardous asteroids
    pot_hazardous_NEOs = get_number_of_potentially_hazardous_neos(data, today)
    proportion = "{:.0f}".format((pot_hazardous_NEOs/total)*100)
    content += f"  🚨 Potentially hazardous asteroids: {pot_hazardous_NEOs} ({proportion}%)\n"
    content += f"  🌎 Closest near earth object: {get_closest_neo(data, today)}\n"

    content += f"\n#NASA #NASAAPI #space #comet #asteroid #twitterbot #bot\n"
    content += f"\nAstronomy Media of the Day 🔽"

    # return tweet content
    return content


def tweet_with_media(content, media):
    api.update_with_media(media, status=content)


def tweet_without_media(content):
    api.update_status(content)


def create_daily_tweet():
    content = create_daily_tweet_content()
    media = get_media_of_the_day(api_key)

    if (media["media_type"] == "video"):
        content += f'\n{media["url"]}'
        # post tweet with video of the day
        tweet_without_media(content)
    else:
        filename = 'temp.jpg'
        request = requests.get(media["url"], stream=True)
        if request.status_code == 200:
            with open(filename, 'wb') as image:
                for chunk in request:
                    image.write(chunk)

            # post tweet with image of the day
            tweet_with_media(content, media=filename)
            os.remove(filename)
        else:
            print("Unable to download image.")

    # print generated content to the console
    print(f"Generated tweet: \n{content}")


if __name__ == "__main__":
    create_daily_tweet()
