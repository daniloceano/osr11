from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/reported events/ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv"
OUTPUT = ROOT / "output/tex/supplementary_documentary_events_table.tex"


SOURCE_INFO = {
    "Análise da suscetibilidade e da vulnerabilidade costeira de um sistema semiabrigado a eventos extremos: Enseada de Tijucas - Santa Catarina": (
        "Master's dissertation",
        r"\citep{santos2018tijucas}",
    ),
    "Padrões atmosféricos associados a riscos de inundação costeira no litoral central e centro-norte de Santa Catarina": (
        "Master's dissertation",
        r"\citep{souza2022padroes}",
    ),
    "Principais eventos de inundação costeira na costa de Santa Catarina registrados pela rede maregráfica da Epagri entre 2012 e 2020": (
        "Scientific note",
        r"\citep{vanz2021inundacao}",
    ),
    "BRASPOR 2018 Resumos – caracterização do clima de ondas e níveis extremos de água": (
        "Conference abstract",
        r"\citep{leal2018climaondas}",
    ),
}


NEWS_LABELS = {
    "Ciclone destelha prédios e deixa Florianópolis sem energia": "Diário do Grande ABC",
    "Ressaca destrói casas e provoca estragos na Praia da Armação/SC": "Revista Emergência",
    "SC: ressaca provoca ondas de 3 metros e dificulta escoamento de enchente": "Terra",
    "Chuvas deixam 19 cidades do RS em emergência e também afetam SC": "R7 Notícias",
}


NOTE_TRANSLATIONS = {
    "Evento de ressaca/inundação costeira descrito em dissertação UFSC focada na Enseada de Tijucas; data registrada como início do episódio.":
        "Event reported in a UFSC dissertation; date recorded as the episode onset.",
    "Data do evento tomada da data da matéria (2005-08-09).":
        "Event date taken from the news publication date (9 August 2005).",
    "Data do evento explícita; publicação em 2010-05-27.":
        "Event date stated explicitly; article published on 27 May 2010.",
    "Data alinhada à expressão 'nesta quinta-feira' e ao carimbo da publicação.":
        "Event date inferred from the expression 'this Thursday' and the publication timestamp.",
    "Evento compilado a partir de inventário acadêmico UFSC; data tratada como início do episódio para fins de deduplicação.":
        "Compiled from a UFSC academic inventory; date treated as episode onset for deduplication.",
    "Evento compilado a partir de inventário acadêmico UFSC; data tratada como início do episódio para fins de deduplicação. Setor costeiro inferido por coerência regional; revisar se desejar.":
        "Compiled from a UFSC academic inventory; date treated as episode onset. Coastal sector inferred from regional location.",
    "Data representativa adotada: 2016-10-28, dentro da janela 27–30/10/2016.":
        "Representative date (28 October 2016) selected within the reported 27--30 October event window.",
    "Fonte acadêmica/anais; manter como registro com necessidade de corroborar em acervo jornalístico ou boletim operacional, se desejado.":
        "Academic conference source; no independent news or operational bulletin was identified in this inventory.",
    "Data registrada como 2017-05-30.":
        "Event date recorded as 30 May 2017.",
    "Data registrada como início da janela do evento.":
        "Date recorded as the beginning of the reported event window.",
    "Ilha da Paz tratada como Joinville para codificação municipal.":
        "Ilha da Paz coded under the municipality of Joinville.",
    "Setor costeiro inferido geograficamente; revisar se desejar aderência estrita ao mapeamento do CSV-base.":
        "Coastal sector inferred from geographic location.",
}


def latex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def source_cell(row: pd.Series) -> tuple[str, str]:
    title = row["source_title"]
    if title in SOURCE_INFO:
        source_type, citation = SOURCE_INFO[title]
        return source_type, citation
    label = NEWS_LABELS[title]
    url = (
        row["source_url"]
        .replace("%", r"\%")
        .replace("&", r"\&")
        .replace("#", r"\#")
        .replace("_", r"\_")
    )
    return "Online news", rf"\href{{{url}}}{{{latex_escape(label)}}}"


def main() -> None:
    df = pd.read_csv(INPUT).sort_values(["date", "city"], kind="stable").reset_index(drop=True)
    rows = []
    for idx, row in df.iterrows():
        source_type, source = source_cell(row)
        note = NOTE_TRANSLATIONS.get(row["notes"], latex_escape(row["notes"]))
        rows.append(
            f"{idx + 1} & {latex_escape(row['city'])} & {row['date']} & "
            f"{latex_escape(row['coastal_sector'])} & {source_type} & {source} & {note} \\\\"
        )

    content = r"""% Supplementary table generated from:
% data/reported events/ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv
% Required packages in the main preamble:
% \usepackage{booktabs,longtable,array,ragged2e,pdflscape,hyperref}
% If natbib is not already loaded: \usepackage[round]{natbib}
% Bibliography file: supplementary_documentary_events_references.bib

\begin{landscape}
\begingroup
\scriptsize
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.12}
\begin{longtable}{@{}r >{\RaggedRight\arraybackslash}p{2.4cm} p{1.65cm}
  >{\RaggedRight\arraybackslash}p{1.75cm}
  >{\RaggedRight\arraybackslash}p{1.85cm}
  >{\RaggedRight\arraybackslash}p{2.2cm}
  >{\RaggedRight\arraybackslash}p{8.0cm}@{}}
\caption{Documentary records of coastal-impact events in Santa Catarina included in the positive-event inventory used for threshold calibration. News sources are linked directly; academic and institutional sources are cited bibliographically. Dates denote the documented event date or, for multi-day episodes, the representative onset date used in the inventory.}\label{tab:supp_documentary_events}\\
\toprule
ID & Municipality & Date & Coastal sector & Source type & Source & Curation note \\
\midrule
\endfirsthead
\multicolumn{7}{c}{\tablename\ \thetable\ (continued)}\\
\toprule
ID & Municipality & Date & Coastal sector & Source type & Source & Curation note \\
\midrule
\endhead
\midrule
\multicolumn{7}{r}{Continued on next page}\\
\endfoot
\bottomrule
\endlastfoot
""" + "\n".join(rows) + r"""
\end{longtable}
\endgroup
\end{landscape}
"""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
