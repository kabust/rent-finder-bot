<img src="demo/logo.png" width=100%>

# Rent Finder Bot
Telegram Bot for scraping real estate in Poland to rent in real-time. 
Bot sends scheduled messages every 5 minutes, so you can receive the freshest ads out there.

# Link
https://t.me/rent_fndr_bot

# Features
* OLX Detailed Scraping with each ad features
* Telegram Bot with states and DB interactions
* Scheduling with asyncio
* An option to choose and update city
* Inline buttons and Keyboard menu
* Simple admin messaging
* Bot pausing
* To be add: filtering (by price, surface size, ad type, etc.)

# Technologies
* Beautiful Soup and Requests for scraping
* aiogram3 to handle Telegram Bot
* sqlite3 to store and manipulate data
* Asyncio for concurrent scraping and aiogram polling

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
alembic upgrade head
python -m main
```

To update your DB schema:
```bash
alembic revision --autogenerate -m "revision_description"
```
