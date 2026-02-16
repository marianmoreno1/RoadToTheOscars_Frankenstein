"""
Script para capturar el HTML de Rotten Tomatoes y analizarlo
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os

def capturar_html():
    """Captura el HTML de una página de reseñas"""
    
    # Configurar Chrome
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Comentado para ver qué pasa
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # URL de prueba
    url = 'https://www.rottentomatoes.com/m/frankenstein_2025/reviews?type=user'
    
    print(f"Cargando: {url}")
    driver.get(url)
    
    print("Esperando 10 segundos para que cargue todo...")
    time.sleep(10)
    
    # Hacer scroll
    print("Haciendo scroll...")
    for i in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    # Guardar HTML
    output_path = "/Users/allende/Desktop/5 ICAI /Segundo cuatri/Analítica Social y de la Web /Trabajo Práctico /Datos/Rotten Tomatoes"
    html_file = os.path.join(output_path, 'RT_HTML_CAPTURA.html')
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    
    print(f"\n✓ HTML guardado en: {html_file}")
    print("\nPor favor, abre ese archivo y envíamelo para analizar la estructura.")
    
    driver.quit()

if __name__ == "__main__":
    capturar_html()