import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E DADOS (MOCK)
# ==========================================
st.set_page_config(page_title="Dashboard Imobiliário", layout="wide")

# Inicializando banco de dados na memória do Streamlit
if 'reservas' not in st.session_state:
    # Dados de exemplo para o protótipo
    dados_iniciais = {
        'ID': [1, 2],
        'Data_Reserva': [pd.to_datetime(datetime.now().date() - timedelta(days=5)), pd.to_datetime(datetime.now().date())],
        'Corretor': ['João', 'Maria'],
        'Cliente': ['Carlos Silva', 'Ana Paula'],
        'Empreendimento': ['Residencial Alpha / 101', 'Torre Beta / 502'],
        'VGV': [450000.0, 320000.0],
        'Status': ['Em andamento', 'Nova Reserva'],
        'Data_Status': [pd.to_datetime(datetime.now().date() - timedelta(days=5)), pd.to_datetime(datetime.now().date())],
        'Observacao': ['Aguardando documentação do fiador', 'Cliente enviando proposta']
    }
    st.session_state.reservas = pd.DataFrame(dados_iniciais)

# Função para avaliar alerta de 4 dias
def verificar_alerta(row):
    if row['Status'] != 'Vendida':
        dias_parada = (pd.to_datetime(datetime.now().date()) - row['Data_Status']).days
        if dias_parada > 4:
            return f"⚠️ {dias_parada} dias parada"
    return "✅ No prazo"

# ==========================================
# 2. MENU LATERAL
# ==========================================
st.sidebar.title("Navegação")
menu = st.sidebar.radio("Selecione a área:", 
                        ["Dashboard & Metas", "Controle de Reservas", "Simulador de Obra"])

# ==========================================
# 3. MÓDULO: DASHBOARD E RANKING (VGV)
# ==========================================
if menu == "Dashboard & Metas":
    st.title("📊 Dashboard Gerencial e Metas")
    
    df = st.session_state.reservas
    # Filtra apenas o que está vendido para o ranking e metas
    vendas_efetivadas = df[df['Status'] == 'Vendida']
    
    # -- META PESSOAL --
    st.markdown("### 🎯 Minha Meta Pessoal")
    col1, col2 = st.columns([1, 2])
    with col1:
        meta_pessoal = st.number_input("Definir Meta (R$):", min_value=0.0, value=10000000.0, step=100000.0)
    
    total_vendido = vendas_efetivadas['VGV'].sum() if not vendas_efetivadas.empty else 0.0
    percentual_meta = (total_vendido / meta_pessoal) * 100 if meta_pessoal > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Meta Definida", f"R$ {meta_pessoal:,.2f}")
    col2.metric("Total Vendido (Realizado)", f"R$ {total_vendido:,.2f}")
    col3.metric("Progresso da Meta", f"{percentual_meta:.1f}%")
    st.progress(min(percentual_meta / 100, 1.0))
    
    st.divider()
    
    # -- RANKING DE CORRETORES --
    st.markdown("### 🏆 Ranking de Corretores (VGV)")
    # Agrupa por corretor (considerando todos os corretores que já cadastraram algo para mostrar quem está com R$ 0)
    corretores_totais = df['Corretor'].unique()
    ranking = vendas_efetivadas.groupby('Corretor')['VGV'].sum().reset_index()
    
    # Adiciona os que não venderam nada
    for c in corretores_totais:
        if c not in ranking['Corretor'].values:
            ranking = pd.concat([ranking, pd.DataFrame({'Corretor': [c], 'VGV': [0.0]})], ignore_index=True)
            
    ranking = ranking.sort_values(by='VGV', ascending=True) # Ascendente para o gráfico ficar do maior p/ menor no topo
    
    if not ranking.empty:
        fig = px.bar(ranking, x='VGV', y='Corretor', orientation='h', 
                     title="VGV Efetivado por Corretor", text='VGV',
                     color='VGV', color_continuous_scale='Greens')
        fig.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma venda efetivada ainda.")

# ==========================================
# 4. MÓDULO: CONTROLE DE RESERVAS
# ==========================================
elif menu == "Controle de Reservas":
    st.title("📋 Controle de Reservas (Input Manual)")
    
    # Formulário de Nova Reserva / Atualização
    with st.expander("➕ Adicionar Nova Reserva", expanded=False):
        with st.form("form_nova_reserva"):
            col1, col2, col3 = st.columns(3)
            corretor_input = col1.text_input("Corretor")
            cliente_input = col2.text_input("Cliente")
            unidade_input = col3.text_input("Empreendimento / Unidade")
            
            col4, col5 = st.columns(2)
            vgv_input = col4.number_input("VGV (R$)", min_value=0.0, step=1000.0)
            status_input = col5.selectbox("Status", ["Nova Reserva", "Em andamento", "Vendida"])
            
            obs_input = st.text_area("Observações (O que falta para virar venda?)")
            
            submit = st.form_submit_button("Salvar Reserva")
            
            if submit:
                novo_id = len(st.session_state.reservas) + 1
                nova_linha = pd.DataFrame([{
                    'ID': novo_id,
                    'Data_Reserva': pd.to_datetime(datetime.now().date()),
                    'Corretor': corretor_input,
                    'Cliente': cliente_input,
                    'Empreendimento': unidade_input,
                    'VGV': vgv_input,
                    'Status': status_input,
                    'Data_Status': pd.to_datetime(datetime.now().date()),
                    'Observacao': obs_input
                }])
                st.session_state.reservas = pd.concat([st.session_state.reservas, nova_linha], ignore_index=True)
                st.success("Reserva salva com sucesso!")
                st.rerun()
                
    st.divider()
    
    # Filtro de visualização
    st.markdown("### 🔍 Visão de Reservas")
    corretores_lista = ["Todos"] + list(st.session_state.reservas['Corretor'].unique())
    filtro_corretor = st.selectbox("Filtrar por Corretor:", corretores_lista)
    
    df_exibicao = st.session_state.reservas.copy()
    if filtro_corretor != "Todos":
        df_exibicao = df_exibicao[df_exibicao['Corretor'] == filtro_corretor]
        
    # Aplicar regra de alerta
    df_exibicao['Alerta'] = df_exibicao.apply(verificar_alerta, axis=1)
    
    # Formatação das datas para exibição
    df_exibicao['Data_Reserva'] = df_exibicao['Data_Reserva'].dt.strftime('%d/%m/%Y')
    df_exibicao['Data_Status'] = df_exibicao['Data_Status'].dt.strftime('%d/%m/%Y')
    
    # Mostrar a tabela ordenando para os alertas aparecerem primeiro
    df_exibicao = df_exibicao.sort_values(by='Alerta', ascending=False)
    
    st.dataframe(df_exibicao[['Alerta', 'Data_Reserva', 'Corretor', 'Cliente', 'Empreendimento', 'VGV', 'Status', 'Data_Status', 'Observacao']], 
                 use_container_width=True, hide_index=True)

# ==========================================
# 5. MÓDULO: SIMULADOR DE EVOLUÇÃO DE OBRA
# ==========================================
elif menu == "Simulador de Obra":
    st.title("🏗️ Simulador de Evolução de Obra (TR)")
    st.markdown("Simule a evolução do saldo devedor durante o período de obras considerando a taxa TR.")
    
    with st.sidebar:
        st.markdown("### Parâmetros da Simulação")
        meses_obra = st.slider("Prazo de Obras (Meses)", 12, 60, 36)
        
    col1, col2, col3 = st.columns(3)
    valor_financiado = col1.number_input("Valor Financiado Inicial (R$)", value=300000.0, step=10000.0)
    valor_parcela = col2.number_input("Valor da Parcela Mensal (R$)", value=3000.0, step=100.0)
    tr_projetada = col3.number_input("TR Projetada ao Mês (%)", value=0.15, step=0.01)
    
    if st.button("Gerar Simulação"):
        tabela_simulacao = []
        saldo_inicial = valor_financiado
        
        for mes in range(1, meses_obra + 1):
            correcao_tr = saldo_inicial * (tr_projetada / 100)
            saldo_final = saldo_inicial + correcao_tr - valor_parcela
            
            # Impede que o saldo fique negativo
            if saldo_final < 0:
                saldo_final = 0
                valor_parcela = saldo_inicial + correcao_tr
            
            tabela_simulacao.append({
                "Mês": mes,
                "Saldo Inicial (R$)": round(saldo_inicial, 2),
                "Correção TR (R$)": round(correcao_tr, 2),
                "Parcela Paga (R$)": round(valor_parcela, 2),
                "Saldo Final (R$)": round(saldo_final, 2)
            })
            
            saldo_inicial = saldo_final
            
            if saldo_inicial <= 0:
                break
                
        df_simulacao = pd.DataFrame(tabela_simulacao)
        st.markdown(f"### Projeção para {len(df_simulacao)} meses")
        st.dataframe(df_simulacao, use_container_width=True, hide_index=True)
        
        # Gráfico do decréscimo do saldo
        fig2 = px.line(df_simulacao, x='Mês', y='Saldo Final (R$)', title="Evolução do Saldo Devedor ao Longo da Obra", markers=True)
        st.plotly_chart(fig2, use_container_width=True)