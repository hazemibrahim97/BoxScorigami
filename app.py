import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
np.seterr(divide='ignore')

# Page config
st.set_page_config(
    page_title='NBA Box-scorigami',
    layout='wide'
)

# Data preparation
@st.cache_data
def load_data():
    df = pd.read_csv('combined.csv')
    df = df.dropna(subset=['Player'])
    return df

df = load_data()
all_players = sorted(df['Player'].unique())
all_teams = sorted(df['Team'].unique())

# Constants
stat_options = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PF', 'FGA', 'FGM', '3FA', '3FM', 'FTA', 'FTM']
table_columns = ["Player","GameDay",'WinOrLoss',"PTS","REB","AST","STL","BLK","TO","PF","FGA", 'FGM', "3FA", '3FM',"FTA","FTM"]

def filter_data(df, player, team, playoffs):
    if player != 'All':
        df = df.loc[df['Player'] == player]
    
    if team != 'All':
        df = df.loc[df['Team'] == team]
        
    if playoffs == 'Regular Season':
        df = df.loc[pd.isnull(df['Playoffs'])]
    elif playoffs == 'Playoffs':
        df = df.loc[df['Playoffs'] == 'Y']
        
    return df

def get_pivot(selected_stats, player, team, playoffs):
    counts_df = filter_data(df, player, team, playoffs)
    
    counts_df = counts_df[selected_stats].value_counts().reset_index(name='count')

    min_stat1, max_stat1 = 0, df[selected_stats[0]].max()
    min_stat2, max_stat2 = 0, df[selected_stats[1]].max()

    all_combinations = pd.DataFrame(
        [(stat1, stat2) for stat1 in range(min_stat1, max_stat1 + 1) for stat2 in range(min_stat2, max_stat2 + 1)],
        columns=[selected_stats[0], selected_stats[1]]
    )

    filled_counts_df = all_combinations.merge(counts_df, on=[selected_stats[0], selected_stats[1]], how='left').fillna(0)
    filled_counts_df['count'] = filled_counts_df['count'].astype(int)
    
    heatmap_data = filled_counts_df.pivot(index=selected_stats[1], columns=selected_stats[0], values='count')
    heatmap_data = heatmap_data.iloc[::-1]
    
    return heatmap_data, filled_counts_df['count'].values

def create_heatmap(x_stat, y_stat, player, team, playoffs, show_potential=False):
    stats_data, raw_counts = get_pivot([x_stat, y_stat], player, team, playoffs)
    
    # Get max values for axis limits
    x_max = stats_data.columns.max()
    y_max = stats_data.index.max()
    
    # Convert pivot table to points
    points_df = pd.DataFrame()
    for i in range(len(stats_data.index)):
        for j in range(len(stats_data.columns)):
            points_df = pd.concat([points_df, pd.DataFrame({
                'x': [stats_data.columns[j]],
                'y': [stats_data.index[i]],
                'count': [stats_data.iloc[i, j]]
            })])
    
    
    if show_potential:
        # Show potential points in green, existing in gray
        fig = go.Figure(data=[
            go.Scatter(
                x=points_df[points_df['count'] == 0]['x'],
                y=points_df[points_df['count'] == 0]['y'],
                mode='markers',
                marker=dict(
                    size=8,
                    color='lightgreen',
                    symbol='square',
                    line=dict(
                        color='white',
                        width=0.1
                    )
                ),
                name='Potential',
                hovertemplate=f'{x_stat}: %{{x}}<br>{y_stat}: %{{y}}<br>Not yet achieved<extra></extra>'
            ),
            go.Scatter(
                x=points_df[points_df['count'] > 0]['x'],
                y=points_df[points_df['count'] > 0]['y'],
                mode='markers',
                marker=dict(
                    size=8,
                    color='#0E1117',
                    symbol='square',
                    line=dict(
                        color='white',
                        width=0
                    )
                ),
                name='Achieved',
                hovertemplate=f'{x_stat}: %{{x}}<br>{y_stat}: %{{y}}<br>Frequency: %{{text}}<extra></extra>',
                text=points_df[points_df['count'] > 0]['count']
            )
        ])
    else:
        
        fig = go.Figure(data=[
            go.Scatter(
                x=points_df[points_df['count'] > 0]['x'],
                y=points_df[points_df['count'] > 0]['y'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=np.log1p(points_df[points_df['count'] > 0]['count']),
                    colorscale='Viridis',
                    showscale=False,
                    colorbar=dict(
                        title='Log Frequency'
                    ),
                    symbol='square',
                    line=dict(
                        color='white',
                        width=0.05
                    )
                ),
                hovertemplate=f'{x_stat}: %{{x}}<br>{y_stat}: %{{y}}<br>Frequency: %{{text}}<extra></extra>',
                text=points_df[points_df['count'] > 0]['count']
            ),
            go.Scatter(
                x=points_df[points_df['count'] == 0]['x'],
                y=points_df[points_df['count'] == 0]['y'],
                mode='markers',
                marker=dict(
                    size=8,
                    color='#0E1117',
                    symbol='square',
                    line=dict(
                        color='white',
                        width=0
                    )
                ),
                # name='',
                hovertemplate=f'{x_stat}: %{{x}}<br>{y_stat}: %{{y}}<br>Not yet achieved<extra></extra>'
            )
            
        ])
        

    fig.update_layout(
        title=f"{x_stat} and {y_stat} box score frequencies" if not show_potential else f"Available Boxscorigamis for {x_stat} and {y_stat}",
        xaxis=dict(
            title=x_stat,
            dtick=2,
            tickmode='linear',
            tickangle=0,
            showgrid=False,
            gridcolor='rgba(128,128,128,0.2)',
            automargin=True,
            range=[-0.5, x_max + 0.5],
            fixedrange=True
        ),
        yaxis=dict(
            title=y_stat,
            dtick=1,
            tickmode='linear',
            showgrid=False,
            gridcolor='rgba(128,128,128,0.2)',
            automargin=True,
            range=[-0.5, y_max + 0.5],
            fixedrange=True
        ),
        autosize=True,
        margin=dict(l=50, r=50, t=80, b=50),
        height=550,
        plot_bgcolor='#0E1117',
        showlegend=show_potential,
        dragmode=False
    )
    
    return fig

def create_histogram(stat, player, team, playoffs):
    counts_df = filter_data(df, player, team, playoffs)
    freq_counts = counts_df[stat].value_counts().sort_index()
    
    colorscale = 'rdbu'
    color_values = np.log1p(freq_counts.values)

    fig = go.Figure(data=go.Bar(
        x=freq_counts.index,
        y=freq_counts.values,
        marker=dict(
            color=color_values,
            colorscale=colorscale,
            showscale=False,
            line=dict(
                color='white',
                width=0.25
            )
        ),
        hovertemplate=f'{stat}: %{{x}}<br>Frequency: %{{y}}<extra></extra>'
    ))

    fig.update_layout(
        title=f"Histogram of {stat} Box Scores",
        xaxis=dict(
            title=stat,
            tickmode='array',
            tickvals=list(df[stat].unique()),
            tickangle=0,
            dtick=2,
            automargin=True,
            fixedrange=True
        ),
        yaxis=dict(
            title="Frequency",
            type='log' if player == 'All' else 'linear',
            automargin=True,
            fixedrange=True
        ),
        autosize=True,
        height=550,
        margin=dict(l=50, r=50, t=80, b=50),
        bargap=0.2,
        bargroupgap=0.1,
        plot_bgcolor='#0E1117',
        dragmode=False,
    )

    return fig

def get_box_scores(x_stat, y_stat, x_value, y_value, player, team, playoffs):
    filtered_data = df.loc[(df[x_stat] == x_value)]
    if x_stat != y_stat:
        filtered_data = filtered_data.loc[filtered_data[y_stat] == y_value]
    
    filtered_data = filter_data(filtered_data, player, team, playoffs)
    return filtered_data.sort_values(by='GameDay', ascending=False)



# Sidebar
with st.sidebar:
    st.title("NBA Box-scorigami")
    st.caption("Box scores valid for the 1990-2025 seasons.")
    
    st.header("Select stats")
    
    # Initialize session state only once at startup
    if 'initialized' not in st.session_state:
        st.session_state.x_stat = 'PTS'
        st.session_state.y_stat = 'REB'
        st.session_state.player = 'All'
        st.session_state.team = 'All'
        st.session_state.playoffs = 'Both'
        st.session_state.show_potential = False
        st.session_state.initialized = True
    
    # Define callback for reset button
    def reset_filters():
        st.session_state.x_stat = 'PTS'
        st.session_state.y_stat = 'REB'
        st.session_state.player = 'All'
        st.session_state.team = 'All'
        st.session_state.playoffs = 'Both'
        st.session_state.show_potential = False
    
    col1, col2 = st.columns(2)
    with col1:
        x_stat = st.selectbox("X-axis:", 
                            stat_options, 
                            key='x_stat')
    with col2:
        y_stat = st.selectbox("Y-axis:", 
                            stat_options, 
                            key='y_stat')
        
    show_potential = st.toggle("Show potential Box-scorigamis", 
                             key='show_potential')
    
    st.header("Select filters")
    
    player = st.selectbox("Player:", 
                         ['All'] + list(all_players),
                         key='player')
    team = st.selectbox("Team:", 
                       ['All'] + list(all_teams),
                       key='team')
    playoffs = st.selectbox("Type:", 
                          ['Both', 'Regular Season', 'Playoffs'],
                          key='playoffs')

    if st.button("Reset filters", on_click=reset_filters):
        pass
# Main content
if x_stat == y_stat:
    fig = create_histogram(x_stat, player, team, playoffs)
else:
    fig = create_heatmap(x_stat, y_stat, player, team, playoffs, show_potential)

# Display the plot
clicked_point = st.plotly_chart(fig, use_container_width=True, on_select="rerun", config={'displayModeBar': False})


if clicked_point and 'points' in clicked_point['selection']:
    points = clicked_point['selection']['points']
    if points:
        x_value = points[0]['x']
        if x_stat != y_stat:
            y_value = points[0]['y']
        else:
            y_value = None

        box_scores = get_box_scores(x_stat, y_stat, x_value, y_value, player, team, playoffs)

        if not box_scores.empty:
            y_stat_string = f" and {y_stat} = {y_value}" if x_stat != y_stat else ''
            player_string = f" by {player}" if player != 'All' else ''
            team_string = f" for {team}" if team != 'All' else ''
            
            if len(box_scores) >= 10:
                base_title = "Latest 10"
            else:
                base_title = "All"
            
            if playoffs == 'Playoffs':
                game_type = " Playoff"
            elif playoffs == 'Regular Season':
                game_type = " Regular Season"
            else:
                game_type = ""
                
            title = f"{base_title}{game_type} box scores with {x_stat} = {x_value}{y_stat_string}{player_string}{team_string}"
            
            st.subheader(title)
            st.dataframe(
                box_scores[table_columns].head(10),
                hide_index=True,
                use_container_width=True
            )