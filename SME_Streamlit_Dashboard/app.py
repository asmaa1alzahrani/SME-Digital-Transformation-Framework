from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from readiness import load_questions, score, GATES, LEVEL_NAMES

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
OUT = ROOT / 'output'
st.set_page_config(page_title='SME Compliance Intelligence', page_icon='📊', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
.block-container{padding-top:1.7rem;max-width:1450px}h1,h2,h3{letter-spacing:-.025em}
[data-testid="stMetric"]{background:#f5f8fc;border:1px solid #e2e8f0;border-radius:14px;padding:17px}
[data-testid="stSidebar"]{background:#f5f8fc}
.pill{display:inline-block;padding:5px 12px;border-radius:18px;background:#e9f4ef;color:#1c7655;font-weight:600}
.info{background:#f3f7fc;border-left:4px solid #3478bd;border-radius:8px;padding:13px 16px}
</style>''', unsafe_allow_html=True)

@st.cache_data
def get_questions():
    return load_questions(DATA/'questions.csv')
qs=get_questions()
EXAMPLE=pd.read_csv(DATA/'example_sme.csv').set_index('id')['answer'].to_dict()
if 'answers' not in st.session_state: st.session_state.answers={k:EXAMPLE.get(k,'Yes') for k in qs.index}
if 'name' not in st.session_state: st.session_state.name='Example: new micro café'
if 'workers' not in st.session_state: st.session_state.workers=8
if 'assessed' not in st.session_state: st.session_state.assessed=False

with st.sidebar:
    st.title('◈ SME Intelligence')
    st.caption('Compliance-driven digital transformation')
    page=st.radio('Navigate', ['Overview', 'SME Assessment', 'Dependencies', 'Evaluation Lab'], label_visibility='collapsed')
    st.divider()
    st.caption('FRAMEWORK STATUS')
    st.write('**12** regulatory indicators · **4** sequential gates')
    st.info('Research prototype. Rules and evidence require expert and regulatory verification before real-world use.')
    if st.button('↺ Reset synthetic example',use_container_width=True):
        st.session_state.answers={k:EXAMPLE.get(k,'Yes') for k in qs.index}
        for k in qs.index: st.session_state.pop(f'input_{k}', None)
        st.session_state.name='Example: new micro café'
        st.session_state.workers=8
        st.session_state.assessed=False
        st.rerun()

answers={q:st.session_state.answers[q] for q in qs.index}
r=score(answers,qs)
COLORS={'G1':'#2863a5','G2':'#2e9c88','G3':'#d69c39','G4':'#7d6fbd'}
LABELS={'G1':'Registration','G2':'Staff Records','G3':'Ongoing Duties','G4':'Saudization'}

def metric_strip(result):
    a,b,c,d=st.columns(4)
    a.metric('Readiness level',f"{result['level']} / 4",LEVEL_NAMES[result['level']])
    b.metric('Coverage',f"{result['coverage']:.0%}",help='For comparison only; does not determine the readiness level')
    c.metric('Gates met',f"{sum(result['gate_met'].values())} / 4")
    d.metric('Open requirements',len(result['open_items']))

def gate_chart(result):
    fig=go.Figure()
    for g in GATES:
        fig.add_trace(go.Bar(y=[g],x=[1],orientation='h',name=LABELS[g],marker_color=('#249777' if result['gate_met'][g] else '#e5a14b'),text=('MET' if result['gate_met'][g] else 'NOT MET'),textposition='inside',hovertemplate=f'{g} · {LABELS[g]}<extra></extra>',showlegend=False))
    fig.update_layout(height=290,margin=dict(l=5,r=5,t=12,b=8),xaxis=dict(visible=False,range=[0,1.05]),yaxis=dict(autorange='reversed',title=None),plot_bgcolor='rgba(0,0,0,0)',paper_bgcolor='rgba(0,0,0,0)')
    return fig

def gap_chart():
    df=qs.reset_index()[['id','gate']].copy()
    df['answer']=df['id'].map(answers)
    counts=df.assign(unmet=df.answer.eq('No').astype(int)).groupby('gate',sort=False)['unmet'].sum().reindex(GATES)
    fig=px.bar(x=counts.index,y=counts.values,color=counts.index,color_discrete_map=COLORS,text=counts.values)
    fig.update_traces(textposition='outside',hovertemplate='Gate %{x}<br>Unmet %{y}<extra></extra>')
    fig.update_layout(height=290,showlegend=False,xaxis_title=None,yaxis_title='Unmet requirements',yaxis=dict(dtick=1,range=[0,max(2,counts.max()+1)]),margin=dict(l=5,r=5,t=15,b=10))
    return fig

def blocking_panel(result):
    if result['blocking_id']:
        q=result['blocking_id']
        st.warning(f"**Priority blocker: {q}** — {result['blocking_question']}")
        st.write('**Where to check:**',result['where_to_fix'])
        st.write('**Regulatory record references:**',result['evidence'])
        st.caption('Recorded consequence (from the research extraction; verify before operational use): '+str(result['if_no']))
    else: st.success('All four gates met under the current assessment rules.')

if page=='Overview':
    st.title('SME Compliance Intelligence')
    st.caption('Executive dashboard · Current assessment · '+st.session_state.name)
    metric_strip(r)
    left,right=st.columns([1.3,1])
    with left:
        st.subheader('Sequential gate readiness')
        st.plotly_chart(gate_chart(r),use_container_width=True)
    with right:
        st.subheader('Compliance gaps by gate')
        st.plotly_chart(gap_chart(),use_container_width=True)
    st.subheader('Recommended next action')
    blocking_panel(r)
    st.caption('A gate may be met even if an earlier gate is not. Readiness level counts only consecutive gates from G1. Synthetic demonstration data unless real answers are supplied.')
    st.info('To change answers, open **SME Assessment** in the left navigation. Changes are applied when you press Assess Readiness.')

elif page=='SME Assessment':
    st.title('Interactive SME Assessment')
    st.caption('Answer all 12 questions. N/A is accepted only where the rule allows it; eligibility for N/A is not independently verified.')
    with st.form('assessment'):
        x,y=st.columns([3,1])
        name=x.text_input('SME name',value=st.session_state.name)
        workers=y.number_input('Workers',min_value=0,max_value=100000,value=int(st.session_state.workers))
        submitted_answers={}
        for g in GATES:
            st.subheader(f'{g} — {LABELS[g]}')
            group=qs[qs['gate']==g]
            for q,rec in group.iterrows():
                left,right=st.columns([3.3,1])
                left.markdown(f'**{q}** · {rec["question"]}')
                left.caption('N/A condition: '+str(rec['na_allowed_when']))
                options=['Yes','No'] if int(rec['na_never'])==1 else ['Yes','No','N/A']
                current=st.session_state.answers[q]
                submitted_answers[q]=right.selectbox(f'Answer {q}',options,index=options.index(current) if current in options else 0,key=f'input_{q}',label_visibility='collapsed')
        submitted=st.form_submit_button('✓ Assess Readiness',type='primary',use_container_width=True)
    if submitted:
        st.session_state.answers=submitted_answers
        st.session_state.name=name
        st.session_state.workers=workers
        st.session_state.assessed=True
        st.rerun()
    if st.session_state.assessed:
        st.divider()
        st.subheader('Assessment results')
        metric_strip(r)
        c1,c2=st.columns([1.2,1])
        with c1: st.plotly_chart(gate_chart(r),use_container_width=True)
        with c2: blocking_panel(r)
        st.subheader('Open requirements')
        open_df=qs.loc[r['open_items']].reset_index()[['id','gate','question','where_to_check','records']] if r['open_items'] else pd.DataFrame(columns=['id','gate','question','where_to_check','records'])
        st.dataframe(open_df,use_container_width=True,hide_index=True)
        st.download_button('Download assessment CSV',pd.DataFrame([{'id':q,'answer':answers[q]} for q in qs.index]).to_csv(index=False).encode(),file_name='sme_assessment.csv',mime='text/csv')
        st.caption('What-if analysis: modify any answer above and press Assess Readiness again. No real-world remediation is performed.')

elif page=='Dependencies':
    st.title('Regulatory Dependency Explorer')
    st.caption('Evidence-linked relationships supplied by the research team; link direction does not by itself establish a legal prerequisite.')
    links=pd.read_csv(DATA/'gate_links.csv')
    g=st.selectbox('Filter by source gate',['All']+GATES)
    if g!='All': links=links[links['from_gate']==g]
    st.metric('Evidence-linked rows',len(links))
    st.dataframe(links,use_container_width=True,hide_index=True)
    st.download_button('Download filtered links',links.to_csv(index=False).encode(),file_name='gate_links_filtered.csv',mime='text/csv')
    st.subheader('Indicator reference catalogue')
    st.dataframe(qs.reset_index()[['id','gate','question','records','where_to_check','na_allowed_when']],hide_index=True,use_container_width=True)

else:
    st.title('Simulation & Evaluation Lab')
    st.caption('Research simulations (A1–A7). Synthetic patterns, not real SME prevalence or observed policy effects.')
    tab1,tab2,tab3=st.tabs(['Exhaustive enumeration','Monte Carlo','Lift potential'])
    with tab1:
        df=pd.read_csv(OUT/'enumeration_band_by_level.csv')
        st.subheader('4,096 binary patterns · Coverage band vs readiness level')
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.caption('All 2^12 Yes/No combinations have equal weight in this enumeration.')
    with tab2:
        df=pd.read_csv(OUT/'monte_carlo.csv')
        st.subheader('80,000 synthetic SMEs across two generators')
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.caption('Results depend on assumed response-generation distributions; they are not population estimates.')
    with tab3:
        df=pd.read_csv(OUT/'lift_potential.csv')
        st.subheader('First-blocker counterfactual')
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.caption('Fixing only the first blocker is a hypothetical answer change, not a measured causal intervention.')
