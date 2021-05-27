import psycopg2
import pandas as pd
from numpy.polynomial import polynomial as poly
import matplotlib.pyplot as plt

# Class defining the global variables needed for the program.
class ProgramVariables:
    conn = psycopg2.connect(
        host="localhost",
        database="rockmagnetics_database",
        user="joshuagrinham",
        password="Ga’hoole96",
        port="5430")

    ipx_correction_coefficients = [-4.58522426983974E-12, -1.81155824712452E-09, -3.75228938151544E-05]
    opx_correction_coefficients = [2.972887653939990E-17, -5.988533636562880E-14, 4.831687000309200E-11,
                                   -2.292774669851590E-08, 8.108144263095880E-07]

    zero = 1
    good_curie_hip = True
    good_curie_hop = True
    good_curie_lip = True
    good_curie_lop = True

#   Variable allowing shorthand reference to ProgramVariables Class.
var = ProgramVariables

#   Function to retrieve list of high temperature experiments meeting inputted requirements.
def get_high_temp_exp_list(search, order):

    data = pd.read_sql_query(
        '''DROP TABLE IF EXISTS exp_list_temp_table;
            SELECT experiment_list.exp_id as exp_id, avg(abs(tx_datatable.opx_raw)) as opx_avg
                    INTO TEMP exp_list_temp_table
                    FROM rockmagnetics_schema.experiment_list
                    JOIN rockmagnetics_schema.tx_datatable
                        ON experiment_list.exp_id = tx_datatable.exp_id
                    JOIN rockmagnetics_schema.sample_list
                        ON experiment_list.sample_id = sample_list.sample_id
                    WHERE experiment_list.exp_type ILIKE 'high'
                        AND sample_list.sample_description ILIKE \'%''' + search + '''%\'
                    GROUP BY experiment_list.exp_id;
            SELECT DISTINCT exp_id
                FROM exp_list_temp_table
                WHERE opx_avg > 10e-''' + order + '''
                ORDER BY exp_id ASC;
        ''',
        con=var.conn)
    return data

#   Function to retrieve high temperature data for a specified experiment ID.
def get_high_temp_data(search):

    data = pd.read_sql_query(
        '''SELECT tx_datatable.exp_id, tx_datatable.temperature, tx_datatable.ipx_raw, tx_datatable.opx_raw
        FROM rockmagnetics_schema.experiment_list
        JOIN rockmagnetics_schema.tx_datatable
            ON experiment_list.exp_id = tx_datatable.exp_id
        JOIN rockmagnetics_schema.sample_list
            ON experiment_list.sample_id = sample_list.sample_id
        WHERE experiment_list.exp_type ILIKE 'high'
            AND experiment_list.exp_id ILIKE \'''' + search + '''\';
        ''',
        con=var.conn)
    return data

# Function to split off the heating cycle of a high temperature experiment from the main dataframe.
def split_into_heating(df):
    max_temp = df['temperature'].idxmax()
    # print(max_temp)

    row_pos = max_temp + 1
    # print(row_pos)

    h_df = df.drop(range(row_pos, len(df['temperature']))).sort_values(by='temperature', ascending=True)
    # print(h_df)

    h_df['ipx_corr'] = [correction_ipx_high(sus, temp) for (sus, temp) in zip(h_df['ipx_raw'],
                                                                              h_df['temperature'])]
    h_df['opx_corr'] = [correction_opx_high(sus, temp) for (sus, temp) in zip(h_df['opx_raw'],
                                                                              h_df['temperature'])]
    h_df['ipx_corr_norm'] = [(ipx_corr/h_df['ipx_corr'].mean()) for ipx_corr in h_df['ipx_corr']]
    h_df['opx_corr_norm'] = [(opx_corr/h_df['opx_corr'].mean()) for opx_corr in h_df['opx_corr']]

    return h_df

# Function to split off the cooling cycle of a high temperature experiment from the main dataframe.
def split_into_cooling(df):
    max_temp = df['temperature'].idxmax()
        # print(max_temp)

    row_pos = max_temp + 1
        # print(row_pos)
    l_df = df.drop(range(0, row_pos)).sort_values(by='temperature', ascending=True)
    # print(l_df)
    l_df['ipx_corr'] = [correction_ipx_high(sus, temp) for (sus, temp) in zip(l_df['ipx_raw'],
                                                                              l_df['temperature'])]
    l_df['opx_corr'] = [correction_opx_high(sus, temp) for (sus, temp) in zip(l_df['opx_raw'],
                                                                              l_df['temperature'])]
    l_df['ipx_corr_norm'] = [(ipx_corr/l_df['ipx_corr'].mean()) for ipx_corr in l_df['ipx_corr']]
    l_df['opx_corr_norm'] = [(opx_corr/l_df['opx_corr'].mean()) for opx_corr in l_df['opx_corr']]

    return l_df

#   Function allowing the program to rerun with deiiferent search criteria.
def again():
    question = input("Would you like to see the results for another experiment? Type 'n' or 'y':")
    if question == 'y':
        return 0
    elif question == 'n':
        return 1
    else:
        print('EXCEPTION')

#   Function allowing the callibration of high temperature in-phase susceptibility data.
def correction_ipx_high(ipx_raw, temperature):
    correction = ((temperature**2)*var.ipx_correction_coefficients[0])+(
                temperature*var.ipx_correction_coefficients[1])+var.ipx_correction_coefficients[2]
    return ipx_raw - correction

#   Function allowing the callibration of high temperature in-phase susceptibility data.
def correction_opx_high(opx_raw, temperature):
    correction = ((temperature**4) * var.opx_correction_coefficients[0]) + (
            (temperature**3) * var.opx_correction_coefficients[1]) + (
            (temperature**2) * var.opx_correction_coefficients[2]) + (
            temperature * var.opx_correction_coefficients[3]) + var.opx_correction_coefficients[4]
    return opx_raw - correction

#   Function allowing for the numerical differentiation of susceptibility data - tripletwise.
def tripletwise_derivative(temps, ip, op):
    def mid_point_temp_calc(start_pos, temps):
        mid_point_temp = []
        while start_pos <= len(temps)-2:
            temp = (temps[start_pos]+temps[start_pos-1]+temps[start_pos+1])/3
            mid_point_temp.append(temp)
            start_pos += 1
        return mid_point_temp


    def first_der_calc(start_pos, temps, sus):
        first_der_list = []
        while start_pos <= len(temps)-2:
            x = [temps[start_pos-1], temps[start_pos], temps[start_pos+1]]
            y = [sus[start_pos-1], sus[start_pos], sus[start_pos+1]]
            fx = poly.polyfit(x, y, 1)
            first_der_list.append(fx[-1])
            start_pos += 1
        return first_der_list

    x = mid_point_temp_calc(1, temps)
    y = first_der_calc(1,temps,ip)
    z = first_der_calc(1,temps,op)

    return pd.DataFrame(zip(x,y,z),).rename(columns={0:"temp", 1:"first_der_ip", 2:"first_der_op"})

#   Function defining the main program allowing entering of search terms, automatic calculation of curie temperatures,
#   and plotting of results.
def main():
    x = 0
    while x == 0:
        search = input("Enter a search term to only show data from samples including the phrase in their sample"
                       "description (eg Magnetite):")
        order = input("Only show results with average opx in excess of SI E-")
        exp_list_df = get_high_temp_exp_list(search, order)
        print(exp_list_df)
        list_start_pos_for_exp_id = 0
        while list_start_pos_for_exp_id <= len(list(exp_list_df['exp_id'])):

            exp_id = list(exp_list_df['exp_id'])[list_start_pos_for_exp_id]
            print(exp_id)
            df1 = get_high_temp_data(exp_id)
            df2 = get_high_temp_data(exp_id)
            h_df = split_into_heating(df1)
            c_df = split_into_cooling(df2)

            first_derivative_h_df = tripletwise_derivative(list(h_df["temperature"]), list(h_df["ipx_corr"]), list(h_df["opx_corr"]))
            first_derivative_c_df = tripletwise_derivative(list(c_df["temperature"]), list(c_df["ipx_corr"]), list(c_df["opx_corr"]))


            heating_or_cooling = 'h'
            if heating_or_cooling == 'h':
                #print(h_df)
                #print(first_derivative_h_df)
                max_first_der_ip = first_derivative_h_df.iloc[first_derivative_h_df['first_der_ip'].idxmax()]['temp']
                min_first_der_ip = first_derivative_h_df.iloc[first_derivative_h_df['first_der_ip'].idxmin()]['temp']
                if abs(max_first_der_ip-min_first_der_ip)<=30:
                    pass
                    print('Out-of-phase curie temperature found on first attempt from heating curve.')
                else:
                    print('Out-of-phase curie temperature not found on first attempt from heating curve.')
                    start = 0
                    end = -1
                    sort_der = first_derivative_h_df.sort_values(by=['first_der_ip'], ascending=False).reset_index(drop=True)
                    while abs(max_first_der_ip - min_first_der_ip) >= 30:
                        max_first_der_ip = sort_der.iloc[start]['temp']
                        start += 1
                        if abs(max_first_der_ip - min_first_der_ip) >= 30:
                            min_first_der_ip = sort_der.iloc[end]['temp']
                            end -= 1
                        else:
                            pass
                        if start == 5:
                            print('Curie point estimation suspected to be inaccurate.')
                        else:
                            pass
                max_first_der_op = first_derivative_h_df.iloc[first_derivative_h_df['first_der_op'].idxmax()]['temp']
                min_first_der_op = first_derivative_h_df.iloc[first_derivative_h_df['first_der_op'].idxmin()]['temp']
                if abs(max_first_der_op-min_first_der_op)<=30:
                    pass
                    print('Out-of-phase curie temperature found on first attempt from heating curve.')
                else:
                    print('Out-of-phase curie temperature not found on first attempt from heating curve.')
                    start = 0
                    end = -1
                    sort_der = first_derivative_h_df.sort_values(by=['first_der_op'], ascending=False).reset_index(drop=True)
                    while abs(max_first_der_op - min_first_der_op) >= 30:
                        max_first_der_op = sort_der.iloc[start]['temp']
                        start += 1
                        if abs(max_first_der_op - min_first_der_op) >= 30:
                            min_first_der_op = sort_der.iloc[end]['temp']
                            end -= 1
                        else:
                            pass
                        if start == 5:
                            print('Curie point estimation suspected to be inaccurate.')
                        else:
                            pass
                # print(second_derivative_h_df)
                print("In-Phase First Derivative (Temp of Max,Temp of Min): ", max_first_der_ip, min_first_der_ip)
                print("Out-of-Phase First Derivative (Temp of Max,Temp of Min): ", max_first_der_op, min_first_der_op)
                print("Curie Estimates Using Midpoint of Max-Min First Derivative (In-Phase, Out-of-Phase): ",
                      str((max_first_der_ip+min_first_der_ip)/2),
                      str((max_first_der_op+min_first_der_op)/2))
                fig, ax = plt.subplots()
                secax = ax.twinx()
                h_df.plot('temperature', 'ipx_corr', ax=ax, color='r', label='In-Phase Heating')
                h_df.plot('temperature', 'opx_corr', ax=secax, color='y', label='Out-of-Phase Heating')
                secax.plot(((max_first_der_op + min_first_der_op) / 2), (h_df.max()['opx_corr'] * 1.1), 'y+')
                ax.plot(((max_first_der_ip + min_first_der_ip) / 2), (h_df.max()['ipx_corr'] * 1.1), 'r+')
                plt.xlabel('Temperature (ºC)')
                ax.set_ylabel('In-Phase Magnetic Susceptibility')
                secax.set_ylabel('Out-of-Phase Magnetic Susceptibility')
                secax.get_legend().remove()
                plot_1, labels_1 = ax.get_legend_handles_labels()
                plot_2, labels_2 = secax.get_legend_handles_labels()
                lines = plot_1 + plot_2
                labels = labels_1 + labels_2
                ax.legend(lines, labels)
                plt.title(exp_id)
                plt.show()



            elif heating_or_cooling == 'c':
                print(c_df)
                print(first_derivative_c_df)
                max_first_der_ip = first_derivative_c_df.iloc[first_derivative_c_df['first_der_ip'].idxmax()]['temp']
                min_first_der_ip = first_derivative_c_df.iloc[first_derivative_c_df['first_der_ip'].idxmin()]['temp']
                if abs(max_first_der_ip-min_first_der_ip)<=30:
                    pass
                    print('In-phase curie temperature found on first attempt from cooling curve.')
                else:
                    print('In-phase curie temperature not found on first attempt from cooling curve.')
                    start = 0
                    end = -1
                    sort_der = first_derivative_c_df.sort_values(by=['first_der_ip'], ascending=False).reset_index(drop=True)
                    while abs(max_first_der_ip - min_first_der_ip) >= 30:
                        max_first_der_ip = sort_der.iloc[start]['temp']
                        start += 1
                        if abs(max_first_der_ip - min_first_der_ip) >= 30:
                            min_first_der_ip = sort_der.iloc[end]['temp']
                            end -= 1
                        else:
                            pass
                        if start == 5:
                            print('Curie point estimation suspected to be inaccurate.')
                        else:
                            pass
                max_first_der_op = first_derivative_c_df.iloc[first_derivative_c_df['first_der_op'].idxmax()]['temp']
                min_first_der_op = first_derivative_c_df.iloc[first_derivative_c_df['first_der_op'].idxmin()]['temp']
                if abs(max_first_der_op-min_first_der_op)<=30:
                    pass
                    print('Out-of-phase curie temperature found on first attempt from cooling curve.')
                else:
                    print('Out-of-phase curie temperature found on first attempt from cooling curve.')
                    start = 0
                    end = -1
                    sort_der = first_derivative_c_df.sort_values(by=['first_der_op'], ascending=False).reset_index(drop=True)
                    while abs(max_first_der_op - min_first_der_op) >= 30:
                        max_first_der_op = sort_der.iloc[start]['temp']
                        start += 1
                        if abs(max_first_der_op - min_first_der_op) >= 30:
                            min_first_der_op = sort_der.iloc[end]['temp']
                            end -= 1
                        else:
                            pass
                        if start == 5:
                            print('Curie point estimation suspected to be inaccurate.')
                        else:
                            pass
                print("In-Phase (Max, Min): ", max_first_der_ip, min_first_der_ip)
                print("Out-of-Phase (Max, Min): ", max_first_der_op, min_first_der_op)
                print("Curie Estimates (In-Phase, Out-of-Phase): ",
                      str((max_first_der_ip+min_first_der_ip)/2),
                      str((max_first_der_op+min_first_der_op)/2))
                fig, ax = plt.subplots(figsize=(15, 10))
                c_df.plot('temperature', 'ipx_corr_norm', ax=ax, color='r')
                c_df.plot('temperature', 'opx_corr_norm', ax=ax, color='g')
                plt.plot(((max_first_der_op+min_first_der_op)/2), 0.4, 'g+', ((max_first_der_ip+min_first_der_ip)/2), 0.6, 'r+')
                plt.xlabel('Temperature (ºC)')
                plt.ylabel('Magnetic Susceptibility (Normalised)')
                plt.title(exp_id)
                plt.show()

            elif heating_or_cooling == 'h+c':
                max_first_der_ip = first_derivative_h_df.iloc[first_derivative_h_df['first_der_ip'].idxmax()]['temp']
                min_first_der_ip = first_derivative_h_df.iloc[first_derivative_h_df['first_der_ip'].idxmin()]['temp']
                if abs(max_first_der_ip-min_first_der_ip)<=30:
                    pass
                    print('In-phase curie temperature found on first attempt from heating curve.')
                else:
                    print('In-phase curie temperature not found on first attempt from heating curve.')
                    start = 0
                    end = -1
                    sort_der = first_derivative_h_df.sort_values(by=['first_der_ip'], ascending=False).reset_index(drop=True)
                    while abs(max_first_der_ip - min_first_der_ip) >= 30:
                        max_first_der_ip = sort_der.iloc[start]['temp']
                        start += 1
                        if abs(max_first_der_ip - min_first_der_ip) >= 30:
                            min_first_der_ip = sort_der.iloc[end]['temp']
                            end -= 1
                        else:
                            pass
                        if start == 5:
                            print('Curie point estimation suspected to be inaccurate.')
                            var.good_curie_hip = False
                        else:
                            pass
                max_first_der_op = first_derivative_h_df.iloc[first_derivative_h_df['first_der_op'].idxmax()]['temp']
                min_first_der_op = first_derivative_h_df.iloc[first_derivative_h_df['first_der_op'].idxmin()]['temp']
                if abs(max_first_der_op-min_first_der_op) <= 30:
                    pass
                    print('Out-of-phase curie temperature found on first attempt from heating curve.')
                else:
                    print('Out-of-phase curie temperature not found on first attempt from heating curve.')
                    start = 0
                    end = -1
                    sort_der = first_derivative_h_df.sort_values(by=['first_der_op'], ascending=False).reset_index(drop=True)
                    while abs(max_first_der_op - min_first_der_op) >= 30:
                        max_first_der_op = sort_der.iloc[start]['temp']
                        start += 1
                        if abs(max_first_der_op - min_first_der_op) >= 30:
                            min_first_der_op = sort_der.iloc[end]['temp']
                            end -= 1
                        else:
                            pass
                        if start == 5:
                            print('Curie point estimation suspected to be inaccurate.')
                            var.good_curie_hop = False
                        else:
                            pass
                max_first_der_lip = first_derivative_c_df.iloc[first_derivative_c_df['first_der_ip'].idxmax()]['temp']
                min_first_der_lip = first_derivative_c_df.iloc[first_derivative_c_df['first_der_ip'].idxmin()]['temp']
                if abs(max_first_der_lip-min_first_der_lip)<=30:
                    pass
                    print('In-phase curie temperature found on first attempt from cooling curve.')
                else:
                    print('In-phase curie temperature not found on first attempt from cooling curve.')
                    start = 0
                    end = -1
                    sort_der = first_derivative_c_df.sort_values(by=['first_der_ip'], ascending=False).reset_index(drop=True)
                    while abs(max_first_der_lip - min_first_der_lip) >= 30:
                        max_first_der_lip = sort_der.iloc[start]['temp']
                        start += 1
                        if abs(max_first_der_lip - min_first_der_lip) >= 30:
                            min_first_der_lip = sort_der.iloc[end]['temp']
                            end -= 1
                        else:
                            pass
                        if start == 5:
                            print('Curie point estimation suspected to be inaccurate.')
                            var.good_curie_lip = False
                        else:
                            pass
                max_first_der_lop = first_derivative_c_df.iloc[first_derivative_c_df['first_der_op'].idxmax()]['temp']
                min_first_der_lop = first_derivative_c_df.iloc[first_derivative_c_df['first_der_op'].idxmin()]['temp']
                if abs(max_first_der_lop-min_first_der_lop)<=30:
                    pass
                    print('Out-of-phase curie temperature found on first attempt from cooling curve.')
                else:
                    print('Out-of-phase curie temperature found on first attempt from cooling curve.')
                    start = 0
                    end = -1
                    sort_der = first_derivative_c_df.sort_values(by=['first_der_op'], ascending=False).reset_index(drop=True)
                    while abs(max_first_der_lop - min_first_der_lop) >= 30:
                        max_first_der_lop = sort_der.iloc[start]['temp']
                        start += 1
                        if abs(max_first_der_lop - min_first_der_lop) >= 30:
                            min_first_der_lop = sort_der.iloc[end]['temp']
                            end -= 1
                        else:
                            pass
                        if start == 5:
                            print('Curie point estimation suspected to be inaccurate.')
                            var.good_curie_lop = False
                        else:
                            pass
                print("Curie Estimates For Heating (In-Phase, Out-of-Phase): ",
                      str((max_first_der_ip+min_first_der_ip)/2),
                      str((max_first_der_op+min_first_der_op)/2))
                print("Curie Estimates For Cooling (In-Phase, Out-of-Phase): ",
                      str((max_first_der_lip + min_first_der_lip) / 2),
                      str((max_first_der_lop + min_first_der_lop) / 2))
                fig, ax = plt.subplots()
                secax = ax.twinx()
                h_df.plot('temperature', 'ipx_corr', ax=ax, color='r', label='In-Phase Heating')
                h_df.plot('temperature', 'opx_corr', ax=secax, color='y', label='Out-of-Phase Heating')
                c_df.plot('temperature', 'ipx_corr', ax=ax, color='b', label='In-Phase Cooling')
                c_df.plot('temperature', 'opx_corr', ax=secax, color='g', label='Out-of-Phase Cooling')
                if var.good_curie_hop == True:
                    ax.plot(((max_first_der_op+min_first_der_op)/2), (h_df.max()['opx_corr']*1.1), 'g+')
                else:
                    pass
                if var.good_curie_hip == True:
                    ax.plot(((max_first_der_ip+min_first_der_ip)/2), (h_df.max()['ipx_corr']*1.1), 'r+')
                else:
                    pass
                if var.good_curie_lop == True:
                    secax.plot(((max_first_der_lop+min_first_der_lop)/2), (c_df.max()['opx_corr']*1.1), 'y+')
                else:
                    pass
                if var.good_curie_lip == True:
                    secax.plot(((max_first_der_lip+min_first_der_lip)/2), (c_df.max()['ipx_corr']*1.1), 'b+')
                else:
                    pass

                plt.xlabel('Temperature (ºC)')
                ax.set_ylabel('In-Phase Magnetic Susceptibility')
                secax.set_ylabel('Out-of-Phase Magnetic Susceptibility')
                secax.get_legend().remove()
                plot_1, labels_1 = ax.get_legend_handles_labels()
                plot_2, labels_2 = secax.get_legend_handles_labels()
                lines = plot_1 + plot_2
                labels = labels_1 + labels_2
                ax.legend(lines, labels)
                plt.title(exp_id)
                plt.show()

            else:
                print('EXCEPTION')

            list_start_pos_for_exp_id += 1

        x += again()


if __name__ == '__main__':
    main()
    var.conn.close()