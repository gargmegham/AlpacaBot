# AlpacaBot

Welcome to AlpacaBot! This repository contains the source code for a bot that interacts with Alpaca API.

## Features

- given a list of stocks
- run script on daily basis
- It checks price for every stock from list
- Stores an upmove/downmove
- if move has a streak of certain number of days
    1. if it's set to track give alert
    2. if it's set to trade
        1. if streak is of down move
            1. if we have this stock in our account:
                a. if price falls below stop loss, sell 5 of your number of shares
        1. if streak is of up move
            1. keep the stock if you already have it and trail your stop loss upwards
            2. buy 5 if you don't have it with x% of tradable cash
- To add a new test case:
    1. in test_assets folder make a new json file similar to others with a serial incremented number
    2. in app/test.py change value of range in for loop

## Installation

1. Clone the repository: `git clone https://github.com/gargmegham/AlpacaBot.git`
2. Install the dependencies: `pip install -r requirements.txt`

## Configuration

1. Replace sample secrets under secrets directory with your own secrets

## Usage

1. Run the bot: `python main.py`
2. The bot will start interacting with the Alpaca API.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request. Make sure to follow the [contribution guidelines](CONTRIBUTING.md).

## License

This project is licensed under the [MIT License](LICENSE).


## Contact

For any questions or inquiries, please contact [meghamgarg@gmail.com](mailto:meghamgarg@gmail.com).
