import pandas as pd
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import HttpResponse
from .forms import ExcelUploadForm
import io

def process_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Leer el archivo Excel
                excel_file = request.FILES['excel_file']
                xls = pd.ExcelFile(excel_file)

                # Leer las hojas ASISTENCIA y PROYECCION NOMINA
                asistencia_df = pd.read_excel(xls, 'ASISTENCIA')
                proyeccion_nomina_df = pd.read_excel(xls, 'proyeccion nomina')

                # Crear lista de fechas para el mes actual
                today = datetime.now()
                current_month_start = datetime(today.year, today.month, 1)
                next_month = today.month % 12 + 1
                current_month_end = datetime(today.year if next_month > 1 else today.year + 1, next_month, 1) - timedelta(days=1)
                dates = pd.date_range(current_month_start, current_month_end)

                # Agregar columnas con las fechas a los DataFrames
                for date in dates:
                    date_str = date.strftime('%Y-%m-%d')
                    asistencia_df[date_str] = 0
                    proyeccion_nomina_df[date_str] = 0

                # Actualizar asistencia_df
                for index, row in asistencia_df.iterrows():
                    fecha = row['FECHA']
                    cant_raciones = row['CANT RACIONES']
                    fecha_str = fecha.strftime('%Y-%m-%d') if pd.notna(fecha) else None
                    if fecha_str in asistencia_df.columns:
                        asistencia_df.at[index, fecha_str] = cant_raciones

                # Actualizar proyeccion_nomina_df
                for index, row in proyeccion_nomina_df.iterrows():
                    fecha_i = row[9]
                    fecha_f = row[10]
                    cant_raciones = row[11]
                    if pd.notna(fecha_i) and pd.notna(fecha_f):
                        date_range = pd.date_range(fecha_i, fecha_f)
                        for date in date_range:
                            date_str = date.strftime('%Y-%m-%d')
                            if date_str in proyeccion_nomina_df.columns:
                                if date.weekday() < 5:
                                    proyeccion_nomina_df.at[index, date_str] = cant_raciones
                                else:
                                    proyeccion_nomina_df.at[index, date_str] = 0

                # Filtrar y reordenar columnas
                columns_to_keep = ['NOMBRE COLABORADOR', 'MODALIDAD', 'INSITUCION EDUCATIVA']
                september_dates = [date.strftime('%Y-%m-%d') for date in dates if date.month == today.month]
                columns_to_keep.extend(september_dates)

                asistencia_filtered = asistencia_df[columns_to_keep]
                proyeccion_nomina_filtered = proyeccion_nomina_df[columns_to_keep]

                # Combinar y agrupar DataFrames
                merged_df = pd.concat([asistencia_filtered, proyeccion_nomina_filtered])
                grouped_df = merged_df.groupby(['NOMBRE COLABORADOR', 'MODALIDAD', 'INSITUCION EDUCATIVA'], as_index=False).sum()

                # Crear el archivo Excel en memoria
                output = io.BytesIO()
                grouped_df.to_excel(output, index=False)
                output.seek(0)

                # Devolver el archivo como respuesta HTTP
                response = HttpResponse(
                    output.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename=nomina_procesada.xlsx'
                return response

            except Exception as e:
                form.add_error(None, f'Error al procesar el archivo: {str(e)}')
    else:
        form = ExcelUploadForm()

    return render(request, 'nomina_app/upload.html', {'form': form})