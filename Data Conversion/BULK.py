import time
import easygui
import os
from datetime import datetime
import xlsxwriter as xl


class ProgramVariables:
    directory = 'DataMine_files'
    subdirectory_1 = 'TXT_Files'
    subdirectory_2 = 'EXCEL FILES'

    bulkdata = directory+'/'+subdirectory_1+'/'+'bulkdata.txt'

    startpos = {bulkdata: -1}
    datatype = {bulkdata: 'bulk'}
    headings = ['Sample ID', 'Measuring Mode',
                'Measurement Order Index', 'Field Strength (A/m)', 'Field Frequency (Hz)',
                'Temperature (ºC)', 'Raw Sample Susceptibility (In-Phase)',
                'Raw Sample Susceptibility (Out-of-Phase)',
                'Holder Susceptibility (In-Phase)', 'Holder Susceptibility (Out-of-Phase)',
                'Corrected Sample Susceptibility (In-Phase)', 'Corrected Sample Susceptibility (Out-of-Phase)',
                'Phase Difference (º)', 'Volume (cm^3)', 'In-Phase Volume Susceptibility (ipχᵥ)',
                'Out-of-Phase Volume Susceptibility (opχᵥ)', 'Mass (g)',
                'In-Phase Mass Susceptibility (ipχmass)',
                'Out-of-Phase Mass Susceptibility (opχmass)', 'Range', 'Time Cycle',
                'Time Measured', 'Time', 'Date', 'Instrument Name', 'Note']
    welcomemessage = '''This program takes .bulk bulk susceptibility files
    from the KLY5-A Kappabridge and converts the data to a comma deliminated .txt
    for further data processing. All input files are appended to a single .txt file
    per data type.'''

    today = str(datetime.now().strftime('%d'+'-'+'%m'+'-'+'%Y'+'_'+'%H'+':'+'%M'))

    cache = {}


pro = ProgramVariables


def setup():
    try:
        if not os.path.exists(pro.directory):
            os.mkdir(pro.directory)
        if not os.path.exists(pro.directory + '/' + pro.subdirectory_1):
            os.mkdir(pro.directory + '/' + pro.subdirectory_1)
        if not os.path.exists(pro.directory + '/' + pro.subdirectory_2):
            os.mkdir(pro.directory + '/' + pro.subdirectory_2)
    except Exception as e:
        print(e)


def main():
    fileselect = ''

    print(pro.welcomemessage)
    input("To begin press \'enter\' and select a file or file(s):")

    while fileselect == '':
        try:
            filepath = easygui.fileopenbox(title='Select a file', filetypes=['*.bulk'], multiple=True)
        except Exception as e:
            print(e)
        for f in filepath:
            print(f)
            fileread(f)
        fileselect = input("press enter to select more files or type \'n\' to continue")

    excel = input("Press enter to create an EXCEL spreadsheet or type \'n\' to continue")

    if excel == '':
        filepath = pro.directory+'/'+pro.subdirectory_2+'/'+pro.today+'.xlsx'
        workbook = xl.Workbook(filepath)
        for key in pro.startpos:
            if pro.startpos[key] != -1:
                worksheet = workbook.add_worksheet(pro.datatype[key])
                spreadsheetcolumntitles = pro.headings

                column = 0
                for title in spreadsheetcolumntitles:
                    row = 0
                    worksheet.write(row, column, title)
                    column += 1
                with open(key, 'r') as f:
                    f.seek(pro.startpos[key])
                    i = 1
                    line = f.readline()
                    while line != '':
                        worksheet.write_row(i, 0, line.split(','))
                        i += 1
                        line = f.readline()
        workbook.close()
        print("EXCEL Spreadsheet created at"+pro.directory+'/'+pro.subdirectory_2+'/'+pro.today+'.xlsx')
    else:
        print("ok")

    time.sleep(2)


def fileread(f):
    with open(f, 'r') as datafile:
        databasefile = ''
        heading = datafile.readline()
        indices = []
        n = 1
        results = datafile.read().split()

        valid = True

        if results[n] == 'k(H)':
            databasefile = pro.bulkdata
        else:
            valid = False
            print("EXCEPTION")
        if valid:
            with open(databasefile, 'a+') as fd:
                start = 0
                if pro.startpos[databasefile] == -1:
                    start = fd.tell()
                    pro.startpos[databasefile] = start
                if databasefile not in pro.cache:
                    fd.seek(0)
                    already = {line for line in fd}
                    pro.cache[databasefile] = already
                datafile.seek(0)
                datafile.readline()
                for line in datafile:
                    listfd = []
                    row = line.split()
                    for index in indices:
                        listfd.append(row[index])
                    separator = ","
                    towrite = separator.join(row) + '\n'
                    if towrite not in pro.cache[databasefile]:
                        pro.cache[databasefile].add(towrite)
                        fd.write(towrite)
                print(f"Extracted {f} data and wrote to: " + databasefile)


if __name__ == '__main__':
    setup()
    main()