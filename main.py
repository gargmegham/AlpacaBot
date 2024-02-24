from __future__ import print_function

import base64
import configparser
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText

import alpaca_trade_api as tradeapi
import pandas as pd
from google.cloud import storage

from app.google_service import create_Service
from app.utils import (
    downMove,
    hasEnoughBuyingPower,
    isMarketOpen,
    isNewInWatchlist,
    placeOrder,
    priceBelowStoploss,
    startMove,
    streakReachedThreshold,
    trailStoploss,
    updateStockPrice,
    upMove,
)

GOOGLE_CLIENT_SECRET_FILE = "secrets/google_client_secrets.json"
API_NAME = "gmail"
API_VERSION = "v1"
SCOPES = ["https://mail.google.com/"]

config = configparser.ConfigParser()
config.read("secrets/secrets.ini")
secrets = config["DEFAULT"]
TO_MAIL = secrets["TO_MAIL"]
SERVICE = create_Service(
    GOOGLE_CLIENT_SECRET_FILE, API_NAME, API_VERSION, secrets["BUCKET_NAME"], SCOPES
)
alerts = list()


def addMoveAlert(stock, move_type, streak):
    global alerts
    alert = "ALERT {} in {} MOVE for last {} days".format(stock, move_type, streak)
    alerts.append(alert)


def addFundAlert(
    stock, buying_power, tradeThresh, curr_price, buyQuantity, move_type, streak
):
    global alerts
    alert = (
        "Not enough funds, please add {}$. ALERT {} in {} MOVE for last {} days".format(
            (buyQuantity * float(curr_price)) / (tradeThresh / 100)
            - float(buying_power),
            stock,
            move_type,
            streak,
        )
    )
    alerts.append(alert)


def create_message(subject="Alerts from your alpaca trading bot", to=TO_MAIL):
    global alerts
    msg = ""
    for alert in alerts:
        msg += alert
        msg += "\n"
    message = MIMEText(msg)
    message["to"] = to
    message["subject"] = subject
    raw_string = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw_string}


def sendAlerts():
    try:
        SERVICE.users().messages().send(userId="me", body=create_message()).execute()
    except Exception:
        pass


def downMoveStrategy(
    curr_price, stock, watchlist, api, account, streakThresh, sellQuantity
):
    # if previously was not in down move set down move and streak
    if watchlist[stock]["MOVE_TYPE"] != "DOWN":
        watchlist = startMove(watchlist, stock, move_type="DOWN")
    # increment streak
    watchlist[stock]["streak"] += 1
    # if streak is greater than threshold
    if streakReachedThreshold(watchlist[stock]["streak"], streakThresh):
        # if type is alert, add an alert
        if watchlist[stock]["type"] == "ALERT":
            addMoveAlert(
                stock, watchlist[stock]["MOVE_TYPE"], watchlist[stock]["streak"]
            )
        else:
            # if account is blocked, add an alert
            if account.trading_blocked:
                alerts.append(
                    "trading blocked. ALERT {} in {} MOVE for last {} days".format(
                        stock, watchlist[stock]["MOVE_TYPE"], watchlist[stock]["streak"]
                    )
                )
            else:
                try:
                    position = api.get_position(stock)
                    # if we have it in our account, place a market sell order with day type if price is below stop loss
                    if priceBelowStoploss(
                        float(curr_price), watchlist[stock]["stop_loss"]
                    ):
                        placeOrder(api, stock, "sell", sellQuantity)
                except:
                    pass
    return watchlist


def upMoveStrategy(
    curr_price,
    stock,
    watchlist,
    api,
    account,
    streakThresh,
    tradeThresh,
    buyQuantity,
    prev_price,
):
    if curr_price > prev_price:
        # if previously was not in up move set up move and streak
        if watchlist[stock]["MOVE_TYPE"] != "UP":
            watchlist = startMove(watchlist, stock, move_type="UP")
        # increment streak
        watchlist[stock]["streak"] += 1
    # if type is alert, add an alert
    if watchlist[stock]["type"] == "ALERT":
        # if streak is greater than threshold
        if (
            streakReachedThreshold(watchlist[stock]["streak"], streakThresh)
            and curr_price > prev_price
        ):
            addMoveAlert(
                stock, watchlist[stock]["MOVE_TYPE"], watchlist[stock]["streak"]
            )
    else:
        # if account is blocked, add an alert
        if account.trading_blocked:
            alerts.append(
                "trading blocked. ALERT {} in {} MOVE for last {} days".format(
                    stock, watchlist[stock]["MOVE_TYPE"], watchlist[stock]["streak"]
                )
            )
        else:
            try:
                # if you have enough buying power place a buy order
                if hasEnoughBuyingPower(
                    account.buying_power, tradeThresh, buyQuantity, curr_price
                ):
                    placeOrder(api, stock, "buy", buyQuantity)
                    # trail your stop loss
                    watchlist = trailStoploss(watchlist, stock, curr_price)
                else:
                    # if you don't have enough buying power send an alert
                    addFundAlert(
                        stock,
                        account.buying_power,
                        tradeThresh,
                        curr_price,
                        buyQuantity,
                        watchlist[stock]["MOVE_TYPE"],
                        watchlist[stock]["streak"],
                    )
            except:
                pass
    return watchlist


def alreadyWatching(
    prev_price,
    curr_price,
    stock,
    watchlist,
    api,
    account,
    streakThresh,
    tradeThresh,
    buyQuantity,
    sellQuantity,
    priceFourteenDaysAgo,
):
    # if price moved down
    if downMove(prev_price, curr_price):
        watchlist = downMoveStrategy(
            curr_price, stock, watchlist, api, account, streakThresh, sellQuantity
        )
    # if price moved up
    elif upMove(prev_price=priceFourteenDaysAgo, curr_price=curr_price):
        watchlist = upMoveStrategy(
            curr_price,
            stock,
            watchlist,
            api,
            account,
            streakThresh,
            tradeThresh,
            buyQuantity,
            prev_price,
        )
    return watchlist


def startEngine(
    streakThresh=7,
    tradeThresh=33,
    buyQuantity=5,
    sellQuantity=5,
    inputPath="assets/watchlist.json",
):
    try:
        api = tradeapi.REST(
            secrets["APCA_API_KEY_ID"],
            secrets["APCA_API_SECRET_KEY"],
            secrets["APCA_API_BASE_URL"],
        )
        clock = api.get_clock()
        # check if market is closed
        if not isMarketOpen(clock):
            return
        account = api.get_account()
        bucket_name = "august-ensign-318717.appspot.com"
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(inputPath)
        data = blob.download_as_text()
        watchlist = json.loads(data)
        stocks = list(watchlist.keys())
        barset = api.get_barset(stocks, "day", limit=1)
        for stock in watchlist:
            try:
                curr_price = barset[stock][0].c
            except:
                continue
            prev_price = watchlist[stock]["LAST_PRICE"]
            today = datetime.now()
            fourteenDaysAgo = today - timedelta(days=14)
            fourteenDaysAgo = fourteenDaysAgo.strftime("%Y-%m-%d")
            fourteenDaysAgo = pd.Timestamp(
                fourteenDaysAgo, tz="America/New_York"
            ).isoformat()
            try:
                priceFourteenDaysAgo = api.get_barset(
                    [stock], "day", start=fourteenDaysAgo, end=fourteenDaysAgo
                )
                priceFourteenDaysAgo = priceFourteenDaysAgo[stock][0].c
            except:
                priceFourteenDaysAgo = prev_price
            # if this is not a new stock
            if not isNewInWatchlist(stock, watchlist):
                watchlist = alreadyWatching(
                    prev_price,
                    curr_price,
                    stock,
                    watchlist,
                    api,
                    account,
                    streakThresh,
                    tradeThresh,
                    buyQuantity,
                    sellQuantity,
                    priceFourteenDaysAgo,
                )
            # update the last seen price of this stock
            watchlist = updateStockPrice(watchlist, stock, curr_price)
        # update the json file
        newData = json.dumps(watchlist)
        newBlob = bucket.get_blob("watchlist.json")
        newBlob.upload_from_string(newData)
    except Exception as e:
        pass


def main(**kwargs):
    try:
        startEngine()
        if len(alerts):
            sendAlerts()
        return
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
