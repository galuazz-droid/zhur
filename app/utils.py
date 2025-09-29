def calculate_cash_end(cash_start, cash_in, incassation, salary, rko, pko, exchange):
    return cash_start + cash_in - incassation - salary - rko + pko + exchange

def validate_counter(counter_start, counter_end, total_revenue, tolerance=1.0):
    return abs((counter_end - counter_start) - total_revenue) <= tolerance
