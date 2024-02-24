def isMarketOpen(clock):
    return clock.is_open


def isNewInWatchlist(stock, watchlist):
    try:
        if watchlist[stock]["LAST_PRICE"] == "NONE":
            return True
        return False
    except:
        return False


def upMove(prev_price, curr_price):
    if prev_price < curr_price:
        return True
    return False


def downMove(prev_price, curr_price):
    if prev_price > curr_price:
        return True
    return False


def startMove(watchlist, stock, move_type):
    try:
        watchlist[stock]["MOVE_TYPE"] = move_type
        watchlist[stock]["streak"] = 0
        return watchlist
    except:
        return False


def placeOrder(api, symbol, side, qty):
    try:
        api.submit_order(
            symbol=symbol, side=side, type="market", qty=qty, time_in_force="day"
        )
        return True
    except:
        return False


def streakReachedThreshold(streak, streakThresh):
    return streak >= streakThresh


def priceBelowStoploss(curr_price, stop_loss):
    return curr_price <= stop_loss


def trailStoploss(watchlist, stock, curr_price):
    watchlist[stock]["stop_loss"] = (
        curr_price - (watchlist[stock]["stop_loss_percent"] * float(curr_price)) / 100
    )
    return watchlist


def hasEnoughBuyingPower(buying_power, tradeThresh, buyQuantity, curr_price):
    return ((float(buying_power) * tradeThresh) / 100) > (buyQuantity * curr_price)


def updateStockPrice(watchlist, stock, curr_price):
    watchlist[stock]["LAST_PRICE"] = curr_price
    return watchlist
