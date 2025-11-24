from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, List, Tuple
import os
import csv
import io
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np


# Tu código integrado
def clasificar_superficie_conica(ecuacion: Dict[str, float]) -> str:
    A = ecuacion.get('A', 0)
    B = ecuacion.get('B', 0)
    C = ecuacion.get('C', 0)
    D = ecuacion.get('D', 0)
    E = ecuacion.get('E', 0)
    F = ecuacion.get('F', 0)

    coeficientes_cuadrados = [A, B, C]
    ceros = coeficientes_cuadrados.count(0)

    if D != 0 or E != 0 or F != 0:
        return "Clasificación compleja (con términos mixtos)"

    if ceros == 0:
        if (A > 0 and B > 0 and C > 0) or (A < 0 and B < 0 and C < 0):
            return "Elipsoide"
        if A * B * C < 0 and ceros == 0:
            return "Hiperboloide de una o dos hojas"

    if ceros == 1:
        return "Paraboloide (Elíptico o Hiperbólico)"

    if ceros == 2:
        return "Cilindro o Par de planos"

    return "No clasificable o Plano"


def calcular_valor_ecuacion(ecuacion: Dict[str, float], x: float, y: float, z: float) -> float:
    A, B, C, D, E, F, G, H, I, J = (
        ecuacion.get(c, 0) for c in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    )

    valor = (
            A * x ** 2 + B * y ** 2 + C * z ** 2 +
            D * x * y + E * x * z + F * y * z +
            G * x + H * y + I * z + J
    )
    return valor


# Función para guardar en CSV
def guardar_registro_calculo(ecuacion: Dict[str, float], tipo: str, punto: str, valor: float, en_superficie: bool):
    archivo = 'calculo_registros.csv'
    existe = os.path.exists(archivo)
    with open(archivo, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not existe:
            writer.writerow(['Ecuacion', 'Tipo_Superficie', 'Punto', 'Valor', 'En_Superficie'])
        writer.writerow([str(ecuacion), tipo, punto, valor, en_superficie])


# Función para leer registros del CSV
def leer_registros_calculo():
    archivo = 'calculo_registros.csv'
    if not os.path.exists(archivo):
        return []
    with open(archivo, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return list(reader)


# Función para editar registro (por índice)
def editar_registro_calculo(indice: int, nuevos_datos: Dict[str, Any]):
    archivo = 'calculo_registros.csv'
    if not os.path.exists(archivo):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    registros = leer_registros_calculo()
    if indice < 0 or indice >= len(registros):
        raise HTTPException(status_code=400, detail="Índice inválido")

    # Recalcular con nuevos datos
    ecuacion = nuevos_datos['ecuacion']
    punto = nuevos_datos['punto']
    tipo = clasificar_superficie_conica(ecuacion)
    valor = calcular_valor_ecuacion(ecuacion, punto['x'], punto['y'], punto['z'])
    en_superficie = abs(valor) < 1e-6

    registros[indice] = {
        'Ecuacion': str(ecuacion),
        'Tipo_Superficie': tipo,
        'Punto': f"({punto['x']}, {punto['y']}, {punto['z']})",
        'Valor': valor,
        'En_Superficie': en_superficie
    }

    # Reescribir CSV
    with open(archivo, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Ecuacion', 'Tipo_Superficie', 'Punto', 'Valor', 'En_Superficie'])
        writer.writeheader()
        writer.writerows(registros)


# Función para eliminar registro (por índice)
def eliminar_registro_calculo(indice: int):
    archivo = 'calculo_registros.csv'
    if not os.path.exists(archivo):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    registros = leer_registros_calculo()
    if indice < 0 or indice >= len(registros):
        raise HTTPException(status_code=400, detail="Índice inválido")

    del registros[indice]

    # Reescribir CSV
    with open(archivo, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Ecuacion', 'Tipo_Superficie', 'Punto', 'Valor', 'En_Superficie'])
        writer.writeheader()
        writer.writerows(registros)


def generar_grafica_3d(ecuacion: Dict[str, float]):
    A, B, C, D, E, F, G, H, I, J = (
        ecuacion.get(c, 0) for c in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    )

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Rango para la malla
    x = np.linspace(-10, 10, 50)
    y = np.linspace(-10, 10, 50)
    X, Y = np.meshgrid(x, y)

    # Determinar el tipo de superficie y calcular Z
    try:
        if C != 0:
            # Caso general: Despejamos Z de la ecuación cuadrática
            # C*z² + I*z + (A*x² + B*y² + D*xy + E*xz + F*yz + G*x + H*y + J) = 0
            # Simplificamos asumiendo E=F=0 (no hay términos xz, yz)

            if E == 0 and F == 0:
                # Ecuación cuadrática en z: C*z² + I*z + resto = 0
                resto = A * X ** 2 + B * Y ** 2 + D * X * Y + G * X + H * Y + J

                # Fórmula cuadrática: z = (-I ± √(I² - 4*C*resto)) / (2*C)
                discriminante = I ** 2 - 4 * C * resto

                # Solo graficamos donde el discriminante es positivo
                Z_positivo = np.where(discriminante >= 0,
                                      (-I + np.sqrt(np.maximum(discriminante, 0))) / (2 * C),
                                      np.nan)
                Z_negativo = np.where(discriminante >= 0,
                                      (-I - np.sqrt(np.maximum(discriminante, 0))) / (2 * C),
                                      np.nan)

                # Graficar ambas ramas (superior e inferior)
                ax.plot_surface(X, Y, Z_positivo, alpha=0.7, cmap='viridis', edgecolor='none')
                ax.plot_surface(X, Y, Z_negativo, alpha=0.7, cmap='plasma', edgecolor='none')
            else:
                # Caso con términos mixtos (más complejo)
                Z = (-A * X ** 2 - B * Y ** 2 - D * X * Y - G * X - H * Y - J) / C
                ax.plot_surface(X, Y, Z, alpha=0.7, cmap='viridis', edgecolor='none')

        elif B != 0:
            # Despejamos Y si C=0
            Y_calc = (-A * X ** 2 - G * X - J) / B
            Z_range = np.linspace(-10, 10, 50)
            X_mesh, Z_mesh = np.meshgrid(x, Z_range)
            Y_mesh = (-A * X_mesh ** 2 - G * X_mesh - J) / B
            ax.plot_surface(X_mesh, Y_mesh, Z_mesh, alpha=0.7, cmap='viridis', edgecolor='none')

        elif A != 0:
            # Despejamos X si B=C=0
            X_calc = (-G - np.sqrt(np.maximum(G ** 2 - 4 * A * J, 0))) / (2 * A)
            Y_range = np.linspace(-10, 10, 50)
            Z_range = np.linspace(-10, 10, 50)
            Y_mesh, Z_mesh = np.meshgrid(Y_range, Z_range)
            X_mesh = np.full_like(Y_mesh, X_calc)
            ax.plot_surface(X_mesh, Y_mesh, Z_mesh, alpha=0.7, cmap='viridis', edgecolor='none')

        else:
            # Plano o superficie degenerada
            Z = np.zeros_like(X)
            ax.plot_surface(X, Y, Z, alpha=0.5, cmap='gray', edgecolor='none')

    except Exception as e:
        print(f"Error al generar gráfica: {e}")
        # Fallback: superficie plana
        Z = np.zeros_like(X)
        ax.plot_surface(X, Y, Z, alpha=0.5, cmap='gray', edgecolor='none')

    # Configuración de ejes
    ax.set_xlabel('Eje X', fontsize=10)
    ax.set_ylabel('Eje Y', fontsize=10)
    ax.set_zlabel('Eje Z', fontsize=10)
    ax.set_title('Superficie Cónica 3D', fontsize=12, fontweight='bold')

    # Ajustar límites de ejes para mejor visualización
    ax.set_xlim([-10, 10])
    ax.set_ylim([-10, 10])
    ax.set_zlim([-10, 10])

    # Guardar en buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf

router = APIRouter()

templates_engine = Jinja2Templates(directory=os.path.join("templates"))


@router.post("/clasificar_evaluar", response_model=Dict[str, Any], tags=["Calculo Vectorial"])
def clasificar_y_evaluar_superficie(
        ecuacion_data: Dict[str, float],
        puntos_evaluacion: List[Dict[str, float]]
):
    ecuacion_dict = ecuacion_data

    tipo_superficie = clasificar_superficie_conica(ecuacion_dict)

    resultados_evaluacion = []
    for punto in puntos_evaluacion:
        valor = calcular_valor_ecuacion(ecuacion_dict, punto['x'], punto['y'], punto['z'])
        resultados_evaluacion.append({
            "punto": f"({punto['x']}, {punto['y']}, {punto['z']})",
            "valor_en_ecuacion": valor,
            "esta_en_superficie": abs(valor) < 1e-6
        })

    return {
        "ecuacion_recibida": ecuacion_dict,
        "tipo_superficie": tipo_superficie,
        "evaluacion_puntos": resultados_evaluacion
    }


# Nuevo endpoint para resultado emergente (JSON)
@router.post("/clasificar_evaluar_json", response_class=JSONResponse, tags=["Calculo Vectorial"])
async def clasificar_y_evaluar_json(
        A: float = Form(0.0), B: float = Form(0.0), C: float = Form(0.0),
        D: float = Form(0.0), E: float = Form(0.0), F: float = Form(0.0),
        G: float = Form(0.0), H: float = Form(0.0), I: float = Form(0.0),
        J: float = Form(0.0),
        punto_x: float = Form(0.0), punto_y: float = Form(0.0), punto_z: float = Form(0.0)
):
    ecuacion_data = {
        "A": A, "B": B, "C": C, "D": D, "E": E, "F": F,
        "G": G, "H": H, "I": I, "J": J
    }

    puntos_evaluacion = [{"x": punto_x, "y": punto_y, "z": punto_z}]

    try:
        resultados = clasificar_y_evaluar_superficie(ecuacion_data, puntos_evaluacion)
        # Guardar registro
        evaluacion = resultados['evaluacion_puntos'][0]
        guardar_registro_calculo(
            resultados['ecuacion_recibida'],
            resultados['tipo_superficie'],
            evaluacion['punto'],
            evaluacion['valor_en_ecuacion'],
            evaluacion['esta_en_superficie']
        )
        return resultados
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Nuevo endpoint para gráfica 3D
@router.get("/graficar_superficie", response_class=StreamingResponse, tags=["Calculo Vectorial"])
async def graficar_superficie(
        A: float = 1.0, B: float = 1.0, C: float = 1.0,
        D: float = 0.0, E: float = 0.0, F: float = 0.0,
        G: float = 0.0, H: float = 0.0, I: float = 0.0,
        J: float = 0.0
):
    ecuacion = {
        "A": A, "B": B, "C": C, "D": D, "E": E, "F": F,
        "G": G, "H": H, "I": I, "J": J
    }
    buf = generar_grafica_3d(ecuacion)
    return StreamingResponse(buf, media_type="image/png")


# Nuevo endpoint para editar registro
@router.post("/editar_registro", response_class=JSONResponse, tags=["Calculo Vectorial"])
async def editar_registro(
        indice: int = Form(...),
        A: float = Form(0.0), B: float = Form(0.0), C: float = Form(0.0),
        D: float = Form(0.0), E: float = Form(0.0), F: float = Form(0.0),
        G: float = Form(0.0), H: float = Form(0.0), I: float = Form(0.0),
        J: float = Form(0.0),
        punto_x: float = Form(0.0), punto_y: float = Form(0.0), punto_z: float = Form(0.0)
):
    nuevos_datos = {
        'ecuacion': {
            "A": A, "B": B, "C": C, "D": D, "E": E, "F": F,
            "G": G, "H": H, "I": I, "J": J
        },
        'punto': {"x": punto_x, "y": punto_y, "z": punto_z}
    }
    try:
        editar_registro_calculo(indice, nuevos_datos)
        return {"message": "Registro editado y recalculado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Nuevo endpoint para eliminar registro
@router.post("/eliminar_registro", response_class=JSONResponse, tags=["Calculo Vectorial"])
async def eliminar_registro(indice: int = Form(...)):
    try:
        eliminar_registro_calculo(indice)
        return {"message": "Registro eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leer_registros_calculo", response_class=JSONResponse, tags=["Calculo Vectorial"])
async def leer_registros_calculo_endpoint():
    return leer_registros_calculo()


@router.get("/calculo_vectorial", response_class=HTMLResponse, tags=["Vistas"])
async def get_calculo_vectorial_form(request: Request):
    registros = leer_registros_calculo()
    return templates_engine.TemplateResponse("calculo.html", {"request": request, "registros": registros})


@router.post("/resultado_calculo", response_class=HTMLResponse, tags=["Vistas"])
async def post_calculo_vectorial(
        request: Request,
        A: float = Form(0.0), B: float = Form(0.0), C: float = Form(0.0),
        D: float = Form(0.0), E: float = Form(0.0), F: float = Form(0.0),
        G: float = Form(0.0), H: float = Form(0.0), I: float = Form(0.0),
        J: float = Form(0.0),
        punto_x: float = Form(0.0), punto_y: float = Form(0.0), punto_z: float = Form(0.0)
):
    ecuacion_data = {
        "A": A, "B": B, "C": C, "D": D, "E": E, "F": F,
        "G": G, "H": H, "I": I, "J": J
    }

    punto_data = {"x": punto_x, "y": punto_y, "z": punto_z}
    puntos_evaluacion = [punto_data]

    try:
        resultados = clasificar_y_evaluar_superficie(ecuacion_data, puntos_evaluacion)
        return templates_engine.TemplateResponse("resultado.html", {"request": request, "resultados": resultados})
    except Exception as e:
        return templates_engine.TemplateResponse("error.html", {"request": request, "error_message": str(e)},
                                                 status_code=500)