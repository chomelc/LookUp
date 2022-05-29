from dotenv import load_dotenv
import os
import requests
import json
from datetime import date
from config import create_api

load_dotenv()
api_key = os.getenv("NASA_API_KEY")


def getToday():
    return date.today().strftime("%Y-%m-%d")


def getTodayAsText():
    return date.today().strftime("%B %d, %Y")


def getData(url):
    response_API = requests.get(f"{url}")
    data = response_API.text
    return json.loads(data)


def getMediaOfTheDay(api_key):
    url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}"
    return getData(url)


def getNEOsByApproachDate(date, api_key):
    # retrieve Near Earth Objects by approach date
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={date}&end_date={date}&api_key={api_key}"
    return getData(url)


def getNumberOfNEOs(data):
    return data["element_count"]


def getNumberOfPotentiallyHazardousNEOs(data, today):
    count = 0
    for item in data["near_earth_objects"][today]:
        if (item["is_potentially_hazardous_asteroid"]):
            count += 1
    return count


def createTweetContent():
    today = getToday()
    content = f"Beep beep, here's {getTodayAsText()} update:\n\n"

    # get data
    data = getNEOsByApproachDate(today, api_key)

    # total NEOs
    total = getNumberOfNEOs(data)
    content += f"  ☄️ Approaching near earth objects: {total}\n"

    # potentially hazardous asteroids
    pot_hazardous_NEOs = getNumberOfPotentiallyHazardousNEOs(data, today)
    proportion = "{:.0f}".format((pot_hazardous_NEOs/total)*100)
    content += f"  🚨 Potentially hazardous asteroids: {pot_hazardous_NEOs} ({proportion}%)\n"

    content += f"\n#NASA #NASAAPI #space #comet #asteroid #twitterbot #bot\n"
    content += f"\nAstronomy Media of the Day 🔽"

    # return tweet content
    return content


def createTweet(api):
    content = createTweetContent()
    media = getMediaOfTheDay(api_key)

    if (media["media_type"] == "video"):
        content += f'\n{media["url"]}'
        api.update_status(content)
    else:
        filename = 'temp.jpg'
        request = requests.get(media["url"], stream=True)
        if request.status_code == 200:
            with open(filename, 'wb') as image:
                for chunk in request:
                    image.write(chunk)

            # post tweet with image of the day
            api.update_with_media(filename, status=content)
            os.remove(filename)
        else:
            print("Unable to download image.")

    # print generated content to the console
    print(f"Generated tweet: \n{content}")


if __name__ == "__main__":
    api = create_api()
    createTweet(api)
