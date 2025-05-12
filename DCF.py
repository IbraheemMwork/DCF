import yfinance as yf
import numpy as np

# Function to fetch Free Cash Flow (FCF)
def fetch_fcf(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    cashflow = stock.cashflow
    
    # Print available cashflow data for debugging
    print("Available cash flow data:")
    print(cashflow)
    
    try:
        # Try to fetch Operating Cash Flow and Capital Expenditures
        operating_cash_flow = cashflow.loc['Cash Flow From Continuing Operating Activities']
        capital_expenditures = cashflow.loc['Capital Expenditure']
        
        # Calculate Free Cash Flow: Operating Cash Flow - Capital Expenditures
        fcf = operating_cash_flow + capital_expenditures  # CapEx is usually negative
        fcf = fcf.dropna()  # Remove any NaN values
        
        if len(fcf) == 0:
            raise ValueError(f"Free Cash Flow data is not available for {ticker_symbol}.")
        
        return fcf
    except KeyError as e:
        # Handle missing data more gracefully
        print(f"KeyError: {e}. Attempting to find alternative data.")
        return None

# Function to get the growth rate from market consensus (via Yahoo Finance)
def get_growth_rate(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    growth_rate = info.get('earningsQuarterlyGrowth', None)  # Earnings growth (quarterly)
    if growth_rate is None:
        print(f"Growth rate data is not available for {ticker_symbol}. Using default growth rate.")
        return 0.08  # Default growth rate of 8% if not available
    return growth_rate

# Function to calculate the DCF
def calculate_dcf(
    last_fcf,
    growth_rate,
    discount_rate,
    terminal_growth_rate,
    projection_years
):
    projected_fcfs = [last_fcf * ((1 + growth_rate) ** year) for year in range(1, projection_years + 1)]
    discounted_fcfs = [fcf / ((1 + discount_rate) ** year) for year, fcf in enumerate(projected_fcfs, start=1)]

    # Terminal value
    terminal_value = projected_fcfs[-1] * (1 + terminal_growth_rate) / (discount_rate - terminal_growth_rate)
    discounted_terminal_value = terminal_value / ((1 + discount_rate) ** projection_years)

    total_value = sum(discounted_fcfs) + discounted_terminal_value
    return total_value


# === Example usage ===
ticker = input("enter your ticker ")  # Replace with the desired stock symbol

try:
    # Fetch FCF data
    fcfs = fetch_fcf(ticker)
    stock = yf.Ticker(ticker)  # Needed again to look for sharesOutstanding 
    
    if fcfs is None:
        print(f"Unable to fetch Free Cash Flow for {ticker}. Please check the available cash flow data above.")
    else:
        # Fetch growth rate (either from market consensus or default)
        growth_rate = get_growth_rate(ticker)
        
        # Estimate WACC (Discount Rate) and Terminal Growth Rate
        discount_rate = 0.0782  # Default WACC/Discount Rate (You can replace this with actual market data)
        terminal_growth_rate = min(growth_rate,0.03)  # Terminal Growth Rate, typically 2-3% for mature companies
        projection_years = 5  # Projection for the next 5 years

        latest_fcf = fcfs.iloc[0] / 1e6  # Convert to millions for clarity

        # Calculate DCF
        dcf_value = calculate_dcf(
            last_fcf=latest_fcf,
            growth_rate=growth_rate,
            discount_rate=discount_rate,
            terminal_growth_rate=terminal_growth_rate,
            projection_years=projection_years
        )

        print(f"\nLatest FCF for {ticker}: ${latest_fcf:.2f} million")
        print(f"Growth Rate for {ticker}: {growth_rate * 100:.2f}%")
        print(f"Estimated DCF for {ticker}: ${dcf_value:.2f} million")

        # Estimate intrinsic stock price
        shares_outstanding = stock.info.get("sharesOutstanding", None)
        if shares_outstanding:
            dcf_per_share = (dcf_value * 1e6) / shares_outstanding  # Convert from millions
            print(f"DCF Estimated Stock Price for {ticker}: ${dcf_per_share:.2f}")
        else:
            print("Shares outstanding data not available.")

except Exception as e:
    print("Error:", e)