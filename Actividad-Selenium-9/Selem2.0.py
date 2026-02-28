

import time
import csv
import datetime
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
OUTPUT_CSV  = "equipos_finalistas.csv"
OUTPUT_HTML = "reporte_pruebas.html"

URLS_RAW = """
https://idea.republicadeideas.do/finalista/cimai-agro-centro-itinerante-de-movilidad-academica-e-investigacion-agroindustrial-973
https://idea.republicadeideas.do/finalista/plaxa-dominicana-produccion-de-acido-lactico-a-partir-de-residuos-organicos-para-la-transicion-hacia-plasticos-biodegradables-948
https://idea.republicadeideas.do/finalista/agrovision-rddrones-e-inteligencia-artificial-para-la-deteccion-temprana-de-enfermedades-en-cultivos-934
https://idea.republicadeideas.do/finalista/trace-on-sistema-de-bioempaques-inteligentes-con-biosensores-integrados-contra-adulteracion-y-degradacion-de-alimentos-941
https://idea.republicadeideas.do/finalista/trazabilidad-real-time-por-blockchain-y-contratos-inteligentes-960
https://idea.republicadeideas.do/finalista/brotao-gemelo-digital-agricola-978
https://idea.republicadeideas.do/finalista/agromar-del-mar-al-campo-961
https://idea.republicadeideas.do/finalista/valdesia-export-hub-957
https://idea.republicadeideas.do/finalista/valverde-autosostenible-valas-950
https://idea.republicadeideas.do/finalista/reinapp-perfeccionamiento-de-postulacion-951
"""


# ─────────────────────────────────────────────
#  CLASE DE RESULTADO DE CASO DE PRUEBA
# ─────────────────────────────────────────────
class ResultadoPrueba:
    """Almacena el resultado de un caso de prueba individual."""

    def __init__(self, id_caso, nombre_caso, url):
        self.id_caso      = id_caso
        self.nombre_caso  = nombre_caso
        self.url          = url
        self.estado       = "NO EJECUTADO"   # PASS | FAIL | ERROR
        self.detalle      = ""
        self.valor_actual = ""
        self.duracion_seg = 0.0

    def pasar(self, detalle="", valor_actual=""):
        self.estado       = "PASS"
        self.detalle      = detalle
        self.valor_actual = valor_actual

    def fallar(self, detalle="", valor_actual=""):
        self.estado       = "FAIL"
        self.detalle      = detalle
        self.valor_actual = valor_actual

    def error(self, detalle=""):
        self.estado  = "ERROR"
        self.detalle = detalle


# ─────────────────────────────────────────────
#  INICIALIZACIÓN DEL DRIVER
# ─────────────────────────────────────────────
def iniciar_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    return webdriver.Edge(service=Service(), options=options)


# ─────────────────────────────────────────────
#  EXTRACCIÓN DE VOTOS
# ─────────────────────────────────────────────
def obtener_votos(driver):
    """
    Intenta extraer el número de votos de la página.
    Retorna el número como string, o '0' si no se encuentra.
    """
    # Estrategia 1: elemento que contenga la palabra "voto"
    elementos = driver.find_elements(By.XPATH, "//*[contains(text(),'voto')]")
    for el in elementos:
        for token in el.text.split():
            if token.isdigit():
                return token

    # Estrategia 2 (fallback): span/div con número corto visible
    for el in driver.find_elements(By.XPATH, "//span|//div"):
        txt = el.text.strip()
        if txt.isdigit() and len(txt) < 7:
            return txt

    return "0"


# ─────────────────────────────────────────────
#  SUITE DE CASOS DE PRUEBA POR URL
# ─────────────────────────────────────────────
def ejecutar_casos_para_url(driver, wait, url, indice):
    """
    Ejecuta los 5 casos de prueba para una URL dada.
    Retorna una lista de ResultadoPrueba y los datos del equipo (nombre, votos).
    """
    resultados = []
    nombre_equipo = ""
    votos_equipo  = "0"

    # ── CASO 1: Carga exitosa de la página ──────────────────────────────────
    caso1 = ResultadoPrueba(
        id_caso     = f"TC{indice:02d}-01",
        nombre_caso = "Carga exitosa de la página",
        url         = url
    )
    t0 = time.time()
    try:
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        url_actual = driver.current_url

        # Aserción: la URL actual debe contener el dominio esperado
        assert "republicadeideas.do" in url_actual, \
            f"URL inesperada: {url_actual}"

        caso1.pasar(
            detalle      = "Página cargada y URL verificada correctamente.",
            valor_actual = url_actual
        )
    except AssertionError as e:
        caso1.fallar(detalle=str(e), valor_actual=driver.current_url)
    except TimeoutException:
        caso1.error(detalle="Timeout: la página no cargó en 30 segundos.")
    except Exception as e:
        caso1.error(detalle=f"Excepción inesperada: {e}")
    caso1.duracion_seg = round(time.time() - t0, 2)
    resultados.append(caso1)

    # ── CASO 2: Presencia del h1 (título principal) ──────────────────────────
    caso2 = ResultadoPrueba(
        id_caso     = f"TC{indice:02d}-02",
        nombre_caso = "Presencia del título principal (h1)",
        url         = url
    )
    t0 = time.time()
    try:
        # Esperar a que el h1 exista Y tenga contenido de texto (carga dinámica)
        wait.until(lambda d: d.find_element(By.TAG_NAME, "h1").text.strip() != "")
        h1 = driver.find_element(By.TAG_NAME, "h1").text.strip()

        # Aserción: el h1 no debe estar vacío
        assert h1 != "", "El elemento h1 existe pero está vacío."

        nombre_equipo = h1
        caso2.pasar(
            detalle      = "H1 presente y no vacío.",
            valor_actual = h1
        )
    except AssertionError as e:
        caso2.fallar(detalle=str(e), valor_actual="(vacío)")
    except (TimeoutException, NoSuchElementException):
        caso2.error(detalle="No se encontró el elemento h1 en la página.")
    except Exception as e:
        caso2.error(detalle=f"Excepción inesperada: {e}")
    caso2.duracion_seg = round(time.time() - t0, 2)
    resultados.append(caso2)

    # Espera adicional para contenido dinámico
    time.sleep(2)

    # ── CASO 3: Nombre del equipo no vacío ───────────────────────────────────
    caso3 = ResultadoPrueba(
        id_caso     = f"TC{indice:02d}-03",
        nombre_caso = "Nombre del equipo no vacío",
        url         = url
    )
    t0 = time.time()
    try:
        assert nombre_equipo != "", \
            "El nombre del equipo está vacío (depende del Caso 2)."
        assert len(nombre_equipo) >= 3, \
            f"Nombre demasiado corto ({len(nombre_equipo)} chars): '{nombre_equipo}'"

        caso3.pasar(
            detalle      = f"Nombre válido con {len(nombre_equipo)} caracteres.",
            valor_actual = nombre_equipo
        )
    except AssertionError as e:
        caso3.fallar(detalle=str(e), valor_actual=nombre_equipo)
    except Exception as e:
        caso3.error(detalle=f"Excepción inesperada: {e}")
    caso3.duracion_seg = round(time.time() - t0, 2)
    resultados.append(caso3)

    # ── CASO 4: Extracción de votos (valor numérico >= 0) ────────────────────
    caso4 = ResultadoPrueba(
        id_caso     = f"TC{indice:02d}-04",
        nombre_caso = "Extracción de votos (valor numérico >= 0)",
        url         = url
    )
    t0 = time.time()
    try:
        votos_str = obtener_votos(driver)

        # Aserción 1: debe ser numérico
        assert votos_str.isdigit(), \
            f"El valor de votos no es numérico: '{votos_str}'"

        # Aserción 2: debe ser >= 0
        assert int(votos_str) >= 0, \
            f"Número de votos negativo: {votos_str}"

        votos_equipo = votos_str
        caso4.pasar(
            detalle      = "Votos extraídos y validados correctamente.",
            valor_actual = votos_str
        )
    except AssertionError as e:
        caso4.fallar(detalle=str(e), valor_actual=votos_str if 'votos_str' in dir() else "N/A")
    except Exception as e:
        caso4.error(detalle=f"Excepción inesperada: {e}")
    caso4.duracion_seg = round(time.time() - t0, 2)
    resultados.append(caso4)

    # ── CASO 5: URL contiene el slug del equipo ──────────────────────────────
    caso5 = ResultadoPrueba(
        id_caso     = f"TC{indice:02d}-05",
        nombre_caso = "URL contiene la ruta /finalista/",
        url         = url
    )
    t0 = time.time()
    try:
        url_actual = driver.current_url

        # Aserción: la URL final debe mantener /finalista/ (sin redireccionamiento extraño)
        assert "/finalista/" in url_actual, \
            f"La URL final no contiene '/finalista/': {url_actual}"

        caso5.pasar(
            detalle      = "Ruta /finalista/ verificada en la URL final.",
            valor_actual = url_actual
        )
    except AssertionError as e:
        caso5.fallar(detalle=str(e), valor_actual=driver.current_url)
    except Exception as e:
        caso5.error(detalle=f"Excepción inesperada: {e}")
    caso5.duracion_seg = round(time.time() - t0, 2)
    resultados.append(caso5)

    return resultados, nombre_equipo, votos_equipo


# ─────────────────────────────────────────────
#  GENERACIÓN DE REPORTE HTML
# ─────────────────────────────────────────────
def generar_reporte_html(todos_los_resultados, archivo_salida):
    """Genera un reporte HTML visual con los resultados de todas las pruebas."""

    total  = len(todos_los_resultados)
    passed = sum(1 for r in todos_los_resultados if r.estado == "PASS")
    failed = sum(1 for r in todos_los_resultados if r.estado == "FAIL")
    errors = sum(1 for r in todos_los_resultados if r.estado == "ERROR")
    pct    = round((passed / total) * 100, 1) if total > 0 else 0
    fecha  = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    filas_html = ""
    for r in todos_los_resultados:
        color = {"PASS": "#28a745", "FAIL": "#dc3545", "ERROR": "#fd7e14"}.get(r.estado, "#6c757d")
        badge = f'<span style="background:{color};color:#fff;padding:3px 10px;border-radius:12px;font-size:0.85em;font-weight:bold;">{r.estado}</span>'
        filas_html += f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #dee2e6;">{r.id_caso}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #dee2e6;">{r.nombre_caso}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #dee2e6;font-size:0.8em;word-break:break-all;">{r.url}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #dee2e6;text-align:center;">{badge}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #dee2e6;font-size:0.85em;">{r.detalle}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #dee2e6;font-size:0.85em;">{r.valor_actual}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #dee2e6;text-align:center;">{r.duracion_seg}s</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Reporte de Pruebas Selenium – República de Ideas</title>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#f4f6f9; margin:0; padding:24px; color:#333; }}
    h1   {{ color:#1a1a2e; margin-bottom:4px; }}
    .sub  {{ color:#666; font-size:0.9em; margin-bottom:24px; }}
    .cards {{ display:flex; gap:16px; margin-bottom:24px; flex-wrap:wrap; }}
    .card  {{ background:#fff; border-radius:10px; padding:20px 28px; min-width:130px;
              box-shadow:0 2px 8px rgba(0,0,0,.08); text-align:center; }}
    .card .num {{ font-size:2em; font-weight:bold; }}
    .card .lbl {{ font-size:0.85em; color:#666; margin-top:4px; }}
    .green {{ color:#28a745; }} .red {{ color:#dc3545; }} .orange {{ color:#fd7e14; }} .blue {{ color:#007bff; }}
    table  {{ width:100%; border-collapse:collapse; background:#fff;
              border-radius:10px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,.08); }}
    thead  {{ background:#1a1a2e; color:#fff; }}
    thead th {{ padding:12px 14px; text-align:left; font-size:0.9em; }}
    tbody tr:hover {{ background:#f8f9fa; }}
    .progress-bar {{ background:#e9ecef; border-radius:8px; height:18px; overflow:hidden; margin-top:6px; }}
    .progress-fill {{ background:linear-gradient(90deg,#28a745,#5cb85c); height:100%; border-radius:8px;
                      width:{pct}%; transition:width .5s; }}
  </style>
</head>
<body>

  <h1>🧪 Reporte de Pruebas Automatizadas – Selenium</h1>
  <p class="sub">Sitio: <strong>idea.republicadeideas.do</strong> &nbsp;|&nbsp; Ejecutado: {fecha} &nbsp;|&nbsp; Navegador: Microsoft Edge</p>

  <div class="cards">
    <div class="card"><div class="num blue">{total}</div><div class="lbl">Total de casos</div></div>
    <div class="card"><div class="num green">{passed}</div><div class="lbl">✅ PASS</div></div>
    <div class="card"><div class="num red">{failed}</div><div class="lbl">❌ FAIL</div></div>
    <div class="card"><div class="num orange">{errors}</div><div class="lbl">⚠️ ERROR</div></div>
    <div class="card" style="min-width:200px;">
      <div class="num green">{pct}%</div>
      <div class="lbl">Tasa de éxito</div>
      <div class="progress-bar"><div class="progress-fill"></div></div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>ID Caso</th>
        <th>Nombre del Caso</th>
        <th>URL Probada</th>
        <th>Estado</th>
        <th>Detalle / Aserción</th>
        <th>Valor Obtenido</th>
        <th>Duración</th>
      </tr>
    </thead>
    <tbody>
      {filas_html}
    </tbody>
  </table>

  <p style="margin-top:20px;font-size:0.8em;color:#999;">
    Generado automáticamente por Selenium WebDriver (Python) · {fecha}
  </p>
</body>
</html>"""

    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Reporte HTML generado: {archivo_salida}")


# ─────────────────────────────────────────────
#  FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────
def main():
    urls = [u.strip() for u in URLS_RAW.splitlines() if u.strip() and "/finalista/" in u]

    driver = iniciar_driver()
    wait   = WebDriverWait(driver, 30)

    todos_los_resultados = []
    datos_csv            = []

    print(f"\n{'='*60}")
    print(f"  Iniciando suite de pruebas: {len(urls)} URLs × 5 casos")
    print(f"{'='*60}\n")

    for i, url in enumerate(urls, start=1):
        print(f"[{i}/{len(urls)}] {url}")

        resultados_url, nombre, votos = ejecutar_casos_para_url(driver, wait, url, i)
        todos_los_resultados.extend(resultados_url)
        datos_csv.append([nombre, votos])

        for r in resultados_url:
            icono = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️"}.get(r.estado, "?")
            print(f"    {icono} {r.id_caso} – {r.nombre_caso}: {r.estado} ({r.duracion_seg}s)")
            if r.estado != "PASS":
                print(f"       ↳ {r.detalle}")

        print()

    driver.quit()

    # ── Guardar CSV ──────────────────────────────────────────────────────────
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["nombre_equipo", "votos"])
        writer.writerows(datos_csv)
    print(f"CSV de datos guardado: {OUTPUT_CSV}")

    # ── Generar reporte HTML ─────────────────────────────────────────────────
    generar_reporte_html(todos_los_resultados, OUTPUT_HTML)

    # ── Resumen final en consola ─────────────────────────────────────────────
    total  = len(todos_los_resultados)
    passed = sum(1 for r in todos_los_resultados if r.estado == "PASS")
    failed = sum(1 for r in todos_los_resultados if r.estado == "FAIL")
    errors = sum(1 for r in todos_los_resultados if r.estado == "ERROR")

    print(f"\n{'='*60}")
    print(f"  RESUMEN FINAL")
    print(f"  Total : {total}")
    print(f"  ✅ PASS : {passed}")
    print(f"  ❌ FAIL : {failed}")
    print(f"  ⚠️ ERROR: {errors}")
    print(f"  Tasa de éxito: {round(passed/total*100,1)}%")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
