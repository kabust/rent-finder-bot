# Rent Finder Bot
Telegram Bot for scraping real estate in Poland to rent in real-time. 
Bot sends scheduled messages every 5 minutes, so you can receive the freshest ads out there.

# Features
* OLX Scraping
* Telegram Bot with states and DB interactions
* Scheduling with asyncio
* An option to choose city

# Technologies
* Beautiful Soup and Requests for scraping
* aiogram3 to handle Telegram Bot
* sqlite3 to store and manipulate data

# How to run
(You need to have python3 installed)
```bash
git clone https://github.com/kabust/rent-finder-bot.git
cd rent-finder-bot
python -m venv venv

# Windows
venv\Scripts\activate
# MacOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python -m main
```
