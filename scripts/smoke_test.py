import json
import sys
import time
from urllib import request, parse
import http.cookiejar as cookiejar


BASE = "http://localhost:5000"


def http_opener():
    cj = cookiejar.CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(cj))
    opener.addheaders = [("User-Agent", "smoke-test/1.0")]
    return opener


def post_form(opener, url, data_dict):
    data = parse.urlencode(data_dict).encode("utf-8")
    req = request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with opener.open(req, timeout=15) as resp:
        return resp.read(), resp.getcode(), dict(resp.headers)


def post_json(opener, url, data_dict):
    data = json.dumps(data_dict).encode("utf-8")
    req = request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with opener.open(req, timeout=15) as resp:
        return resp.read(), resp.getcode(), dict(resp.headers)


def get_json(opener, url):
    with opener.open(url, timeout=15) as resp:
        return resp.read(), resp.getcode(), dict(resp.headers)


def main():
    op = http_opener()
    print("[1/6] Admin login…", flush=True)
    body, code, _ = post_form(op, f"{BASE}/admin/authenticate", {"username": "admin", "password": "123456"})
    if code not in (200, 302):
        print("  ERROR: login admin fallo", code)
        return 1

    print("[2/6] Registrar candidato…", flush=True)
    body, code, _ = post_json(op, f"{BASE}/admin/registrar_candidato", {
        "nombre_completo": "Smoke Tester",
        "email": f"smoke_{int(time.time())}@example.com",
        "telefono": "3000000000",
        "cargo": "QA"
    })
    if code != 200:
        print("  ERROR: registrar candidato fallo", code, body[:200])
        return 1
    data = json.loads(body)
    if not data.get("success"):
        print("  ERROR: registrar candidato no success", data)
        return 1
    codigo = data["candidato"]["codigo"]
    print("  OK codigo=", codigo)

    print("[3/6] Iniciar evaluacion…", flush=True)
    body, code, _ = post_json(op, f"{BASE}/iniciar_evaluacion", {
        "documento": codigo,
        "telefono": "3000000000"
    })
    if code != 200:
        print("  ERROR: iniciar evaluacion fallo", code, body[:200])
        return 1
    print("  OK")

    print("[4/6] Obtener pregunta…", flush=True)
    body, code, _ = get_json(op, f"{BASE}/obtener_pregunta")
    if code != 200:
        print("  ERROR: obtener_pregunta fallo", code, body[:200])
        return 1
    pregunta = json.loads(body)
    if "error" in pregunta:
        print("  ERROR: respuesta error", pregunta)
        return 1
    print("  OK pregunta_id=", pregunta["id"], " n=", pregunta["pregunta_numero"]) 

    print("[5/6] Responder…", flush=True)
    primera_opcion = pregunta["opciones"][0]
    body, code, _ = post_json(op, f"{BASE}/responder", {
        "pregunta_id": pregunta["id"],
        "respuesta": primera_opcion,
        "respuestas_seleccionadas": [primera_opcion]
    })
    if code != 200:
        print("  ERROR: responder fallo", code, body[:200])
        return 1
    rpta = json.loads(body)
    if not rpta.get("success"):
        print("  ERROR: responder no success", rpta)
        return 1
    print("  OK hay_mas=", rpta.get("hay_mas"))

    print("[6/6] Generar PDF…", flush=True)
    body, code, _ = post_json(op, f"{BASE}/generar_pdf_final", {})
    if code != 200:
        print("  WARN: generar_pdf_final fallo", code, body[:200])
    else:
        resultado = json.loads(body)
        print("  OK pdf_generado=", resultado.get("pdf_generado"), "drive=", resultado.get("drive_upload"))

    print("SMOKE TEST: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
