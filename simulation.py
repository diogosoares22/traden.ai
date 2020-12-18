from models import *
from ledger import Ledger
from stock_database import data_load
from utils import profit_percentage_by_year, time_between_days, get_year, get_month
import matplotlib.pyplot as plt


class Simulation:
    def __init__(self, identifier: int, balance: int, tradable_stocks: list, start_date: str, end_date: str, model):
        self.id = identifier
        self.initial_balance = balance
        self.tradable_stocks = tradable_stocks
        
        self.ledger = Ledger(balance, tradable_stocks)

        self.start_date = start_date
        self.end_date = end_date
        self.current_date = start_date
        self.iterator = 0
        
        self.logs = []
        self.data = data_load(tradable_stocks, start_date, end_date)

        self.model = model(self.tradable_stocks)

        self.actual_end_date = self.data[-1]["date"]
        
        self.evaluations = []

        for el in self.data:
            self.evaluations.append((str(el["date"]), []))

        self.results = []

    def execute(self, no_executions=1):
        self.model.preprocess_data(self.data)
        for i in range(no_executions):
            while (self.current_date != self.actual_end_date):
                self.model.execute(self)
                self.current_date = self.data[self.iterator]["date"]
                self.evaluations[self.iterator][1].append(self.get_current_value())                
                self.iterator += 1
            self.iterator -= 1
            self.sell_all()
            self.store_result()

    def buy(self, stock_name: str, amount: int):
        stock_price = self.stock_current_price(stock_name)
        isPossible = self.ledger.buy(stock_name, stock_price, amount)
        if isPossible:
            self.logs.append({"action":"Bought", "date": self.current_date, "stock_name": stock_name, "stock_price": stock_price, "amount": amount})

    def sell(self, stock_name: str,amount: int):
        stock_price = self.stock_current_price(stock_name)
        isPossible = self.ledger.sell(stock_name, stock_price, amount)
        if isPossible:
            self.logs.append({"action":"Sold", "date": self.current_date, "stock_name": stock_name, "stock_price": stock_price, "amount": amount})

    def sell_all(self):
        stocks = self.ledger.get_stocks()
        for stock in stocks:
            if stocks[stock] > 0:
                self.sell(stock, stocks[stock])

    def reset(self):
        self.ledger = Ledger(self.initial_balance, self.tradable_stocks)
        self.current_date = self.start_date
        self.iterator = 0
        self.logs = []

    def store_result(self):
        self.results.append({"profit": self.ledger.balance - self.initial_balance, "profit_percentage": ((self.ledger.balance - self.initial_balance) / self.initial_balance) * 100
                            ,"profit_percentage_year": profit_percentage_by_year(self.initial_balance, self.ledger.balance, time_between_days(self.start_date, self.end_date)), "logs": self.logs})
        self.reset()

    def stock_current_price(self, stock_name):
        return float(self.data[self.iterator][stock_name]["Close"])

    def get_current_value(self):
        cash = self.ledger.get_balance() 
        stocks_value = 0
        stocks = self.ledger.get_stocks()
        for stock in stocks:
            stocks_value += self.stock_current_price(stock) * stocks[stock]
        return cash + stocks_value 

    def get_results(self):
        return self.results

    def get_result(self, no_execution=0):
        if len(self.results) > no_execution: 
            return self.results[no_execution]

    def get_ledger(self):
        return self.ledger
    
    def get_iteration(self):
        return self.iterator

    def get_id(self):
        return self.id

    def get_initial_balance(self):
        return self.initial_balance

    def get_tradable_stocks(self):
        return self.tradable_stocks

    def get_start_date(self):
        return self.start_date

    def get_end_date(self):
        return self.end_date

    def get_model(self):
        return self.model.__class__.__name__
    
    def get_graph(self, mode="daily"):
        plt.xlabel("Time ({})".format(mode))
        plt.ylabel("Capital")    
        X = []
        Y = []
        for el in self.get_evaluations(mode=mode):
            Y.append(sum(el[1]) / len(el[1]))
        X = range(1,len(Y) + 1)
        plt.plot(X,Y)
        plt.show()

    def get_evaluations(self, mode="daily"):
        if mode=="daily":
            return self.evaluations
        elif mode=="monthly":
            filtered_evaluations = [self.evaluations[0]]
            for i in range(len(self.evaluations)):
                date = self.evaluations[i][0]
                previous_date = filtered_evaluations[-1][0]
                if get_year(date) != get_year(previous_date) or get_month(date) != get_month(previous_date):
                    filtered_evaluations.append(self.evaluations[i])
        elif mode=="yearly":
            filtered_evaluations = [self.evaluations[0]]
            for i in range(len(self.evaluations)):
                date = self.evaluations[i][0]
                previous_date = filtered_evaluations[-1][0]
                if get_year(date) != get_year(previous_date):
                    filtered_evaluations.append(self.evaluations[i])
        return filtered_evaluations

    def logs_str(self, no_execution=0):
        if len(self.results)==0:
            return 
        logs = self.results[no_execution]["logs"]
        logs_format = ""
        for log in logs:
            logs_format += "\t{} {} stocks of {} with price {} at {}\n".format(log["action"], log["amount"], log["stock_name"], log["stock_price"], log["date"])
        return logs_format
