from shiny import App, ui, reactive, render
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from shinywidgets import output_widget, render_widget 
from shinyswatch import theme


from pandas.api.types import is_numeric_dtype, is_object_dtype
from mycorp_server import mycorp_ui
from yvcdh_server import yvcdh_ui
import logging
logging.basicConfig(level=logging.DEBUG)

### TODO
## a tab to display full corpus? or pre-loaded charts of each corpus?
## show some example uses
## allow for more conditions during search (e.g. genre)
## allow for stacking / scattering of search terms if there are multiples


app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style(
            """
            .navbar {
                flex-wrap: wrap !important;
                position: relative !important; /* Prevent overlap */
            }
            .content-area {
                padding-top: 60px !important; /* Adjust depending on navbar height */
            }
            """
        )
    ),
    ui.page_navbar(
        ui.nav_panel('Instructions', 
            ui.markdown(
                "<br>Load a dataset of your choice in the above panel. You can then execute a search. If you want to search for two or more words\
                <br>in any or all table columns you can chain them together like so: hitler|himmler.\
                <br>The search syntax follows Python's Regular Expressions. For more info on how to use regex for complex searches, see:\
                <br>[Python regex](https://docs.python.org/3/howto/regex.html)\
                <br>After the search, you can click on \"Graph Search Output\" and plot your search results. For example, after a search you can plot an histogram of\
                <br>the different producing countries:\
                <br><br><img src=\"https://github.com/jackewiebohne/genocide_films/raw/main/img/histogram.png\" alt=\"Histogram\" style=\"width:100%;max-width:900px;\"><br><br>\
                <br>Or you can graph a scatterplot of the occurrences of multiple search terms over time with dots sized by total duration of the results in any given year\
                <br><br><img src=\"https://github.com/jackewiebohne/genocide_films/raw/main/img/scatter.png\" alt=\"Scatterplot\" style=\"width:100%;max-width:900px;\">\
                <br><br><br><br><br>This project was funded by the European Commission as part of Horizon 2020, Grant number: 101025897\
                " ## further info on vectors
            )
        ),
        ui.nav_panel('Explanation', 
            ui.markdown('<br>Filmographies of Yad Vashem and the Cinematography of the Holocaust as well as a hand-curated dataset of genocide doucmentaries can be searched and graphed.\
                <br>Coming soon: Semantic similarity searches (using trained vector libraries) will also be made available and custom graphing for these will allow for unique\
                <br>data visualisations (e.g. clustering of film-vectors by genre, director, specific search terms, changes of vectors over time etc.).\
                <br>**More explanation will follow.**'\
            )
        ),
        ui.nav_panel('Hand-curated genocide documentary filmography',
            ui.output_ui('mycorp_ui_output'), 
            value='mycorp',
        ),

        ui.nav_panel('Yad Vashem and Cinematography of the Holocaust filmographies', 
            ui.output_ui('yvcdh_ui_output'),
            value='yvcdh',
        ),
        ui.nav_panel('Graph Search Output',
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_radio_buttons(
                        "plot_choices", "Choose a plot option:", 
                        choices={"line": "Line-Graph", "histogram": "Histogram",'heatmap':"Heatmap", "stacked": "Stacked-Area Chart", 'scatter':'scatter'}
                    ),
                    ui.output_ui('cond_radio_plot_choices'),
                    ui.input_action_button("plot_button", "Plot"), 
                    position='right'
                ),
                output_widget("plot")
            )
        ),       

        id='active_nav',
        title='Explore and Chart Production Data of Films on the Holocaust and Genocide',
        collapsible=True,
        position='fixed-top'
    ), theme=theme.cyborg
)


def server(input, output, session):

    cur_df = reactive.Value({'mycorp':pd.DataFrame(), 'yvcdh':pd.DataFrame()})
    filtered_df = reactive.Value(pd.DataFrame())
    search_performed = reactive.Value(False)

    @output
    @render.ui
    @reactive.event(input.active_nav)
    def yvcdh_ui_output():
        logging.debug(f'rendering yvcdh')
        return yvcdh_ui(cur_df, filtered_df, search_performed) 

    @output
    @render.ui
    @reactive.event(input.active_nav)
    def mycorp_ui_output():
        logging.debug(f'rendering mycorp')
        return mycorp_ui(cur_df, filtered_df, search_performed) 

    @reactive.effect
    @reactive.event(input.search)
    @reactive.event(input.active_nav)
    def perform_search():
        active_nav = input.active_nav()
        logging.debug(f'performing search on {cur_df()[active_nav].__name__}')
        search_term = input.search_term()
        search_column = input.search_column()
        date_range = input.dates()
        duration_range = input.duration()
        case_sensitive = input.case() == 'True'
        
        duration = list(range(int(duration_range[0]), int(duration_range[1])))
        dates = list(range(int(date_range[0]), int(date_range[1]) + 1))
        
        result = cur_df()[active_nav].search(
            searchinput=search_term,
            search_col=search_column,
            dates=dates,
            duration=duration,
            case=case_sensitive
        )
        
        filtered_df.set(result)
        search_performed.set(True)
        search_df_name =  'mycorp' if 'DATE' in filtered_df().columns else 'yvcdh'
        logging.debug(f'search successfully performed on {search_df_name}')


    @output
    @render_widget
    @reactive.event(input.plot_button)
    def plot():

        df = filtered_df()
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data to plot.",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            fig.update_layout(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="white"
            )
            return fig

        plot_type = input.plot_choices()
        x_col = input.x_input()
        xtype = df[x_col].dtypes
        template = 'seaborn'
        logging.debug(f'plotting search with choice {plot_type} and search input {input.search_term()}')

        # configure df when a categorical data column has been used for numerical axes
        if plot_type in ('line', 'heatmap'):
            # TODO: condition title on duration slider as well
            y_col = input.y_input()
            ytype = df[y_col].dtypes
            title = f'Graph of {x_col} and {y_col} for search-input {input.search_term()} from {input.dates()[0]} to {input.dates()[1]}'

            if is_object_dtype(xtype):
                df = df.groupby([y_col])[x_col].size().reset_index(name='num_' + str(x_col))
                if plot_type == 'line': return px.line(df, x='num_' + x_col, y=y_col, title=title, template=template)
                else: return px.density_heatmap(df, x='num_' + x_col, y=y_col, template=template, marginal_x="histogram", marginal_y="histogram", text_auto=True)

            elif is_object_dtype(ytype):
                df = df.groupby([x_col])[y_col].size().reset_index(name='num_' + str(y_col))
                if plot_type == 'line': return px.line(df, x=x_col, y='num_' + y_col, title=title, template=template)
                else: return px.density_heatmap(df, x=x_col, y='num_' + y_col, template=template, marginal_x="histogram", marginal_y="histogram", text_auto=True)

            else:
                if plot_type == 'line': return px.line(df, x=x_col, y=y_col, title=title, template=template)
                else: return px.density_heatmap(df, x=x_col, y=y_col, template=template, marginal_x="histogram", marginal_y="histogram", text_auto=True)

        # for stacked and scatter: if searchterm is multiple terms sep. by | then we can stack or color those
        elif plot_type in ('stacked', 'scatter'):
            y_col = input.y_input()
            ytype = df[y_col].dtypes
            z_col = input.z_input() # color / stacking == categorical

            if plot_type == 'stacked':
                title = f'Graph of {x_col} and {y_col} for search-input {input.search_term()} from {input.dates()[0]} to {input.dates()[1]}'

                if z_col!='none':

                    if is_object_dtype(xtype):
                        df = df.groupby([y_col, z_col])[x_col].size().reset_index(name='num_' + str(x_col))
                        return px.area(df, x='num_' + x_col, y=y_col, color=z_col, template=template, title=title)
                    elif is_object_dtype(ytype):
                        df = df.groupby([x_col, z_col])[y_col].size().reset_index(name='num_' + str(y_col))
                        return px.area(df, x=x_col, y='num_' + y_col, color=z_col, template=template, title=title)
                    else: return px.area(df, x=x_col, y=y_col, color=z_col, template=template, title=title)
                else:
                    if is_object_dtype(xtype):
                        df = df.groupby([y_col])[x_col].size().reset_index(name='num_' + str(x_col))
                        return px.area(df, x='num_' + x_col, y=y_col, template=template, title=title)
                    elif is_object_dtype(ytype):
                        df = df.groupby([x_col])[y_col].size().reset_index(name='num_' + str(y_col))
                        return px.area(df, x='num_' + x_col, y=y_col, template=template, title=title)
                    else: return px.area(df, x=x_col, y=y_col, template=template, title=title)

            elif plot_type == 'scatter':
                w_col = input.w_input() # size

                if z_col != 'none':

                    if w_col != 'none':
                        title = f'Graph of {x_col} and {y_col} sized by {w_col} for search-input {input.search_term()} from {input.dates()[0]} to {input.dates()[1]}'
                        if is_object_dtype(xtype):
                            print(xtype, ytype)
                            df = df.groupby([y_col, z_col])[[x_col, w_col]].agg({x_col: 'size', w_col:'sum'}).reset_index()\
                                                                .rename(columns={x_col: 'num_'+x_col, w_col: 'sum_'+w_col})
                            return px.scatter(df, x='num_' + x_col, y=y_col, color=z_col, size='sum_'+w_col, template=template, title=title)
                        elif is_object_dtype(ytype):
                            df = df.groupby([x_col, z_col])[[y_col, w_col]].agg({y_col: 'size', w_col:'sum'}).reset_index()\
                                                                .rename(columns={y_col: 'num_'+y_col, w_col: 'sum_'+w_col})
                            return px.scatter(df, x=x_col, y='num_' + y_col, color=z_col, size='sum_'+w_col, template=template, title=title)
                        else: return px.scatter(df, x=x_col, y=y_col, color=z_col, size=w_col, template=template, title=title)
                    else:
                        title = f'Graph of {x_col} and {y_col} for search-input {input.search_term()} from {input.dates()[0]} to {input.dates()[1]}'
                        if is_object_dtype(xtype):
                            df = df.groupby([y_col, z_col])[x_col].size().reset_index(name='num_' + str(x_col))
                            return px.scatter(df, x='num_' + x_col, y=y_col, color=z_col, template=template, title=title)
                        elif is_object_dtype(ytype):
                            df = df.groupby([x_col, z_col])[y_col].size().reset_index(name='num_' + str(y_col))
                            return px.scatter(df, x=x_col, y='num_' + y_col, color=z_col, template=template, title=title)
                        else: return px.scatter(df, x=x_col, y=y_col, color=z_col, template=template, title=title)

                else:

                    if w_col != 'none':
                        title = f'Graph of {x_col} and {y_col} sized by {w_col} for search-input {input.search_term()} from {input.dates()[0]} to {input.dates()[1]}'
                        if is_object_dtype(xtype):
                            df = df.groupby([y_col])[[x_col, w_col]].agg({x_col: 'size', w_col:'sum'}).reset_index()\
                                                                .rename(columns={x_col: 'num_'+x_col, w_col: 'sum_'+w_col})
                            return px.scatter(df, x='num_' + x_col, y=y_col, size='sum_'+w_col, template=template, title=title)
                        elif is_object_dtype(ytype):
                            df = df.groupby([x_col])[[y_col, w_col]].agg({y_col: 'size', w_col:'sum'}).reset_index()\
                                                                .rename(columns={y_col: 'num_'+y_col, w_col: 'sum_'+w_col})
                            return px.scatter(df, x=x_col, y='num_' + y_col, size='sum_'+w_col, template=template, title=title)
                        else: return px.scatter(df, x=x_col, y=y_col, size=w_col, template=template, title=title)
                    else:
                        title = f'Graph of {x_col} and {y_col} for search-input {input.search_term()} from {input.dates()[0]} to {input.dates()[1]}'
                        if is_object_dtype(xtype):
                            df = df.groupby([y_col])[x_col].size().reset_index(name='num_' + str(x_col))
                            return px.scatter(df, x='num_' + x_col, y=y_col,template=template, title=title)
                        elif is_object_dtype(ytype):
                            df = df.groupby([x_col])[y_col].size().reset_index(name='num_' + str(y_col))
                            return px.scatter(df, x=x_col, y='num_' + y_col, template=template, title=title)
                        else: return px.scatter(df, x=x_col, y=y_col, template=template, title=title)

        elif plot_type == 'histogram':
            title = f'Histogram of {x_col} for search-input {input.search_term()} from {input.dates()[0]} to {input.dates()[1]}'

            if is_object_dtype(xtype):
                grp = df.groupby(x_col).size().reset_index(name='num_' + str(x_col)).sort_values(by='num_'+x_col, ascending=False)
                return px.bar(grp, x=x_col, y='num_'+ x_col, template=template, title=title)
            else: return px.histogram(df, x=x_col, template=template, title=title)

    @output
    @render.ui
    def cond_radio_plot_choices():
        active_nav = 'mycorp' if 'DATE' in filtered_df().columns else 'yvcdh'
        if not isinstance(cur_df().get(active_nav), pd.DataFrame):
            input_df = filtered_df()
            rchoice = input.plot_choices()
            common_select_out = [ui.input_select('x_input', 'If a non-numerical axis is chosen (e.g. \"summary\"), it will count the elements of this axis. Select x-axis:', 
                        choices=[c for c in input_df.columns], selected=cur_df()[active_nav].timeaxis),
                        ui.input_select('y_input', 'Select y-axis', choices=[c for c in input_df.columns])
                        ]
            logging.debug(f'radio choices based on active nav {active_nav} with radio choice {rchoice}')
            
            if input_df.empty:
                return ui.card('Nothing to plot. Perform a search first')
            
            elif rchoice == 'line':
                return common_select_out
            
            elif rchoice == 'histogram':
                return [ui.input_select('x_input', 'If a non-numerical axis is chosen (e.g. \"summary\"), it will count the elements of this axis. Select x-axis:', 
                        choices=[c for c in input_df.columns], selected=cur_df()[active_nav].timeaxis)]
            
            elif rchoice == 'heatmap':
                return common_select_out
            
            elif rchoice == 'stacked':
                return common_select_out + \
                        [ui.input_select('z_input', 'Select third display value (used for stacking)', choices=[c for c in input_df.columns])]
            
            elif rchoice == 'scatter':
                return common_select_out + \
                        [ui.input_select('z_input', 'Select third display value (used for color)', choices=[c for c in input_df.columns] + ['none'], selected='none'),
                        ui.input_select('w_input', 'Select fourth display value (used for size of scatter dots)', choices= cur_df()[active_nav].numeric_axes + ['none'], # has to be numeric 
                        selected='none')
                        ]
        else: return ui.markdown('Perform a Search First')


    ## TODO!
    def download_search_data():
        pass


app = App(app_ui, server)

if __name__ == "__main__":
    app.run()