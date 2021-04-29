import psycopg2 as psy
import pandas as pd
from numpy.polynomial import polynomial as poly
import matplotlib.pyplot as plt


class ProgramVariables:
    conn = psy.connect(
        host="localhost",
        database="rockmagnetics_database",
        user="joshuagrinham",
        password="Ga’hoole96",
        port="5430"
    )
    # Coefficients for Correction of High-Temperature Data
    # (please see calibration curves on excel spreadsheet for details)
    ipx_high_corr = [-4.58522426983974E-12, -1.81155824712452E-09, -3.75228938151544E-05]
    opx_high_corr = [2.972887653939990E-17, -5.988533636562880E-14, 4.831687000309200E-11,
                     -2.292774669851590E-08, 8.108144263095880E-07]

    # Coefficients for Correction of Low-Temperature Data
    # (please see calibration curves on excel spreadsheet for details)
    ipx_low_corr = []
    opx_low_corr = []


def getdata():
    print("place holder text")


if __name__ == '__main__':
    getdata()
