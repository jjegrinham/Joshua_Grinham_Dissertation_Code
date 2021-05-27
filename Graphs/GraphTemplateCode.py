import psycopg2 as psy
import pandas as pd
import matplotlib.pyplot as plt

#   Class defining the variables required by the program.
#   Personal data has been removed from the database connection variable and left blank.
class ProgramVariables:
    conn = psy.connect(
        host="localhost",
        database="rockmagnetics_database",
        user="",
        password="",
        port="5430"
    )
    # Coefficients for Correction of High-Temperature Data. Arranged in list from highest to lowest (eg
    # x^3, x^2, intercept).
    # (please see calibration curves on excel spreadsheet for details (Appendix 1))
    ipx_high_corr = [-0.00000000000458522426983974,
                     -0.00000000181155824712452,
                     -0.0000375228938151544]
    opx_high_corr = [0.0000000000000000297288765394038,
                     -0.0000000000000598853363656341,
                     0.0000000000483168700030944,
                     -0.0000000229277466985162,
                     0.000000810814426309621]

    # Coefficients for Correction of Low-Temperature Data. Arranged in list from highest to lowest (eg
    # x^3, x^2, intercept).
    # (please see calibration curves on excel spreadsheet for details)
    ipx_low_corr = [-0.0000000000000000000913781577507006,
                    -0.0000000000000000517213936716471,
                    -0.0000000000000111150069157988,
                    -0.00000000000112172900389166,
                    -0.0000000000525100817020263,
                    -0.000000000936668292654381,
                    -0.0000000109525493849015,
                    -0.0000442595157084559]
    opx_low_corr = [-0.0000000000000968912887222068,
                    -0.0000000000326540766471886,
                    -0.00000000478589791788062,
                    -0.000000731911692176397]

#   Defines variable for shorthand reference to Program Variables Class.
var = ProgramVariables

#   Function allowing formatted dataframe to be retrieved from the database using SQL query. Specific for each graph.
def getdata():
    data = pd.read_sql_query(
#   Insert SQL Query here.
        '''
        ''',
        con=var.conn)
    return data

#   Function allowing for the callibration of in-phase thermosusceptibility data.
def correction_ipx_high(exp_type, ipx_raw, temperature):
    if exp_type == "high":
        correction = ((temperature ** 2) * var.ipx_high_corr[0])\
                     + (temperature * var.ipx_high_corr[1])\
                     + var.ipx_high_corr[2]
        return ipx_raw - correction
    elif exp_type == "low":
        correction = ((temperature ** 7) * var.ipx_low_corr[0])\
                     + ((temperature ** 6) * var.ipx_low_corr[1])\
                     + ((temperature ** 5) * var.ipx_low_corr[2])\
                     + ((temperature ** 4) * var.ipx_low_corr[3])\
                     + ((temperature ** 3) * var.ipx_low_corr[4])\
                     + ((temperature ** 2) * var.ipx_low_corr[5]) \
                     + (temperature * var.ipx_low_corr[6]) \
                     + var.ipx_low_corr[7]
        return ipx_raw - correction
    else:
        print("Error: Data Not Callibrated. Experiment Type Not Defined.")

#   Function allowing for the callibration of out-of-phase thermosusceptibility data.
def correction_opx_high(exp_type, opx_raw, temperature):
    if exp_type == "high":
        correction = ((temperature ** 4) * var.opx_high_corr[0])\
                     + ((temperature ** 3) * var.opx_high_corr[1]) \
                     + ((temperature ** 2) * var.opx_high_corr[2])\
                     + (temperature * var.opx_high_corr[3])\
                     + var.opx_high_corr[4]
        return opx_raw - correction
    elif exp_type == "low":
        correction = ((temperature ** 3) * var.opx_low_corr[0])\
                     + ((temperature ** 2) * var.opx_low_corr[1]) \
                     + (temperature * var.opx_low_corr[2]) \
                     + var.opx_low_corr[3]
        return opx_raw - correction
    else:
        print("Error: Data Not Callibrated. Experiment Type Not Defined.")

#   Function for seperating out the heating cycle of high temperature experiments from a dataframe.
def split_into_heating(df):
    max_temp = df['temperature'].idxmax()
    row_pos = max_temp + 1
    h_df = df.drop(range(row_pos, len(df['temperature']))).sort_values(by='temperature', ascending=True)
    h_df['ipx_corr'] = [correction_ipx_high("high", sus, temp) for (sus, temp) in zip(h_df['ipx_raw'],
                                                                              h_df['temperature'])]
    h_df['opx_corr'] = [correction_opx_high("high", sus, temp) for (sus, temp) in zip(h_df['opx_raw'],
                                                                              h_df['temperature'])]
    return h_df

#   Function for seperating out the heating cycle of high temperature experiments from a dataframe.
def split_into_cooling(df):
    max_temp = df['temperature'].idxmax()
    row_pos = max_temp + 1
    l_df = df.drop(range(0, row_pos)).sort_values(by='temperature', ascending=True)
    l_df['ipx_corr'] = [correction_ipx_high(sus, temp) for (sus, temp) in zip(l_df['ipx_raw'],
                                                                              l_df['temperature'])]
    l_df['opx_corr'] = [correction_opx_high(sus, temp) for (sus, temp) in zip(l_df['opx_raw'],
                                                                              l_df['temperature'])]
    return l_df

# Function for the correction of negative phase angles.
def phasecorrection(phaseangle):
    if phaseangle >= 0:
        return phaseangle
    else:
        return abs(phaseangle)

# Function for plotting the graphs. Specific to each graph so for this template the function has been left blank.
def generate_graphs():

if __name__ == '__main__':
    generate_graphs()
