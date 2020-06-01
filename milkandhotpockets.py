import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from itertools import cycle
import asyncio
import random
import time

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')


desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
chrome_options = Options()
#chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")

browser = webdriver.Chrome(options = chrome_options, executable_path = (desktop + "\chromedriver"))
browser.get('https://www.amazon.com/ap/signin?_encoding=UTF8&ignoreAuthState=1&openid.assoc_handle=usflex&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.ns.pape=http%3A%2F%2Fspecs.openid.net%2Fextensions%2Fpape%2F1.0&openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_custrec_signin&switch_account=')

u = browser.find_element_by_id('ap_email')
for x in USER:
    u.send_keys(x)
    time.sleep(random.randint(1, 5))
u.send_keys(Keys.ENTER)

pw = browser.find_element_by_name('password')
for x in PASSWORD:
    pw.send_keys(x)
    time.sleep(random.randint(1, 5))
pw.send_keys(Keys.ENTER)

class list_item(object):
    def __init__(self, title, link, available = False):
        self.title = title
        self.link = link
        self.available = available

class grocery_items(object):
    def __init__(self):
        self.items = []

    def additems(self, item):
        self.items.append(item)

master_list = grocery_items()

bot = commands.Bot(command_prefix = '.')
client = discord.Client()

async def background1(channel, current_item):
    try:
        browser.get(current_item.link)
        availability = browser.find_element_by_class_name('a-size-medium').text
        print(availability)
        if availability == 'Out of Stock':
            current_item.available = False
        else:
            if current_item.available == False:
                await channel.send("```{} is now in stock!```".format(current_item.title))
            current_item.available = True
    except:
        if current_item.available == False:
            await channel.send("```{} is now in stock!```".format(current_item.title))
        current_item.available = True

async def background():
    await client.wait_until_ready()
    channel = client.get_channel(#CHANNEL)
    while True:
        counter = len(master_list.items)
        while(counter == 0):
            counter = len(master_list.items)
            await asyncio.sleep(10)
        groceries = cycle(master_list.items)
        while len(master_list.items) == counter:
            current_item = next(groceries)
            await background1(channel, current_item)
            await asyncio.sleep(300)

@client.event
async def on_ready():
    print('Bot is ready')

async def search(message, item):
    browser.get('https://www.amazon.com/alm/storefront?almBrandId=QW1hem9uIEZyZXNo')
    browser.find_element_by_id('twotabsearchtextbox').send_keys(item, Keys.ENTER)
    titles = browser.find_elements_by_class_name("a-size-mini")
    links = []
    for x in titles:
        try:
            links.append([x.text, x.find_element_by_css_selector('*').get_attribute('href')])
        except:
            pass
    if len(links) == 0:
        await message.channel.send("No results for {}!".format(item))
    else:
        s = ""
        counter1 = 0
        while(counter1 != len(links) and (len(s + '{}. {}\n'.format(counter1 + 1, links[counter1][1]))) < (1976 - len(str(counter1)))):
            s += '{}. {}\n'.format(counter1 + 1, links[counter1][1])
            counter1 += 1
        s += "```"
        s = "```Top {} Results from Amazon\n".format(counter1) + s
        await message.channel.send(s)

async def add(message, item):
    try:
        browser.get(item)
        if browser.find_element_by_id('fresh-merchant-info').text != 'Ships from and sold by AmazonFresh.':
            print(error)
        add = list_item(browser.find_element_by_id('productTitle').text, item)
        master_list.additems(add)
        await message.channel.send('```{} has been added to list!```'.format(add.title))
    except:
        await message.channel.send('```Invalid Link!```')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    elif message.content == '.list':
        if len(master_list.items) == 0:
            await message.channel.send('```There are currently no items.```')
        else:
            string1 = "```Current Grocery Items\n"
            for x in range(len(master_list.items)):
                string1 += "{}. {}\n".format(x + 1, master_list.items[x].title)
            string1 += "```"
            await message.channel.send(string1)

    elif len(message.content.split(' ')) > 1 and message.content.split(' ')[0] == '.search':
        item = message.content.split(' ')
        item = ' '.join(item[1:])
        await search(message, item)

    elif len(message.content.split(' ')) > 1 and message.content.split(' ')[0] ==  '.add':
        item = message.content.split(' ')
        item = ''.join(item[1:])
        await add(message, item)

    elif message.content == '.clear':
        master_list.items = []
        await message.channel.send('```List has been cleared.```')

client.loop.create_task(background())
client.run(TOKEN)
