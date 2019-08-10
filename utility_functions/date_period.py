from datetime import datetime, timedelta
from connect2Databricks.read2Databricks import redshift_ccg_read, redshift_cdw_read
from utility_functions.benchmark import timer
from utility_functions.custom_errors import *


def date_period(period: int, start_date: str = ''):
    """
    Author: Allison Wu
    Description: A function that returns end_date = start_date + period (in days).
    :param period: can be either positive or negative integers to specify the period
    :param start_date: has to be in YYYYMMDD format
    :return: end_date: in YYYYMMDD format
    """

    # TODO Check the stat_date format - Has to be YYYYMMDD
    if start_date == '':
        datetime_start_date = datetime.now()
    else:
        datetime_start_date = datetime.strptime(start_date, '%Y%m%d')

    end_date: str = datetime.strftime(datetime_start_date + timedelta(days=period), '%Y%m%d')
    start_date: str = datetime.strftime(datetime_start_date, '%Y%m%d')
    return start_date, end_date


@timer
def bound_date_check(
        table_name: str,
        dt_col_name: str,
        start_date: str,
        end_date: str,
        env: str,
        date_format: str = 'DATE', #YYYYMMDD
        division: str = 'CCG',
):
    """
    Author: Allison Wu

    :param table_name: table name you'd like to check dates on, eg. ccgds.f_sls_invc_model_vw
    :param dt_col_name: the date column you're checking for, eg. invc_dt
    :param start_date: start date of the bound date. Bound is exclusive. Errors are thrown when min_date > start_date.
    :param end_date: end date of the bound date.  Bound is exclusive. Errors are thrown when max_date < end_date.
    :param env: envrionment of the table
    :param date_format: the date format of the dates, takes either 'DATE' or 'YYYYMMDD'
    :param division: enter either 'CCG' or 'LSG' to make sure it uses the correct credentials
    :return: check_max (TRUE or FALSE), check_min (TRUE or FALSE), max_date, min_date
    """
    test_query = ''
    if date_format == 'DATE':
        test_query = \
            f"SELECT TO_CHAR(CAST(MAX({dt_col_name}) AS DATE),'YYYYMMDD') AS max_date,  " \
            f"TO_CHAR(CAST(MIN({dt_col_name}) AS DATE),'YYYYMMDD') AS min_date " \
            f"FROM {table_name} "

    elif date_format == 'YYYYMMDD':
        test_query = \
            f"SELECT MAX({dt_col_name}) AS max_date,  " \
            f"MIN({dt_col_name}) AS min_date " \
            f"FROM {table_name} "

    if division == 'CCG':
        bound_date_df = redshift_ccg_read(test_query, env = env, schema = None, cache = False).toPandas()
    elif division == 'LSG':
        bound_date_df = redshift_cdw_read(test_query, env = env, schema = None, cache = False).toPandas()

    max_date = str(bound_date_df['max_date'][0])
    min_date = str(bound_date_df['min_date'][0])
    check_max = True
    check_min = True

    if max_date < end_date:
        check_max = False

    if min_date > start_date:
        check_min = False

    if not check_max:
        raise EndDateTooLateError(
            f'max_date = {max_date} while end_date ={end_date}. Max date < end_date. '
            f'Check the validity of {table_name}.'
        )
        exit()

    if not check_min:
        raise StartDateTooEarlyError(
            f'min_date = {min_date} while start_date ={start_date}. min date > Start date. '
            f'Check the validity of {table_name}.'
        )
        exit()

    if check_max and check_min:
        print('Data table is complete within date range.')

    return check_max, check_min, max_date, min_date
