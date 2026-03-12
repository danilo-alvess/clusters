import re
import unicodedata
from difflib import get_close_matches
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Respostas por Cluster", page_icon="🧩", layout="wide")


# =========================
# Helpers
# =========================
def load_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file)
        except Exception:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding="latin-1")
    if name.endswith(".xlsx") or name.endswith(".xls"):
        uploaded_file.seek(0)
        return pd.read_excel(uploaded_file)
    raise ValueError("Formato não suportado. Envie CSV ou Excel.")


def normalize_text(value: Optional[str]) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )
    text = text.replace("_", " ")
    text = re.sub(r"\s*-\s*", " - ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def padronizar_linha(texto: Optional[str]) -> str:
    s = normalize_text(texto)
    if not s:
        return ""

    substituicoes = {
        "camossim": "camocim",
        "juazeiro do norte": "juazeiro",
        "jeri": "jijoca de jericoacoara",
        "croata": "croata da serra",
        "vicosa": "vicosa do ceara",
        "solonopolo": "solonopole",
        "camina grande": "campina grande",
        "fortalexa": "fortaleza",
    }
    for origem, destino in substituicoes.items():
        s = s.replace(origem, destino)

    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("- fortaleza", " - fortaleza")
    s = s.replace("fortaleza-", "fortaleza - ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def encontrar_coluna_linha(df: pd.DataFrame, preferida: str = "") -> Optional[str]:
    if preferida and preferida in df.columns:
        return preferida
    for col in df.columns:
        col_norm = normalize_text(col)
        if "qual linha" in col_norm or col_norm == "linha" or "linha" in col_norm:
            return col
    return None


def aplicar_correspondencia(
    df_pesquisa: pd.DataFrame,
    df_cluster: pd.DataFrame,
    pesquisa_col: str,
    cluster_col: str,
) -> pd.DataFrame:
    base = df_pesquisa.copy()
    cluster = df_cluster.copy()

    base["linha_original"] = base[pesquisa_col].astype(str)
    base["linha_norm"] = base[pesquisa_col].apply(padronizar_linha)

    cluster["linha_cluster_original"] = cluster[cluster_col].astype(str)
    cluster["linha_norm"] = cluster[cluster_col].apply(padronizar_linha)

    mapa_cluster = cluster.drop_duplicates(subset=["linha_norm"])[
        ["linha_norm", cluster_col, "Categoria", "Cluster"]
    ].copy()
    mapa_cluster = mapa_cluster.rename(columns={cluster_col: "Linha_cluster"})

    merged = base.merge(mapa_cluster, on="linha_norm", how="left")

    opcoes = mapa_cluster["linha_norm"].dropna().unique().tolist()
    faltantes = merged[merged["Cluster"].isna() & merged["linha_norm"].ne("")].copy()

    sugestoes = {}
    for linha in faltantes["linha_norm"].dropna().unique():
        match = get_close_matches(linha, opcoes, n=1, cutoff=0.82)
        sugestoes[linha] = match[0] if match else None

    merged["linha_norm_sugerida"] = merged["linha_norm"].map(sugestoes)

    mapa_aux = mapa_cluster.rename(
        columns={
            "linha_norm": "linha_norm_sugerida",
            "Linha_cluster": "Linha_cluster_sugerida",
            "Categoria": "Categoria_sugerida",
            "Cluster": "Cluster_sugerido",
        }
    )

    merged = merged.merge(
        mapa_aux[
            [
                "linha_norm_sugerida",
                "Linha_cluster_sugerida",
                "Categoria_sugerida",
                "Cluster_sugerido",
            ]
        ],
        on="linha_norm_sugerida",
        how="left",
    )

    merged["Linha_final"] = merged["Linha_cluster"]
    merged["Categoria_final"] = merged["Categoria"]
    merged["Cluster_final"] = merged["Cluster"]
    merged["Tipo_match"] = "Exato"

    mask_sugerido = merged["Cluster_final"].isna() & merged["Cluster_sugerido"].notna()
    merged.loc[mask_sugerido, "Linha_final"] = merged.loc[mask_sugerido, "Linha_cluster_sugerida"]
    merged.loc[mask_sugerido, "Categoria_final"] = merged.loc[mask_sugerido, "Categoria_sugerida"]
    merged.loc[mask_sugerido, "Cluster_final"] = merged.loc[mask_sugerido, "Cluster_sugerido"]
    merged.loc[mask_sugerido, "Tipo_match"] = "Aproximado"

    mask_sem = merged["Cluster_final"].isna()
    merged.loc[mask_sem, "Tipo_match"] = "Sem correspondência"

    return merged


# =========================
# App
# =========================
st.title("🧩 Respostas por Cluster")
st.write("Faça upload dos arquivos na barra lateral para calcular a quantidade de respostas por cluster.")

st.sidebar.header("Arquivos")
upload_pesquisa = st.sidebar.file_uploader(
    "Dataset de pesquisa", type=["csv", "xlsx", "xls"], key="pesquisa"
)
upload_cluster = st.sidebar.file_uploader(
    "Planilha de clusterização", type=["csv", "xlsx", "xls"], key="cluster"
)

st.sidebar.markdown("---")
usar_match_aproximado = st.sidebar.checkbox("Usar correspondência aproximada", value=True)

if upload_pesquisa is None or upload_cluster is None:
    st.warning("Envie os dois arquivos para continuar.")
    st.stop()

try:
    df_pesquisa = load_file(upload_pesquisa)
    df_cluster = load_file(upload_cluster)
except Exception as e:
    st.error(f"Erro ao carregar arquivos: {e}")
    st.stop()

col_pesquisa = encontrar_coluna_linha(df_pesquisa)
col_cluster = encontrar_coluna_linha(df_cluster)

if not col_pesquisa:
    st.error("Não encontrei automaticamente a coluna de linha no dataset de pesquisa.")
    st.write("Colunas encontradas no dataset de pesquisa:", list(df_pesquisa.columns))
    st.stop()

if not col_cluster:
    st.error("Não encontrei automaticamente a coluna de linha na planilha de clusterização.")
    st.write("Colunas encontradas na planilha de clusterização:", list(df_cluster.columns))
    st.stop()

if "Categoria" not in df_cluster.columns or "Cluster" not in df_cluster.columns:
    st.error("A planilha de clusterização precisa ter as colunas 'Linha', 'Categoria' e 'Cluster'.")
    st.write("Colunas encontradas na planilha de clusterização:", list(df_cluster.columns))
    st.stop()

resultado = aplicar_correspondencia(df_pesquisa, df_cluster, col_pesquisa, col_cluster)

if not usar_match_aproximado:
    resultado.loc[
        resultado["Tipo_match"] == "Aproximado",
        ["Linha_final", "Categoria_final", "Cluster_final"],
    ] = pd.NA
    resultado.loc[resultado["Tipo_match"] == "Aproximado", "Tipo_match"] = "Sem correspondência"

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total de respostas", len(resultado))
with c2:
    st.metric("Com cluster atribuído", int(resultado["Cluster_final"].notna().sum()))
with c3:
    pct = resultado["Cluster_final"].notna().mean() * 100 if len(resultado) else 0
    st.metric("Cobertura", f"{pct:.1f}%")
with c4:
    st.metric("Sem correspondência", int(resultado["Cluster_final"].isna().sum()))

st.markdown("---")

cluster_count = (
    resultado.dropna(subset=["Cluster_final"])
    .groupby(["Cluster_final", "Categoria_final"], dropna=False)
    .size()
    .reset_index(name="Quantidade de respostas")
    .sort_values(["Cluster_final", "Quantidade de respostas"], ascending=[True, False])
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Quantidade de respostas por cluster")
    if not cluster_count.empty:
        resumo_cluster = (
            resultado.dropna(subset=["Cluster_final"])
            .groupby("Cluster_final")
            .size()
            .reset_index(name="Quantidade de respostas")
        )
        fig = px.bar(
            resumo_cluster,
            x="Cluster_final",
            y="Quantidade de respostas",
            text="Quantidade de respostas",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(resumo_cluster, use_container_width=True)
    else:
        st.warning("Nenhuma resposta foi associada a cluster.")

with col2:
    st.subheader("Quantidade por cluster e categoria")
    if not cluster_count.empty:
        fig2 = px.bar(
            cluster_count,
            x="Cluster_final",
            y="Quantidade de respostas",
            color="Categoria_final",
            barmode="group",
            text="Quantidade de respostas",
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(cluster_count, use_container_width=True)
    else:
        st.warning("Sem dados para exibir.")

st.markdown("---")

linha_count = (
    resultado.dropna(subset=["Cluster_final"])
    .groupby(["Cluster_final", "Linha_final"], dropna=False)
    .size()
    .reset_index(name="Quantidade de respostas")
    .sort_values("Quantidade de respostas", ascending=False)
)

st.subheader("Linhas associadas e seus clusters")
st.dataframe(linha_count, use_container_width=True)

st.subheader("Diagnóstico de correspondência")
diag = resultado["Tipo_match"].value_counts(dropna=False).reset_index()
diag.columns = ["Tipo de match", "Quantidade"]
fig3 = px.pie(diag, names="Tipo de match", values="Quantidade")
st.plotly_chart(fig3, use_container_width=True)
st.dataframe(diag, use_container_width=True)

sem_match = (
    resultado[resultado["Cluster_final"].isna()][["linha_original", "linha_norm"]]
    .drop_duplicates()
    .sort_values("linha_original")
)
if not sem_match.empty:
    st.subheader("Linhas sem correspondência")
    st.dataframe(sem_match, use_container_width=True)

st.subheader("Base final")
st.dataframe(
    resultado[
        ["linha_original", "linha_norm", "Linha_final", "Categoria_final", "Cluster_final", "Tipo_match"]
    ],
    use_container_width=True,
)

csv_saida = resultado.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="Baixar base com cluster atribuído",
    data=csv_saida,
    file_name="respostas_com_cluster.csv",
    mime="text/csv",
)