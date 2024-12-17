import json

import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd


data = pd.read_csv(
    './final_dataset.csv',
)

def count_languages(entry):
    languages_dict = json.loads(entry)
    return len(languages_dict)

data['language_count'] = data['language'].apply(count_languages)

filtered = data[data['language_count'] > 1]
filtered[['language', 'language_count']]
data = data[data['revenue'] != 0]
df_revenue = data.dropna(subset=['revenue']).query('revenue != 0')




app = dash.Dash(__name__)
server = app.server

# Layout of the Dash app
app.layout = html.Div([
    dcc.Input(
        id='movie-search',
        type='text',
        placeholder='Enter movie name...'
    ),
    dcc.Graph(
        id='scatter-plot',
        config={'scrollZoom': True}
    )
])


def assign_quadrant(row, revenue_median, rating_median, revenue_column):
    if row[revenue_column] < revenue_median and row['normalized_rating_x'] < rating_median:
        return 'Low Rating & Low Revenue'
    elif row[revenue_column] < revenue_median and row['normalized_rating_x'] >= rating_median:
        return 'High Rating & Low Revenue'
    elif row[revenue_column] >= revenue_median and row['normalized_rating_x'] < rating_median:
        return 'Low Rating & High Revenue'
    else:
        return 'High Rating & High Revenue'

colorblind_palette = [
    '#117733', # Green
    '#44AA99', # Cyan
    '#88CCEE', # Sky blue
    '#DDCC77'] # Yellow


# Callback to update the graph based on the search input
@app.callback(
    Output('scatter-plot', 'figure'),
    Input('movie-search', 'value')
)
def update_graph(search_value):
    revenue_median = df_revenue['revenue'].median()
    rating_median = df_revenue['normalized_rating_x'].median()

    # Determine the success category for each movie
    df_revenue['Success Category'] = df_revenue.apply(
        lambda row: assign_quadrant(row, revenue_median, rating_median, 'revenue'), axis=1
    )

    # Filter out the highlighted points
    if search_value:
        highlighted_points = df_revenue[df_revenue['movie_name'].str.contains(search_value, case=False, na=False)]
    else:
        highlighted_points = pd.DataFrame()

    # Create the base scatter plot
    fig = px.scatter(
        df_revenue,
        x='revenue',
        y='normalized_rating_x',
        hover_name='movie_name',
        color='Success Category',
        color_discrete_sequence=colorblind_palette,
        title="Revenue vs Normalized Rating",
        labels={'revenue': 'Movie Revenue ($), logscale', 'normalized_rating_x': 'Normalized Movie Rating'},
        template='plotly_white'
    )

    # Add highlighted points with a red circle
    if not highlighted_points.empty:
        fig.add_trace(
            px.scatter(
                highlighted_points,
                x='revenue',
                y='normalized_rating_x',
            ).data[0]
        )
        fig.data[-1].update(
            mode='markers',
            marker=dict(
                size=13,  # Increase the size for better visibility
                color='rgba(255, 0, 0, 0)',  # Transparent fill
                line=dict(color='#AA4499', width=2),  # Red outline
            ),
            name='Highlighted'
        )

    # Add median lines
    fig.add_shape(
        type='line',
        x0=revenue_median, x1=revenue_median,
        y0=df_revenue['normalized_rating_x'].min(), y1=df_revenue['normalized_rating_x'].max(),
        line=dict(color='Gray', width=1, dash="dash")
    )
    fig.add_shape(
        type='line',
        x0=df_revenue['revenue'].min(), x1=df_revenue['revenue'].max(),
        y0=rating_median, y1=rating_median,
        line=dict(color='Gray', width=1, dash="dash")
    )

    fig.update_layout(
        xaxis_type="log",
        width=1000,
        height=600
    )
    return fig


if __name__ == '__main__':
    print('Running the Dash app!')
    app.run(debug=True)
    print('Dash app closed!')
