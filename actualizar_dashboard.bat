@echo off
echo ============================================
echo   CaseTox Dashboard - Actualizacion de datos
echo ============================================
echo.

echo [1/3] Exportando datos de PostgreSQL...
python -c "import pandas as pd; from sqlalchemy import create_engine; from urllib.parse import quote_plus; password = quote_plus('INML.2025*'); engine = create_engine(f'postgresql://postgres:{password}@localhost:5432/CaseTox Manager'); pd.read_sql('SELECT * FROM tamizaje.tamizaje', engine).to_csv('D:/00QTOF/TAMIZAJE/casetox-dashboard/data/tamizaje.csv', index=False); pd.read_sql('SELECT * FROM tamizaje.asignacion', engine).to_csv('D:/00QTOF/TAMIZAJE/casetox-dashboard/data/asignacion.csv', index=False); print('CSVs exportados correctamente!')"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se pudieron exportar los datos. Verifica que PostgreSQL este corriendo.
    pause
    exit /b 1
)

echo.
echo [2/3] Subiendo cambios a GitHub...
cd /d D:\00QTOF\TAMIZAJE\casetox-dashboard
git add data/
git commit -m "Actualizar datos %date% %time:~0,5%"
git push

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se pudo subir a GitHub. Verifica tu conexion a internet.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Dashboard actualizado exitosamente!
echo   Streamlit Cloud se actualizara en ~1 min
echo ============================================
echo.
pause
