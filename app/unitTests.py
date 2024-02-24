import unittest

from app.utils import (
    downMove,
    hasEnoughBuyingPower,
    isNewInWatchlist,
    priceBelowStoploss,
    startMove,
    streakReachedThreshold,
    trailStoploss,
    updateStockPrice,
    upMove,
)


class TestTrade(unittest.TestCase):

    def test_isNewInWatchlist(self):
        self.assertTrue(
            isNewInWatchlist(watchlist={"MSFT": {"LAST_PRICE": "NONE"}}, stock="MSFT")
        )
        self.assertFalse(
            isNewInWatchlist(watchlist={"MSFT": {"LAST_PRICE": 268}}, stock="MSFT")
        )
        self.assertFalse(
            isNewInWatchlist(watchlist={"MSFT": {"LAST_PRICE": 268.72}}, stock="MSFT")
        )
        self.assertFalse(
            isNewInWatchlist(watchlist={"MSFT": {"LAST_PRICE": 268.72}}, stock="JPM")
        )

    def test_upMove(self):
        self.assertTrue(upMove(prev_price=100, curr_price=120))
        self.assertFalse(upMove(prev_price=1200, curr_price=120))
        self.assertFalse(upMove(prev_price=100, curr_price=100))

    def test_downMove(self):
        self.assertFalse(downMove(prev_price=100, curr_price=120))
        self.assertTrue(downMove(prev_price=1200, curr_price=120))
        self.assertFalse(downMove(prev_price=100, curr_price=100))

    def test_streakReachedThreshold(self):
        self.assertFalse(streakReachedThreshold(streak=4, streakThresh=7))
        self.assertTrue(streakReachedThreshold(streak=7, streakThresh=7))
        self.assertFalse(streakReachedThreshold(streak=4, streakThresh=5))

    def test_priceBelowStoploss(self):
        self.assertFalse(priceBelowStoploss(curr_price=12, stop_loss=11))
        self.assertTrue(priceBelowStoploss(curr_price=101, stop_loss=102))
        self.assertFalse(priceBelowStoploss(curr_price=1010, stop_loss=101))
        self.assertTrue(priceBelowStoploss(curr_price=99, stop_loss=101))

    def test_hasEnoughBuyingPower(self):
        self.assertTrue(
            hasEnoughBuyingPower(
                buying_power=1000, tradeThresh=10, buyQuantity=10, curr_price=9
            )
        )
        self.assertTrue(
            hasEnoughBuyingPower(
                buying_power=1000, tradeThresh=10, buyQuantity=10, curr_price=9.9
            )
        )
        self.assertTrue(
            hasEnoughBuyingPower(
                buying_power=1000, tradeThresh=10, buyQuantity=10, curr_price=1.6
            )
        )
        self.assertFalse(
            hasEnoughBuyingPower(
                buying_power=1000, tradeThresh=10, buyQuantity=10, curr_price=11
            )
        )
        self.assertFalse(
            hasEnoughBuyingPower(
                buying_power=1000, tradeThresh=10, buyQuantity=10, curr_price=95
            )
        )
        self.assertFalse(
            hasEnoughBuyingPower(
                buying_power=1000, tradeThresh=10, buyQuantity=10, curr_price=800
            )
        )

    def test_startMove(self):
        watchlist = {
            "JPM": {
                "type": "ALERT",
                "LAST_PRICE": 154.32,
                "MOVE_TYPE": "DOWN",
                "streak": 9,
                "stop_loss": "NONE",
                "stop_loss_percent": 2,
            }
        }
        watchlist = startMove(watchlist, "JPM", "UP")
        self.assertEqual(watchlist["JPM"]["MOVE_TYPE"], "UP")
        self.assertEqual(watchlist["JPM"]["streak"], 0)
        watchlist = {
            "JPM": {
                "type": "ALERT",
                "LAST_PRICE": 154.32,
                "MOVE_TYPE": "NONE",
                "streak": "NONE",
                "stop_loss": "NONE",
                "stop_loss_percent": 2,
            }
        }
        watchlist = startMove(watchlist, "JPM", "UP")
        self.assertEqual(watchlist["JPM"]["MOVE_TYPE"], "UP")
        self.assertEqual(watchlist["JPM"]["streak"], 0)
        watchlist = {
            "JPM": {
                "type": "ALERT",
                "LAST_PRICE": 154.32,
                "MOVE_TYPE": "UP",
                "streak": 5,
                "stop_loss": "NONE",
                "stop_loss_percent": 2,
            }
        }
        watchlist = startMove(watchlist, "JPM", "DOWN")
        self.assertEqual(watchlist["JPM"]["MOVE_TYPE"], "DOWN")
        self.assertEqual(watchlist["JPM"]["streak"], 0)

    def test_updateStockPrice(self):
        watchlist = {
            "JPM": {
                "type": "ALERT",
                "LAST_PRICE": 154.32,
                "MOVE_TYPE": "DOWN",
                "streak": 9,
                "stop_loss": "NONE",
                "stop_loss_percent": 2,
            }
        }
        watchlist = updateStockPrice(watchlist, "JPM", 101)
        self.assertEqual(watchlist["JPM"]["LAST_PRICE"], 101)
        watchlist = {
            "JPM": {
                "type": "ALERT",
                "LAST_PRICE": "NONE",
                "MOVE_TYPE": "DOWN",
                "streak": 9,
                "stop_loss": "NONE",
                "stop_loss_percent": 2,
            }
        }
        watchlist = updateStockPrice(watchlist, "JPM", 10.2)
        self.assertEqual(watchlist["JPM"]["LAST_PRICE"], 10.2)

    def test_trailStoploss(self):
        watchlist = {
            "JPM": {
                "type": "TRADE",
                "LAST_PRICE": 100,
                "MOVE_TYPE": "UP",
                "streak": 7,
                "stop_loss": 95,
                "stop_loss_percent": 5,
            }
        }
        watchlist = trailStoploss(watchlist, "JPM", 110)
        self.assertEqual(watchlist["JPM"]["stop_loss"], 104.5)
        watchlist = {
            "JPM": {
                "type": "TRADE",
                "LAST_PRICE": 100,
                "MOVE_TYPE": "UP",
                "streak": 7,
                "stop_loss": 95,
                "stop_loss_percent": 10,
            }
        }
        watchlist = trailStoploss(watchlist, "JPM", 110)
        self.assertEqual(watchlist["JPM"]["stop_loss"], 99)


if __name__ == "__main__":
    unittest.main()
