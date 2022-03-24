import argparse
import requests
import time

from bs4 import BeautifulSoup as bs
from os import path, mkdir
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


SCROLL_PAUSE_TIME = 1


def init_driver(url: str):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)

    driver.get(url)

    return driver


def parse_post(url: str, path_to: str):

    driver = init_driver(url=url)

    content = driver.page_source.encode('utf-8').strip()

    soup = bs(content, 'html5lib')

    table = soup.find('div', attrs={'class': 'article-render'})

    article_name = soup.find(
        'h1', attrs={'class': 'article__title', 'itemprop': 'headline'}).text

    article = '\n'.join([row.text
                         for row in table.find_all('span')])

    with open(path.join(path_to, f'{article_name}.txt'), 'w+') as f:
        f.write(article[1:-2])


def main(profile_url: str, download_path: str):
    # create download dir
    if not path.exists(download_path):
        mkdir(download_path)

    req = requests.get(profile_url)
    soup = bs(req.content, 'html5lib')

    # get yandx_zen chanel name
    table = soup.find(
        'div', attrs={'class': 'desktop-channel-info-layout__title'})
    chanel_name = '_'.join([row.text.strip().replace('/', '_')
                           for row in table.findAll('span')])

    # create download subdir
    sub_dir = path.join(download_path, chanel_name)
    if not path.exists(sub_dir):
        mkdir(sub_dir)

    # parse articles
    driver = init_driver(profile_url)

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    posts = driver.find_elements(by=By.CLASS_NAME,
                                 value="card-image-compact-view__content")

    for block in posts:
        post_url = bs(block.get_attribute('innerHTML'),
                      "html.parser").find('a')['href']
        parse_post(post_url, sub_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download articles of an author from Yandex Zen')

    parser.add_argument(
        '-u', '--url', help='Yandex Zen profile url', required=True)
    parser.add_argument(
        '-p', '--path_to', help='Download directory', required=True)
    args = vars(parser.parse_args())

    profile_url = args['url']
    download_path = args['path_to']

    main(profile_url, download_path)
