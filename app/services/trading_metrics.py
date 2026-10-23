"""
Performance Metrics Engine for the Trading Journey Database.

Computes advanced trading metrics: max drawdown, average risk-reward ratio,
profit factor, winning/losing streaks, and average trade duration.
"""

from datetime import datetime


class TradingMetricsEngine:
    """
    Computes advanced performance metrics from a list of chronologically-ordered
    closed trades.

    All methods handle the edge case of 0 closed trades by returning "N/A"
    or 0 as appropriate.
    """

    def __init__(self, closed_trades: list):
        """
        Accepts chronologically-ordered closed trades.

        Args:
            closed_trades: List of Trade objects ordered by date (ascending).
                           Each trade should have: pnl, entry_price, exit_price,
                           stop_loss, target, date, created_at.
        """
        self.closed_trades = closed_trades

    def max_drawdown(self) -> float | str:
        """
        Calculates the largest peak-to-trough decline in cumulative P&L
        (expressed as an absolute value).

        Trades are ordered chronologically by date.

        Returns:
            float: The max drawdown value (absolute), or 0 if cumulative P&L
                   never declines from a peak.
            str: "N/A" if there are no closed trades.
        """
        if not self.closed_trades:
            return "N/A"

        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0

        for trade in self.closed_trades:
            pnl = trade.pnl if trade.pnl is not None else 0.0
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_dd:
                max_dd = drawdown

        return max_dd

    def average_risk_reward(self) -> float | str:
        """
        Calculates the mean of abs(target - entry_price) / abs(entry_price - stop_loss)
        for all closed trades where both target and stop_loss are provided and
        stop_loss != entry_price.

        Returns:
            float: The average risk-reward ratio.
            str: "N/A" if fewer than 2 eligible trades.
        """
        if not self.closed_trades:
            return "N/A"

        ratios = []
        for trade in self.closed_trades:
            if (trade.target is not None and
                    trade.stop_loss is not None and
                    trade.stop_loss != trade.entry_price):
                reward = abs(trade.target - trade.entry_price)
                risk = abs(trade.entry_price - trade.stop_loss)
                ratios.append(reward / risk)

        if len(ratios) < 2:
            return "N/A"

        return sum(ratios) / len(ratios)

    def profit_factor(self) -> float | str:
        """
        Calculates gross profit / abs(gross loss) for closed trades.

        Returns:
            str: "∞" if there are no losing trades (but there are winning trades).
            float: 0 if there are no winning trades.
            float: The profit factor ratio.
            str: "N/A" if there are no closed trades.
        """
        if not self.closed_trades:
            return "N/A"

        gross_profit = 0.0
        gross_loss = 0.0

        for trade in self.closed_trades:
            pnl = trade.pnl if trade.pnl is not None else 0.0
            if pnl > 0:
                gross_profit += pnl
            elif pnl < 0:
                gross_loss += pnl  # negative value

        if gross_loss == 0:
            if gross_profit > 0:
                return "∞"
            return 0

        return gross_profit / abs(gross_loss)

    def current_winning_streak(self) -> int | str:
        """
        Calculates the number of consecutive trades with pnl > 0 from the most
        recent trade backward. Trades with pnl == 0 are excluded from streak
        counting.

        Returns:
            int: The current winning streak count.
            str: "N/A" if there are no closed trades.
        """
        if not self.closed_trades:
            return "N/A"

        streak = 0
        for trade in reversed(self.closed_trades):
            pnl = trade.pnl if trade.pnl is not None else 0.0
            if pnl == 0:
                continue
            if pnl > 0:
                streak += 1
            else:
                break

        return streak

    def current_losing_streak(self) -> int | str:
        """
        Calculates the number of consecutive trades with pnl < 0 from the most
        recent trade backward. Trades with pnl == 0 are excluded from streak
        counting.

        Returns:
            int: The current losing streak count.
            str: "N/A" if there are no closed trades.
        """
        if not self.closed_trades:
            return "N/A"

        streak = 0
        for trade in reversed(self.closed_trades):
            pnl = trade.pnl if trade.pnl is not None else 0.0
            if pnl == 0:
                continue
            if pnl < 0:
                streak += 1
            else:
                break

        return streak

    def longest_winning_streak(self) -> int | str:
        """
        Calculates the longest run of consecutive trades with pnl > 0 across
        all closed trades. Trades with pnl == 0 are excluded.

        Returns:
            int: The longest winning streak.
            str: "N/A" if there are no closed trades.
        """
        if not self.closed_trades:
            return "N/A"

        longest = 0
        current = 0

        for trade in self.closed_trades:
            pnl = trade.pnl if trade.pnl is not None else 0.0
            if pnl == 0:
                continue
            if pnl > 0:
                current += 1
                if current > longest:
                    longest = current
            else:
                current = 0

        return longest

    def longest_losing_streak(self) -> int | str:
        """
        Calculates the longest run of consecutive trades with pnl < 0 across
        all closed trades. Trades with pnl == 0 are excluded.

        Returns:
            int: The longest losing streak.
            str: "N/A" if there are no closed trades.
        """
        if not self.closed_trades:
            return "N/A"

        longest = 0
        current = 0

        for trade in self.closed_trades:
            pnl = trade.pnl if trade.pnl is not None else 0.0
            if pnl == 0:
                continue
            if pnl < 0:
                current += 1
                if current > longest:
                    longest = current
            else:
                current = 0

        return longest

    def average_trade_duration(self) -> float | str:
        """
        Calculates the mean number of days between the trade date and the
        created_at date for closed trades.

        Returns:
            float: Average duration in days.
            str: "N/A" if there are no closed trades or no trades with
                 both date and created_at set.
        """
        if not self.closed_trades:
            return "N/A"

        durations = []
        for trade in self.closed_trades:
            if trade.date is not None and trade.created_at is not None:
                # trade.date is a date object, trade.created_at is a datetime
                trade_date = trade.date
                created_date = trade.created_at.date() if isinstance(
                    trade.created_at, datetime) else trade.created_at
                delta = (trade_date - created_date).days
                durations.append(abs(delta))

        if not durations:
            return "N/A"

        return sum(durations) / len(durations)

    def compute_all(self) -> dict:
        """
        Computes and returns all metrics as a dictionary.

        Returns:
            dict: A dictionary with keys for each metric:
                - max_drawdown
                - average_risk_reward
                - profit_factor
                - current_winning_streak
                - current_losing_streak
                - longest_winning_streak
                - longest_losing_streak
                - average_trade_duration
        """
        return {
            "max_drawdown": self.max_drawdown(),
            "average_risk_reward": self.average_risk_reward(),
            "profit_factor": self.profit_factor(),
            "current_winning_streak": self.current_winning_streak(),
            "current_losing_streak": self.current_losing_streak(),
            "longest_winning_streak": self.longest_winning_streak(),
            "longest_losing_streak": self.longest_losing_streak(),
            "average_trade_duration": self.average_trade_duration(),
        }