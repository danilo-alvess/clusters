import io
import re
import unicodedata
from difflib import get_close_matches
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Respostas por Cluster", page_icon="🧩", layout="wide")

# Cronograma embutido no código
CRONOGRAMA_CSV = """Coluna 1,Linha,Origem e Destino Linha,Via,Classe Conforto,Previsão de Chegada,Serviço,Hora,SEG,TER,QUA,QUI,SEX,SÁB,DOM,Volume Total de Chegada,Rótulos de Linha,Contagem de Linha
Ordinário,100736,Sao Luis - Fortaleza,Parnaíba,Leito,02:50:00,10406480,08:30,1,1,1,1,1,1,1,7,2,1
Ordinário,100290,Juazeiro do Norte - Fortaleza,Penaforte,Executivo/Leito,03:18:58,10101940,17:00,1,1,1,1,1,1,1,7,3,4
Ordinário,100244,Vicosa do Ceara - Fortaleza,Tianguá,Executivo,03:30:56,10201570,21:00,1,1,1,1,1,1,1,7,4,6
Ordinário,100568,Jijoca de Jericoacoara - Fortaleza,Itarema,Executivo/Leito,03:37:31,10205120,22:15,1,1,1,1,1,1,1,7,5,5
Ordinário,100256,Croata da Serra - Fortaleza,Tianguá,Executivo,03:46:24,10201460,20:00,1,1,1,1,1,1,1,7,6,9
Ordinário,100248,Sao Benedito - Fortaleza,Tianguá,Executivo,04:11:37,10201520,21:30,-,-,-,-,1,-,1,2,7,7
Ordinário,100286,Crato - Fortaleza,Ipaumirim,Executivo/Leito,04:16:55,10205000,17:30,1,1,1,1,1,-,1,6,8,9
Ordinário,100326,Chaval - Fortaleza,Martinópole,Executivo/Leito,04:27:02,10102850,21:00,1,1,1,1,1,1,1,7,9,4
Ordinário,100298,Camocim - Fortaleza,Martinópole,Executivo,04:32:09,10202870,22:00,-,-,-,-,1,-,1,2,10,4
Ordinário,100278,Juazeiro do Norte - Fortaleza,Iguatu,Executivo/Leito,04:33:28,10207550,18:30,1,1,1,1,1,1,1,7,11,7
Ordinário,100266,Catarina - Fortaleza,Iguatu,Executivo,04:37:36,10205630,21:00,-,-,-,-,-,-,-,0,12,6
Ordinário,100274,Juazeiro do Norte - Fortaleza,Cedro,Executivo,05:02:46,10201840,18:45,1,1,1,1,1,-,1,6,13,9
Ordinário,100276,Campos Sales - Fortaleza,Iguatu,Executivo,05:08:58,10205440,19:00,1,1,1,1,1,1,1,7,14,3
Ordinário,100354,Juazeiro do Norte - Fortaleza,Icó,Executivo/Leito,05:28:32,10203130,19:00,1,1,1,1,1,1,1,7,15,3
Ordinário,100282,Juazeiro do Norte - Fortaleza,Iguatu,Executivo/Leito,05:33:28,10205870,19:30,1,1,1,1,1,1,1,7,16,7
Ordinário,100676,Natal - Fortaleza,Mossoró,Leito,05:53:12,10406790,20:30,1,1,1,1,1,1,1,7,17,6
Ordinário,100286,Crato - Fortaleza,Aurora,Executivo/Leito,06:16:55,10205010,19:30,1,1,1,1,1,-,1,6,18,7
Ordinário,100682,Parnaiba - Fortaleza,Parnaíba,Semileito,06:17:36,10306200,19:00,1,1,1,1,1,-,1,6,19,7
Ordinário,100706,Teresina - Fortaleza,Teresina,Semileito/Leito,06:19:48,10306910,19:00,1,1,1,1,1,1,1,7,20,3
Ordinário,100676,Natal - Fortaleza,Mossoró,Semileito/Leito,06:23:12,10306770,21:00,1,1,1,1,1,1,1,7,21,7
Ordinário,100282,Juazeiro do Norte - Fortaleza,Iguatu,Leito,06:33:28,10401880,20:30,1,1,1,1,1,1,1,7,22,5
Ordinário,100598,Santana do Cariri - Fortaleza,Icó,Executivo,06:40:02,10105230,19:00,-,-,-,-,1,-,-,1,23,3
Ordinário,100849,Sao Paulo - Fortaleza,Floriano,Semileito,06:44:42,10307575,15:00,-,1,-,-,-,1,-,2,Total Geral,122
Ordinário,100668,Parnaiba - Fortaleza,Parnaíba,Leito,06:45:48,10406130,22:00,1,1,1,1,1,1,1,7,,
Ordinário,100690,Sao Luis - Fortaleza,CE 085,Executivo,06:55:18,10206240,14:00,-,-,-,-,1,-,1,2,,
Ordinário,100706,Teresina - Fortaleza,Teresina,Cama/Leito,07:19:48,10506920,20:00,1,1,1,1,1,1,1,7,,
Ordinário,100676,Natal - Fortaleza,Mossoró,Cama/Leito,07:23:12,10506810,22:00,1,1,1,1,1,1,1,7,,
Ordinário,100282,Juazeiro do Norte - Fortaleza,Iguatu,Cama/Leito,07:33:28,10507480,21:30,1,1,1,1,1,1,1,7,,
Ordinário,100702,Patos - Fortaleza,Paraíba,Semileito/Leito,07:44:48,10306300,19:30,-,1,1,1,1,-,1,5,,
Ordinário,100702,Patos - Fortaleza,Paraíba,Semileito/Leito,07:44:48,10307190,19:30,1,-,-,-,-,-,-,1,,
Ordinário,100818,Joao Pessoa - Fortaleza,Mossoró,Leito,07:45:54,10407350,19:30,1,1,1,1,1,1,1,7,,
Ordinário,100666,Campina Grande - Fortaleza,Patos,Leito,07:58:42,10406120,17:00,-,-,-,-,-,1,-,1,,
Ordinário,100708,Sao Luis - Fortaleza,Teresina,Leito,08:02:36,10406330,12:30,1,1,1,1,1,1,1,7,,
Ordinário,100282,Juazeiro do Norte - Fortaleza,Iguatu,Executivo/Leito,08:03:28,10201860,22:00,1,1,1,1,1,1,1,7,,
Ordinário,100706,Teresina - Fortaleza,Teresina,Leito,08:19:48,10406960,21:00,1,-,-,1,1,1,1,5,,
Ordinário,100676,Natal - Fortaleza,Mossoró,Semileito,08:23:12,10306800,23:00,1,1,1,1,1,1,1,7,,
Ordinário,100684,Caruaru - Fortaleza,Pernambuco,Executivo,08:30:48,10206210,15:30,1,-,-,-,-,-,-,1,,
Ordinário,100282,Juazeiro do Norte - Fortaleza,Iguatu,Leito,08:33:28,10403120,22:30,1,1,1,1,1,1,1,7,,
Ordinário,100230,Sobral - Fortaleza,Itapajé,Executivo,08:44:39,10101610,04:30,1,1,1,1,1,1,-,6,,
Ordinário,100688,Campina Grande - Fortaleza,Joao Pessoa,Leito,08:49:54,10406230,18:00,1,1,1,1,1,-,1,6,,
Ordinário,100779,Belém - Fortaleza,Teresina,Semileito/Leito,08:55:30,10306715,05:20,1,1,1,1,1,1,1,7,,
Ordinário,100282,Juazeiro do Norte - Fortaleza,Iguatu,Executivo/Leito,09:03:28,10205390,23:00,1,1,1,1,1,1,1,7,,
Ordinário,100404,Amontada - Fortaleza,Itapipoca,Executivo,09:07:01,10103630,06:00,1,1,1,1,1,1,-,6,,
Ordinário,100704,Recife - Fortaleza,Pernambuco,Leito,09:13:00,10406880,18:00,1,1,1,1,1,1,1,7,,
Ordinário,100706,Teresina - Fortaleza,Teresina,Semileito/Leito,09:19:48,10306930,22:00,1,1,1,1,1,1,1,7,,
Ordinário,100388,Sobral - Fortaleza,Itapipoca,Executivo,10:21:54,10103440,05:15,1,1,1,1,1,1,1,7,,
Ordinário,100692,Caruaru - Fortaleza,Pernambuco,Leito,10:27:12,10406250,17:00,1,1,1,1,1,1,1,7,,
Ordinário,100236,Massape - Fortaleza,Itapajé,Executivo,10:36:32,10101710,06:00,1,1,1,1,1,1,1,7,,
Ordinário,100704,Recife - Fortaleza,Pernambuco,Cama/Leito,10:43:00,10506890,19:30,1,1,1,1,1,1,1,7,,
Ordinário,100717,Salvador - Fortaleza,Aracaju,Leito,11:11:36,10406985,08:30,1,1,1,1,1,1,1,7,,
Ordinário,100704,Recife - Fortaleza,Pernambuco,Leito,11:13:00,10406870,20:00,1,1,1,1,1,1,1,7,,
Ordinário,100232,Sobral - Fortaleza,Itapajé,Executivo/Leito,11:14:39,10201580,07:00,1,1,1,1,1,1,1,7,,
Ordinário,100468,Pedra Branca - Fortaleza,Quixeramobim,Executivo,11:23:57,10104280,06:00,1,1,1,1,1,1,-,6,,
Ordinário,100608,Jijoca de Jericoacoara - Fortaleza,Bela Cruz,Executivo/Leito,11:26:38,10205430,06:15,1,1,1,1,1,1,1,7,,
Ordinário,100396,Prea - Fortaleza,Bela Cruz,Executivo,11:45:49,10103340,06:30,1,1,1,1,1,-,-,5,,
Ordinário,100410,Jijoca de Jericoacoara - Fortaleza,Itarema,Executivo,11:54:17,10103780,06:30,1,1,1,1,1,1,1,7,,
Ordinário,100466,Solonópole - Fortaleza,Milhã,Executivo,12:06:44,10204430,06:00,1,1,1,1,1,1,-,6,,
Ordinário,100704,Recife - Fortaleza,Pernambuco,Semileito/Leito,12:13:00,10306860,21:00,1,1,1,1,1,1,1,7,,
Ordinário,100230,Sobral - Fortaleza,Itapajé,Executivo,12:14:39,10101620,08:00,1,1,1,1,1,1,1,7,,
Ordinário,100712,Maceio - Fortaleza,Pernambuco,Semileito/Leito,12:16:06,10306360,17:00,1,1,1,1,1,1,1,7,,
Ordinário,100234,Camocim - Fortaleza,Martinópole,Executivo,12:32:09,10101410,06:00,1,1,1,1,1,1,1,7,,
Ordinário,100759,Marabá - Fortaleza,Marabá,Semileito/Leito,12:52:30,10306615,08:00,1,1,1,1,1,1,1,7,,
Ordinário,100574,Sao Benedito - Fortaleza,Reriutaba,Executivo,13:01:53,10104990,05:30,1,1,1,1,1,1,1,7,,
Ordinário,100466,Solonópole - Fortaleza,Milhã,Executivo,13:06:44,10204440,07:00,-,-,-,-,-,-,1,1,,
Ordinário,100404,Amontada - Fortaleza,Itapipoca,Executivo,13:07:01,10104390,10:00,1,-,-,-,1,1,1,4,,
Ordinário,100256,Croata da Serra - Fortaleza,Tianguá,Executivo,13:16:24,10101460,05:30,1,1,1,1,1,1,1,7,,
Ordinário,100302,Iguatu - Fortaleza,Quixelo,Executivo,13:33:13,10102690,06:45,1,-,-,1,1,1,-,4,,
Ordinário,100382,Camocim - Fortaleza,Itarema,Executivo,13:37:19,10205830,07:00,1,1,1,1,1,1,1,7,,
Ordinário,100721,Salvador - Fortaleza,Petrolina,Leito,13:43:54,10406975,13:00,1,1,1,1,1,1,1,7,,
Ordinário,100230,Sobral - Fortaleza,Itapajé,Executivo,13:44:39,10101640,09:30,1,1,1,1,1,1,1,7,,
Ordinário,100262,Iguatu - Fortaleza,Icó,Executivo,13:59:16,10101770,06:00,1,1,1,1,1,1,1,7,,
Ordinário,100270,Iguatu - Fortaleza,Mombaça,Executivo,14:15:36,10203730,07:00,1,1,1,1,1,1,1,7,,
Ordinário,100324,Catarina - Fortaleza,Piquet Carneiro,Executivo,14:20:07,10102840,07:00,1,1,1,1,1,1,1,7,,
Ordinário,100708,Sao Luis - Fortaleza,Teresina,Executivo,14:32:36,10206940,19:00,1,-,-,-,1,-,1,3,,
Ordinário,100240,Chaval - Fortaleza,Coreaú,Executivo/Leito,15:14:14,10101440,07:00,1,1,1,1,1,1,1,7,,
Ordinário,100242,Vicosa do Ceara - Fortaleza,Tianguá,Executivo,15:30:56,10101540,09:00,1,1,1,1,1,1,1,7,,
Ordinário,100306,Iguatu - Fortaleza,Dep Irapuan Pinheiro,Executivo,15:40:01,10105080,08:00,1,1,1,1,1,1,-,6,,
Ordinário,100662,Parnaiba - Fortaleza,Parnaíba,Leito,16:01:54,10406100,07:15,1,1,1,1,1,1,1,7,,
Ordinário,100404,Amontada - Fortaleza,Itapipoca,Executivo,16:07:01,10104350,13:00,1,1,1,1,1,1,1,7,,
Ordinário,100246,Sao Benedito - Fortaleza,Tianguá,Executivo,16:11:37,10101500,09:30,1,1,1,1,1,1,1,7,,
Ordinário,100272,Juazeiro do Norte - Fortaleza,Cedro,Executivo,16:17:46,10102790,06:00,1,1,1,1,1,1,1,7,,
Ordinário,100763,Goiania - Fortaleza,Petrolina,Semileito,16:28:18,10306635,14:00,1,-,1,-,1,-,-,3,,
Ordinário,100276,Campos Sales - Fortaleza,Iguatu,Executivo,16:38:58,10104010,06:30,1,1,1,1,1,1,1,7,,
Ordinário,100396,Prea - Fortaleza,Bela Cruz,Executivo,16:45:49,10103570,11:30,-,-,-,-,-,-,1,1,,
Ordinário,100282,Juazeiro do Norte - Fortaleza,Iguatu,Executivo/Leito,17:03:28,10201910,07:00,-,-,-,-,-,-,-,0,,
Ordinário,100278,Juazeiro do Norte - Fortaleza,Iguatu,Executivo/Leito,17:03:28,10207530,07:00,1,1,1,1,1,1,1,7,,
Ordinário,100344,Crato - Fortaleza,Ipaumirim,Executivo,17:04:57,10103100,06:00,1,1,1,1,1,1,1,7,,
Ordinário,100232,Sobral - Fortaleza,Itapajé,Executivo/Leito,17:14:39,10201590,13:00,1,1,1,1,1,1,1,7,,
Ordinário,100739,Goiania - Fortaleza,Petrolina,Semileito,17:21:06,10306505,14:00,-,1,-,1,-,1,1,4,,
Ordinário,100468,Pedra Branca - Fortaleza,Quixeramobim,Executivo,17:53:57,10105410,12:30,-,-,-,-,-,-,1,1,,
Ordinário,100568,Jijoca de Jericoacoara - Fortaleza,Itarema,Executivo/Leito,18:22:31,10205110,13:00,-,-,-,-,-,-,-,0,,
Ordinário,100568,Jijoca de Jericoacoara - Fortaleza,Itarema,Executivo/Leito,18:22:31,10207590,13:00,1,1,1,1,1,1,1,7,,
Ordinário,100676,Natal - Fortaleza,Mossoró,Leito,18:23:12,10406780,09:00,1,1,1,1,1,1,1,7,,
Ordinário,100380,Camocim - Fortaleza,Itarema,Executivo,18:25:08,10103390,11:30,1,1,1,1,1,1,1,7,,
Ordinário,100242,Vicosa do Ceara - Fortaleza,Tianguá,Executivo,18:30:56,10101550,12:00,1,1,1,1,1,1,1,7,,
Ordinário,100278,Juazeiro do Norte - Fortaleza,Iguatu,Executivo,18:33:28,10104060,08:30,1,1,1,1,1,1,1,7,,
Ordinário,100384,Jijoca de Jericoacoara - Fortaleza,Bela Cruz,Executivo,18:42:50,10104960,13:30,1,1,1,1,1,1,1,7,,
Ordinário,100466,Solonópole - Fortaleza,Milhã,Executivo,19:06:44,10104270,13:00,1,1,1,1,1,1,1,7,,
Ordinário,100388,Sobral - Fortaleza,Itapipoca,Executivo,19:06:54,10203450,14:00,1,1,1,1,1,1,1,7,,
Ordinário,100230,Sobral - Fortaleza,Itapajé,Executivo,19:14:39,10101660,15:00,1,1,1,1,1,-,1,6,,
Ordinário,100264,Juazeiro do Norte - Fortaleza,Orós,Executivo,19:18:04,10102800,09:30,1,1,1,1,1,1,1,7,,
Ordinário,100234,Camocim - Fortaleza,Martinópole,Executivo,19:32:09,10103700,13:00,1,1,1,1,1,1,1,7,,
Ordinário,100302,Iguatu - Fortaleza,Quixelo,Executivo,19:48:13,10102280,13:00,-,-,-,-,-,-,1,1,,
Ordinário,100706,Teresina - Fortaleza,Teresina,Semileito/Leito,19:49:48,10206320,08:30,1,1,1,1,1,1,1,7,,
Ordinário,100278,Juazeiro do Norte - Fortaleza,Iguatu,Executivo/Leito,20:03:28,10204060,10:00,1,1,1,1,1,1,1,7,,
Ordinário,100404,Amontada - Fortaleza,Itapipoca,Executivo,20:37:01,10204400,17:30,1,1,1,1,1,-,1,6,,
Ordinário,100412,Camocim - Fortaleza,Bela Cruz,Executivo,20:42:10,10104340,14:00,-,-,-,-,1,-,1,2,,
Ordinário,100334,Sao Benedito - Fortaleza,Reriutaba,Executivo,21:06:15,10102970,14:00,1,1,1,1,1,1,1,7,,
Ordinário,100306,Iguatu - Fortaleza,Dep Irapuan Pinheiro,Executivo,21:10:01,10102710,13:30,-,-,-,-,-,-,1,1,,
Ordinário,100664,Parnaiba - Fortaleza,Parnaíba,Executivo,21:14:24,10206110,12:00,1,1,1,1,1,1,1,7,,
Ordinário,100232,Sobral - Fortaleza,Itapajé,Executivo,21:14:39,10201690,17:00,1,-,-,1,1,-,1,4,,
Ordinário,100676,Natal - Fortaleza,Mossoró,Semileito/Leito,21:23:12,10306170,12:00,1,1,1,1,1,1,1,7,,
Ordinário,100268,Iguatu - Fortaleza,Mombaça,Executivo,21:45:36,10101750,14:30,1,1,1,1,1,1,1,7,,
Ordinário,100390,Sobral - Fortaleza,Miraíma,Executivo,21:48:43,10103430,17:30,-,-,-,-,1,-,1,2,,
Ordinário,100230,Sobral - Fortaleza,Itapajé,Executivo,22:14:39,10101680,18:00,1,-,-,1,1,-,1,4,,
Ordinário,100238,Camocim - Fortaleza,Coreaú,Executivo,22:18:01,10101400,15:00,-,-,-,-,1,-,1,2,,
Ordinário,100354,Juazeiro do Norte - Fortaleza,Icó,Executivo/Leito,22:28:32,10203860,12:00,1,1,1,1,1,1,1,7,,
Ordinário,100382,Camocim - Fortaleza,Itarema,Executivo,22:37:19,10205600,16:00,1,1,1,1,1,1,1,7,,
Ordinário,100704,Recife - Fortaleza,Pernambuco,Semileito/Leito,22:43:00,10307040,07:30,1,1,1,1,1,1,1,7,,
Ordinário,100232,Sobral - Fortaleza,Itapajé,Executivo/Leito,23:14:39,10201600,19:00,1,1,1,1,1,1,1,7,,
Ordinário,100278,Juazeiro do Norte - Fortaleza,Iguatu,Executivo/Leito,23:18:28,10207540,13:15,1,1,1,1,1,1,1,7,,
Ordinário,100246,Sao Benedito - Fortaleza,Tianguá,Executivo,23:41:37,10101510,17:00,1,1,1,1,1,1,1,7,,"""


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


@st.cache_data
def load_default_cronograma() -> pd.DataFrame:
    return pd.read_csv(io.StringIO(CRONOGRAMA_CSV))


def normalize_text(value: Optional[str]) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
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


def encontrar_coluna_timestamp(df: pd.DataFrame) -> Optional[str]:
    for col in df.columns:
        c = normalize_text(col)
        if "carimbo de data" in c or ("data" in c and "hora" in c) or c == "timestamp":
            return col
    return None


def aplicar_correspondencia(df_pesquisa: pd.DataFrame, df_cluster: pd.DataFrame, pesquisa_col: str, cluster_col: str) -> pd.DataFrame:
    base = df_pesquisa.copy().reset_index(drop=True)
    base["_row_id"] = base.index
    cluster = df_cluster.copy()

    base["linha_original"] = base[pesquisa_col].astype(str)
    base["linha_norm"] = base[pesquisa_col].apply(padronizar_linha)

    cluster["linha_cluster_original"] = cluster[cluster_col].astype(str)
    cluster["linha_norm"] = cluster[cluster_col].apply(padronizar_linha)

    mapa_cluster = cluster.drop_duplicates(subset=["linha_norm"])[["linha_norm", cluster_col, "Categoria", "Cluster"]].copy()
    mapa_cluster = mapa_cluster.rename(columns={cluster_col: "Linha_cluster"})

    merged = base.merge(mapa_cluster, on="linha_norm", how="left")

    opcoes = mapa_cluster["linha_norm"].dropna().unique().tolist()
    faltantes = merged[merged["Cluster"].isna() & merged["linha_norm"].ne("")].copy()

    sugestoes = {}
    for linha in faltantes["linha_norm"].dropna().unique():
        match = get_close_matches(linha, opcoes, n=1, cutoff=0.82)
        sugestoes[linha] = match[0] if match else None

    merged["linha_norm_sugerida"] = merged["linha_norm"].map(sugestoes)

    mapa_aux = mapa_cluster.rename(columns={
        "linha_norm": "linha_norm_sugerida",
        "Linha_cluster": "Linha_cluster_sugerida",
        "Categoria": "Categoria_sugerida",
        "Cluster": "Cluster_sugerido",
    })

    merged = merged.merge(
        mapa_aux[["linha_norm_sugerida", "Linha_cluster_sugerida", "Categoria_sugerida", "Cluster_sugerido"]],
        on="linha_norm_sugerida",
        how="left",
    )

    merged["Linha_final"] = merged["Linha_cluster"]
    merged["Categoria_final"] = merged["Categoria"]
    merged["Cluster_final"] = merged["Cluster"]
    merged["Tipo_match"] = "Exato"
    merged["codigo_erro"] = ""
    merged["motivo_erro"] = ""

    mask_sugerido = merged["Cluster_final"].isna() & merged["Cluster_sugerido"].notna()
    merged.loc[mask_sugerido, "Linha_final"] = merged.loc[mask_sugerido, "Linha_cluster_sugerida"]
    merged.loc[mask_sugerido, "Categoria_final"] = merged.loc[mask_sugerido, "Categoria_sugerida"]
    merged.loc[mask_sugerido, "Cluster_final"] = merged.loc[mask_sugerido, "Cluster_sugerido"]
    merged.loc[mask_sugerido, "Tipo_match"] = "Aproximado"

    mask_sem = merged["Cluster_final"].isna()
    merged.loc[mask_sem, "Tipo_match"] = "Sem correspondência"

    mask_linha_vazia = merged["linha_norm"].fillna("").eq("")
    merged.loc[mask_linha_vazia, "codigo_erro"] = "SEM_LINHA"
    merged.loc[mask_linha_vazia, "motivo_erro"] = "A resposta não possui valor preenchido para a linha."

    mask_match_aprox_existia = (
        merged["Tipo_match"].eq("Sem correspondência")
        & merged["linha_norm"].fillna("").ne("")
        & merged["linha_norm_sugerida"].notna()
    )
    merged.loc[mask_match_aprox_existia, "codigo_erro"] = "MATCH_NAO_APLICADO"
    merged.loc[mask_match_aprox_existia, "motivo_erro"] = "Existe uma sugestão aproximada de linha, mas ela não foi aplicada como correspondência final."

    mask_texto_sem_mapa = (
        merged["Tipo_match"].eq("Sem correspondência")
        & merged["linha_norm"].fillna("").ne("")
        & merged["linha_norm_sugerida"].isna()
    )
    merged.loc[mask_texto_sem_mapa, "codigo_erro"] = "LINHA_NAO_MAPEADA"
    merged.loc[mask_texto_sem_mapa, "motivo_erro"] = "A linha informada não foi encontrada na planilha de clusterização, nem por correspondência aproximada."

    return merged


def preparar_pesquisa(df_pesquisa: pd.DataFrame) -> pd.DataFrame:
    out = df_pesquisa.copy()
    col_ts = encontrar_coluna_timestamp(out)
    if col_ts:
        out["timestamp_resposta"] = pd.to_datetime(out[col_ts], errors="coerce")
        out["dia_semana_num"] = out["timestamp_resposta"].dt.dayofweek
        out["hora_resposta_min"] = out["timestamp_resposta"].dt.hour * 60 + out["timestamp_resposta"].dt.minute
    else:
        out["timestamp_resposta"] = pd.NaT
        out["dia_semana_num"] = pd.NA
        out["hora_resposta_min"] = pd.NA
    return out


def preparar_cronograma(df_cron: pd.DataFrame) -> pd.DataFrame:
    cron = df_cron.copy()

    cron["rota_norm"] = cron["Origem e Destino Linha"].apply(padronizar_linha)
    cron["previsao_dt"] = pd.to_datetime(cron["Previsão de Chegada"], format="%H:%M:%S", errors="coerce")
    cron["hora_dt"] = pd.to_datetime(cron["Hora"], format="%H:%M:%S", errors="coerce")

    cron["previsao_min"] = cron["previsao_dt"].dt.hour * 60 + cron["previsao_dt"].dt.minute
    cron["hora_min"] = cron["hora_dt"].dt.hour * 60 + cron["hora_dt"].dt.minute

    dias_cols = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]

    for col in dias_cols:
        cron[col] = (
            cron[col]
            .astype(str)
            .str.strip()
            .replace({
                "-": 0,
                "nan": 0,
                "": 0,
                " ": 0,
                "x": 1,
                "X": 1,
            })
        )
        cron[col] = pd.to_numeric(cron[col], errors="coerce").fillna(0).astype(int)

    cron["dias_ativos"] = cron[dias_cols].values.tolist()

    cron = cron.sort_values(["previsao_dt", "Origem e Destino Linha"]).reset_index(drop=True)
    cron["_cron_id"] = cron.index

    return cron


def extrair_linha_vizinhanca(resultado: pd.DataFrame, rid: int) -> Optional[str]:
    contexto = resultado[(resultado["_row_id"] >= rid - 2) & (resultado["_row_id"] <= rid + 2)].copy()
    contexto = contexto[contexto["_row_id"] != rid]
    candidatos = contexto["Linha_final"].dropna().astype(str).tolist()
    if candidatos:
        return pd.Series(candidatos).value_counts().index[0]
    return None


def dia_ativo(row: pd.Series, dia_semana_num) -> bool:
    if pd.isna(dia_semana_num):
        return True
    idx = int(dia_semana_num)
    dias = row["dias_ativos"]
    if idx < 0 or idx > 6 or not isinstance(dias, list):
        return True
    try:
        return bool(dias[idx])
    except Exception:
        return True


def score_cronograma(row: pd.Series, linha_ref_norm: str, hora_ref_min, dia_semana_num) -> float:
    score = 0.0

    # semelhança da rota
    if linha_ref_norm:
        rota = row["rota_norm"]
        if rota == linha_ref_norm:
            score += 100
        else:
            prox = get_close_matches(linha_ref_norm, [rota], n=1, cutoff=0.6)
            if prox:
                # dá nota parcial para parecido
                score += 70

    # aderência do dia da semana
    if dia_ativo(row, dia_semana_num):
        score += 20

    # proximidade entre hora da resposta e previsão
    if pd.notna(hora_ref_min) and pd.notna(row["previsao_min"]):
        delta_prev = abs(float(row["previsao_min"]) - float(hora_ref_min))
        score += max(0, 30 - min(delta_prev, 30))  # até 30 pontos

    # proximidade entre hora da resposta e hora da operação
    if pd.notna(hora_ref_min) and pd.notna(row["hora_min"]):
        delta_hora = abs(float(row["hora_min"]) - float(hora_ref_min))
        score += max(0, 20 - min(delta_hora, 20))  # até 20 pontos

    return score


def estimar_linha_hibrida(resultado: pd.DataFrame, cron: pd.DataFrame) -> pd.DataFrame:
    resultado = resultado.copy()
    linhas_estimadas = []
    score_estimado = []

    for _, row in resultado.iterrows():
        if pd.notna(row["Cluster_final"]):
            linhas_estimadas.append(row.get("Linha_final"))
            score_estimado.append(np.nan)
            continue

        rid = int(row["_row_id"])
        linha_viz = extrair_linha_vizinhanca(resultado, rid)
        linha_ref = linha_viz if linha_viz else row["linha_original"]
        linha_ref_norm = padronizar_linha(linha_ref)

        hora_ref = row.get("hora_resposta_min", pd.NA)
        dia_ref = row.get("dia_semana_num", pd.NA)

        cron_scores = cron.copy()
        cron_scores["score_estimativa"] = cron_scores.apply(
            lambda r: score_cronograma(r, linha_ref_norm, hora_ref, dia_ref), axis=1
        )
        melhor = cron_scores.sort_values("score_estimativa", ascending=False).iloc[0]

        linhas_estimadas.append(melhor["Origem e Destino Linha"] if melhor["score_estimativa"] > 0 else pd.NA)
        score_estimado.append(melhor["score_estimativa"] if melhor["score_estimativa"] > 0 else np.nan)

    resultado["Linha_estimada_vizinhanca"] = [
        extrair_linha_vizinhanca(resultado, int(rid)) for rid in resultado["_row_id"]
    ]
    resultado["Linha_estimada_hibrida"] = linhas_estimadas
    resultado["Score_estimativa_hibrida"] = score_estimado
    resultado["linha_estimada_norm"] = resultado["Linha_estimada_hibrida"].apply(padronizar_linha)
    return resultado


def localizar_contexto_cronograma(cron: pd.DataFrame, linha_norm: str, hora_ref_min=None, dia_semana_num=None) -> pd.DataFrame:
    if not linha_norm and pd.isna(hora_ref_min):
        return pd.DataFrame()

    cron_aux = cron.copy()
    cron_aux["score_contexto"] = cron_aux.apply(
        lambda r: score_cronograma(r, linha_norm, hora_ref_min, dia_semana_num), axis=1
    )

    melhor = cron_aux.sort_values("score_contexto", ascending=False).iloc[0]
    if melhor["score_contexto"] <= 0:
        return pd.DataFrame()

    pos = int(melhor["_cron_id"])
    return cron_aux[(cron_aux["_cron_id"] >= pos - 2) & (cron_aux["_cron_id"] <= pos + 2)].copy()


st.title("🧩 Respostas por Cluster")
st.write("Faça upload do dataset de pesquisa e da planilha de clusterização. O cronograma de previsão já está embutido no código.")

st.sidebar.header("Arquivos")
upload_pesquisa = st.sidebar.file_uploader("Dataset de pesquisa", type=["csv", "xlsx", "xls"], key="pesquisa")
upload_cluster = st.sidebar.file_uploader("Planilha de clusterização", type=["csv", "xlsx", "xls"], key="cluster")

st.sidebar.markdown("---")
usar_match_aproximado = st.sidebar.checkbox("Usar correspondência aproximada", value=True)

if upload_pesquisa is None or upload_cluster is None:
    st.warning("Envie os dois arquivos para continuar.")
    st.stop()

try:
    df_pesquisa = preparar_pesquisa(load_file(upload_pesquisa))
    df_cluster = load_file(upload_cluster)
    df_cron = preparar_cronograma(load_default_cronograma())
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
    mask_aprox = resultado["Tipo_match"] == "Aproximado"
    resultado.loc[
        mask_aprox,
        ["Linha_final", "Categoria_final", "Cluster_final"],
    ] = pd.NA
    resultado.loc[mask_aprox, "Tipo_match"] = "Sem correspondência"
    resultado.loc[mask_aprox, "codigo_erro"] = "MATCH_APROXIMADO_DESATIVADO"
    resultado.loc[mask_aprox, "motivo_erro"] = "A linha tinha correspondência aproximada, mas essa opção foi desativada no app."

resultado = estimar_linha_hibrida(resultado, df_cron)

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
        resumo_cluster = resultado.dropna(subset=["Cluster_final"]).groupby("Cluster_final").size().reset_index(name="Quantidade de respostas")
        fig = px.bar(resumo_cluster, x="Cluster_final", y="Quantidade de respostas", text="Quantidade de respostas")
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

st.subheader("Linhas sem correspondência")
sem_match = resultado[resultado["Cluster_final"].isna()].copy()

if sem_match.empty:
    st.success("Não há linhas sem correspondência.")
else:
    tabela_sem_match = sem_match[
        [
            "_row_id", "linha_original", "linha_norm", "Linha_estimada_vizinhanca",
            "Linha_estimada_hibrida", "Score_estimativa_hibrida", "codigo_erro", "motivo_erro"
        ]
    ].rename(columns={
        "_row_id": "Linha da resposta",
        "linha_original": "Linha informada",
        "linha_norm": "Linha normalizada",
        "Linha_estimada_vizinhanca": "Estimativa pela vizinhança",
        "Linha_estimada_hibrida": "Estimativa híbrida",
        "Score_estimativa_hibrida": "Score da estimativa",
        "codigo_erro": "Código de erro",
        "motivo_erro": "Motivo",
    })
    st.dataframe(tabela_sem_match, use_container_width=True)

    opcoes = [
        f'Linha {int(r["_row_id"])} | {r["linha_original"]}'
        for _, r in sem_match.iterrows()
    ]
    escolha = st.selectbox("Escolha uma linha sem correspondência para inspecionar", opcoes)

    row_id = int(escolha.split("|")[0].replace("Linha", "").strip())
    foco = resultado[resultado["_row_id"] == row_id].iloc[0]

    st.markdown("### Contexto na pesquisa (2 acima e 2 abaixo)")
    contexto_pesquisa = resultado[
        (resultado["_row_id"] >= row_id - 2) & (resultado["_row_id"] <= row_id + 2)
    ][
        [
            "_row_id", "linha_original", "Linha_final", "Linha_estimada_vizinhanca",
            "Linha_estimada_hibrida", "Cluster_final", "Tipo_match", "codigo_erro"
        ]
    ].rename(columns={
        "_row_id": "Posição",
        "linha_original": "Linha informada",
        "Linha_final": "Linha atribuída",
        "Linha_estimada_vizinhanca": "Estimativa vizinhança",
        "Linha_estimada_hibrida": "Estimativa híbrida",
        "Cluster_final": "Cluster",
        "Tipo_match": "Tipo de match",
        "codigo_erro": "Código de erro",
    })
    st.dataframe(contexto_pesquisa, use_container_width=True)

    st.markdown("### Contexto no cronograma (2 acima e 2 abaixo)")
    linha_referencia = foco["linha_estimada_norm"] if pd.notna(foco["linha_estimada_norm"]) else padronizar_linha(foco["linha_original"])
    contexto_cron = localizar_contexto_cronograma(
        df_cron,
        linha_referencia,
        foco.get("hora_resposta_min", pd.NA),
        foco.get("dia_semana_num", pd.NA),
    )

    if contexto_cron.empty:
        st.info("Não encontrei contexto correspondente no cronograma para essa linha estimada.")
    else:
        st.dataframe(
            contexto_cron[
                [
                    "_cron_id", "Linha", "Origem e Destino Linha", "Via", "Classe Conforto",
                    "Previsão de Chegada", "Hora", "SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM", "score_contexto"
                ]
            ].rename(columns={
                "_cron_id": "Posição cronograma",
                "Linha": "Código da linha",
                "Origem e Destino Linha": "Rota",
                "Via": "Via",
                "Classe Conforto": "Classe",
                "Previsão de Chegada": "Previsão de chegada",
                "Hora": "Hora da operação",
                "score_contexto": "Score contexto",
            }),
            use_container_width=True,
        )

st.markdown("---")
st.subheader("Base final")
st.dataframe(
    resultado[
        [
            "_row_id",
            "linha_original",
            "linha_norm",
            "Linha_final",
            "Categoria_final",
            "Cluster_final",
            "Tipo_match",
            "codigo_erro",
            "motivo_erro",
            "Linha_estimada_vizinhanca",
            "Linha_estimada_hibrida",
            "Score_estimativa_hibrida",
        ]
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
