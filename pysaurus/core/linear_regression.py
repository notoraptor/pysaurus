class LinearRegression:
    @classmethod
    def linear_regression(cls, x: list, y: list):
        # x and y must have same length.
        avg_x = cls._average(x)
        avg_y = cls._average(y)
        cov_xy = cls._covariance(x, y)
        v_x = cls._variance(x)
        v_y = cls._variance(y)
        a = cov_xy / v_x
        b = avg_y - a * avg_x
        r = cov_xy / ((v_x * v_y) ** 0.5)
        return a, b, r

    @classmethod
    def _covariance(cls, values_x: list, values_y: list):
        assert len(values_x) == len(values_y)
        avg_x = cls._average(values_x)
        avg_y = cls._average(values_y)
        return sum((x - avg_x) * (y - avg_y) for x, y in zip(values_x, values_y)) / len(
            values_x
        )

    @classmethod
    def _variance(cls, values: list):
        avg_x = cls._average(values)
        return sum(x**2 for x in values) / len(values) - avg_x**2

    @classmethod
    def _average(cls, values: list):
        return sum(values) / len(values)
