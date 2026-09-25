from datetime import date, datetime

import click


class DateParamType(click.ParamType):
    name = "date"

    def convert(self, value, param, ctx) -> date | None:
        if value is None or isinstance(value, date):
            return value
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            self.fail(f"'{value}' is not a valid date. Format must be YYYY-MM-DD.", param, ctx)


CLICK_DATE_PARAM = DateParamType()