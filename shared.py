import re
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +https://www.google.com/bot.html)",
    "referer": "no-referrer-when-downgrade",
    "Connection": "close",
}

def get_request(url):
    """
    attempts to make a conection to retrieve url content
    if connection unsuccessful None object returned
    """
    try:
        response = requests.get(url, headers=headers, timeout=15)
        raw_html = response.content
    except requests.exceptions.RequestException as e:
        return None
    return raw_html


def make_decimal(string):
    result = 0
    if string:
        result = re.sub('[^0-9.]', '', string)
        try:
            result = float(result)
        except:
            result = 0
            pass
    return result