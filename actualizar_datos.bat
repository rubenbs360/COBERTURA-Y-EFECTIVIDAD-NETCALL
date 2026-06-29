@echo off
chcp 65001 > nul
echo ===================================================
echo 🚀 INICIANDO ACTUALIZACIÓN DE DATOS DEL DASHBOARD
echo ===================================================
echo.

echo 📂 [1/3] Procesando archivos Excel y CSV locales...
python build_data.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ ERROR: Ocurrió un problema al ejecutar build_data.py.
    echo Asegúrese de tener instaladas las dependencias (pandas, openpyxl, numpy).
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo 💾 [2/3] Registrando cambios en Git...
git add data/
git commit -m "Actualización automática de datos"

echo.
echo ☁️ [3/3] Subiendo cambios a GitHub Pages (proyectrubs.com)...
git push origin main

echo.
echo ===================================================
echo 🎉 ¡ACTUALIZACIÓN COMPLETADA CON ÉXITO!
echo La web se actualizará automáticamente en unos minutos.
echo ===================================================
echo.
pause
