import requests as req
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

_ENDPOINT_ = 'https://ftx.com/api'
tickers = ['BTC-PERP', 'ETH-PERP', 'ADA-PERP']
number_of_tickers = len(tickers)
HOUR = 3600
START = 1633046400
END = 1635721200

consolidated_ticker_data = []


def get_data(ticker):
    response = req.get(_ENDPOINT_ + f'/markets/{ticker}/candles?resolution={HOUR}' +
                       f'&start_time={START}&end_time={END}')

    # Handling HTTP Status Codes
    if not 200 <= response.status_code <= 299:
        sys.exit('HTTP Request Error. Please check API endpoint.')

    data = response.json()
    hourly_data = []
    for hour_info in data["result"]:
        hourly_data.append(hour_info["close"])

    consolidated_ticker_data.append(hourly_data)


def __main__():
    for ticker in tickers:
        get_data(ticker)

    df = pd.DataFrame(consolidated_ticker_data).T
    df.columns = tickers
    df = df.pct_change()
    mva(df)


def mva(df):
    # Covariance matrix of the assets. Should be n x n matrix
    covariance_vector = df.cov()
    sigma_list = []
    miu_list = []
    for x in df:
        # For each ticker, multiply the daily varianace by 250 and sqrt it for sigma over entire period.
        variance = df[x].var() * 250
        sigma = np.sqrt(variance)
        sigma_list.append(sigma)

        # Expected value of the rate of return
        miu = df[x].mean()
        miu_list.append(miu)

    recorded_weights = []
    recorded_miu = []
    recorded_sigma = []

    miu_vector = np.array(miu_list)
    for portfolio in range(10000):
        # Using np.random.random to generate random weights.
        randomized_weights = np.random.random(number_of_tickers)
        weight_vector = randomized_weights / randomized_weights.sum()
        recorded_weights.append(weight_vector)

        # Return is miu vector * weight vector
        portfolio_return = np.matmul(miu_vector.transpose(), weight_vector)
        recorded_miu.append(portfolio_return)

        # Portfolio variance = weight_vector_transpose * covariance_vector * weight_vector
        # Note that the covariance_vector is still in terms of daily variances+covariances.
        # Therefore, portfolio_volatility needs to be multiplied by sqrt(250)
        portfolio_variance = np.matmul(np.matmul(weight_vector.transpose(), covariance_vector), weight_vector)
        portfolio_sigma = np.sqrt(portfolio_variance * 250)
        recorded_sigma.append(portfolio_sigma)

    # Plotting of M.V Frontier
    plt.scatter(recorded_sigma, recorded_miu)
    plt.show()

    # Minimum variance portfolio
    results = pd.DataFrame(list(zip(recorded_miu, recorded_sigma)), columns=['Return', 'Risk'])
    index_of_lowest_risk_portfolio = results['Risk'].idxmin(axis=1)
    final_weights = recorded_weights[index_of_lowest_risk_portfolio]
    final_results = results.iloc[index_of_lowest_risk_portfolio]

    # Output of different weights:
    print(f'GMVP Return: {final_results[0]} Volatility: {final_results[1]}')
    for count, ticker in enumerate(tickers):
        print(f'{ticker}: {round(final_weights[count] * 100, 2)}% of portfolio')

    # Write to output file
    with open('Results.txt', 'w') as file:
        output_dict = {}
        for count, ticker in enumerate(tickers):
            output_dict[ticker] = final_weights[count]
        file.write(json.dumps(output_dict))


if __name__ == '__main__':
    __main__()

