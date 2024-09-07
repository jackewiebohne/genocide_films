from shiny import ui
from mycorp_handler import mycorp_handler
from shinywidgets import output_widget, render_widget

def mycorp_ui(cur_df):
    cur_df.set(mycorp_handler('https://raw.githubusercontent.com/jackewiebohne/genocide_films/main/data/genocide_corpus.tsv'))
    df_dur_max = cur_df().df.DURATION.max()

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