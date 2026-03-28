import streamlit as st
import json
import os
from datetime import datetime
from github import Github

# ─────────────────────────────────────────────
# CONFIGURAÇÃO — lê as credenciais do GitHub
# ─────────────────────────────────────────────
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME    = st.secrets["REPO_NAME"]      # ex: "seu-usuario/gerenciador-tarefas"
FILE_PATH    = "tasks.json"

PESSOAS = ["Eu", "Meu Amigo"]

# ─────────────────────────────────────────────
# FUNÇÕES DE PERSISTÊNCIA (lê/salva no GitHub)
# ─────────────────────────────────────────────
def get_repo():
    g = Github(GITHUB_TOKEN)
    return g.get_repo(REPO_NAME)

def load_tasks():
    """Carrega as tarefas do tasks.json no GitHub."""
    try:
        repo = get_repo()
        contents = repo.get_contents(FILE_PATH)
        return json.loads(contents.decoded_content.decode("utf-8"))
    except Exception as e:
        st.error(f"Erro ao carregar tarefas: {e}")
        return []

def save_tasks(tasks):
    """Salva as tarefas no tasks.json no GitHub."""
    try:
        repo = get_repo()
        contents = repo.get_contents(FILE_PATH)
        repo.update_file(
            path=FILE_PATH,
            message=f"Atualização de tarefas — {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            content=json.dumps(tasks, ensure_ascii=False, indent=2),
            sha=contents.sha
        )
        return True
    except Exception as e:
        st.error(f"Erro ao salvar tarefas: {e}")
        return False

# ─────────────────────────────────────────────
# INTERFACE
# ─────────────────────────────────────────────
st.set_page_config(page_title="Tarefas Compartilhadas", page_icon="✅", layout="centered")
st.title("✅ Gerenciador de Tarefas")
st.caption("Compartilhado entre duas pessoas — atualiza em tempo real.")

# Carrega tarefas
tasks = load_tasks()

# ── Formulário: adicionar tarefa ─────────────
st.divider()
st.subheader("➕ Nova Tarefa")

with st.form("nova_tarefa", clear_on_submit=True):
    descricao = st.text_input("Descrição da tarefa", placeholder="Ex: Comprar mantimentos")
    responsavel = st.selectbox("Atribuir para", PESSOAS)
    submitted = st.form_submit_button("Adicionar")

    if submitted:
        if descricao.strip():
            nova = {
                "id": int(datetime.now().timestamp() * 1000),
                "descricao": descricao.strip(),
                "responsavel": responsavel,
                "concluida": False,
                "criada_em": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            tasks.append(nova)
            if save_tasks(tasks):
                st.success("Tarefa adicionada!")
                st.rerun()
        else:
            st.warning("Digite uma descrição para a tarefa.")

# ── Filtro por pessoa ─────────────────────────
st.divider()
st.subheader("📋 Tarefas Pendentes")

filtro = st.radio("Filtrar por responsável", ["Todos"] + PESSOAS, horizontal=True)

pendentes = [t for t in tasks if not t["concluida"]]
if filtro != "Todos":
    pendentes = [t for t in pendentes if t["responsavel"] == filtro]

if not pendentes:
    st.info("Nenhuma tarefa pendente. 🎉")
else:
    for tarefa in pendentes:
        col1, col2, col3 = st.columns([0.08, 0.72, 0.20])
        with col1:
            concluir = st.checkbox("", key=f"check_{tarefa['id']}")
        with col2:
            st.markdown(f"**{tarefa['descricao']}**  \n"
                        f"👤 `{tarefa['responsavel']}` · 🕐 {tarefa['criada_em']}")
        with col3:
            if concluir:
                for t in tasks:
                    if t["id"] == tarefa["id"]:
                        t["concluida"] = True
                if save_tasks(tasks):
                    st.rerun()

# ── Tarefas concluídas ────────────────────────
concluidas = [t for t in tasks if t["concluida"]]
if concluidas:
    st.divider()
    with st.expander(f"✔️ Concluídas ({len(concluidas)})"):
        for tarefa in concluidas:
            col1, col2, col3 = st.columns([0.72, 0.20, 0.08])
            with col1:
                st.markdown(f"~~{tarefa['descricao']}~~ · 👤 `{tarefa['responsavel']}`")
            with col3:
                if st.button("🗑️", key=f"del_{tarefa['id']}", help="Remover"):
                    tasks = [t for t in tasks if t["id"] != tarefa["id"]]
                    if save_tasks(tasks):
                        st.rerun()