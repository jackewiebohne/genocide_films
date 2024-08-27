from shiny import App, ui, reactive, render
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from shinywidgets import output_widget, render_widget 
from shinyswatch import theme
from yvcdh_handler import yvcdh_handler
from pandas.api.types import is_numeric_dtype, is_object_dtype
## TODO:
## a tab to display full corpus? or pre-loaded charts of each corpus?
## example uses
## allow for more conditions during search (e.g. genre, duration slider)
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
                <br>Currently only the documentaries in the filmographies of Yad Vashem and Cinematography of the Holocaust can be searched and graphed.\
                <br>A full search of these filmographies (scraped from the above websites) regardless of genre will be possible once data cleaning is finished.\
                <br>My own hand-curated set of documentaries on genocide more generally will also be made available soon.\
                <br>Semantic similarity searches (using trained vector libraries) will also be made available and custom graphing for these will allow for unique\
                <br>data visualisations (e.g. clustering of film-vectors by genre, director, specific search terms, changes of vectors over time etc.) will also be possible soon.'\
            ) ## add explanation html file to be imported
        ),
        ui.nav_panel('Instructions', 
            ui.markdown(
                "**Instructions**:<br>You can search the tables for single words. If you want to search for two words in any given row you can chain them together like so: hitler|himmler.\
                <br>The search syntax follows Python's Regular Expressions. For more info on complex searches, see:<br>[Python regex](https://docs.python.org/3/howto/regex.html)\
                \
                " ## add instruction texts: tell about complex regex searches and give link to further info
            )
        ),
        ui.nav_panel('Yad Vashem and Cinematography of the Holocaust filmographies', 
            ui.output_ui('yvcdh_ui')
        ),
        ui.nav_panel('Hand-curated genocide documentary filmography', 'Nothing yet'),
            # ui.output_ui('my_corp_ui')
        title='Explore and Chart Production Data of Documentaries on the Holocaust and Genocide'
    ), theme=theme.cyborg
)


def server(input, output, session):

    ## functions for retrieving backend info and plotting of yvcdh
    # trigger_yvcdh_pressed = reactive.Value(False)
    yvcdh_handled = reactive.Value(None)

    filtered_df = reactive.Value(pd.DataFrame())
    search_performed = reactive.Value(False)
    
    @reactive.Effect
    @reactive.event(input.search_yvcdh)
    def perform_search():
        search_term = input.search_term()
        search_column = input.search_column()
        date_range = input.dates()
        duration_range = input.duration()
        case_sensitive = input.case() == 'True'
        
        duration = list(range(int(duration_range[0]), int(duration_range[1])))
        dates = list(range(int(date_range[0]), int(date_range[1]) + 1))
        
        try:
            result = yvcdh_handled().search(
                searchinput=search_term,
                search_col=search_column,
                dates=dates,
                duration=duration,
                case=case_sensitive
            )
            # result.columns = [c.upper() for c in result.columns]
        except ValueError as e:
            result = pd.DataFrame()
            print(f"Search error: {e}")
        
        # Update the reactive value with the search result
        filtered_df.set(result)
        search_performed.set(True)
        
    @output
    @render.data_frame
    def table():
        # If no search has been performed yet
        if not search_performed():
            return pd.DataFrame(columns=["Perform a search"]) # return text value instead of table?
    
        # If a search was performed but no results found
        df = filtered_df()
        if df.empty:
            return pd.DataFrame(columns=["No results found"])
        else:
            return render.DataTable(df, styles=custom_table)

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
                    choices=[c for c in input_df], selected='year'),
                    ui.input_select('y_input', 'Select y-axis', choices=[c for c in input_df])
                    ]
        if input_df.empty:
            return ui.card('Nothing to plot. Perform a search first')
        elif rchoice == 'line':
            return common_select_out
        elif rchoice == 'histogram':
            return [ui.input_select('x_input', 'If a non-numerical axis is chosen (e.g. \"summary\"), it will count the elements of this axis. Select x-axis:', 
                    choices=[c for c in input_df], selected='year')]
        elif rchoice == 'heatmap':
            return common_select_out
        elif rchoice == 'stacked':
            return common_select_out + \
                    [ui.input_select('z_input', 'Select third display value (used for stacking)', choices=[c for c in input_df])]
        elif rchoice == 'scatter':
            return common_select_out + \
                    [ui.input_select('z_input', 'Select third display value (used for color)', choices=[c for c in input_df] + ['none'], selected='none'),
                    ui.input_select('w_input', 'Select fourth display value (used for size of scatter dots)', choices=['year', 'duration', 'none'], # has to be numeric 
                    selected='none')
                    ]


    ## TODO!
    def download_search_data():
        pass


    # logic to display the yvcdh-specific ui
    @output
    @render.ui
    def yvcdh_ui():
        yvcdh_handled.set(yvcdh_handler('https://raw.githubusercontent.com/jackewiebohne/genocide_films/main/data/yad_vashem_CdH_joint.tsv'))
        yvcdh_dur_max = yvcdh_handled().df.duration.max()
        return ui.layout_sidebar(  
            ui.sidebar(
                ui.input_text("search_term", "Enter a Word to Search for:"),
                ui.input_select("search_column", "Select Columns to Search in:", choices=['all'] + yvcdh_handled().strcols, selected='summary'),
                ui.input_slider("dates", "Select Date Range:", 1900, 2024, value=(1900, 2024), sep=''),
                ui.input_slider("duration", "Select Duration Range:", 0, yvcdh_dur_max, value=(0, yvcdh_dur_max), sep=''),
                ui.input_selectize('case', "Case Sensitive?", choices=['False', 'True'], selected='False'),
                ui.input_action_button("search_yvcdh", "Search"), 
                position='left'
            ),
            ui.navset_card_tab(
                ui.nav_panel('Table View',
                    ## add output text that says how many results were found
                    ui.output_data_frame('table')
                ),
                ui.nav_panel('Chart View',
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
                )       
            )
        )

app = App(app_ui, server)

# To run the app, ensure this script is executed directly
if __name__ == "__main__":
    app.run()
