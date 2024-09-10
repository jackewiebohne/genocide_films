from shiny import ui, reactive, render
from yvcdh_handler import yvcdh_handler
from shinywidgets import output_widget, render_widget
from pandas import DataFrame

custom_table = {
    'style': {
        "width": '50%',
        'font-size':'11px',
        'box-shadow': '0 1px 2px rgba(0,0,0,0.1)'
    }
}


def yvcdh_ui(cur_df, filtered_df, search_performed):

    ## rendering dataframe
    @render.data_frame
    def yvcdh_table():
        if not search_performed():
            return DataFrame(columns=["Perform a search"]) # return text value instead of table?
        elif filtered_df().empty:
            return DataFrame(columns=["No results found"])
        else:
            return render.DataTable(filtered_df(), styles=custom_table)


    if not isinstance(cur_df()['yvcdh'], DataFrame): 
        df_dur_max = cur_df()['yvcdh'].df.duration.max()
    else:
        cur_df().update({'yvcdh': yvcdh_handler('https://raw.githubusercontent.com/jackewiebohne/genocide_films/main/data/yad_vashem_CdH_joint.tsv')})
        cur_df.set(cur_df())
        df_dur_max = cur_df()['yvcdh'].df.duration.max()

    ## ui output
    return ui.layout_sidebar(  
        ui.sidebar(
            ui.input_text("search_term", "Enter a Word to Search for:"),
            ui.input_select("search_column", "Select Columns to Search in:", choices=['all'] + cur_df()['yvcdh'].strcols, selected='all'),
            ui.input_slider("dates", "Select Date Range:", 1900, 2024, value=(1900, 2024), sep=''),
            ui.input_slider("duration", "Select Duration Range:", 0, df_dur_max, value=(0, df_dur_max), sep=''),
            ui.input_selectize('case', "Case Sensitive?", choices=['False', 'True'], selected='False'),
            ui.input_action_button("search", "Search"), 
            position='left'
        ),
        ui.card(ui.output_data_frame('yvcdh_table'),)
    )