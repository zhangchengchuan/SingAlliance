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

    # Just pass in the dataframe of percentage change
    mva(df.pct_change())


def mva(df):
    # Covariance matrix of the assets
    covariance_matrix = df.cov()
    inverse_covariance_matrix = np.linalg.inv(covariance_matrix.values)

    # Miu vector
    miu_list = [df[x].mean() for x in df]
    miu_vector = np.array(miu_list)

    # ANALYTICAL METHOD: By GMVP Formula
    ones = np.ones(len(tickers))

    # a is placeholder for (1 * C-1 * 1)
    a = np.matmul(np.matmul(ones.transpose(), inverse_covariance_matrix), ones)
    weight_vector = (np.matmul(inverse_covariance_matrix, ones)) / a
    print(weight_vector)

    # GRAPHICAL METHOD: Graph of Mean Variance Frontier
    recorded_weights = []
    recorded_miu = []
    recorded_sigma = []

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
        portfolio_variance = np.matmul(np.matmul(weight_vector.transpose(), covariance_matrix), weight_vector)
        portfolio_sigma = np.sqrt(portfolio_variance * 250)
        recorded_sigma.append(portfolio_sigma)

    # Getting the Global minimum variance portfolio
    results = pd.DataFrame(list(zip(recorded_miu, recorded_sigma)), columns=['Return', 'Risk'])
    index_of_lowest_risk_portfolio = results['Risk'].idxmin(axis=1)
    final_weights = recorded_weights[index_of_lowest_risk_portfolio]
    final_results = results.iloc[index_of_lowest_risk_portfolio]

    # Output of different weights:
    print(f'GMVP Return: {final_results[0]} Volatility: {final_results[1]}')
    for count, ticker in enumerate(tickers):
        print(f'{ticker}: {round(final_weights[count] * 100, 2)}% of portfolio')

    # Writing to output file
    with open('Results.txt', 'w') as file:
        output_dict = {}
        for count, ticker in enumerate(tickers):
            output_dict[ticker] = final_weights[count]
        file.write(json.dumps(output_dict))

    # Plotting of M.V Frontier
    plt.scatter(recorded_sigma, recorded_miu)
    plt.show()


if __name__ == '__main__':
    __main__()
