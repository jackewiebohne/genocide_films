from shiny import ui
from yvcdh_handler import yvcdh_handler
from shinywidgets import output_widget, render_widget


def yvcdh_ui(cur_df):
    cur_df.set(yvcdh_handler('https://raw.githubusercontent.com/jackewiebohne/genocide_films/main/data/yad_vashem_CdH_joint.tsv'))
    df_dur_max = cur_df().df.duration.max()

    return ui.layout_sidebar(  
        ui.sidebar(
            ui.input_text("search_term", "Enter a Word to Search for:"),
            ui.input_select("search_column", "Select Columns to Search in:", choices=['all'] + cur_df().strcols, selected='all'),
            ui.input_slider("dates", "Select Date Range:", 1900, 2024, value=(1900, 2024), sep=''),
            ui.input_slider("duration", "Select Duration Range:", 0, df_dur_max, value=(0, df_dur_max), sep=''),
            ui.input_selectize('case', "Case Sensitive?", choices=['False', 'True'], selected='False'),
            ui.input_action_button("search", "Search"), 
            position='left'
        ),
        ui.navset_card_tab(
            ui.nav_panel('Table View',
                # ui.markdown(f'**found {len(cur_df().df)} results**'),
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