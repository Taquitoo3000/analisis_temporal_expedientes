# Análisis Temporal de los Tiempos de Conclusión de Expedientes
Este código analiza la siguiente información. Si tienes un dataframe con la siguiente estructura en los registros:
| Expediente |  Zona  | Conclusión | Fecha_Inicio | Fecha_Conclusion |
|:----------:|:-------|:-----------|:-------------|:-----------------|
|    1011    | zona A | En trámite |  10/11/2022  |                  |
|    1012    | zona B | Admisión   |  11/11/2022  |    01/01/2023    |
|    1408    | zona C | Sometido   |  11/11/2022  |    01/01/2023    |
|  ...       | ...    | ...        |  ...         |    ...           |

En el cual se tiene un ID como `Expediente`. distintos tipos de Conclusión en los cuales puede terminar un expediente o en su defecto, estar aun sin concluir. Al inicio del código se establecen las condiciones iniciales
```
python
sub = 'A'
conclusion = 'admis'
año_i = 2020
año_f = 2025
```
Se realizan los siguientes análisis
  1. **Gráfica de Valores de Tendencia Central**: Gráficas con de la mediana/media/moda segun tus necesidades en distintos años
  2. 
  3. **Distribución Temporal**: Densidad de expedientes concluidos con respecto al tiempo transcurrido hasta su conclusión
