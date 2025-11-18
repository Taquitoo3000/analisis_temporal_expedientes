import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from datetime import datetime
import pyodbc
from scipy import stats

# paramteros a evaluar
sub = 'A'
conclusion = 'admis'
año_i = 2020
año_f = 2025

# carga de datos
print("="*60)
print("UPLOADING ACCESS...")
print("="*60)
archivo_access = 'D:/concentrado 2000-2025.mdb'
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    r'DBQ=' + archivo_access + ';'
)
conn = pyodbc.connect(conn_str)
quejas = pd.read_sql("SELECT * FROM [Quejas]", conn)
expediente = pd.read_sql("SELECT * FROM [Expediente]", conn)
conn.close()
print("="*60)
print("LOADED ACCESS")
print("="*60)

# Merge Quejas and Expediente
df = pd.merge(
    quejas,
    expediente,
    on='Expediente',
    how='inner',
    suffixes=('', '_expediente')
)

# Filtrar por años específicos
df['FechaInicio'] = pd.to_datetime(df['FechaInicio'], errors='coerce')
df['Año_Fecha'] = df['FechaInicio'].dt.year
df = df[df['Año_Fecha'].between(año_i, año_f)]
df = df[
    df['Conclusión'].str.contains(f'{conclusion}', case=False, na=False)
    | df['Conclusión'].str.contains('en tr', case=False, na=False)]
df = df[df['SubProcu'].str.contains(f'zona {sub}', case=False, na=False)]
df = df.sort_values(['FechaInicio', 'Expediente'])
df = df.reset_index(drop=True)

# Drop duplicates with unique Expediente
columnas = [
    'Expediente', 
    'SubProcu', 
    'FechaInicio', 
    'LugarProcedencia', 
    'Recepcion', 
    'Conclusión', 
    'F_Conclusion', 
    'GrupoVulnerable',
    'Año_Fecha'
]
df = df[columnas].drop_duplicates()

# Extraer año del expediente
df = df.copy()
df.loc[:, 'Año'] = df['Año_Fecha']

# Analisis de Fechas
df = df.drop_duplicates(subset=['Expediente'], keep='first')
df = df.copy()
df.loc[:, 'FechaInicio'] = pd.to_datetime(df['FechaInicio'], errors='coerce')
df.loc[:, 'F_Conclusion'] = pd.to_datetime(df['F_Conclusion'], errors='coerce')
df_concluidos = df[df['F_Conclusion'].notna()].copy()
df_concluidos.loc[:, 'TiempoDias'] = (df_concluidos['F_Conclusion'] - df_concluidos['FechaInicio']).dt.days
df_concluidos = df_concluidos[df_concluidos['TiempoDias'] >= 0]

# Analisis de eficiencia
fecha_corte = datetime.now()

# dataframe completo (incluyendo no concluidos)
df_completo = df.copy()

# calcular dias transcurridos (para todos los expedientes)
df_completo['DiasTranscurridos'] = np.where(
    df_completo['F_Conclusion'].notna(),
    (df_completo['F_Conclusion'] - df_completo['FechaInicio']).dt.days,
    (fecha_corte - df_completo['FechaInicio']).dt.days
)
df_completo = df_completo[df_completo['DiasTranscurridos'] >= 0]

# eficiencia por año
indicadores_eficiencia = []
años = [str(año) for año in range(año_i, año_f + 1)]
for año in años:
    df_año = df_completo[df_completo['Año'] == int(año)]
    
    if len(df_año) > 0:
        # Expedientes concluidos
        concluidos = df_año[df_año['F_Conclusion'].notna()]
        en_tramite = df_año[df_año['F_Conclusion'].isna()]
        
        # Tasa de conclusión
        tasa_conclusion = len(concluidos) / len(df_año) * 100 if len(df_año) > 0 else 0
        
        # Tiempos de los concluidos (eficiencia real)
        if len(concluidos) > 0:
            tiempo_promedio = concluidos['DiasTranscurridos'].mean()
            tiempo_mediano = concluidos['DiasTranscurridos'].median()
            p90 = concluidos['DiasTranscurridos'].quantile(0.9)  # El 90% más rápido
        else:
            tiempo_promedio = tiempo_mediano = p90 = np.nan
        
        indicadores_eficiencia.append({
            'Año': año,
            'Total_Expedientes': len(df_año),
            'Concluidos': len(concluidos),
            'En_Tramite': len(en_tramite),
            'Tasa_Conclusion_%': tasa_conclusion,
            'Tiempo_Promedio_Dias': tiempo_promedio,
            'Tiempo_Mediano_Dias': tiempo_mediano,
            'P90_Dias': p90,
        })

# Convertir a DataFrame
df_eficiencia = pd.DataFrame(indicadores_eficiencia)
print("\n" + "="*80)
print("INDICADORES DE EFICIENCIA POR AÑO")
print("="*80)
print(df_eficiencia.round(2))

# Graficas comparativas de eficiencia
plt.figure(figsize=(10, 6))
num_años = len(años)
colores = sns.color_palette("husl", num_años)
# Gráfica 1: Tiempo mediano de conclusión
plt.bar(df_eficiencia['Año'], df_eficiencia['Tiempo_Mediano_Dias'],
              color=colores[:len(df_eficiencia)], alpha=0.7)
plt.title('Mediano de Conclusión (días)', fontweight='bold')
plt.ylabel('Días')
plt.grid(alpha=0.3)
if conclusion == 'sobre': plt.ylim(0, 400) # MAXIMO
if conclusion == 'admis': plt.ylim(0, 65) # MAXIMO
for i, v in enumerate(df_eficiencia['Tiempo_Mediano_Dias']):
        if not pd.isna(v):
            plt.text(i, v, f'{v:.0f}', ha='center', va='bottom', fontweight='bold')
plt.savefig(f"mediana/{conclusion}_sub{sub}.png", 
           dpi=300, 
           bbox_inches='tight',
           facecolor='white',
           transparent=False)
plt.close()

# Gráfica: Distribución acumulativa
for i, año in enumerate(años):
    df_año_concluidos = df_completo[
        (df_completo['Año'] == int(año)) & 
        (df_completo['F_Conclusion'].notna())
    ]
    if len(df_año_concluidos) > 0:
        sorted_times = np.sort(df_año_concluidos['DiasTranscurridos'])
        y_vals = np.arange(1, len(sorted_times)+1) / len(sorted_times) * 100
        plt.plot(sorted_times, y_vals, label=f'Año {año}', 
                      color=colores[i], linewidth=2.5)

plt.title('Distribución Acumulativa de Tiempos de Conclusión', 
                   fontweight='bold', fontsize=12)
plt.xlabel('Días hasta conclusión', fontweight='bold')
plt.ylabel('Expedientes Concluidos (%)', fontweight='bold')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(alpha=0.3)
plt.xlim(0, 730) # Dos años
for percentil in [25, 50, 75, 90]:
    plt.axhline(y=percentil, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)

plt.tight_layout()
plt.savefig(f"distribuciones_acumulativas/{conclusion}_sub{sub}.png", 
           dpi=300, 
           bbox_inches='tight',
           facecolor='white',
           transparent=False)
plt.close()

# KDE
plt.figure(figsize=(10, 5))
for i, año in enumerate(años):
    df_año = df_concluidos[df_concluidos['Año'] == int(año)]
    kde_data = df_año['TiempoDias']
    kde = sns.kdeplot(data=kde_data, 
                        label=f'Año {año}', 
                        color=colores[i], 
                        linewidth=2,
                        alpha=0.8)
plt.xlabel('Días hasta conclusión', fontweight='bold', fontsize=12)
plt.ylabel('Densidad', fontweight='bold', fontsize=12)
plt.title(f'Distribución de Tiempos de Conclusión Zona {sub}', fontweight='bold', fontsize=14)
plt.legend(bbox_to_anchor=(1, 1), loc='upper left')
plt.grid(alpha=0.3)
plt.xlim(left=-10)
plt.tight_layout()
plt.savefig(f"distribuciones_temporales/{conclusion}_sub{sub}.png", 
           dpi=300, 
           bbox_inches='tight',
           facecolor='white',
           transparent=False)
plt.close()

# 6. ANÁLISIS DE TENDENCIA
print("\n" + "="*80)
print("ANÁLISIS DE TENDENCIA DE EFICIENCIA")
print("="*80)

# Calcular mejoras/aumentos entre años consecutivos
if len(df_eficiencia) > 1:
    for i in range(1, len(df_eficiencia)):
        año_actual = df_eficiencia.iloc[i]['Año']
        año_anterior = df_eficiencia.iloc[i-1]['Año']
        
        cambio_tiempo = df_eficiencia.iloc[i]['Tiempo_Mediano_Dias'] - df_eficiencia.iloc[i-1]['Tiempo_Mediano_Dias']
        cambio_tasa = df_eficiencia.iloc[i]['Tasa_Conclusion_%'] - df_eficiencia.iloc[i-1]['Tasa_Conclusion_%']
        
        if not pd.isna(cambio_tiempo):
            if cambio_tiempo < 0:
                print(f"✅ {año_actual} vs {año_anterior}: MEJORÓ en {abs(cambio_tiempo):.1f} días")
            else:
                print(f"❌ {año_actual} vs {año_anterior}: EMPEORÓ en {cambio_tiempo:.1f} días")
        
        if not pd.isna(cambio_tasa):
            if cambio_tasa > 0:
                print(f"✅ {año_actual} vs {año_anterior}: MAYOR tasa de conclusión (+{cambio_tasa:.1f}%)")
            else:
                print(f"❌ {año_actual} vs {año_anterior}: MENOR tasa de conclusión ({cambio_tasa:.1f}%)")
        print("---")
else:
    print("No hay suficientes datos para analizar tendencias")

# RESUMEN FINAL
print("\n" + "="*80)
print("RESUMEN EJECUTIVO")
print("="*80)
print(f"Período analizado: {años[0]} - {años[-1]}")
print(f"Tipo de conclusión: {conclusion}")
print(f"Subprocuraduría: {'Todas' if not sub else 'Zona ' + sub}")
print(f"Expedientes analizados: {len(df_completo):,}")
print(f"Expedientes concluidos: {len(df_concluidos):,}")
print(f"Expedientes en trámite: {len(df_completo) - len(df_concluidos):,}")