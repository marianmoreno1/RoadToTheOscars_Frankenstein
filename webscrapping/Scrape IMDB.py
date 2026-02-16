import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FrankensteinScraper:
    def __init__(self):
        self.driver = None
        self.output_path = "/Users/allende/Desktop/5 ICAI /Segundo cuatri/Analítica Social y de la Web /Trabajo Práctico /IMDB Y ROTTENTOMATOES/frankenstein_reviews.xlsx"
        
    def setup_driver(self):
        """Configura el driver de Selenium"""
        logger.info("Configurando el driver de Selenium...")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Ejecutar en segundo plano
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        logger.info("Driver configurado correctamente")
        
    def scrape_imdb(self, url):
        """Extrae información de IMDB"""
        logger.info(f"Iniciando scraping de IMDB: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Extraer información básica
            movie_data = {}
            
            try:
                movie_data['Título'] = self.driver.find_element(By.CSS_SELECTOR, 'h1[data-testid="hero__pageTitle"]').text
                logger.info(f"Título encontrado: {movie_data['Título']}")
            except:
                movie_data['Título'] = "N/A"
                logger.warning("No se pudo encontrar el título")
            
            try:
                movie_data['Año'] = self.driver.find_element(By.CSS_SELECTOR, 'a[href*="releaseinfo"]').text
            except:
                movie_data['Año'] = "N/A"
                
            try:
                movie_data['Rating'] = self.driver.find_element(By.CSS_SELECTOR, 'div[data-testid="hero-rating-bar__aggregate-rating__score"] span').text
            except:
                movie_data['Rating'] = "N/A"
                
            try:
                movie_data['Num_Votos'] = self.driver.find_element(By.CSS_SELECTOR, 'div[data-testid="hero-rating-bar__aggregate-rating__score"] + div').text
            except:
                movie_data['Num_Votos'] = "N/A"
            
            # Ir a la página de reseñas
            reviews_data = []
            try:
                reviews_url = url.replace('?ref_=nv_sr_srsg_1_tt_7_nm_0_in_0_q_frankens', '') + 'reviews'
                logger.info(f"Navegando a reseñas: {reviews_url}")
                self.driver.get(reviews_url)
                time.sleep(3)
                
                # Cargar más reseñas
                load_more_count = 0
                max_loads = 50  # Aproximadamente 1000 reseñas (20 por carga)
                
                while load_more_count < max_loads:
                    try:
                        load_more_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.ipc-see-more__button, button[data-testid="load-more-trigger"]'))
                        )
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", load_more_button)
                        time.sleep(1)
                        self.driver.execute_script("arguments[0].click();", load_more_button)
                        load_more_count += 1
                        logger.info(f"Cargadas {(load_more_count + 1) * 25} reseñas aproximadamente...")
                        time.sleep(2)
                    except TimeoutException:
                        logger.info("No hay más reseñas para cargar o botón no disponible")
                        break
                    except Exception as e:
                        logger.warning(f"Error al cargar más reseñas: {e}")
                        break
                
                # Extraer reseñas
                reviews = self.driver.find_elements(By.CSS_SELECTOR, 'div.ipc-list-card__content')
                logger.info(f"Encontradas {len(reviews)} reseñas en total")
                
                for idx, review in enumerate(reviews[:1000], 1):
                    try:
                        review_dict = {}
                        
                        try:
                            # Expandir reseña si está colapsada
                            expand_button = review.find_element(By.CSS_SELECTOR, 'button.ipc-overflowText-overlay')
                            self.driver.execute_script("arguments[0].click();", expand_button)
                            time.sleep(0.3)
                        except:
                            pass
                        
                        try:
                            # El autor está en el URL de la reseña
                            author_link = review.find_element(By.CSS_SELECTOR, 'a.ipc-title-link-wrapper')
                            review_url = author_link.get_attribute('href')
                            # Extraer ID de usuario del URL si es posible
                            review_dict['URL_Reseña'] = review_url
                        except:
                            review_dict['URL_Reseña'] = "N/A"
                        
                        try:
                            review_dict['Rating_Usuario'] = review.find_element(By.CSS_SELECTOR, 'span.ipc-rating-star--rating').text
                        except:
                            review_dict['Rating_Usuario'] = "N/A"
                        
                        try:
                            review_dict['Título_Reseña'] = review.find_element(By.CSS_SELECTOR, 'h3.ipc-title__text').text
                        except:
                            review_dict['Título_Reseña'] = "N/A"
                        
                        try:
                            review_dict['Texto'] = review.find_element(By.CSS_SELECTOR, 'div.ipc-html-content-inner-div').text
                        except:
                            review_dict['Texto'] = "N/A"
                        
                        reviews_data.append(review_dict)
                        
                        if idx % 50 == 0:
                            logger.info(f"Procesadas {idx} reseñas de IMDB...")
                            
                    except Exception as e:
                        logger.warning(f"Error procesando reseña {idx}: {e}")
                        continue
                
                logger.info(f"Total de reseñas extraídas de IMDB: {len(reviews_data)}")
                
            except Exception as e:
                logger.error(f"Error al extraer reseñas de IMDB: {e}")
            
            return movie_data, reviews_data
            
        except Exception as e:
            logger.error(f"Error general en scraping de IMDB: {e}")
            return {}, []
    
    def scrape_rotten_tomatoes(self, url):
        """Extrae información de Rotten Tomatoes"""
        logger.info(f"Iniciando scraping de Rotten Tomatoes: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(4)
            
            # Extraer información básica
            movie_data = {}
            
            try:
                movie_data['Título'] = self.driver.find_element(By.CSS_SELECTOR, 'h1[data-qa="score-panel-movie-title"]').text
                logger.info(f"Título encontrado: {movie_data['Título']}")
            except:
                try:
                    movie_data['Título'] = self.driver.find_element(By.CSS_SELECTOR, 'h1').text
                except:
                    movie_data['Título'] = "N/A"
                logger.warning("No se pudo encontrar el título")
            
            try:
                movie_data['Tomatometer'] = self.driver.find_element(By.CSS_SELECTOR, 'rt-button[slot="criticsScore"]').get_attribute('percentage')
            except:
                movie_data['Tomatometer'] = "N/A"
            
            try:
                movie_data['Audience_Score'] = self.driver.find_element(By.CSS_SELECTOR, 'rt-button[slot="audienceScore"]').get_attribute('percentage')
            except:
                movie_data['Audience_Score'] = "N/A"
            
            # Extraer reseñas de audiencia
            reviews_data = []
            
            try:
                # Ir a la sección de reseñas de audiencia
                reviews_url = url + '/reviews?type=user'
                logger.info(f"Navegando a reseñas de audiencia: {reviews_url}")
                self.driver.get(reviews_url)
                time.sleep(3)
                
                # Cargar más reseñas
                load_more_count = 0
                max_loads = 50  # Intentar cargar hasta 1000 reseñas
                
                while load_more_count < max_loads:
                    try:
                        # Scroll hasta el final para cargar más reseñas
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        
                        # Buscar el botón "Load More" o similar
                        load_more_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//rt-button[contains(text(), 'Load More') or contains(text(), 'Ver más')]"))
                        )
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", load_more_button)
                        time.sleep(1)
                        self.driver.execute_script("arguments[0].click();", load_more_button)
                        load_more_count += 1
                        logger.info(f"Cargadas más reseñas ({load_more_count} veces)...")
                        time.sleep(2)
                    except TimeoutException:
                        logger.info("No hay más reseñas para cargar en Rotten Tomatoes")
                        break
                    except Exception as e:
                        logger.warning(f"Error al cargar más reseñas: {e}")
                        break
                
                # Extraer reseñas
                reviews = self.driver.find_elements(By.CSS_SELECTOR, 'review-card[slot="tile"]')
                logger.info(f"Encontradas {len(reviews)} reseñas de audiencia en total")
                
                for idx, review in enumerate(reviews[:1000], 1):
                    try:
                        review_dict = {}
                        
                        try:
                            review_dict['Autor'] = review.find_element(By.CSS_SELECTOR, 'rt-link[slot="name"]').text
                        except:
                            review_dict['Autor'] = "N/A"
                        
                        try:
                            review_dict['Fecha'] = review.find_element(By.CSS_SELECTOR, 'span[slot="timestamp"]').text
                        except:
                            review_dict['Fecha'] = "N/A"
                        
                        try:
                            rating_elem = review.find_element(By.CSS_SELECTOR, 'rating-stars-group[slot="rating"]')
                            review_dict['Rating_Usuario'] = rating_elem.get_attribute('score')
                        except:
                            review_dict['Rating_Usuario'] = "N/A"
                        
                        try:
                            # Intentar expandir la reseña si tiene botón "See more"
                            try:
                                see_more = review.find_element(By.CSS_SELECTOR, 'rt-link[slot="reviewLink"]')
                                # No hacemos click, solo tomamos el texto visible
                            except:
                                pass
                            
                            review_dict['Texto'] = review.find_element(By.CSS_SELECTOR, 'drawer-more[slot="review"] span[slot="content"]').text
                        except:
                            review_dict['Texto'] = "N/A"
                        
                        try:
                            # Verificar si es usuario verificado
                            is_verified = review.get_attribute('verified-review')
                            review_dict['Verificado'] = "Sí" if is_verified == "" or is_verified else "No"
                        except:
                            review_dict['Verificado'] = "N/A"
                        
                        reviews_data.append(review_dict)
                        
                        if idx % 50 == 0:
                            logger.info(f"Procesadas {idx} reseñas de Rotten Tomatoes...")
                            
                    except Exception as e:
                        logger.warning(f"Error procesando reseña {idx}: {e}")
                        continue
                
                logger.info(f"Total de reseñas extraídas de Rotten Tomatoes: {len(reviews_data)}")
                
            except Exception as e:
                logger.error(f"Error al extraer reseñas de Rotten Tomatoes: {e}")
            
            return movie_data, reviews_data
            
        except Exception as e:
            logger.error(f"Error general en scraping de Rotten Tomatoes: {e}")
            return {}, []
    
    def save_to_excel(self, imdb_data, rt_data):
        """Guarda los datos en Excel con dos hojas"""
        logger.info("Guardando datos en Excel...")
        
        try:
            with pd.ExcelWriter(self.output_path, engine='openpyxl') as writer:
                # Hoja de IMDB
                if imdb_data[1]:  # Si hay reseñas
                    df_imdb = pd.DataFrame(imdb_data[1])
                    df_imdb.insert(0, 'Fuente', 'IMDB')
                    df_imdb.to_excel(writer, sheet_name='IMDB', index=False)
                    logger.info(f"Hoja IMDB creada con {len(df_imdb)} reseñas")
                else:
                    pd.DataFrame({'Error': ['No se pudieron extraer reseñas']}).to_excel(writer, sheet_name='IMDB', index=False)
                
                # Hoja de Rotten Tomatoes
                if rt_data[1]:  # Si hay reseñas
                    df_rt = pd.DataFrame(rt_data[1])
                    df_rt.insert(0, 'Fuente', 'Rotten Tomatoes')
                    df_rt.to_excel(writer, sheet_name='Rotten Tomatoes', index=False)
                    logger.info(f"Hoja Rotten Tomatoes creada con {len(df_rt)} reseñas")
                else:
                    pd.DataFrame({'Error': ['No se pudieron extraer reseñas']}).to_excel(writer, sheet_name='Rotten Tomatoes', index=False)
            
            logger.info(f"Archivo guardado exitosamente en: {self.output_path}")
            
        except Exception as e:
            logger.error(f"Error al guardar el archivo Excel: {e}")
    
    def run(self):
        """Ejecuta el scraping completo"""
        try:
            self.setup_driver()
            
            # URLs
            imdb_url = "https://www.imdb.com/es-es/title/tt1312221/?ref_=nv_sr_srsg_1_tt_7_nm_0_in_0_q_frankens"
            rt_url = "https://www.rottentomatoes.com/m/frankenstein_2025"
            
            # Scraping IMDB
            logger.info("="*50)
            logger.info("INICIANDO SCRAPING DE IMDB")
            logger.info("="*50)
            imdb_movie, imdb_reviews = self.scrape_imdb(imdb_url)
            
            # Scraping Rotten Tomatoes
            logger.info("="*50)
            logger.info("INICIANDO SCRAPING DE ROTTEN TOMATOES")
            logger.info("="*50)
            rt_movie, rt_reviews = self.scrape_rotten_tomatoes(rt_url)
            
            # Guardar en Excel
            logger.info("="*50)
            logger.info("GUARDANDO RESULTADOS")
            logger.info("="*50)
            self.save_to_excel((imdb_movie, imdb_reviews), (rt_movie, rt_reviews))
            
            logger.info("="*50)
            logger.info("PROCESO COMPLETADO EXITOSAMENTE")
            logger.info(f"Reseñas IMDB: {len(imdb_reviews)}")
            logger.info(f"Reseñas Rotten Tomatoes: {len(rt_reviews)}")
            logger.info("="*50)
            
        except Exception as e:
            logger.error(f"Error en la ejecución principal: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Driver cerrado")

if __name__ == "__main__":
    scraper = FrankensteinScraper()
    scraper.run()