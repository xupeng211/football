# examples/minimal_backtest.py


import pandas as pd


# This is a placeholder for the actual backtest engine
# In a real scenario, you would import it from your project
class BacktestEngine:
    def run(self, data: pd.DataFrame, strategy: dict) -> dict:
        print("Running backtest...")
        initial_capital = strategy.get("initial_capital", 10000)
        win_rate = 0
        # Simulate a simple strategy
        if not data.empty:
            # Win if home odds are lower than away odds
            wins = data[data["odds_h"] < data["odds_a"]].shape[0]
            total_trades = data.shape[0]
            win_rate = (wins / total_trades) if total_trades > 0 else 0
            profit = (wins * 100) - (
                (total_trades - wins) * 100
            )  # Simplified profit calc
        else:
            profit = 0
            total_trades = 0

        final_capital = initial_capital + profit
        print(
            f"Backtest complete. Trades: {total_trades}, Final Capital: ${final_capital:.2f}, Win Rate: {win_rate:.2%}"
        )
        return {
            "final_capital": final_capital,
            "win_rate": win_rate,
            "trades": total_trades,
        }


def create_sample_data() -> pd.DataFrame:
    """Creates a sample DataFrame of historical match data for backtesting."""
    data = {
        "date": pd.to_datetime(
            ["2023-08-01", "2023-08-02", "2023-08-03", "2023-08-04"]
        ),
        "home_team": ["Team A", "Team C", "Team E", "Team G"],
        "away_team": ["Team B", "Team D", "Team F", "Team H"],
        "home_win_prob": [0.5, 0.4, 0.6, 0.3],
        "draw_prob": [0.3, 0.3, 0.2, 0.4],
        "away_win_prob": [0.2, 0.3, 0.2, 0.3],
        "odds_h": [2.0, 2.5, 1.6, 3.3],
        "odds_d": [3.0, 3.0, 4.0, 3.0],
        "odds_a": [4.0, 2.5, 5.0, 2.1],
        "result": ["home_win", "draw", "home_win", "away_win"],
    }
    return pd.DataFrame(data)


def run_backtest() -> None:
    """Runs a minimal backtest with sample data and a simple strategy."""
    historical_data = create_sample_data()
    engine = BacktestEngine()

    # Define a simple investment strategy
    strategy = {
        "name": "simple_odds_strategy",
        "description": "Bet on the team with the lower odds.",
        "initial_capital": 10000,
        "bet_size": 100,
    }

    # Run the backtest
    result = engine.run(historical_data, strategy)
    print("\nBacktest Results:")
    print(f"- Strategy: {strategy['name']}")
    print(f"- Final Capital: ${result['final_capital']:.2f}")
    print(f"- Win Rate: {result['win_rate']:.2%}")


if __name__ == "__main__":
    run_backtest()
