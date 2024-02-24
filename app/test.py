from main import main, alerts, sendAlerts

if __name__ == "__main__":
    try:
        for i in range(1, 3):
            main(
                streakThresh=7,
                tradeThresh=33,
                buyQuantity=5,
                sellQuantity=5,
                inputPath="tests/{}.json".format(i),
            )
        if len(alerts):
            sendAlerts()
    except KeyboardInterrupt:
        pass
