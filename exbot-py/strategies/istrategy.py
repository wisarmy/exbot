from abc import ABC, abstractmethod

from strategies import strategy


class IStrategy(ABC):
    @abstractmethod
    def populate_indicators(self, df):
        pass

    @abstractmethod
    def populate_buy_trend(self, df):
        pass

    @abstractmethod
    def populate_sell_trend(self, df):
        pass

    @abstractmethod
    def populate_close_position(self, df):
        pass

    def trade(self, ex, df, args):
        side = None
        if args.debug == False:
            match args.amount_type:
                case "quantity":
                    side = strategy.amount_limit(
                        ex,
                        df,
                        args.symbol,
                        args.amount,
                        args.amount_max,
                        reversals=args.reversals,
                    )
                case "usdt":
                    side = strategy.uamount_limit(
                        ex,
                        df,
                        args.symbol,
                        args.amount,
                        args.amount_max,
                        reversals=args.reversals,
                    )

                case _:
                    raise ValueError(f"Invalid amount_type: {args.amount_type}")
        return side

    @abstractmethod
    def run(self, df, ex, args):
        pass
