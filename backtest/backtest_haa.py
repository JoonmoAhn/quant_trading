# refernce : https://blog.naver.com/quant_92/223312575832

import os
import glob
import logging
from datetime import timedelta, datetime

import pandas as pd
import numpy as np

# from google.colab import files


class Configuration:
    def __init__(self):
        # 여기에 모든 설정을 초기화합니다.
        self.tickers = [
            "TIP",
            "IEF",
            "SPY",
            "QQQ",
            "VEA",
            "VWO",
            "TLT",
            "PDBC",
            "VNQ",
            "LQD",
            "GLD",
            "BIL",
        ]
        self.logging_level = logging.INFO
        self.logging_format = '%(asctime)s - %(levelname)s - %(message)s'
        self.date_format = '%Y-%m-%d %H:%M:%S'
        # 추가 설정이 필요한 경우 여기에 추가합니다.


config = Configuration()  # 설정 객체를 만듭니다.

logging.basicConfig(
    level=config.logging_level, format=config.logging_format, datefmt=config.date_format
)


# def delete_files(tickers):
#     """주어진 티커들에 대한 파일들을 삭제합니다."""
#     for ticker in tickers:
#         for file_path in glob.glob(f"{ticker}*"):
#             os.remove(file_path)
#             logging.info(f"{file_path} 파일이 삭제되었습니다.")


# def upload_files():
#     """파일을 업로드하고 성공 여부를 반환합니다."""
#     print("파일을 업로드해주세요:")
#     uploaded = files.upload()
#     return bool(uploaded)


def safe_load_adjusted_close_price(data_dir, ticker, start_date, end_date):
    file_path = os.path.join(data_dir, ticker + ".csv")
    if not os.path.exists(file_path):
        logging.error(f"{file_path} does not exist.")
        return None

    try:
        data = pd.read_csv(file_path, index_col="Date", parse_dates=True)["Adj Close"]
        data = data[start_date:end_date]
        if data.isnull().any():
            logging.warning(f"Data missing for {ticker}. Skipping this ticker.")
            return None
        return data.round(12)
    except FileNotFoundError:
        logging.error(f"File {file_path} not found.")
        return None
    except pd.errors.EmptyDataError:
        logging.error(f"No data in {file_path}.")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return None


def get_business_days_count(start_date, end_date):
    """특정 기간 동안의 실제 영업일 수를 반환합니다."""
    return np.busday_count(start_date.date(), end_date.date())


def calculate_momentum_scores(df, end_date):
    """스코어를 계산하여 반환합니다."""
    momentum_scores = {}
    end_date_dt = pd.Timestamp(end_date)

    # 실제 영업일 기반으로 각 기간 설정
    periods = {
        21: get_business_days_count(end_date_dt - pd.DateOffset(months=1), end_date_dt),
        63: get_business_days_count(end_date_dt - pd.DateOffset(months=3), end_date_dt),
        126: get_business_days_count(end_date_dt - pd.DateOffset(months=6), end_date_dt),
        252: get_business_days_count(end_date_dt - pd.DateOffset(months=12), end_date_dt),
    }

    for ticker in df.columns:
        current_price = df[ticker].iloc[-1]
        prices = [df[ticker].iloc[-periods[p]] for p in periods]
        returns = [(current_price - price) / price for price in prices]
        momentum_scores[ticker] = sum(returns) / len(returns) * 100

    return momentum_scores


def print_market_condition(momentum_scores, df, start_of_month, end_of_month):
    offensive_assets = ['SPY', 'QQQ', 'TLT', 'VEA', 'VWO', 'PDBC', 'GLD', 'VNQ']
    defensive_assets = ['BIL', 'LQD', 'IEF']

    # TIP의 스코어 계산
    tip_momentum_score = momentum_scores['TIP']

    # 모멘텀 스코어를 사용하여 상황 판단
    if tip_momentum_score > 0:
        print("🔵▶️ 상승장 상황")
        top4_assets = sorted(
            [asset for asset in momentum_scores if asset in offensive_assets],
            key=lambda asset: momentum_scores[asset],
            reverse=True,
        )[:4]
        for ticker in top4_assets:
            print(f"추천 투자 종목: {ticker} (모멘텀 스코어: {round(momentum_scores[ticker], 2)}%)")
    else:
        print("🔵▶️ 하락장 상황")
        handle_negative_market_condition(momentum_scores, df, start_of_month, end_of_month)


def handle_negative_market_condition(momentum_scores, df, start_of_month, end_of_month):
    scores = {ticker: momentum_scores[ticker] for ticker in ['IEF', 'LQD', 'BIL']}
    if all(value <= 0 for value in scores.values()):
        print("모든 종목의 모멘텀 스코어가 0 또는 음수입니다. 현금을 보유하세요.")
    else:
        best_defensive_asset = max(scores, key=scores.get)
        print(
            f"추천 투자 종목: {best_defensive_asset} (모멘텀 스코어: {round(scores[best_defensive_asset], 2)}%)"
        )


def display_momentum_scores(momentum_scores):

    offensive_assets = ['SPY', 'QQQ', 'TLT', 'VEA', 'VWO', 'PDBC', 'GLD', 'VNQ']
    print("\n🟢 Offensive Assets:")
    for ticker in offensive_assets:
        print(f"{ticker}: {round(momentum_scores.get(ticker, 0), 2)}")

    defensive_assets = ['BIL', 'LQD', 'IEF']
    print("\n🔴 Defensive Assets:")
    for ticker in defensive_assets:
        print(f"{ticker}: {round(momentum_scores.get(ticker, 0), 2)}")


def display_results(tickers, momentum_scores, df, end_date):
    start_of_month, end_of_month = get_month_range(end_date)

    # 나머지 출력 및 로직 처리를 진행
    month_to_hold = (pd.Timestamp(end_date).month % 12) + 1
    year_to_hold = pd.Timestamp(end_date).year + (1 if month_to_hold == 1 else 0)

    print(f"\n{year_to_hold}년 {month_to_hold}월 보유 종목:")

    # TIP의 모멘텀 스코어 출력
    tip_momentum_score = momentum_scores['TIP']
    print(f"TIP의 모멘텀 스코어: {round(tip_momentum_score, 2)}%")

    print_market_condition(momentum_scores, df, start_of_month, end_of_month)
    display_momentum_scores(momentum_scores)


def get_month_range(date_str):
    """주어진 날짜의 월의 시작과 끝 날짜를 반환합니다."""
    date_dt = pd.Timestamp(date_str)
    start_of_month = date_dt.replace(day=1)
    end_of_month = (start_of_month + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
    return start_of_month, end_of_month


def main():
    # delete_files(config.tickers)

    # if not upload_files():
    #     logging.error("파일 업로드에 실패하였습니다. 프로그램을 종료합니다.")
    #     return

    cur_file_path = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(cur_file_path), "data")

    start_date = input("시작 날짜를 입력하세요. (YYYY-MM-DD): ")
    end_date = input("마지막 날짜를 입력하세요. (YYYY-MM-DD): ")

    # start_date = "2021-01-01"
    # end_date = "2024-01-01"

    for _ in range(12):
        df = pd.DataFrame()

        for ticker in config.tickers:
            adjusted_close_data = safe_load_adjusted_close_price(
                data_dir, ticker, start_date, end_date
            )
            if adjusted_close_data is not None:
                df[ticker] = adjusted_close_data

        # TIP difference 계산
        one_year_ago = df.index[df.index <= pd.Timestamp(end_date)][-252]
        TIP_12m_avg = df['TIP'][one_year_ago:end_date].mean()
        tip_difference = df['TIP'].iloc[-1] - TIP_12m_avg

        momentum_scores = calculate_momentum_scores(df, end_date)  # 모멘텀 스코어 계산
        display_results(config.tickers, momentum_scores, df, end_date)
        end_date = (pd.Timestamp(end_date) - pd.DateOffset(months=1)).strftime('%Y-%m-%d')


if __name__ == "__main__":
    main()
