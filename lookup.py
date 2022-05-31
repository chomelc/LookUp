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


def create_title_string():
    return f"Beep beep, here's {get_today_as_text()} update:\n\n"


def create_approaching_neos_string(total):
    return f"  ☄️ Approaching near earth objects: {total}\n"


def create_hazardous_neos_string(pot_hazardous_NEOs, proportion):
    return f"  🚨 Potentially hazardous asteroids: {pot_hazardous_NEOs} ({proportion}%)\n"


def create_closest_neo_string(data, today):
    return f"  🌎 Closest near earth object: {get_closest_neo(data, today)}\n"


def create_hashtags_string():
    return f"\n#NASA #NASAAPI #space #comet #asteroid #twitterbot #bot"


def create_media_of_the_day_string(orientation):
    content = f"Astronomy Media of the Day "
    content += "🔽" if orientation == "down" else "▶️"
    return content


def create_daily_tweet_content():
    today = get_today()
    content = create_title_string()

    # get data
    data = get_neos_by_approach_date(today, api_key)

    # total NEOs
    total = get_number_of_neos(data)
    content += create_approaching_neos_string(total)

    # potentially hazardous asteroids
    pot_hazardous_NEOs = get_number_of_potentially_hazardous_neos(data, today)
    proportion = "{:.0f}".format((pot_hazardous_NEOs/total)*100)
    content += create_hazardous_neos_string(pot_hazardous_NEOs, proportion)
    content += create_closest_neo_string(data, today)

    content += create_hashtags_string()

    # return tweet content
    return content


def create_daily_subtweet_content():
    content = create_media_of_the_day_string(orientation="down")
    return content


def tweet_with_media(content, media):
    tweet = api.update_with_media(media, status=content)
    return tweet


def tweet_without_media(content):
    tweet = api.update_status(content)
    return tweet


def reply_tweet_with_media(tweet_id, content, media):
    api.update_with_media(
        media, status=content, in_reply_to_status_id=tweet_id, auto_populate_reply_metadata=True)


def reply_tweet_without_media(tweet_id, content):
    api.update_status(content, in_reply_to_status_id=tweet_id,
                      auto_populate_reply_metadata=True)


def create_daily_tweet():
    content = create_daily_tweet_content()

    # print generated content to the console
    print(f"Generated tweet: \n{content}")
    # return tweet to get tweet_id for subtweet
    return tweet_without_media(content)


def create_daily_subtweet(tweet):
    content = create_daily_subtweet_content()
    media = get_media_of_the_day(api_key)

    if (media["media_type"] == "video"):
        content += f'\n{media["url"]}'
        # post tweet with video of the day
        reply_tweet_without_media(tweet.id_str, content)
    else:
        filename = 'temp.jpg'
        request = requests.get(media["url"], stream=True)
        if request.status_code == 200:
            with open(filename, 'wb') as image:
                for chunk in request:
                    image.write(chunk)

            # post tweet with image of the day
            reply_tweet_with_media(tweet.id_str, content, media=filename)
            os.remove(filename)
        else:
            print("Unable to download image.")

    # print generated content to the console
    print(f"\nGenerated subtweet (in response to {tweet.id_str}): \n{content}")


if __name__ == "__main__":
    tweet = create_daily_tweet()
    create_daily_subtweet(tweet)
