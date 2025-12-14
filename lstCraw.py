import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup Chrome
options = Options()
# --- 1. CẤU HÌNH ---
search_query = "Nhà hàng đường Nguyễn Huệ, Quận 1" # Từ khóa tìm kiếm

options = Options()
# options.add_argument('headless') # Tắt headless để xem trình duyệt chạy và tránh bị chặn
options.add_argument("--lang=vi")  # Giả lập tiếng Việt

browser = webdriver.Chrome(options=options)
wait = WebDriverWait(browser, 10)

def scrape_list():
    try:
        browser.get("https://www.google.com/maps")
        
        # --- 2. TÌM KIẾM ---
        print(f"Đang tìm kiếm: {search_query}")
        # Tìm ô input search
        search_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
        search_box.clear()
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.ENTER) # Nhấn Enter
        
        time.sleep(3) # Chờ kết quả tải ra

        # --- 3. CUỘN DANH SÁCH KẾT QUẢ (QUAN TRỌNG) ---
        # Google Maps chứa kết quả trong một thẻ div có role="feed"
        print("Đang cuộn để tải danh sách...")
        
        # Tìm thẻ div chứa danh sách (thường có role='feed')
        feed_element = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@role, "feed")]')))
        
        # Logic cuộn: Cuộn xuống, chờ tải, kiểm tra xem đã hết chưa
        last_height = browser.execute_script("return arguments[0].scrollHeight", feed_element)
        
        while True:
            # Cuộn xuống cuối thẻ feed
            browser.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed_element)
            time.sleep(2) # Chờ Google tải thêm địa điểm
            
            # Kiểm tra chiều cao mới
            new_height = browser.execute_script("return arguments[0].scrollHeight", feed_element)
            
            # Kiểm tra xem có hiển thị thông báo "Bạn đã xem hết" chưa (Css class: m6QErb tLjsW eK4R0e)
            # Hoặc đơn giản là so sánh chiều cao scroll
            if new_height == last_height:
                print("Đã cuộn hết danh sách (hoặc Google ngừng tải).")
                break
            last_height = new_height

        # --- 4. LẤY DỮ LIỆU TỪNG THẺ ---
        # Mỗi địa điểm nằm trong thẻ div có class chứa 'Nv2PK'
        items = browser.find_elements(By.CLASS_NAME, "Nv2PK")
        print(f"--> Tìm thấy tổng cộng {len(items)} địa điểm.")
        results = []

        for item in items:
            try:
                # Tìm thẻ <a> chứa link (thẻ này bao trùm cả khối, class thường là 'hfpxzc')
                link_element = item.find_element(By.CLASS_NAME, "hfpxzc")
                link = link_element.get_attribute("href")
                name = link_element.get_attribute("aria-label") # Tên thường nằm trong aria-label
                
                # Lấy đánh giá (Rating) - Class: MW4etd
                try:
                    rating = item.find_element(By.CLASS_NAME, "MW4etd").text
                except:
                    rating = "N/A"
                
                try:
                    number_of_reviews = item.find_element(By.CLASS_NAME, "UY7F9").text
                except:
                    number_of_reviews = "N/A"
                
                clean_text_rating = rating.strip("()").replace(",", ".")
                number_rating = float(clean_text_rating)
                
                clean_text_reviews = number_of_reviews.strip("()").replace('.', '')
                number_of_reviews = int(clean_text_reviews)

                if number_rating <= 4.5 and number_of_reviews >= 50:
                    # Lưu vào danh sách
                    data = {
                        "Tên": name,
                        "Đánh giá": rating,
                        "Link Google Map": link,
                        "Số đánh giá": number_of_reviews
                    }
                    results.append(data)
                    print(f"Đã lấy: {name} ({rating})")
                else:
                    print(f"Bỏ qua: {name} ({rating}, {number_of_reviews} đánh giá)")
            except Exception as e:
                print("Bỏ qua 1 địa điểm lỗi:", e)

        # --- 5. XUẤT RA CSV ---
        keys = results[0].keys()
        with open('danh_sach_nha_hang.csv', 'w', newline='', encoding='utf-8-sig') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(results)
            print("\nĐã lưu file danh_sach_nha_hang.csv thành công!")

    except Exception as e:
        print("Lỗi chương trình:", e)
    finally:
        browser.quit()

if __name__ == "__main__":
    scrape_list()