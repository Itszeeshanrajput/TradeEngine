import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
from dash.dash_table.Format import Format, Scheme
import json
import pandas as pd
import collections

# --- App Initialization with a Dark Theme ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG], update_title='Updating...')
app.title = "Forex Bot Dashboard"

# --- Helper Functions ---
def create_summary_card(title, value, color):
    """Creates a card for the account summary. Now formats the number."""
    formatted_value = f"${value:,.2f}" if isinstance(value, (int, float)) else "N/A"
    return dbc.Card(
        dbc.CardBody([
            html.H4(title, className="card-title"),
            html.H2(formatted_value, className="card-text", style={'color': color}),
        ])
    )

# --- App Layout ---
app.layout = dbc.Container([
    # -- Header and Controls --
    dbc.Row([
        dbc.Col(html.H1("🤖 Forex Bot Dashboard"), width=8),
        dbc.Col([
            dbc.Button("⏸️ Pause Trading", id="pause-button", color="warning", className="me-2"),
            dbc.Button("▶️ Resume Trading", id="resume-button", color="success"),
        ], width=4, className="d-flex align-items-center justify-content-end"),
    ], align="center", className="my-4"),
    
    html.Div(id="status-bar", className="mb-3"),

    # -- Live Account Summary --
    dbc.Row(id='account-summary-row', className="mb-4"),

    # -- Live Open Positions --
    dbc.Row([
        dbc.Col([
            html.H3("Live Open Positions"),
            dash_table.DataTable(
                id='open-positions-table',
                style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white', 'fontWeight': 'bold'},
                style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'border': '1px solid #444', 'textAlign': 'left'},
                style_data_conditional=[
                    {'if': {'column_id': 'profit', 'filter_query': '{profit} > 0'}, 'color': '#28a745', 'fontWeight': 'bold'},
                    {'if': {'column_id': 'profit', 'filter_query': '{profit} < 0'}, 'color': '#dc3545', 'fontWeight': 'bold'},
                ],
            ),
        ]),
    ]),

    # -- Live Log Viewer --
    dbc.Row([
        dbc.Col([
            html.H3("Live Trade Log", className="mt-4"),
            html.Pre( # Use <pre> for better formatting of log text
                id='log-output',
                style={'height': '400px', 'overflowY': 'scroll', 'border': '1px solid #444', 'padding': '10px', 'backgroundColor': '#222'}
            )
        ]),
    ], className="mt-4"),

    dcc.Interval(id='interval-component', interval=3 * 1000, n_intervals=0)
], fluid=True)


# --- Callbacks ---

@app.callback(
    Output('status-bar', 'children'),
    Input('pause-button', 'n_clicks'),
    Input('resume-button', 'n_clicks'),
    prevent_initial_call=True
)
def update_control_status(pause_clicks, resume_clicks):
    ctx = dash.callback_context
    if not ctx.triggered: return ""
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    status = 'paused' if button_id == 'pause-button' else 'running'
    with open('control.json', 'w') as f: json.dump({'status': status}, f)
    color = "warning" if status == 'paused' else "success"
    message = f"Bot command received: Trading is now {'PAUSED' if status == 'paused' else 'RUNNING'}."
    return dbc.Alert(message, color=color, duration=4000)


@app.callback(
    Output('account-summary-row', 'children'),
    Output('open-positions-table', 'data'),
    Output('open-positions-table', 'columns'),
    Output('log-output', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_dashboard(n):
    summary_cards = [
        dbc.Col(create_summary_card("Balance", "N/A", "white")),
        dbc.Col(create_summary_card("Equity", "N/A", "white")),
        dbc.Col(create_summary_card("Margin", "N/A", "white")),
    ]
    positions_data = []
    log_text = "Waiting for data... Is the main bot script running?"

    try:
        with open('dashboard_data.json', 'r') as f:
            data = json.load(f)
            acc_info = data.get('account_info', {})
            balance = acc_info.get('balance', 'N/A')
            equity = acc_info.get('equity', 'N/A')
            margin = acc_info.get('margin', 'N/A')
            summary_cards = [
                dbc.Col(create_summary_card("Balance", balance, "#4db6ac")),
                dbc.Col(create_summary_card("Equity", equity, "#4dd0e1")),
                dbc.Col(create_summary_card("Margin", margin, "#ba68c8")),
            ]
            positions_data = data.get('positions', [])
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Define columns with specific formatting for numbers
    columns = [
        {'name': 'Symbol', 'id': 'symbol'}, {'name': 'Type', 'id': 'type'},
        {'name': 'Volume', 'id': 'volume', 'type': 'numeric'},
        {'name': 'Open Price', 'id': 'price_open', 'type': 'numeric', 'format': Format(precision=5)},
        {'name': 'Current Price', 'id': 'price_current', 'type': 'numeric', 'format': Format(precision=5)},
        {'name': 'Stop Loss', 'id': 'sl', 'type': 'numeric', 'format': Format(precision=5)},
        {'name': 'Take Profit', 'id': 'tp', 'type': 'numeric', 'format': Format(precision=5)},
        # --- THIS IS THE CORRECTED LINE ---
        {'name': 'Profit', 'id': 'profit', 'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed, sign='+')},
    ]
    
    try:
        with open('trade_bot.log', 'r') as f:
            log_text = ''.join(collections.deque(f, 200))
    except FileNotFoundError:
        log_text = "Log file 'trade_bot.log' not found."

    return summary_cards, positions_data, columns, log_text

if __name__ == '__main__':
    print("Starting GUI server on http://127.0.0.1:8050")
    print("Run main.py in a separate terminal to start the bot.")
    app.run(debug=False, port=8050)