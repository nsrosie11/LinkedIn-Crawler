import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import random
import json
import urllib.parse
import logging
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

class SalesNavigatorScraper:
    def __init__(self, email, password, connect_note=None, progress_queue=None, template_name=None, lead_limit=None):
        self.email = email
        self.password = password
        self.driver = None
        self.leads_data = []
        self.connect_note = connect_note or "Hi! I'd love to connect and learn more about your work."
        self.progress_queue = progress_queue
        self.template_name = template_name
        self.lead_limit = lead_limit  # Add lead limit parameter
        self.setup_logging()
        self.is_running = True

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('linkedin_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def report_progress(self, message, status='info', data=None):
        if self.progress_queue:
            progress = {
                'message': message,
                'status': status,
                'data': data,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.progress_queue.put(progress)
        self.logger.info(message)

    # --- INI ADALAH FUNGSI setup_driver YANG SUDAH DIPERBAIKI ---
    def setup_driver(self):
        """Menginisialisasi WebDriver menggunakan webdriver-manager untuk mengunduh driver yang kompatibel."""
        try:
            # Menggunakan opsi dari kode Anda sebelumnya, yang baik untuk menghindari deteksi
            options = Options()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Baris di bawah ini adalah perbaikan utamanya!
            # Ini akan secara otomatis mengunduh dan mengatur ChromeDriver yang benar.
            service = Service(ChromeDriverManager().install())
            
            # Menginisialisasi driver dengan service yang sudah diatur
            self.driver = webdriver.Chrome(service=service, options=options)
            
            self.report_progress("Driver berhasil diatur!", 'success')
            return True
        except Exception as e:
            self.report_progress(f"Gagal mengatur driver: {str(e)}", 'error')
            return False
    # --- AKHIR FUNGSI setup_driver YANG SUDAH DIPERBAIKI ---
    
    def direct_access_and_connect(self, search_url, action='connect'):
        try:
            if not self.setup_driver():
                print("Gagal menyiapkan driver, keluar...")
                return
            
            # Try to access the search URL directly
            self.driver.get(search_url)
            time.sleep(random.uniform(2, 4))
            
            # Check if we need to login
            if "login" in self.driver.current_url.lower():
                print("Login diperlukan, melanjutkan dengan login...")
                self.login_to_sales_navigator()
                # After login, navigate back to search URL
                self.driver.get(search_url)
                time.sleep(random.uniform(2, 4))
            
            page = 1
            while self.is_running:  # Modified while loop to check running state
                self.report_progress(f"Memproses halaman {page}")
                
                self.extract_leads_from_page(action)
                
                if not self.is_running:
                    break
                
                # Try to move to next page
                try:
                    next_button = self.driver.find_element(By.CLASS_NAME, "search-results__pagination-next-button")
                    if not next_button.is_enabled():
                        break
                    next_button.click()
                    time.sleep(random.uniform(2, 4))
                    page += 1
                except Exception as e:
                    self.report_progress("Tidak ada halaman lagi untuk diproses", 'info')
                    break
                    
        except Exception as e:
            self.report_progress(f"Error dalam crawler: {str(e)}", 'error')
        finally:
            if self.driver:
                self.driver.quit()

    def login_to_sales_navigator(self):
        self.driver.get('https://www.linkedin.com/sales')
        time.sleep(random.uniform(2, 4))
        
        # Check if already logged in by looking for common Sales Navigator elements
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-global-typeahead__input"))
            )
            self.report_progress("Sudah masuk, melewati proses login")
            return
        except TimeoutException:
            self.report_progress("Tidak ada sesi aktif yang ditemukan, melanjutkan dengan login")
            
        # Proceed with login if needed
        self.driver.get('https://www.linkedin.com/login')
        time.sleep(random.uniform(2, 4))
        
        email_field = self.driver.find_element(By.ID, 'username')
        password_field = self.driver.find_element(By.ID, 'password')
        
        self.type_like_human(email_field, self.email)
        self.type_like_human(password_field, self.password)
        
        password_field.submit()
        time.sleep(5)
        
    def type_like_human(self, element, text):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15)) 

    def scrape_search_results(self, search_url):
        try:
            if not self.setup_driver():
                print("Gagal menyiapkan driver, keluar...")
                return
                
            self.login_to_sales_navigator()
            
            # Navigate to the search URL
            self.driver.get(search_url)
            time.sleep(random.uniform(3, 5))
            
            page = 1
            while True:
                print(f"Mengambil data dari halaman {page}")
                
                # Extract leads from current page
                page_leads = self.extract_leads_from_page()
                self.leads_data.extend(page_leads)
                
                # Save progress after each page
                self.save_leads_to_file()
                
                # Try to click next page button
                try:
                    next_button = self.driver.find_element(By.CLASS_NAME, "search-results__pagination-next-button")
                    if not next_button.is_enabled():
                        break
                    next_button.click()
                    time.sleep(random.uniform(3, 5))
                    page += 1
                except:
                    break
                    
        finally:
            self.driver.quit()
            
    def save_leads_to_file(self):
        try:
            # Create db directory if it doesn't exist
            os.makedirs(os.path.join('/Users/dani/Documents/web/linkedin-crawler/db'), exist_ok=True)
            
            # Save to main leads_data.json
            self._save_to_main_file()
            
            # Save to daily template file if template name is provided
            if self.template_name:
                self._save_to_daily_template_file()
                
        except Exception as e:
            self.report_progress(f"Error menyimpan leads ke file: {str(e)}", 'error')
            
    def _save_to_main_file(self):
        try:
            main_file_path = os.path.join('/Users/dani/Documents/web/linkedin-crawler/db', 'leads_data.json')
            
            # Load existing data if file exists
            existing_data = []
            if os.path.exists(main_file_path):
                try:
                    with open(main_file_path, 'r') as f:
                        existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []
            
            # Create a set of existing profile URLs to check for duplicates
            existing_urls = {lead.get('profile_url') for lead in existing_data if lead.get('profile_url')}
            
            # Only add new leads that don't exist in the file
            new_leads = []
            for lead in self.leads_data:
                if lead.get('profile_url') and lead['profile_url'] not in existing_urls:
                    new_leads.append(lead)
                    existing_urls.add(lead['profile_url'])
            
            # Merge only new leads with existing data
            if isinstance(existing_data, list):
                existing_data.extend(new_leads)
            else:
                existing_data = new_leads
            
            # Write the combined data back to file
            with open(main_file_path, 'w') as f:
                json.dump(existing_data, f, indent=2)
                f.flush()
                
            self.report_progress(f"Berhasil menyimpan {len(new_leads)} leads baru ke file utama", 'success')
            
        except Exception as e:
            self.report_progress(f"Error saat menyimpan ke file utama: {str(e)}", 'error')
            
    def _save_to_daily_template_file(self):
        try:
            # Generate daily template filename in db folder
            today = time.strftime('%Y-%m-%d')
            daily_filename = os.path.join('/Users/dani/Documents/web/linkedin-crawler/db', f'{today}-{self.template_name}.json')
            
            # Load existing daily data if file exists
            daily_data = []
            if os.path.exists(daily_filename):
                try:
                    with open(daily_filename, 'r') as f:
                        daily_data = json.load(f)
                except json.JSONDecodeError:
                    daily_data = []
            
            # Create a set of existing profile URLs for the day
            daily_urls = {lead.get('profile_url') for lead in daily_data if lead.get('profile_url')}
            
            # Only add new leads that don't exist in today's file
            new_daily_leads = []
            for lead in self.leads_data:
                if lead.get('profile_url') and lead['profile_url'] not in daily_urls:
                    new_daily_leads.append(lead)
                    daily_urls.add(lead['profile_url'])
            
            # Merge new leads with existing daily data
            if isinstance(daily_data, list):
                daily_data.extend(new_daily_leads)
            else:
                daily_data = new_daily_leads
            
            # Write the combined data to daily file
            with open(daily_filename, 'w') as f:
                json.dump(daily_data, f, indent=2)
                f.flush()
                
            self.report_progress(f"Berhasil menyimpan {len(new_daily_leads)} leads baru ke file template harian", 'success')
            
        except Exception as e:
            self.report_progress(f"Error saat menyimpan ke file template harian: {str(e)}", 'error')
    
    def direct_access_and_connect(self, search_url):
        try:
            if not self.setup_driver():
                print("Gagal menyiapkan driver, keluar...")
                return
            
            # Try to access the search URL directly
            self.driver.get(search_url)
            time.sleep(random.uniform(2, 4))
            
            # Check if we need to login
            if "login" in self.driver.current_url.lower():
                print("Login diperlukan, melanjutkan dengan login...")
                self.login_to_sales_navigator()
                # After login, navigate back to search URL
                self.driver.get(search_url)
                time.sleep(random.uniform(2, 4))
            
            page = 1
            while True and self.is_running:
                print(f"\nMemproses halaman {page}")
                
                # Check if we've reached the lead limit before processing the page
                if self.lead_limit and len(self.leads_data) >= self.lead_limit:
                    self.report_progress(f"Mencapai batas leads {self.lead_limit}. Menghentikan crawler...", 'info')
                    self.is_running = False
                    break
                    
                # Extract leads from current page
                self.extract_leads_from_page()
                
                # Check again after processing the page
                if not self.is_running:
                    break
                
                # Try to move to next page
                try:
                    next_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Next']")
                    if not next_button.is_enabled():
                        print("Mencapai halaman terakhir, menghentikan...")
                        break
                    next_button.click()
                    print(f"Pindah ke halaman {page + 1}")
                    time.sleep(random.uniform(3, 5))
                    page += 1
                except Exception as e:
                    print("Tidak ada halaman lagi yang tersedia")
                    break
                
        finally:
            if self.driver:
                self.driver.quit()

    def extract_leads_from_page(self):
        leads = []
        try:
            # Wait for the search results container to load
            container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search-results-container"))
            )
            
            # Scroll the container down in smaller increments
            last_height = container.get_attribute("scrollHeight")
            while True:
                # Scroll down in increments
                for i in range(3):
                    self.driver.execute_script(
                        f"document.getElementById('search-results-container').scrollTop = {(i + 1) * (int(last_height)/3)}"
                    )
                    time.sleep(1)
                
                # Wait for new content
                time.sleep(5)
                
                # Calculate new scroll height
                new_height = container.get_attribute("scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Scroll back to top
            self.driver.execute_script("document.getElementById('search-results-container').scrollTop = 0")
            time.sleep(random.uniform(1, 2))
            
            # Find all lead cards using li elements within the container's ol
            lead_cards = container.find_element(By.TAG_NAME, "ol").find_elements(By.TAG_NAME, "li")
            
            # Process each lead card one by one
            for index, card in enumerate(lead_cards):
                # Check if we've reached the lead limit
                if self.lead_limit and len(self.leads_data) >= self.lead_limit:
                    self.report_progress(f"Mencapai batas leads {self.lead_limit}. Menghentikan crawler...", 'info')
                    self.is_running = False
                    return leads

                try:
                    # Get lead name and profile URL using the new selector
                    lead_name_element = card.find_element(By.CSS_SELECTOR, '[data-view-name="search-results-lead-name"]')
                    lead_name = lead_name_element.text
                    profile_url = lead_name_element.get_attribute('href')
                    
                    self.report_progress(f"Memproses lead {lead_name} {index + 1} dari {len(lead_cards)} {profile_url}")

                    # Connect flow
                    three_dot_button = card.find_element(By.XPATH, ".//button[contains(@aria-label, 'more actions')]")
                    three_dot_button.click()
                    time.sleep(random.uniform(1, 2))
                    
                    # Find and click the Connect button
                    connect_button = self.driver.find_element(By.XPATH, "//button[normalize-space()='Connect' or contains(normalize-space(), 'Connect')]")
                    if not connect_button.is_enabled():
                        self.report_progress("Tombol 'Connect' tidak dapat diklik, pindah ke lead berikutnya...", 'error')
                        continue
                        
                    connect_button.click()
                    time.sleep(random.uniform(1, 2))
                    
                    try:
                        note_field = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.ID, "connect-cta-form__invitation"))
                        )
                        
                        # Normalize lead name - capitalize first letter of each word
                        normalized_name = ' '.join(word.capitalize() for word in lead_name.lower().split())
                        
                        # Replace [lead_name] with normalized name if it exists in the note
                        personalized_note = self.connect_note.replace('[lead_name]', normalized_name) if '[lead_name]' in self.connect_note else self.connect_note
                        self.type_like_human(note_field, personalized_note)
                        
                        # Find and click the Send button
                        send_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.CLASS_NAME, "connect-cta-form__send"))
                        )
                        if not send_button.is_enabled():
                            self.report_progress("Tombol 'Kirim' tidak dapat diklik, pindah ke lead berikutnya...", 'error')
                            continue
                            
                        send_button.click()
                        self.report_progress(f"Permintaan koneksi dikirim untuk lead {index + 1} {lead_name}", 'success')
                        time.sleep(random.uniform(2, 3))
                        
                        # Update lead data with the new selectors
                        lead_data = {
                            'name': lead_name,
                            'profile_url': profile_url,
                            'connection_status': 'success',
                            'note_sent': personalized_note,  # Store the personalized note
                            'search_url': self.driver.current_url
                        }
                        
                        self.report_progress(f"Berhasil terhubung dengan: {lead_data['name']}", 'success', lead_data)
                        
                    except TimeoutException:
                        self.report_progress("Tidak dapat menemukan kolom catatan atau formulir tertutup, melanjutkan ke lead berikutnya...", 'error')
                        continue
                    except Exception as e:
                        self.report_progress(f"Error dalam alur koneksi: {str(e)}, pindah ke lead berikutnya...", 'error')
                        continue
                    
                    leads.append(lead_data)
                    
                    # Save progress after each lead
                    self.leads_data.append(lead_data)
                    self.save_leads_to_file()
                    self.report_progress(f"Data lead disimpan: {lead_data['name']} - {lead_data['profile_url']} ({len(self.leads_data)}/{self.lead_limit if self.lead_limit else 'unlimited'})", 'success')
                    
                except Exception as e:
                    self.report_progress(f"Error memproses lead {index + 1}: {str(e)}", 'error')
                    continue
                    
        except Exception as e:
            self.report_progress(f"Error memproses halaman: {str(e)}", 'error')
            
        return leads

    def stop(self):
        """Menghentikan crawler dengan baik"""
        self.is_running = False
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.report_progress(f"Error menghentikan driver: {str(e)}", 'error')
