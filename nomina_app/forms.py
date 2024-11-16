from django import forms

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label='Seleccione el archivo Excel',
        help_text='El archivo debe contener las hojas ASISTENCIA y PROYECCION NOMINA'
    )