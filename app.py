import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# =========================
# PASSWORD APP
# =========================
PASSWORD = "14062021"   # ← cambia si quieres

def check_password():
    if "password_ok" not in st.session_state:
        st.session_state.password_ok = False

    if not st.session_state.password_ok:
        st.title("🔐 Finanzas Fernando & María")
        pwd = st.text_input("Contraseña", type="password")

        if pwd == PASSWORD:
            st.session_state.password_ok = True
            st.rerun()
        else:
            st.stop()

check_password()


st.set_page_config(page_title="Gastos Fernando & María")
st.title("💸 Finanzas Fernando & María")

# ------------------------
# CONEXIÓN DB
# ------------------------
conn = sqlite3.connect("gastos.db", check_same_thread=False)
c = conn.cursor()

# ------------------------
# TABLA GASTOS
# ------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    categoria TEXT,
    subcategoria TEXT,
    importe REAL,
    tipo TEXT,
    nota TEXT
)
""")

# Añadir columna persona si la DB es antigua
try:
    c.execute("ALTER TABLE gastos ADD COLUMN persona TEXT")
except:
    pass

# ------------------------
# TABLA PRESUPUESTOS
# ------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS presupuestos (
    mes TEXT,
    categoria TEXT,
    subcategoria TEXT,
    importe REAL
)
""")
conn.commit()

# ------------------------
# CATEGORÍAS
# ------------------------
categorias = {
    "Vivienda": ["Alquiler", "Wifi", "Agua", "Luz", "Calefacción"],
    "Transporte": ["Gasolina coche", "Mantenimiento coche", "Transporte público"],
    "Ocio": ["Restaurantes", "Social", "Delivery"],
    "Compra Comida": [],
    "Gimnasio": [],
    "Viajes": [],
    "Caprichos": [],
    "Inversión": [],
    "Regalos": [],
    "Otros": []
}

# ------------------------
# MENÚ
# ------------------------
menu = st.sidebar.selectbox(
    "Menú",
    ["Registrar gasto", "Presupuesto", "Dashboard Mensual", "Dashboard Anual", "Ver gastos"]
)

# =========================================================
# REGISTRAR GASTO
# =========================================================
if menu == "Registrar gasto":

    st.header("Añadir gasto")

    fecha = st.date_input("Fecha", value=date.today())
    categoria = st.selectbox("Categoría", list(categorias.keys()))

    subcats = categorias[categoria]
    if subcats:
        subcategoria = st.selectbox("Subcategoría", subcats)
    else:
        subcategoria = ""

    importe = st.number_input("Importe (€)", min_value=0.0, step=0.01)
    tipo = st.selectbox("Tipo gasto", ["Compartido", "Personal"])
    persona = ""
    if tipo == "Personal":
            persona = st.selectbox("Persona", ["María", "Fernando"])

    nota = st.text_input("Nota")

    if st.button("Guardar gasto"):
        c.execute("""
        INSERT INTO gastos (fecha, categoria, subcategoria, importe, tipo, nota, persona)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (str(fecha), categoria, subcategoria, importe, tipo, nota, persona))


        conn.commit()
        st.success("Gasto guardado 💾")

# =========================================================
# PRESUPUESTO
# =========================================================
if menu == "Presupuesto":

    st.header("Presupuesto mensual")

    mes = st.text_input("Mes (formato YYYY-MM)", value="2026-03")

    if st.button("Copiar mes anterior"):
        mes_anterior = st.text_input("Mes anterior (YYYY-MM)")
        if mes_anterior:
            df_prev = pd.read_sql_query(
                f"SELECT * FROM presupuestos WHERE mes='{mes_anterior}'",
                conn
            )
            df_prev["mes"] = mes
            df_prev.to_sql("presupuestos", conn, if_exists="append", index=False)
            st.success("Mes copiado")

    st.subheader("Editar presupuestos")

    for cat, subcats in categorias.items():

        st.markdown(f"### {cat}")

        if subcats:
            for sub in subcats:

                current = pd.read_sql_query(
                    f"""
                    SELECT importe FROM presupuestos
                    WHERE mes='{mes}' AND categoria='{cat}' AND subcategoria='{sub}'
                    """, conn
                )

                val = float(current["importe"].iloc[0]) if not current.empty else 0.0

                nuevo = st.number_input(
                    f"{sub}",
                    value=val,
                    key=f"{mes}_{cat}_{sub}"
                )

                if st.button(f"Guardar {cat}-{sub}", key=f"btn_{mes}_{cat}_{sub}"):

                    c.execute("""
                    DELETE FROM presupuestos
                    WHERE mes=? AND categoria=? AND subcategoria=?
                    """, (mes, cat, sub))

                    c.execute("""
                    INSERT INTO presupuestos VALUES (?, ?, ?, ?)
                    """, (mes, cat, sub, nuevo))

                    conn.commit()
                    st.success("Guardado")

        else:

            current = pd.read_sql_query(
                f"""
                SELECT importe FROM presupuestos
                WHERE mes='{mes}' AND categoria='{cat}' AND subcategoria=''
                """, conn
            )

            val = float(current["importe"].iloc[0]) if not current.empty else 0.0

            nuevo = st.number_input(
                f"{cat}",
                value=val,
                key=f"{mes}_{cat}"
            )

            if st.button(f"Guardar {cat}", key=f"btn_{mes}_{cat}"):

                c.execute("""
                DELETE FROM presupuestos
                WHERE mes=? AND categoria=? AND subcategoria=''
                """, (mes, cat))

                c.execute("""
                INSERT INTO presupuestos VALUES (?, ?, ?, ?)
                """, (mes, cat, "", nuevo))

                conn.commit()
                st.success("Guardado")


# =========================================================
# DASHBOARD
# =========================================================
if menu == "Dashboard Mensual":

    st.header("Dashboard Mensual")

    mes = st.text_input(
        "Mes a analizar (YYYY-MM)",
        value="2026-03",
        key="mes_dashboard"
    )

    # ---------------- VISTA
    vista = st.radio(
        "Vista",
        ["Pareja", "María", "Fernando"],
        horizontal=True
    )

    # ---------------- GASTOS
    df_gastos = pd.read_sql_query(
        f"""
        SELECT * FROM gastos
        WHERE substr(fecha,1,7) = '{mes}'
        """,
        conn
    )

    # FILTRO PERSONA
    if vista == "Pareja":
        # SOLO compartidos
         df_gastos = df_gastos[df_gastos["tipo"] == "Compartido"]

    elif vista == "María":
        # compartidos + María
        df_gastos = df_gastos[
            (df_gastos["tipo"] == "Compartido") |
            (df_gastos["persona"] == "María")
        ]

    elif vista == "Fernando":
        # compartidos + Fernando
        df_gastos = df_gastos[
            (df_gastos["tipo"] == "Compartido") |
            (df_gastos["persona"] == "Fernando")
        ]

    # ---------------- PRESUPUESTO
    df_pres = pd.read_sql_query(
        f"""
        SELECT * FROM presupuestos
        WHERE mes = '{mes}'
        """,
        conn
    )

    total_gasto = df_gastos["importe"].sum()
    total_pres = df_pres["importe"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("Gasto total", f"{total_gasto:.2f} €")
    col2.metric("Presupuesto", f"{total_pres:.2f} €")
    col3.metric("Diferencia", f"{total_pres-total_gasto:.2f} €")

    st.divider()

    # =====================================================
    # PREVISIÓN FIN DE MES
    # =====================================================

    from datetime import datetime
    import calendar

    try:
        # convertir "2026-03" → fecha
        year = int(mes.split("-")[0])
        month = int(mes.split("-")[1])

        today = datetime.today()

        # solo si estamos viendo el mes actual
        if today.year == year and today.month == month:

            dias_transcurridos = today.day
            dias_mes = calendar.monthrange(year, month)[1]

            if dias_transcurridos > 0:
                gasto_diario = total_gasto / dias_transcurridos
                prevision = gasto_diario * dias_mes
            else:
                prevision = 0

            st.divider()
            st.subheader("Previsión fin de mes")

            colA, colB = st.columns(2)

            colA.metric("Gasto estimado", f"{prevision:,.0f} €")

            diferencia_prevision = total_pres - prevision

            if diferencia_prevision >= 0:
                colB.metric("Resultado previsto", f"+{diferencia_prevision:,.0f} €")
            else:
                colB.metric("Resultado previsto", f"{diferencia_prevision:,.0f} €")

    except:
        pass


    # =====================================================
    # TABLA COMPARACIÓN ORDENADA COMO EL GRÁFICO
    # =====================================================
    st.subheader("Comparación por categoría")

    # --- TOTAL
    filas = []

    pct_total = (total_gasto/total_pres*100) if total_pres>0 else 0

    filas.append({
        "nombre":"TOTAL",
        "importe_pres":total_pres,
        "importe_gasto":total_gasto,
        "diferencia":total_pres-total_gasto,
        "% gastado":round(pct_total,1)
    })

    # --- CATEGORÍAS
    pres_cat_total = df_pres.groupby("categoria")["importe"].sum().reset_index()
    gasto_cat_total = df_gastos.groupby("categoria")["importe"].sum().reset_index()

    cat_total = pd.merge(
        pres_cat_total,
        gasto_cat_total,
        on="categoria",
        how="outer",
        suffixes=("_pres","_gasto")
    ).fillna(0)

    cat_total = cat_total.sort_values("importe_pres", ascending=False)

    for _, cat_row in cat_total.iterrows():

        categoria = cat_row["categoria"]
        pres_cat_val = cat_row["importe_pres"]
        gasto_cat_val = cat_row["importe_gasto"]

        pct = (gasto_cat_val/pres_cat_val*100) if pres_cat_val>0 else 0

        filas.append({
            "nombre":categoria,
            "importe_pres":pres_cat_val,
            "importe_gasto":gasto_cat_val,
            "diferencia":pres_cat_val-gasto_cat_val,
            "% gastado":round(pct,1)
        })

        # --- SUBCATEGORÍAS
        sub_pres = df_pres[df_pres["categoria"]==categoria]
        sub_gasto = df_gastos[df_gastos["categoria"]==categoria]

        sub_pres = sub_pres.groupby("subcategoria")["importe"].sum().reset_index()
        sub_gasto = sub_gasto.groupby("subcategoria")["importe"].sum().reset_index()

        sub = pd.merge(
            sub_pres,
            sub_gasto,
            on="subcategoria",
            how="outer",
            suffixes=("_pres","_gasto")
        ).fillna(0)

        sub = sub.sort_values("importe_pres", ascending=False)

        for _, sub_row in sub.iterrows():

            if sub_row["subcategoria"] == "":
                continue

            pct_sub = (sub_row["importe_gasto"]/sub_row["importe_pres"]*100) if sub_row["importe_pres"]>0 else 0

            filas.append({
                "nombre":"   └ "+sub_row["subcategoria"],
                "importe_pres":sub_row["importe_pres"],
                "importe_gasto":sub_row["importe_gasto"],
                "diferencia":sub_row["importe_pres"]-sub_row["importe_gasto"],
                "% gastado":round(pct_sub,1)
            })

    comp_df = pd.DataFrame(filas)

    st.dataframe(comp_df)

    st.divider()

    # =====================================================
    # GRÁFICO VISUAL
    # =====================================================
    st.subheader("Presupuesto vs gasto")

    pastel_rojo = "#f3a6a6"

    # ---------- TOTAL
    st.markdown("## TOTAL")

    ratio_total = total_gasto/total_pres if total_pres>0 else 0
    pct_total = ratio_total*100 if total_pres>0 else 0

    st.markdown(
        f"""
        <div style="width:100%;background:#e6e6e6;border-radius:8px;height:28px;position:relative">
            <div style="
                background:{pastel_rojo};
                height:28px;
                border-radius:8px;
                width:{min(ratio_total,1)*100}%;">
            </div>
            {"<div style='position:absolute;width:100%;text-align:center;font-weight:600'>"+str(round(pct_total))+"% gastado</div>" if total_gasto>0 else ""}
        </div>
        <div style="font-size:13px;margin-top:4px;margin-bottom:30px">
            {total_gasto:,.0f}€ gastados de {total_pres:,.0f}€ presupuestados
        </div>
        """,
        unsafe_allow_html=True
    )

    # =====================================================
    # CATEGORÍAS
    # =====================================================

    for _, cat_row in cat_total.iterrows():

        categoria = cat_row["categoria"]
        pres_cat_val = cat_row["importe_pres"]
        gasto_cat_val = cat_row["importe_gasto"]

        if pres_cat_val == 0 and gasto_cat_val == 0:
            continue

        st.markdown(f"## {categoria}")

        ratio = gasto_cat_val/pres_cat_val if pres_cat_val>0 else 0
        pct = ratio*100 if pres_cat_val>0 else 0

        st.markdown(
            f"""
            <div style="width:100%;background:#e6e6e6;border-radius:8px;height:26px;position:relative">
                <div style="
                    background:{pastel_rojo};
                    height:26px;
                    border-radius:8px;
                    width:{min(ratio,1)*100}%;">
                </div>
                {"<div style='position:absolute;width:100%;text-align:center;font-weight:600'>"+str(round(pct))+"% gastado</div>" if gasto_cat_val>0 else ""}
            </div>
            <div style="font-size:13px;margin-top:4px;margin-bottom:20px">
                {gasto_cat_val:,.0f}€ gastados de {pres_cat_val:,.0f}€ presupuestados
            </div>
            """,
            unsafe_allow_html=True
        )

        # SUBCATEGORÍAS
        sub_pres = df_pres[df_pres["categoria"]==categoria]
        sub_gasto = df_gastos[df_gastos["categoria"]==categoria]

        sub_pres = sub_pres.groupby("subcategoria")["importe"].sum().reset_index()
        sub_gasto = sub_gasto.groupby("subcategoria")["importe"].sum().reset_index()

        sub = pd.merge(
            sub_pres,
            sub_gasto,
            on="subcategoria",
            how="outer",
            suffixes=("_pres","_gasto")
        ).fillna(0)

        sub = sub.sort_values("importe_pres", ascending=False)

        for _, sub_row in sub.iterrows():

            if sub_row["subcategoria"] == "":
                continue

            pres_sub = sub_row["importe_pres"]
            gasto_sub = sub_row["importe_gasto"]

            st.markdown(f"**{sub_row['subcategoria']}**")

            ratio = gasto_sub/pres_sub if pres_sub>0 else 0
            pct = ratio*100 if pres_sub>0 else 0

            st.markdown(
                f"""
                <div style="width:100%;background:#e6e6e6;border-radius:8px;height:24px;position:relative">
                    <div style="
                        background:{pastel_rojo};
                        height:24px;
                        border-radius:8px;
                        width:{min(ratio,1)*100}%;">
                    </div>
                    {"<div style='position:absolute;width:100%;text-align:center;font-weight:600'>"+str(round(pct))+"% gastado</div>" if gasto_sub>0 else ""}
                </div>
                <div style="font-size:12px;margin-top:4px;margin-bottom:20px">
                    {gasto_sub:,.0f}€ gastados de {pres_sub:,.0f}€ presupuestados
                </div>
                """,
                unsafe_allow_html=True
            )

    # =====================================================
    # GRÁFICOS
    # =====================================================

    import altair as alt

    pastel_colors = [
        "#f5b7b1",
        "#aed6f1",
        "#a9dfbf",
        "#d7bde2",
        "#f9e79f",
        "#fad7a0",
        "#f8c471",
        "#d5dbdb"
    ]
    # =========================
    # PIE CHART GASTO CATEGORÍA
    # =========================
    st.subheader("Distribución del gasto por categoría")

    if not df_gastos.empty:

        gastos_simple = (
            df_gastos.groupby("categoria")["importe"]
            .sum()
            .reset_index()
        )

        total = gastos_simple["importe"].sum()

        gastos_simple["pct"] = gastos_simple["importe"] / total
        gastos_simple["pct_label"] = (gastos_simple["pct"]*100).round(1).astype(str) + "%"

        # --- DONUT
        pie = alt.Chart(gastos_simple).mark_arc(innerRadius=70).encode(
            theta=alt.Theta("importe:Q"),
            color=alt.Color(
                "categoria:N",
                scale=alt.Scale(range=pastel_colors),
                legend=alt.Legend(title="")
            ),
            tooltip=[
                alt.Tooltip("categoria", title="Categoría"),
                alt.Tooltip("importe", title="€", format=",.0f"),
                alt.Tooltip("pct", title="% total", format=".1%")
            ]
        )

        # --- % SOBRE EL DONUT
        text_pct = alt.Chart(gastos_simple).mark_text(size=13).encode(
        theta=alt.Theta("importe:Q", stack=True),
        radius=alt.value(140),
        text="pct_label",
        opacity=alt.condition(
            alt.datum.pct > 0.05,
            alt.value(1),
            alt.value(0)
            )
        )

        # --- TEXTO CENTRAL
        center = alt.Chart(
            pd.DataFrame({"total":[total]})
        ).mark_text(size=18, fontWeight="bold").encode(
            text=alt.value(f"{total:,.0f}€")
        )

        st.altair_chart(pie + text_pct + center, use_container_width=True)

    else:
        st.info("Aún no hay gastos este mes")

    st.divider()


    # =========================
    # EVOLUCIÓN DEL MES
    # =========================
    st.subheader("Evolución del gasto acumulado")

    if not df_gastos.empty:

        df_gastos["fecha"] = pd.to_datetime(df_gastos["fecha"])

        diario = (
            df_gastos.groupby("fecha")["importe"]
            .sum()
            .cumsum()
            .reset_index()
        )

        line = alt.Chart(diario).mark_line(
            color="#f5b7b1",
            strokeWidth=3
        ).encode(
            x="fecha:T",
            y="importe:Q"
        )

        st.altair_chart(line, use_container_width=True)

# =========================================================
# DASHBOARD ANUAL
# =========================================================
if menu == "Dashboard Anual":

    st.header("Dashboard Anual")

    año = st.text_input("Año a analizar", value="2026", key="año_dashboard")

    # ---------------- GASTOS DEL AÑO
    df_gastos = pd.read_sql_query(
        f"""
        SELECT * FROM gastos
        WHERE substr(fecha,1,4) = '{año}'
        """,
        conn
    )

    # ---------------- PRESUPUESTO DEL AÑO
    df_pres = pd.read_sql_query(
        f"""
        SELECT * FROM presupuestos
        WHERE substr(mes,1,4) = '{año}'
        """,
        conn
    )

    total_gasto = df_gastos["importe"].sum()
    total_pres = df_pres["importe"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("Gasto acumulado", f"{total_gasto:,.0f} €")
    col2.metric("Presupuesto anual", f"{total_pres:,.0f} €")
    col3.metric("Diferencia", f"{total_pres-total_gasto:,.0f} €")

    st.divider()

    # =====================================================
    # GASTO POR MES (GRÁFICO CLAVE)
    # =====================================================
    st.subheader("Gasto por mes")

    if not df_gastos.empty:

        df_gastos["mes"] = df_gastos["fecha"].str[:7]

        gasto_mes = (
            df_gastos.groupby("mes")["importe"]
            .sum()
            .reset_index()
            .sort_values("mes")
        )

        import altair as alt

        pastel = "#aed6f1"

        chart = alt.Chart(gasto_mes).mark_bar().encode(
            x=alt.X("mes:N", title="Mes"),
            y=alt.Y("importe:Q", title="€"),
            color=alt.value(pastel),
            tooltip=["mes","importe"]
        )

        st.altair_chart(chart, use_container_width=True)

    else:
        st.info("Aún no hay gastos este año")

    st.divider()
    
    # =====================================================
    # DONUT ANUAL POR CATEGORÍA
    # =====================================================
    st.subheader("Distribución anual por categoría")

    if not df_gastos.empty:

        import altair as alt
        import pandas as pd

        gastos_simple = (
            df_gastos.groupby("categoria")["importe"]
            .sum()
            .reset_index()
        )

        total = gastos_simple["importe"].sum()

        gastos_simple["pct"] = gastos_simple["importe"] / total
        gastos_simple["pct_label"] = (gastos_simple["pct"]*100).round(1).astype(str) + "%"

        pastel_colors = [
            "#f5b7b1",
            "#aed6f1",
            "#a9dfbf",
            "#d7bde2",
            "#f9e79f",
            "#fad7a0",
            "#f8c471",
            "#d5dbdb"
        ]

        # ---------- DONUT
        pie = alt.Chart(gastos_simple).mark_arc(innerRadius=70).encode(
            theta=alt.Theta("importe:Q"),
            color=alt.Color(
                "categoria:N",
                scale=alt.Scale(range=pastel_colors),
                legend=alt.Legend(title="")
            ),
            tooltip=[
                alt.Tooltip("categoria", title="Categoría"),
                alt.Tooltip("importe", title="€", format=",.0f"),
                alt.Tooltip("pct", title="% total", format=".1%")
            ]
        )

        # ---------- PORCENTAJES
        text_pct = alt.Chart(gastos_simple).mark_text(
            size=13,
            align="center",
            baseline="middle"
        ).encode(
            theta=alt.Theta("importe:Q", stack=True),
            radius=alt.value(120),
            text="pct_label",
            opacity=alt.condition(
                alt.datum.pct > 0.04,
                alt.value(1),
                alt.value(0)
            )
        )

        # ---------- TOTAL CENTRO
        center = alt.Chart(
            pd.DataFrame({"total":[total]})
        ).mark_text(
            size=20,
            fontWeight="bold"
        ).encode(
            text=alt.value(f"{total:,.0f}€")
        )

        # ---------- RENDER
        chart_final = pie + text_pct + center
        st.altair_chart(chart_final, use_container_width=True)

    else:
        st.info("Aún no hay gastos este año")


# =========================================================
# VER GASTOS
# =========================================================
if menu == "Ver gastos":

    st.header("Histórico de gastos")

    df = pd.read_sql_query(
        "SELECT * FROM gastos ORDER BY fecha DESC",
        conn
    )

    if df.empty:
        st.info("No hay gastos aún")

    else:
        for _, row in df.iterrows():

            col1, col2, col3, col4, col5 = st.columns([2,2,2,2,1])

            col1.write(row["fecha"])
            col2.write(row["categoria"])
            col3.write(row["subcategoria"])
            col4.write(f"{row['importe']:.2f} €")

            if col5.button("🗑️", key=f"del_{row['id']}"):

                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM gastos WHERE id=?",
                    (int(row["id"]),)
                )
                conn.commit()
                st.rerun()

    # =====================================================
    # EXPORTAR EXCEL PRO
    # =====================================================
    import io

    st.divider()
    st.subheader("📥 Descargar informe en Excel")

    col1, col2 = st.columns(2)

    fecha_inicio = col1.date_input("Desde")
    fecha_fin = col2.date_input("Hasta")

    df_export = df.copy()

    # ---------- FILTRO FECHAS
    if fecha_inicio:
        df_export = df_export[df_export["fecha"] >= str(fecha_inicio)]

    if fecha_fin:
        df_export = df_export[df_export["fecha"] <= str(fecha_fin)]

    if not df_export.empty:

        # =========================
        # RESUMEN MENSUAL
        # =========================
        df_export["mes"] = df_export["fecha"].str[:7]

        resumen_mes = (
            df_export.groupby("mes")["importe"]
            .sum()
            .reset_index()
            .sort_values("mes")
        )

        # =========================
        # RESUMEN CATEGORÍA
        # =========================
        resumen_cat = (
            df_export.groupby(["categoria","subcategoria"])["importe"]
            .sum()
            .reset_index()
            .sort_values("importe", ascending=False)
        )

        # =========================
        # RESUMEN POR PERSONA
        # =========================
        resumen_persona = (
            df_export.groupby(["tipo","persona"])["importe"]
            .sum()
            .reset_index()
            .sort_values("importe", ascending=False)
        )

        # =========================
        # PRESUPUESTOS RELACIONADOS
        # =========================
        meses = df_export["mes"].unique()

        df_pres_export = pd.read_sql_query(
            f"""
            SELECT * FROM presupuestos
            WHERE mes IN ({",".join([f"'{m}'" for m in meses])})
            """,
            conn
        )

        # =========================
        # CREAR EXCEL
        # =========================
        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:

            df_export.to_excel(writer, sheet_name="Gastos", index=False)
            df_pres_export.to_excel(writer, sheet_name="Presupuestos", index=False)
            resumen_mes.to_excel(writer, sheet_name="Resumen mensual", index=False)
            resumen_cat.to_excel(writer, sheet_name="Resumen categorías", index=False)
            resumen_persona.to_excel(writer, sheet_name="Resumen por persona", index=False)

        buffer.seek(0)

        st.download_button(
            label="📊 Descargar informe completo",
            data=buffer,
            file_name="informe_finanzas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.info("No hay datos en ese rango")
