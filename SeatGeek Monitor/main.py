import json
import requests
import re
import random
import time
from playwright.sync_api import BrowserContext, sync_playwright
from playwright_stealth import stealth_sync
from urllib.request import Request, urlopen
import speech_recognition as sr

word_to_digit = {
    'zero': '0',
    'one': '1',
    'two': '2',
    'three': '3',
    'four': '4',
    'five': '5',
    'six': '6',
    'seven': '7',
    'eight': '8',
    'nine': '9'
}

def GetWav(audiourl):
    localname = "code.wav"
    with requests.get(audiourl) as req:
        req.raise_for_status()
        with open(localname, 'wb') as f:
            f.write(req.content)
    return localname

def GetCode(audio):
    r = sr.Recognizer()
    audio = sr.AudioFile(audio)
    with audio as source:
        audio = r.record(source)
    txt = r.recognize_google(audio)
    numbers = re.findall(r'\b(?:zero|one|two|three|four|five|six|seven|eight|nine)\b', txt)
    return ''.join([word_to_digit[word] for word in numbers])

def SendBot(msg):
    embed = msg
    payload = json.dumps({'content': embed, 'username': 'Beyonce', 'avatar_url': 'https://freepngimg.com/thumb/beyonce/5-2-beyonce-png.png'})
    headers2 = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
        }
    req = Request('https://discord.com/api/webhooks/1141893615493333133/iPYs56-1P6xmBwERAYmG4GmDfFZjOX_8SdvzVfX2VoOBad09Uv48lBw9SR4sj7_cMkej', data=payload.encode(), headers=headers2)
    urlopen(req)

url = 'https://seatgeek.com/beyonce-renaissance-world-tour-tickets/arlington-texas-at-t-stadium-2023-09-21-8-pm/concert/5922745'
proxy_strings = []

with open('proxies.txt', 'r') as file:
    proxy_strings = file.readlines()

proxies = []

for proxy_str in proxy_strings:
    parts = proxy_str.split(':')
    ip_port = f"http://{parts[0]}:{parts[1]}"
    username = parts[2]
    password = parts[3]
    proxy_config = {
        "server": ip_port,
        "username": username,
        "password": password.strip("\n")
    }
    proxies.append(proxy_config)

def Run(browser, proxy_config):
    global amtfound
    global amterror
    context = browser.new_context()
    stealth_sync(context)
    page = context.new_page()
    try:
        page.goto(url, timeout=30000)
        page.wait_for_selector("body")
        if page.query_selector("iframe"):
            wavurl = "null"
            frames = page.frames
            for frame in frames[1:]:
                print("Bypassing Captcha...")

                frame.wait_for_selector("#captcha__audio__button", timeout=10000).click()
                wavurl = frame.eval_on_selector('audio.audio-captcha-track', 'element => element.src')
                frame.wait_for_selector('.audio-captcha-play-button.push-button')
                frame.click('.audio-captcha-play-button.push-button')

                if wavurl != "null":
                    Wav = GetWav(wavurl)
                    Captcha = GetCode(Wav)
                    frame.wait_for_selector('.audio-captcha-inputs')
                    elements = frame.query_selector_all('.audio-captcha-inputs')
                    numbers = list(Captcha)
                    if len(numbers) != 6:
                        print(f"Error with captcha. Retrying... ({Captcha})")
                        browser.close()
                        break
                    for element, number in zip(elements, numbers):
                        time.sleep(random.uniform(0.5, 2))
                        element.type(number)
                break
        time.sleep(3)
        page.goto(url, timeout=30000)
        while True:
            try:
                resale = '.filterPillPresenters__PillButton-sc-c71530ce-0.icWXGb >> text="Hide resale"'
                page.wait_for_selector(resale)
                page.click(resale)
                parentalltickets = page.query_selector('[data-test="all-listings"]')
                alltickets = parentalltickets.query_selector_all(':scope > *')

                for ticket in alltickets[4:]:
                    divss = ticket.query_selector('div')
                    if divss:
                        aria = divss.get_attribute('aria-label')
                        if not "VIP" in aria:
                            SendBot(f"{aria}\nFound tickets! Click URL to purchase: {url}")
                            print("Found tickets")
                            ticket.click()
                            page.wait_for_selector('//*[text()="Go to checkout"]')
                            anchors = page.query_selector_all('a[href*="/checkout?"]')
                            for anchor in anchors:
                                href = "https://seatgeek.com" + anchor.get_attribute('href')
                                SendBot(f"Add to cart link: {href}\n---------------------------------------------------------------")
                            page.query_selector('[aria-label="Back to listings"]').click()
                            
                page.goto(url, timeout=30000)
                time.sleep(5)
            except Exception as x:
                print('Error in loop ' + str(x))
                browser.close()
                break

    except Exception as x:
        print('Error in all ' + str(x))
        browser.close()
        return
    return 0
        
def Main():
    with sync_playwright() as p:
        print(f"\rStarting to monitor {url}")
        while True:
            for proxy_config in proxies:
                #print(str(proxy_config))
                browser = p.chromium.launch(headless=False, proxy=proxy_config)
                Run(browser, proxy_config)
                time.sleep(1)

Main()
