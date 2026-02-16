"""
Scraper para SOLO Top Critics - Con progreso visible
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import os
from datetime import datetime

class TopCriticsScraper:
    def __init__(self, output_path):
        self.output_path = output_path
        self.driver = None
        
    def setup_driver(self):
        """Configura Chrome"""
        chrome_options = Options()
        # chrome_options.add_argument('--headless=new')  # Comentado para VER qué pasa
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(60)
        self.driver.implicitly_wait(10)
        
        print("  ✓ Chrome configurado (visible)")
    
    def click_load_more_button(self):
        """Clickea el botón Load More dentro de Shadow DOM"""
        try:
            script = """
            const allElements = document.querySelectorAll('*');
            for (let el of allElements) {
                if (el.shadowRoot) {
                    const shadowButton = el.shadowRoot.querySelector('button');
                    if (shadowButton) {
                        const text = shadowButton.textContent.trim().toUpperCase();
                        if (text.includes('LOAD MORE') || text.includes('SHOW MORE')) {
                            shadowButton.click();
                            return true;
                        }
                    }
                }
            }
            const normalButtons = document.querySelectorAll('button, rt-button');
            for (let btn of normalButtons) {
                const text = btn.textContent.trim().toUpperCase();
                if (text.includes('LOAD MORE') || text.includes('SHOW MORE')) {
                    btn.click();
                    return true;
                }
            }
            return false;
            """
            return self.driver.execute_script(script)
        except:
            return False
    
    def scroll_and_load_all(self, max_clicks=40):
        """Scroll y clic hasta cargar todas las reseñas"""
        print(f"  🔄 Cargando reseñas (máximo {max_clicks} clics)...")
        
        buttons_clicked = 0
        no_change_streak = 0
        scrolls = 0
        last_count = 0
        
        while no_change_streak < 5 and buttons_clicked < max_clicks:
            # Scroll
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Intentar clickear
            if buttons_clicked < max_clicks:
                if self.click_load_more_button():
                    buttons_clicked += 1
                    print(f"    ✓ Clic #{buttons_clicked}/{max_clicks}")
                    time.sleep(3)
                    no_change_streak = 0
            
            # Contar
            try:
                reviews = self.driver.find_elements(By.TAG_NAME, "review-card")
                current_count = len(reviews)
            except:
                current_count = 0
            
            scrolls += 1
            
            if current_count > last_count:
                print(f"    → {current_count} reseñas (+{current_count - last_count})")
                last_count = current_count
                no_change_streak = 0
            else:
                no_change_streak += 1
        
        print(f"  ✅ {last_count} elementos cargados ({buttons_clicked} clics)")
        return last_count
    
    def extract_reviews(self):
        """Extrae Top Critics"""
        url = 'https://www.rottentomatoes.com/m/frankenstein_2025/reviews/top-critics'
        
        print(f"\n{'='*80}")
        print(f"📋 EXTRAYENDO: Top Critics")
        print(f"{'='*80}")
        print(f"URL: {url}\n")
        
        self.driver.get(url)
        print("⏳ Esperando carga (10s)...")
        time.sleep(10)
        
        # Cargar
        total = self.scroll_and_load_all(max_clicks=40)
        
        if total == 0:
            print("⚠️ No se encontraron elementos review-card")
            return pd.DataFrame()
        
        # Obtener elementos
        reviews = self.driver.find_elements(By.TAG_NAME, "review-card")
        print(f"\n🔍 PROCESANDO {len(reviews)} elementos...")
        print(f"{'='*80}\n")
        
        reviews_data = []
        
        # Procesar TODAS con progreso visible
        for idx, review in enumerate(reviews, 1):
            # Mostrar progreso en CADA reseña
            print(f"  Procesando {idx}/{len(reviews)}...", end='\r')
            
            try:
                review_dict = {'Índice': idx, 'Tipo': 'Top Critics'}
                
                # Autor
                try:
                    elem = review.find_element(By.CSS_SELECTOR, '[slot="name"]')
                    review_dict['Autor'] = elem.text.strip() or 'N/A'
                except:
                    review_dict['Autor'] = 'N/A'
                
                # Publicación
                try:
                    elem = review.find_element(By.CSS_SELECTOR, '[slot="publication"]')
                    review_dict['Publicación'] = elem.text.strip() or 'N/A'
                except:
                    review_dict['Publicación'] = 'N/A'
                
                # Fecha
                try:
                    elem = review.find_element(By.CSS_SELECTOR, '[slot="timestamp"]')
                    review_dict['Fecha'] = elem.text.strip() or 'N/A'
                except:
                    review_dict['Fecha'] = 'N/A'
                
                # Puntuación (para críticos)
                try:
                    container = review.find_element(By.CSS_SELECTOR, '[slot="rating"]')
                    try:
                        score = container.find_element(By.TAG_NAME, "score-icon-critics")
                        sentiment = score.get_attribute("sentiment")
                        rating_text = container.text.strip()
                        
                        if sentiment == "positive":
                            review_dict['Puntuación'] = f"Fresh - {rating_text}" if rating_text else "Fresh"
                        elif sentiment == "negative":
                            review_dict['Puntuación'] = f"Rotten - {rating_text}" if rating_text else "Rotten"
                        else:
                            review_dict['Puntuación'] = rating_text if rating_text else "N/A"
                    except:
                        review_dict['Puntuación'] = 'N/A'
                except:
                    review_dict['Puntuación'] = 'N/A'
                
                # Texto
                try:
                    elem = review.find_element(By.CSS_SELECTOR, '[slot="review"]')
                    text = elem.text.strip() or 'N/A'
                    text = text.replace('Content collapsed.', '').replace('See Less', '').replace('See More', '').strip()
                    review_dict['Texto'] = ' '.join(text.split()) if text else 'N/A'
                except:
                    review_dict['Texto'] = 'N/A'
                
                # Link
                try:
                    elem = review.find_element(By.CSS_SELECTOR, '[slot="reviewLink"]')
                    review_dict['Link'] = elem.get_attribute('href') or 'N/A'
                except:
                    review_dict['Link'] = 'N/A'
                
                # Top Critic
                try:
                    review_dict['Top Critic'] = review.get_attribute('top-critic') or 'false'
                except:
                    review_dict['Top Critic'] = 'false'
                
                reviews_data.append(review_dict)
                
            except Exception as e:
                print(f"\n  ⚠️ Error en reseña #{idx}: {e}")
                continue
        
        # Línea nueva después del progreso
        print()
        
        # Crear DataFrame
        df = pd.DataFrame(reviews_data)
        
        # Filtrar vacías
        if not df.empty:
            mask = (df['Autor'] != 'N/A') | (df['Texto'] != 'N/A')
            df_filtered = df[mask].copy()
            removed = len(df) - len(df_filtered)
            
            print(f"\n✅ {len(df_filtered)} reseñas válidas")
            if removed > 0:
                print(f"🧹 Filtradas {removed} filas vacías")
            
            return df_filtered
        
        return df
    
    def run(self):
        """Ejecuta el scraper"""
        print("\n" + "="*80)
        print("🚀 SCRAPER - SOLO TOP CRITICS")
        print("="*80)
        
        try:
            self.setup_driver()
            
            df = self.extract_reviews()
            
            if not df.empty:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(self.output_path, f'Top_Critics_{timestamp}.xlsx')
                
                df.to_excel(output_file, index=False, engine='openpyxl')
                
                print(f"\n{'='*80}")
                print(f"✅ COMPLETADO")
                print(f"{'='*80}")
                print(f"📊 Reseñas: {len(df)}")
                print(f"📁 Archivo: {output_file}")
                print(f"{'='*80}\n")
            else:
                print("\n⚠️ No se extrajeron reseñas")
                
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Navegador cerrado.\n")


def main():
    output_path = "/Users/allende/Desktop/5 ICAI /Segundo cuatri/Analítica Social y de la Web /Trabajo Práctico /Datos/Rotten Tomatoes"
    os.makedirs(output_path, exist_ok=True)
    
    scraper = TopCriticsScraper(output_path)
    scraper.run()


if __name__ == "__main__":
    main()