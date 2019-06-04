import pandas as pd

import base64
import datetime
import io


from remove_symbol import *
from stem_words import *
import csv
from collections import OrderedDict
import re
import argparse
import os
from nltk.tokenize import sent_tokenize

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import dash_table_experiments as dt
import urllib.parse


##########################
## functions
##########################
def generate_table(dataframe, max_rows = 15):
    return dt.DataTable(
        rows=dataframe.to_dict('records'),
        row_selectable=True,
        selected_row_indices=[],
        columns = (dataframe.columns),
        filterable=True,
        sortable=True,
        # sortColumn = True,
        max_rows_in_viewport = max_rows,
    )



def preprocess_data(DataFrame, ColName, NewColName):
    DataFrame[NewColName] = DataFrame[ColName].apply(lambda x: remove_symbol(str(x)))
    DataFrame[NewColName] = DataFrame[NewColName].apply(lambda x: x.split(' '))
    DataFrame[NewColName] = DataFrame[NewColName].apply(lambda x: [stem_words(word) for word in x])
    return DataFrame

def preprocess_str_data(String):
    StringStem = String.strip('\n')
    StringStem = re.sub('[^a-zA-Z]+', ' ', StringStem)
    StringStem = StringStem.split(' ')
    StringStem = filter(None, StringStem)
    StringStem = [stem_words(word) for word in StringStem]
    return StringStem


def skill_in_title(TitleRoots, SkillRoots, SkillNames,  SkillID):
    Skill = [skillrootidx for skillrootidx, skillroot in enumerate(SkillRoots) if len(set(TitleRoots).intersection(set(skillroot))) == len(set(skillroot))]
    SkillNames = [SkillNames[idx] for idx in Skill]
    SkillNames = list(OrderedDict.fromkeys(SkillNames))
    # SkillNames = '|'.join(SkillNames)
    SkillID = [SkillID[idx] for idx in Skill]
    SkillID = list(OrderedDict.fromkeys(SkillID))
    # SkillID = '|'.join(SkillID)
    return SkillNames, SkillID



def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    text = decoded.decode("utf-8")
    lines = sent_tokenize(text)
    dfSent = pd.DataFrame(lines, columns = ['text'])
    skillsList = []
    lines = sent_tokenize(text)
    for line in lines:
        line = line.lower()
        line = re.sub("[a-zA-Z0-9._%+-]+@[A-Za-z0-9][A-Za-z0-9.-]*[A-Za-z0-9](&gt;|>)?","",line)
        line = line.replace('being', '')
        line = line.replace('experience', '')
        line = line.replace('.com', '')
        line = line.replace('for', '')
        # line = line.replace('For', '')
        line = line.replace('grade', '')
        # line = line.replace('Grade', '')
        # line = line.replace('GRADE', '')
        line = line.replace('present', '')
        line = line.replace('staff', '')
        line = line.replace('include', '')
        line = line.split(',')
        for term in line:
            temp = preprocess_str_data(term)
            term = term.strip()
            skillname, skillid = skill_in_title(temp, dfSkillsRoots, dfSkillsNames, dfSkillsID)
            if len(skillname) == 0:
                continue
            else:
                for skill, ID in zip(skillname, skillid):
                    skillsList.append([skill, ID, term])
        df = pd.DataFrame(skillsList, columns = ['SkillName', 'SkillID', 'Description'])
        df = df.drop_duplicates(subset = ['SkillID'])
    return df



##################################
## load data
##################################
dfSkills = pd.read_csv('Cleaned_Skillv4_v5_surface_and_standard_form_20180822.csv')
dfSkills = dfSkills[(dfSkills['select_for_analysis'] != 'No') & (dfSkills['type'] != 'Remove')]
dfSkills = preprocess_data(dfSkills, 'SkillName', 'SkillRoots')
dfSkillsRoots = list(dfSkills['SkillRoots'])
dfSkillsNames = list(dfSkills['SkillName'])
dfSkillsID = list(dfSkills['SkillID'])



##################################
## build apps
##################################

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H4("Please Upload a .txt file"),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select A File')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),


    html.Div(id='output-data-upload', style={'display': 'none'}),
    dt.DataTable(id = 'skill-table',
        rows=[{}],
        row_selectable=True,
        selected_row_indices=[],
        filterable=True,
        sortable=True,
        columns = ['SkillName', 'SkillID', 'Description'],
        # sortColumn = True,
        max_rows_in_viewport = 10,
        ),
    dash_table.DataTable(id='datatable-upload-container'),



    # buttons
    html.Div([
        # add row button
        html.Div([
            html.Button("Add New Rows", id='add_new_row', n_clicks = 0),
            ],
            style = {'float': 'left'}),


        # download button
        html.Div([
            html.A(
            html.Button('Download Data'),
            id = 'download-link',
            download="parsed_skills.csv",
            target="_blank"
                ),
            ],
            style = {'float': 'right'})
        ]),
])



@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        dftemp = children[0]
        return dftemp.to_json(date_format='iso', orient = 'split')


@app.callback(Output('skill-table', 'rows'),
              [Input('output-data-upload', 'children'),
              Input('add_new_row', 'n_clicks')])
def skill_table_rows(DataFrame, n_clicks):
    dff = pd.read_json(DataFrame, orient = "split")
    Rows = dff.to_dict('records')
    if n_clicks == 0:
        return Rows
    else:
        Rows.extend([{'SkillName':"", "SkillID":"", "Description": ""}]*n_clicks)
        return Rows




@app.callback(
    dash.dependencies.Output('download-link', 'href'),
    [
        Input('skill-table', 'rows'),
        Input('skill-table', 'selected_row_indices')
    ]
)
def update_download_link(DataFrame, Indices):
    """Handles the downloading of the data that the user wants

    Args:
        data_rows (list): a list of the rows and columns in the input table
        column_order (list): list of the column names and the order they should be in. if you don't have this, then the output data will be in a different order every time

    Returns:
        str: A url string output for the button to download the data
    """
    # dftemp = pd.read_json(DataFrame, orient = "split")
    dftemp = pd.DataFrame(DataFrame)
    dftemp = dftemp[['SkillName', 'SkillID', 'Description']]
    if len(Indices) == 0:
        dftemp = dftemp
    else:
        dftemp = dftemp.loc[Indices]
    csv_string = dftemp.to_csv(index=False, encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string


if __name__ == '__main__':
    app.run_server(debug=True)


