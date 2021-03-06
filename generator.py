from numpy import sum
from pandas import DataFrame, pivot_table, ExcelWriter, read_excel
from dateutil.parser import parse

class Generator:
    def __init__(self):
        self.filename = None
    
    def read_file(self, filename):
        try:
            data = read_excel(str(filename), sheet_name=1, skiprows=1)
            data.index += 1
            return data
        except:
            return "Your file went wrong!"

    def get_product_name(self, data):
        product = data['Product'].unique()[0].lower()
        return product

    def get_date(self, data):
        months = {
            1:'Jan.', 2:'Feb.', 3:'Mar.', 4:'Apr.', 5:'May', 6:'Jun.',
            7:'Jul.', 8:'Aug.', 9:'Sep.', 10:'Oct.', 11:'Nov.', 12:'Dec.'
        }

        date = str(data['Month'].unique()[0])
        year = parse(date, fuzzy = True).year
        month = months[parse(date, fuzzy = True).month]

        return year, month

    def extract_specs(self, data):
        for index, row in data.iterrows():
            if '·' not in row['Specification']:
                if row['Specification'][-5:] == 'Tech.':
                    data.at[index, 'New_Spec'] = 'technical'
                else:
                    data.at[index, 'New_Spec'] = row['Specification']
            else:
                formulation = row['Specification'].split(' ')[0].split('·')[-1].lower() + ' ' + 'formulations'
                data.at[index, 'New_Spec'] = formulation

        for index, row in data.iterrows():
            if row['New_Spec'] != 'technical':
                if len(row['New_Spec'].split(' ')) >= 7:
                    data.at[index, 'New_Spec'] = 'formulations'
                else:
                    data.at[index, 'New_Spec'] = row['New_Spec']
            
        
        unique_spec = sorted(list(data['New_Spec'].unique()), reverse = True)
        # print('Specification are ', unique_spec)

        return unique_spec

    def pivot_table(self, data, unique_spec):

        tables = []

        for n in range(len(unique_spec)):
            #  Generate destination pivot table
            pt_destination = pivot_table(data[data['New_Spec'] == unique_spec[n]], index = ['Destination'], columns = ['Buyer'], values = ['Quantity'], aggfunc = [sum], fill_value = 0, margins = True, margins_name = 'Total')
            pt_destination = pt_destination.sort_values(('sum', 'Quantity', 'Total'), ascending = True)

            # ranking the buyer and move TOTAL to the end of column
            pt_destination.T.sort_values(('Buyer'), ascending = True).T
            pt_destination = pt_destination

            # Move the top total to the bottom
            total = pt_destination.iloc[[-1], :]
            pt_destination = pt_destination.sort_values(('sum', 'Quantity', 'Total'), ascending = False)
            pt_destination = pt_destination.drop(index = 'Total')
            pt_destination = pt_destination.append(total)
            tables.append(pt_destination)

            #  Generate exporter pivot table
            pt_exporter = pivot_table(data[data['New_Spec'] == unique_spec[n]], index = ['Company'], columns = ['Buyer'], values = ['Quantity'], aggfunc = [sum], fill_value = 0, margins = True, margins_name = 'Total')
            pt_exporter = pt_exporter.sort_values(('sum', 'Quantity', 'Total'), ascending = True)
            pt_exporter.index.name = 'Exporter'

            # ranking the buyer and move TOTAL to the end of column
            pt_exporter.T.sort_values(('Buyer'), ascending = True).T
            pt_exporter = pt_exporter

            # Move the top total to the bottom
            total = pt_exporter.iloc[[-1], :]
            pt_exporter = pt_exporter.sort_values(('sum', 'Quantity', 'Total'), ascending = False)
            pt_exporter = pt_exporter.drop(index = 'Total')
            pt_exporter = pt_exporter.append(total)
            tables.append(pt_exporter)

        return tables

    def save_to_excel(self, product, year, month, tables, unique_spec):
        writer = ExcelWriter("result.xlsx", engine = 'xlsxwriter')
        row = 2
        table_number = 0
        table_names = ['Exporters and buyers', 'Destinations and buyers']
        table_spec = unique_spec
        table_spec.extend(unique_spec)
        table_spec = sorted(table_spec, reverse = True)
        tnames = []
        
        for table in tables:
            table.to_excel(writer, sheet_name = 'Summary', startrow = row, startcol = 0)
            row = row + len(table.index) + 7
            table_number += 1

            tnames.append('Table {} {} of {} {} in {} {} (kg)'.format(table_number, table_names[table_number % 2], product, table_spec[table_number-1], month, year))

        writer.save()

        return tnames
