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
## example uses
## allow for more conditions during search (e.g. genre)
## allow for stacking / scattering of search terms if there are multiples


custom_table = {
    'style': {
        "width": '50%',
        'font-size':'11px',
        'box-shadow': '0 1px 2px rgba(0,0,0,0.1)'
    }
}


app_ui = ui.page_fluid(
    # ui.tags.head(
    #     ui.tags.link(rel="stylesheet", href="styles.css") ## create style sheet to be imported
    # ), 
    ui.navset_bar(
        ui.nav_panel('Explanation', 
            ui.markdown('**More explanation will follow.**\
                <br>Filmographies of Yad Vashem and the Cinematography of the Holocaust as well as a hand-curated dataset of genocide doucmentaries can be searched and graphed.\
                <br>Coming soon: Semantic similarity searches (using trained vector libraries) will also be made available and custom graphing for these will allow for unique\
                <br>data visualisations (e.g. clustering of film-vectors by genre, director, specific search terms, changes of vectors over time etc.).'\
            )
        ),
        ui.nav_panel('Instructions', 
            ui.markdown(
                "**Instructions**:<br>You can search the tables for single words. If you want to search for two words in any or all table columns you can chain them together like so: hitler|himmler.\
                <br>The search syntax follows Python's Regular Expressions. For more info on how to use regex for complex searches, see:<br>[Python regex](https://docs.python.org/3/howto/regex.html)\
                \
                " ## further info on vectors
            )
        ),
        ui.nav_panel('Hand-curated genocide documentary filmography',
            ui.output_ui('mycorp_ui_output'), value='mycorp' # mycorp_ui
        ),

        ui.nav_panel('Yad Vashem and Cinematography of the Holocaust filmographies', 
            ui.output_ui('yvcdh_ui_output'), value='yvcdh' # yvcdh_ui
        ),

        id='active_nav',
        title='Explore and Chart Production Data of Documentaries on the Holocaust and Genocide'
    ), theme=theme.cyborg
)


def server(input, output, session):

    cur_df = reactive.Value(None)
    filtered_df = reactive.Value(pd.DataFrame())
    search_performed = reactive.Value(False)

    @output
    @render.ui
    def yvcdh_ui_output():
        logging.debug(f'rendering yvcdh')
        return yvcdh_ui(cur_df)

    @output
    @render.ui
    def mycorp_ui_output():
        logging.debug(f'rendering mycorp')
        return mycorp_ui(cur_df)
    
    
    @reactive.effect
    @reactive.event(input.search)
    def perform_search():
        logging.debug(f'performing search on {cur_df().__name__}')
        search_term = input.search_term()
        search_column = input.search_column()
        date_range = input.dates()
        duration_range = input.duration()
        case_sensitive = input.case() == 'True'
        
        duration = list(range(int(duration_range[0]), int(duration_range[1])))
        dates = list(range(int(date_range[0]), int(date_range[1]) + 1))
        
        result = cur_df().search(
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
        ui.output_data_frame('table')
        
    @output
    @render.data_frame
    def table():
        if not search_performed():
            return pd.DataFrame(columns=["Perform a search"]) # return text value instead of table?
        elif filtered_df().empty:
            return pd.DataFrame(columns=["No results found"])
        else:
            search_df_name = 'mycorp' if 'DATE' in filtered_df().columns else 'yvcdh'
            logging.debug(f'df {search_df_name} passed to table rendering function')
            return render.DataTable(filtered_df(), styles=custom_table)


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
        input_df = filtered_df()
        rchoice = input.plot_choices()
        common_select_out = [ui.input_select('x_input', 'If a non-numerical axis is chosen (e.g. \"summary\"), it will count the elements of this axis. Select x-axis:', 
                    choices=[c for c in input_df.columns], selected=cur_df().timeaxis),
                    ui.input_select('y_input', 'Select y-axis', choices=[c for c in input_df.columns])
                    ]
        
        if input_df.empty:
            return ui.card('Nothing to plot. Perform a search first')
        
        elif rchoice == 'line':
            return common_select_out
        
        elif rchoice == 'histogram':
            return [ui.input_select('x_input', 'If a non-numerical axis is chosen (e.g. \"summary\"), it will count the elements of this axis. Select x-axis:', 
                    choices=[c for c in input_df.columns], selected=cur_df().timeaxis)]
        
        elif rchoice == 'heatmap':
            return common_select_out
        
        elif rchoice == 'stacked':
            return common_select_out + \
                    [ui.input_select('z_input', 'Select third display value (used for stacking)', choices=[c for c in input_df.columns])]
        
        elif rchoice == 'scatter':
            return common_select_out + \
                    [ui.input_select('z_input', 'Select third display value (used for color)', choices=[c for c in input_df.columns] + ['none'], selected='none'),
                    ui.input_select('w_input', 'Select fourth display value (used for size of scatter dots)', choices= cur_df().numeric_axes + ['none'], # has to be numeric 
                    selected='none')
                    ]


    ## TODO!
    def download_search_data():
        pass


app = App(app_ui, server)

# To run the app, ensure this script is executed directly
if __name__ == "__main__":
    app.run()