# examples/minimal_predict.py

import json

import requests

API_URL = "http://localhost:8000/predict"


def run_prediction() -> None:
    """Sends a sample prediction request to the API and prints the response."""
    sample_matches = [
        {
            "home": "Manchester United",
            "away": "Arsenal",
            "odds_h": 2.5,
            "odds_d": 3.5,
            "odds_a": 2.8,
        },
        {
            "home": "Chelsea",
            "away": "Liverpool",
            "odds_h": 3.1,
            "odds_d": 3.6,
            "odds_a": 2.2,
        },
    ]

    try:
        response = requests.post(API_URL, json=sample_matches, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes

        predictions = response.json()
        print("Prediction successful!")
        print(json.dumps(predictions, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while calling the API: {e}")
        print(
            "Please ensure the API service is running. You can start it with 'make dev'."
        )


if __name__ == "__main__":
    run_prediction()
