import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GoogleNewsSimpleScraper:
    def __init__(self, output_path):
        self.output_path = output_path
        self.all_articles = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9',
        }
    
    def scrape_google_news_rss(self, query, max_results=50):
        """Extrae noticias usando Google News RSS (más confiable)"""
        articles = []
        
        try:
            logger.info(f"🔍 Buscando: {query}")
            
            # Usar el RSS de Google News (cambiado a región USA)
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            
            response = requests.get(rss_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            logger.info(f"✅ Encontrados {len(items)} artículos en RSS")
            
            for idx, item in enumerate(items[:max_results], 1):
                try:
                    title = item.find('title').text if item.find('title') else "N/A"
                    link = item.find('link').text if item.find('link') else "N/A"
                    pub_date = item.find('pubDate').text if item.find('pubDate') else "N/A"
                    source = item.find('source').text if item.find('source') else "Desconocida"
                    
                    article_data = {
                        "Titular": title,
                        "Fuente": source,
                        "Fecha": pub_date,
                        "URL": link,
                        "Query_Busqueda": query,
                        "Fecha_Extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    articles.append(article_data)
                    
                    if idx % 10 == 0:
                        logger.info(f"   ✓ Procesados {idx} artículos...")
                
                except Exception as e:
                    logger.debug(f"   ✗ Error en artículo {idx}: {e}")
                    continue
            
            logger.info(f"📊 Total extraídos: {len(articles)} artículos\n")
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda '{query}': {e}\n")
        
        return articles
    
    def scrape_multiple_queries(self, queries, max_per_query=50):
        """Scrape múltiples búsquedas"""
        logger.info("="*70)
        logger.info("🚀 INICIANDO EXTRACCIÓN DE GOOGLE NEWS (RSS)")
        logger.info("="*70 + "\n")
        
        for idx, query in enumerate(queries, 1):
            logger.info(f"{'='*70}")
            logger.info(f"🔍 BÚSQUEDA {idx}/{len(queries)}: {query}")
            logger.info(f"{'='*70}\n")
            
            try:
                articles = self.scrape_google_news_rss(query, max_per_query)
                self.all_articles.extend(articles)
                logger.info(f"✅ Completada búsqueda {idx}/{len(queries)}\n")
                time.sleep(2)  # Pausa entre búsquedas
            except Exception as e:
                logger.error(f"❌ Error en búsqueda {idx}: {e}\n")
                continue
        
        # Crear DataFrame y eliminar duplicados
        df = pd.DataFrame(self.all_articles)
        
        if len(df) > 0:
            original_count = len(df)
            df = df.drop_duplicates(subset=["Titular"], keep="first")
            duplicates_removed = original_count - len(df)
            
            logger.info("="*70)
            logger.info("✅ EXTRACCIÓN COMPLETADA")
            logger.info("="*70)
            logger.info(f"   📰 Total artículos extraídos: {original_count}")
            logger.info(f"   🗑️  Duplicados eliminados: {duplicates_removed}")
            logger.info(f"   ✨ Artículos únicos: {len(df)}")
            logger.info(f"   📚 Fuentes únicas: {df['Fuente'].nunique()}")
            
            # Guardar
            df.to_excel(self.output_path, index=False)
            logger.info(f"\n💾 Archivo guardado en: {self.output_path}")
            
            return df
        else:
            logger.warning("\n❌ No se encontraron noticias")
            return pd.DataFrame()


if __name__ == "__main__":
    # Configuración
    output_path = "/Users/allende/Desktop/5 ICAI /Segundo cuatri/Analítica Social y de la Web /Trabajo Práctico /IMDB Y ROTTENTOMATOES/Frankenstein_Google_News_RSS.xlsx"
    
    # Queries de búsqueda en inglés (enfocadas a USA/Oscars)
    queries = [
        "Frankenstein 2025 movie Guillermo del Toro",
        "Frankenstein Jacob Elordi Oscar nomination",
        "Frankenstein Netflix awards season",
        "Frankenstein Venice Film Festival reviews",
        "Guillermo del Toro Frankenstein Academy Awards",
        "Frankenstein 2025 box office performance",
        "Frankenstein movie awards predictions",
        "Frankenstein del Toro critical reception"
    ]
    
    # Crear scraper y ejecutar
    scraper = GoogleNewsSimpleScraper(output_path)
    df_news = scraper.scrape_multiple_queries(queries, max_per_query=100)
    
    # Mostrar muestra de resultados
    if len(df_news) > 0:
        print("\n" + "="*70)
        print("📰 MUESTRA DE RESULTADOS (primeros 10)")
        print("="*70)
        print(df_news[['Titular', 'Fuente', 'Fecha']].head(10))
        print("\n" + "="*70)
        print("📊 DISTRIBUCIÓN POR FUENTE")
        print("="*70)
        print(df_news['Fuente'].value_counts().head(10))