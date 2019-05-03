## import packages
import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import dash_table_experiments as dt
import pandas as pd
import plotly.graph_objs as go
import numpy as np
import cvxopt
from cvxopt import matrix, solvers
from cvxopt import glpk

## function
def generate_table(dataframe, max_rows = 10):
    return html.Div([
    dt.DataTable(
        rows=dataframe.to_dict('records'),
        columns = (dataframe.columns),
        filterable=True,
        sortable=True,
        sortColumn = True,
        max_rows_in_viewport = max_rows,
        # row_selectable = True,
    )
])


FoodType = ['All', 'Vegetarian', 'Vegan', 'Ketogenic', 'Paleo', 'Medi']

['FATS AND OILS', 'FRUITS', 'BEVERAGES', 'VEGETABLES AND LEGUMES',
       'DAIRY', 'BAKED GOODS', 'FISH/SHELLFISH', 'EGGS',
       'MIXED DISHES AND FAST FOODS', 'GRAIN PRODUCTS', 'MEAT',
       'SWEETENERS AND SWEETS', 'NUTS, SEEDS AND PRODUCTS',
       'MISCELLANEOUS', 'POULTRY']

def food_suggestions(Calory, DataFrame, UpperItem, ColName, DietType, Include, Exclude):
	## filter data
	if DietType == 'All':
		DataFrame = DataFrame
	elif DietType == 'Vegetarian':
		DataFrame = DataFrame[DataFrame['Food type'].isin(['FATS AND OILS', 'FRUITS', 'BEVERAGES', 'VEGETABLES AND LEGUMES', 'DAIRY', 'GRAIN PRODUCTS', 'NUTS'])]
	elif DietType == 'Vegan':
		DataFrame = DataFrame[DataFrame['Food type'].isin(['FATS AND OILS', 'FRUITS', 'BEVERAGES', 'GRAIN PRODUCTS', 'NUTS'])]
	elif DietType == 'Ketogenic':
		DataFrame = DataFrame[DataFrame['Food type'].isin(['FATS AND OILS', 'VEGETABLES', 'DAIRY', 'FISH/SHELLFISH', 'EGGS', 'MEAT', 'NUTS', 'POULTRY'])]
	elif DietType == 'Paleo':
		DataFrame = DataFrame[DataFrame['Food type'].isin(['FATS AND OILS', 'FRUITS', 'VEGETABLES', 'FISH/SHELLFISH', 'EGGS', 'MEAT', 'NUTS', 'POULTRY'])]
	elif DietType == 'Medi':
		DataFrame = DataFrame[DataFrame['Food type'].isin(['FATS AND OILS', 'VEGETABLES', 'BAKED GOODS', 'FISH/SHELLFISH', 'EGGS', 'GRAIN PRODUCTS', 'NUTS', 'POULTRY'])]
	# DataFrame =  DataFrame.sample(frac=1).reset_index(drop=True)
	Calory = int(Calory)
	FoodName = list(DataFrame['Food'])
	FoodCal = list(DataFrame['kCal'])
	FoodRestriction = [np.floor(Calory/foodCal) for foodCal in FoodCal]
	FoodRestriction = [np.floor(min(UpperItem, foodRes)) for foodRes in FoodRestriction]
	if Exclude == 'None':
		FoodRestriction = FoodRestriction
	else:
		index = FoodName.index(Exclude)
		FoodRestriction[index] = 0
	# create objective
	if len(ColName) != 0:
		FoodCol = np.zeros((1, len(FoodName)))
		for col in ColName:
			 FoodCol = FoodCal + np.array(list(DataFrame[col]))
		FoodCol = FoodCol.astype(float)
	else:
		FoodCol = FoodCal
	c = cvxopt.matrix([-foodCol for foodCol in FoodCol], tc = 'd')
	# create coefficient for restriction
	G = np.identity(len(FoodName))
	G = np.concatenate((G, -G), axis=0)
	# ones = np.ones((1, len(FoodName)))
	# G = np.concatenate((G, -ones), axis = 0)
	# calory restriction
	res = np.array([foodCal for foodCal in FoodCal])
	res = np.reshape(res, (1, len(res)))
	G = np.concatenate((G, res), axis = 0)
	G = cvxopt.matrix(G, tc = 'd')
	# create bound for restriction
	lowerBound = [0]*len(FoodName)
	if Include == 'None':
		lowerBound = lowerBound
	else:
		index = FoodName.index(Include)
		lowerBound[index] = -1
	h = cvxopt.matrix(FoodRestriction + lowerBound + [Calory])
	## solve linear equation
	# cvxopt.glpk.options['msg_lev'] = 'GLP_MSG_OFF'
	(status, x) = cvxopt.glpk.ilp(c,G,h,I=set(range(len(FoodName))))
	## provide matrix
	solutions = np.array(x).flatten()
	index = np.nonzero(solutions)[0]
	values = solutions[index]
	dftemp = DataFrame.iloc[index, :]
	dftemp['Units'] = values
	return dftemp





## load data
df = pd.read_csv('Food_Nutrients_20190223.csv')
dfZero = df[df['kCal']==0]
df = df[df['kCal']>0]
Nutrients = ['Fat (g)', 'Carbo(g)', 'Protein (g)', 'Calcium [mg]', 'percent water', 'Energy [kcal]', 'Fiber [g]', 'Cholesterol [mg]', 'Saturate Fat [g]', 'Monosat Fat [g]', 'Polyunsat Fat [g]', 'Iron [mg]', 'Magnesium [mg]', 'Sodium [mg]', 'Phosphorous [mg]', 'Ca:P ratio', 'Potassium [mg]', 'Zinc [mg]', 'Niacin [mg]', 'Thiamin [mg]', 'Riboflavin [mg]', 'Vit A [RE]', 'Vit B6 [mg]', 'Vit C [mg]']
FoodType = ['All', 'Vegetarian', 'Vegan', 'Ketogenic', 'Paleo', 'Medi']

## create app
app = dash.Dash()
app.layout = html.Div([
	html.Div([
		html.Div([
			## Nutrients
			dcc.Markdown('Pick Nutrients you want to **maximize**: '),
			dcc.Checklist(
			id = 'maximize-nutrients',
			options = [{'label':i, 'value':i} for i in Nutrients],
			values = [],
			),
			],
			style = {'width': '15%', 'vertical-align': 'top',  'display': 'inline-block'}),

			## others
			html.Div([
				html.Div([
				## selections
				html.Div([
					## input calories
					html.P('Input calories upper bound in Cal:', style = {'color': 'green'}),
					dcc.Input(id='calories-bound', value=1000, type='text'),
				   ],
					style = {'width': '25%', 'vertical-align': 'top',  'display': 'inline-block'}),


					## diet type
					html.Div([
						## select diet type
						html.P('Select Diet Type: ', style = {'color': 'green'}),
						dcc.Dropdown(
							id = 'diet-type',
							options = [{'label':i, 'value':i} for i in FoodType],
							value = 'All'
						)], style = {'width': '25%', 'vertical-align': 'top',  'display': 'inline-block'}),

					## include
					html.Div([
						html.P('Have to Include:', style = {'color': 'green'}),
						dcc.Dropdown(id = 'include-food'),
						], style = {'width': '25%', 'vertical-align': 'top',  'display': 'inline-block'}),

					## include
					html.Div([
						html.P('Have to Exclude:', style = {'color': 'green'}),
						dcc.Dropdown(id = 'exclude-food'),
						], style = {'width': '25%', 'vertical-align': 'top',  'display': 'inline-block'}),
				]),

				## result
				html.Div([
					html.Div(id = 'intermediate-df', style = {'display': 'none'}),
					html.P('Food and Quantity:', style = {'color': 'blue'}),
					dcc.Graph(id = 'food-quantity-graph'),
					html.P(id = 'total-calory'),
					dcc.Graph(id = 'food-calories-graph'),
					html.P('Food Nutrients Table', style = {'color': 'blue'}),
					html.Div(id = 'nutrients-table'),
					],
					),
				],
				style = {'width': '85%', 'vertical-align': 'top',  'display': 'inline-block'})
	])
])



## callback
@app.callback(Output('intermediate-df', 'children'),
	[Input('calories-bound', 'value'),
	Input('maximize-nutrients', 'values'),
	Input('diet-type', 'value'),
	Input('include-food', 'value'),
	Input('exclude-food', 'value')])
def generate_food_suggestion(Calories, Nutrients, DietType, Include, Exclude):
	dftemp = food_suggestions(Calories, df, 5, Nutrients, DietType, Include, Exclude)
	return dftemp.to_json(date_format='iso', orient='split')



@app.callback(Output('total-calory', 'children'),
	[Input('intermediate-df', 'children')])
def total_calaries(Table):
	dftemp = pd.read_json(Table, orient='split')
	dftemp['Calory'] = dftemp['kCal']*dftemp['Units']
	return html.P('Total Food Calories are %s and the distribution is as follows' % str(dftemp['Calory'].sum()), style = {'color': 'blue'})

@app.callback(Output('include-food', 'options'),
	[Input('diet-type', 'value')])
def include_food_options(DietType):
	DataFrame = df.copy()
	if DietType == 'All':
		DataFrame = DataFrame
	elif DietType == 'Vegetarian':
		DataFrame = DataFrame[DataFrame['Food type'].isin(['FATS AND OILS', 'FRUITS', 'BEVERAGES', 'VEGETABLES AND LEGUMES', 'DAIRY', 'GRAIN PRODUCTS', 'NUTS'])]
	elif DietType == 'Vegan':
		DataFrame = DataFrame[DataFrame['Food type'].isin(['FATS AND OILS', 'FRUITS', 'BEVERAGES', 'GRAIN PRODUCTS', 'NUTS'])]
	elif DietType == 'Ketogenic':
		DataFrame = DataFrame[DataFrame['Food type'].isin(['FATS AND OILS', 'VEGETABLES', 'DAIRY', 'FISH/SHELLFISH', 'EGGS', 'MEAT', 'NUTS', 'POULTRY'])]
	elif DietType == 'Paleo':
		DataFrame = DataFrame[DataFrame['Food type'].isin(['FATS AND OILS', 'FRUITS', 'VEGETABLES', 'FISH/SHELLFISH', 'EGGS', 'MEAT', 'NUTS', 'POULTRY'])]
	elif DietType == 'Medi':
		DataFrame = DataFrame[DataFrame['Food type'].isin(['FATS AND OILS', 'VEGETABLES', 'BAKED GOODS', 'FISH/SHELLFISH', 'EGGS', 'GRAIN PRODUCTS', 'NUTS', 'POULTRY'])]
	IncludeFood = list(DataFrame['Food'])
	IncludeFood.append('None')
	IncludeFood = [{'label': i, 'value':i} for i in IncludeFood]
	return IncludeFood


@app.callback(Output('include-food', 'value'),
	[Input('include-food', 'options')])
def include_food_value(Options):
	return Options[-1]['value']


@app.callback(Output('exclude-food', 'options'),
	[Input('include-food', 'options'),
	Input('include-food', 'value')])
def exclude_food_options(Options, Value):
	excludeOptions = [{'label':c['label'], 'value':c['value']} for c in Options if ((c['label']!=Value) & (c['label']!='None'))]
	excludeOptions.append({'label': 'None', 'value': 'None'})
	return excludeOptions

@app.callback(Output('exclude-food', 'value'),
	[Input('exclude-food', 'options')])
def exclude_food_value(Options):
	return Options[-1]['value']


@app.callback(Output('food-quantity-graph', 'figure'),
	[Input('intermediate-df', 'children')])
def food_quantity_graph(Table):
	dftemp = pd.read_json(Table, orient = 'split')
	FoodNames = list(dftemp['Food'])
	Units = list(dftemp['Measure'])
	Quantity = list(dftemp['Units'])
	return {
	'data': [go.Bar(
            x=FoodNames,
            y=Quantity,
            text=[str(quantity) + '*' + str(unit) for quantity, unit in zip(Units, Quantity)],
            # textposition = 'outside',
    )],
    'layout': go.Layout(
	    title='Food Quantity',
	    margin = {
	    't': 35,
	    'b': 150,
	    }
)
}



@app.callback(Output('food-calories-graph', 'figure'),
	[Input('intermediate-df', 'children')])
def food_quantity_graph(Table):
	dftemp = pd.read_json(Table, orient = 'split')
	FoodNames = list(dftemp['Food'])
	Calories = list(dftemp['kCal'])
	Quantity = list(dftemp['Units'])
	CaloriesPercentage = [cal*quantity for cal,quantity in zip(Calories, Quantity)]
	# CaloriesPercentage = np.array(CaloriesPercentage)/sum(CaloriesPercentage)
	return {
	'data': [go.Pie(labels=FoodNames, values=CaloriesPercentage, hoverinfo='label+value')],
    'layout': go.Layout(
	    title='Food Calories Percentage',
	    margin = {
	    't': 30,
	    }
)
}



@app.callback(Output('nutrients-table', 'children'),
	[Input('intermediate-df', 'children')])
def nutrient_table(Table):
	dftemp = pd.read_json(Table, orient = 'split')
	dftemp = dftemp[['Food', 'Fat (g)', 'Carbo(g)', 'Protein (g)', 'Calcium [mg]', 'percent water', 'Energy [kcal]', 'Fiber [g]', 'Cholesterol [mg]', 'Saturate Fat [g]', 'Monosat Fat [g]', 'Polyunsat Fat [g]', 'Iron [mg]', 'Magnesium [mg]', 'Sodium [mg]', 'Phosphorous [mg]', 'Ca:P ratio', 'Potassium [mg]', 'Zinc [mg]', 'Niacin [mg]', 'Thiamin [mg]', 'Riboflavin [mg]', 'Vit A [RE]', 'Vit B6 [mg]', 'Vit C [mg]', 'Units']]
	Total = np.array(dftemp.iloc[:, 1:-1])
	Weight = np.reshape(np.array(dftemp.iloc[:,-1]), (len(Total),1))
	Total = list(np.dot(Total.T, Weight).flatten())
	Total.append(dftemp['Units'].sum())
	Total.insert(0, 'Total')
	dftemp.loc[len(dftemp)] = Total
	return generate_table(dftemp)

## templates
app.css.append_css({'external_url': 'https://codepen.io/amyoshino/pen/jzXypZ.css'})


if __name__ == '__main__':
    app.run_server(debug=True)